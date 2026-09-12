"""CPU contracts the A4 pair-evidence family has to hold before any GPU run."""

from __future__ import annotations

import json

import pytest

from ekg.core.schema import EventNode, EvidenceSpan
from ekg.nodes.encoding import TORCH_AVAILABLE
from ekg.relations.data.maven_ere import TIMEX_EVENT_TYPE, load_maven_ere
from ekg.relations.pair_evidence import (
    A4_ARMS,
    CONFIG_FILE,
    EVIDENCE_BUDGET,
    FULL_ARM,
    LENGTH_MATCHED_ARM,
    NO_CONSTRAINT_ARM,
    REMOVE_CORE_ARM,
    arm_flags,
    counterfactual_sentence_ids,
    document_pair_evidence,
    load_pair_evidence_config,
    necessity_scoreable,
    pair_evidence_config,
    pair_evidence_sidecar,
    sentence_tokens,
    unsupported_cross_sentence_causal,
    validate_a4_arm,
)
from ekg.relations.pairs import candidate_pairs

# Sentence 1 is the only one carrying a cue, so the ranking has something to
# prefer and something to reject; 5 and 6 sit outside every pair's span and are
# what the length-matched control has to draw from.
DOC_TEXT = "\n".join(
    [
        "Rebels attacked the village at dawn.",
        "The raid happened because the harvest failed.",
        "Officials said little that week.",
        "Dozens fled the valley.",
        "Three people died in the hospital.",
        "The valley stayed quiet.",
        "Reporters arrived at the scene the next morning.",
    ]
)


def mention(event_id: str, trigger: str, sent_id: int, *, event_type: str = "Attacking"):
    return EventNode(
        event_id=event_id,
        event_type=event_type,
        doc_id="doc1",
        trigger=trigger,
        trigger_evidence=[
            EvidenceSpan(doc_id="doc1", char_start=0, char_end=len(trigger), sent_id=sent_id,
                         text=trigger)
        ],
    )


NODES = [
    mention("m0", "attacked", 0),
    mention("m1", "raid", 1),
    mention("m1b", "failed", 1, event_type="Failure"),
    mention("m2", "said", 2, event_type="Statement"),
    mention("m3", "fled", 3, event_type="Escaping"),
    mention("m4", "died", 4, event_type="Death"),
]
SENTENCES = sentence_tokens(DOC_TEXT)


def record_for(head_id: str, tail_id: str, nodes=None):
    (record,) = document_pair_evidence(nodes or NODES, DOC_TEXT, [(head_id, tail_id)])
    return record


def test_punctuation_cannot_hide_a_cue() -> None:
    # "because," would never equal "because", and the cue would go unseen.
    assert sentence_tokens("it fell because, later, it rose")[0][2] == "because"


def test_every_candidate_pair_gets_exactly_one_record_in_the_frozen_order(
    fixtures_dir,
) -> None:
    doc = next(iter(load_maven_ere(fixtures_dir / "maven_ere" / "sample_with_text.jsonl")))
    pairs = candidate_pairs(doc)
    records = document_pair_evidence(doc.nodes, doc.doc_text, pairs)

    assert [(r.head_id, r.tail_id) for r in records] == pairs
    sidecar = pair_evidence_sidecar(records, arm=FULL_ARM)
    assert len(sidecar) == len(pairs)
    assert set(sidecar) == {f"{head}::{tail}" for head, tail in pairs}


def test_an_unknown_endpoint_is_an_error_not_a_dropped_candidate() -> None:
    with pytest.raises(ValueError, match="unknown node"):
        document_pair_evidence(NODES, DOC_TEXT, [("m0", "ghost")])


def test_a_mention_without_a_sentence_anchor_cannot_cite_anything() -> None:
    stripped = mention("m9", "vanished", 0)
    stripped.trigger_evidence = []
    with pytest.raises(ValueError, match="no sentence-anchored trigger"):
        document_pair_evidence([*NODES, stripped], DOC_TEXT, [("m0", "m9")])


def test_both_directions_of_a_pair_cite_the_same_sentences() -> None:
    forward = record_for("m0", "m4")
    backward = record_for("m4", "m0")

    # The span between two triggers does not depend on which is the cause, so
    # the two directions must be scored on the same context; if they were not,
    # direction would be confounded with how much text the model saw.
    assert forward.candidates == backward.candidates
    assert forward.selected == backward.selected
    assert forward.substitutes == backward.substitutes
    sidecar = pair_evidence_sidecar([forward, backward], arm=FULL_ARM)
    assert set(sidecar) == {"m0::m4", "m4::m0"}


def test_the_cue_bearing_sentences_between_the_triggers_are_the_ones_cited() -> None:
    record = record_for("m0", "m4")

    assert record.candidates == (0, 1, 2, 3, 4)
    # Sentence 1 wins on its causal cue; with 2 and 3 both cue-free the budget's
    # second slot falls to the one nearer a trigger.
    assert record.selected == (1, 3)
    assert "because" in record.selected_cues
    assert len(record.selected) <= EVIDENCE_BUDGET

    sets = counterfactual_sentence_ids(record, len(SENTENCES), arm=FULL_ARM)
    assert sets["base"] == (0, 1, 2, 3, 4, 5, 6)
    assert sets["masked"] == (0, 2, 4, 5, 6)
    assert sets["retained"] == (0, 1, 3, 4)
    assert necessity_scoreable(record, arm=FULL_ARM)


def test_a_pair_with_nothing_between_it_has_nothing_to_mask() -> None:
    same = record_for("m1", "m1b")
    adjacent = record_for("m0", "m1")

    for record in (same, adjacent):
        assert record.selected == ()
        assert not necessity_scoreable(record, arm=FULL_ARM)
        sets = counterfactual_sentence_ids(record, len(SENTENCES), arm=FULL_ARM)
        # Masking nothing must leave the document untouched rather than quietly
        # dropping a trigger sentence the pooling depends on.
        assert sets["masked"] == sets["base"]
        assert sets["retained"] == record.protected

    # The same-sentence pair still carries the cue its own sentence holds, so it
    # is not counted as an unsupported prediction.
    assert same.protected_cues and same.supported
    assert not adjacent.selected_cues


def test_the_control_cites_matched_length_sentences_from_outside_the_span() -> None:
    record = record_for("m1", "m2")

    assert record.candidates == (1, 2)
    assert record.selected == ()  # nothing between two adjacent sentences
    assert record.substitutes == ()

    spanning = record_for("m0", "m4")
    assert spanning.substitutes_requested == len(spanning.selected)
    # Every substitute must be a sentence the pair does not span, or the control
    # would be intervening on the pair's own evidence.
    assert not set(spanning.substitutes) & set(spanning.candidates)
    # Sentence 1 has 7 tokens and sentence 3 has 4, so the 8-token sentence goes
    # to the first and the 4-token one to the second: matched, not just outside.
    assert spanning.substitutes == (5, 6)


def test_a_document_too_small_to_match_records_the_shortfall() -> None:
    # Three sentences, and the pair spans all of them: no sentence is left to
    # supply a length match. A short control is recorded, never padded.
    nodes = [mention("a", "attacked", 0), mention("b", "died", 2, event_type="Death")]
    text = "It fell.\nIt fell because rain came.\nPeople died."
    (record,) = document_pair_evidence(nodes, text, [("a", "b")])

    assert record.selected == (1,)
    assert record.substitutes == ()
    assert record.substitutes_requested == 1
    assert not necessity_scoreable(record, arm=LENGTH_MATCHED_ARM)


def test_the_control_intervenes_on_its_substitutes_and_not_on_the_evidence() -> None:
    record = record_for("m0", "m4")
    assert record.cited(FULL_ARM) == record.selected
    assert record.cited(LENGTH_MATCHED_ARM) == record.substitutes

    controlled = counterfactual_sentence_ids(record, len(SENTENCES), arm=LENGTH_MATCHED_ARM)
    assert not set(controlled["masked"]) & set(record.substitutes)
    assert set(record.selected) <= set(controlled["masked"])


def test_remove_core_changes_only_the_objective_and_the_arms_move_one_axis() -> None:
    assert arm_flags(REMOVE_CORE_ARM) == arm_flags(FULL_ARM).__class__(False, False, False)
    # full -> no_constraint drops only the consistency terms; full ->
    # length_matched changes only which sentences are cited.
    full = arm_flags(FULL_ARM)
    assert arm_flags(NO_CONSTRAINT_ARM) == full.__class__(True, False, False)
    assert arm_flags(LENGTH_MATCHED_ARM) == full.__class__(True, True, True)

    record = record_for("m0", "m4")
    sets = counterfactual_sentence_ids(record, len(SENTENCES), arm=REMOVE_CORE_ARM)
    assert set(sets) == {"base"}  # no counterfactual forwards at all
    assert not necessity_scoreable(record, arm=REMOVE_CORE_ARM)


def test_an_unknown_arm_is_refused() -> None:
    with pytest.raises(ValueError, match="unknown A4 arm"):
        validate_a4_arm("full_v2")
    with pytest.raises(ValueError, match="unknown A4 arm"):
        pair_evidence_sidecar([], arm="ablation")


def test_a_timex_endpoint_is_cited_by_the_same_path_as_any_other_pair() -> None:
    # Official scoring only reads temporal on a TIMEX endpoint, but the pair is
    # still in the candidate universe, and the evidence path must not branch on
    # it: a branch is exactly how training and inference stop agreeing.
    timex = mention("t0", "later", 4, event_type=TIMEX_EVENT_TYPE)
    nodes = [*NODES, timex]
    with_timex = record_for("m0", "t0", nodes)
    without = record_for("m0", "m4", nodes)

    assert with_timex.candidates == without.candidates
    assert with_timex.selected == without.selected
    assert with_timex.substitutes == without.substitutes
    assert counterfactual_sentence_ids(
        with_timex, len(SENTENCES), arm=FULL_ARM
    ) == counterfactual_sentence_ids(without, len(SENTENCES), arm=FULL_ARM)


def test_a_span_the_document_cannot_hold_is_refused() -> None:
    record = record_for("m0", "m4")
    with pytest.raises(ValueError, match="cannot hold the pair's span"):
        counterfactual_sentence_ids(record, 3, arm=FULL_ARM)


def test_the_mediator_counts_unsupported_cross_sentence_false_positives() -> None:
    supported = record_for("m0", "m4")  # cross-sentence, cue-bearing
    unsupported = record_for("m2", "m3")  # cross-sentence, no cue anywhere
    same_sentence = record_for("m1", "m1b")

    records = [supported, unsupported, same_sentence]
    predicted = {
        ("m0", "m4"): "CAUSE",  # wrong, but a cue licensed it
        ("m2", "m3"): "CAUSE",  # wrong and unlicensed
        ("m1", "m1b"): "CAUSE",  # wrong, and not cross-sentence
    }
    gold = dict.fromkeys(predicted, "NONE")

    counts = unsupported_cross_sentence_causal(records, predicted, gold)
    assert counts == {
        "pairs": 3,
        "cross_sentence": 2,
        "predicted_causal": 3,
        "false_positives": 3,
        "cross_sentence_false_positives": 2,
        "unsupported_cross_sentence_false_positives": 1,
    }

    # A correct cross-sentence prediction is not a false positive, and the
    # denominators must still travel so a drop cannot be read as progress when
    # it came from predicting fewer causal edges.
    right = unsupported_cross_sentence_causal(
        [supported], {("m0", "m4"): "CAUSE"}, {("m0", "m4"): "CAUSE"}
    )
    assert right["predicted_causal"] == 1 and right["false_positives"] == 0


def test_the_mediator_refuses_a_pair_it_has_no_label_for() -> None:
    record = record_for("m0", "m4")
    with pytest.raises(ValueError, match="missing a prediction or a gold label"):
        unsupported_cross_sentence_causal([record], {}, {("m0", "m4"): "NONE"})


def test_a_checkpoint_whose_selector_drifted_is_refused(tmp_path) -> None:
    config = pair_evidence_config(FULL_ARM)
    (tmp_path / CONFIG_FILE).write_text(json.dumps(config), encoding="utf-8")
    assert load_pair_evidence_config(tmp_path)["arm"] == FULL_ARM

    (tmp_path / CONFIG_FILE).write_text(
        json.dumps({**config, "lexicon_sha256": "0" * 64}), encoding="utf-8"
    )
    with pytest.raises(ValueError, match="hash drift"):
        load_pair_evidence_config(tmp_path)

    (tmp_path / CONFIG_FILE).write_text(
        json.dumps({**config, "budget": EVIDENCE_BUDGET + 1}), encoding="utf-8"
    )
    with pytest.raises(ValueError, match="hash drift"):
        load_pair_evidence_config(tmp_path)

    (tmp_path / CONFIG_FILE).write_text(json.dumps({"arm": FULL_ARM}), encoding="utf-8")
    with pytest.raises(ValueError, match="must contain exactly"):
        load_pair_evidence_config(tmp_path)

    (tmp_path / CONFIG_FILE).unlink()
    with pytest.raises(FileNotFoundError, match="arm identity is unknown"):
        load_pair_evidence_config(tmp_path)


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="needs torch")
def test_all_four_arms_are_one_head_that_starts_as_the_reproduction_baseline() -> None:
    import torch

    from ekg.relations.pair_heads import (
        LINEAR_HEAD,
        PAIR_EVIDENCE_HEAD,
        build_pair_head,
    )

    counts = {"causal": 3}
    torch.manual_seed(13)
    evidence_head = build_pair_head(PAIR_EVIDENCE_HEAD, hidden_size=8, subtype_counts=counts)
    torch.manual_seed(13)
    baseline = build_pair_head(LINEAR_HEAD, hidden_size=8, subtype_counts=counts)

    feats = torch.randn(4, 8 * 4)
    dist_ids = torch.zeros(4, dtype=torch.long)
    evidence_head.eval()
    baseline.eval()
    with torch.no_grad():
        # remove_core passes no evidence stream; the other arms pass one, and
        # the residual is zero at init, so all four start at the baseline.
        assert torch.equal(evidence_head(feats, dist_ids)["causal"],
                           baseline(feats, dist_ids)["causal"])
        assert torch.equal(evidence_head(feats, dist_ids, torch.randn(4, 8 * 4))["causal"],
                           baseline(feats, dist_ids)["causal"])


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="needs torch")
def test_the_consistency_terms_score_only_supported_positives() -> None:
    import torch

    from ekg.relations.pair_evidence import sufficiency_necessity_loss

    target = torch.tensor([1, 0, -100])
    scoreable = torch.tensor([True, True, True])
    base = torch.tensor([[0.0, 5.0, 0.0], [0.0, 5.0, 0.0], [0.0, 5.0, 0.0]])
    # Masking the citation costs the gold logit nothing and the evidence alone
    # loses it: both terms must fire on the one positive row.
    loss = sufficiency_necessity_loss(base, base, base - 3.0, target, scoreable=scoreable)
    assert loss.item() == pytest.approx(2.5 + 1.0)

    # The same tensors with no positive row score nothing at all.
    empty = sufficiency_necessity_loss(
        base, base, base - 3.0, torch.tensor([0, 0, -100]), scoreable=scoreable
    )
    assert empty.item() == 0.0

    # A pair with nothing maskable keeps the sufficiency term and drops the
    # necessity term rather than absorbing a constant margin.
    partial = sufficiency_necessity_loss(
        base, base, base - 0.25, target, scoreable=torch.tensor([False, True, True])
    )
    assert partial.item() == 0.0


def test_every_arm_has_a_config_and_all_four_are_covered() -> None:
    assert set(A4_ARMS) == {FULL_ARM, REMOVE_CORE_ARM, LENGTH_MATCHED_ARM, NO_CONSTRAINT_ARM}
    for arm in A4_ARMS:
        assert pair_evidence_config(arm)["arm"] == arm
