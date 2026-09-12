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
    FULL_ARM,
    LENGTH_MATCHED_ARM,
    NO_CONSTRAINT_ARM,
    REMOVE_CORE_ARM,
    arm_flags,
    consistency_rows,
    context_dependence_report,
    counterfactual_sentence_ids,
    document_pair_evidence,
    load_pair_evidence_config,
    necessity_scoreable,
    pair_evidence_config,
    pair_evidence_sidecar,
    sentence_lengths,
    validate_a4_arm,
)
from ekg.relations.pairs import candidate_pairs

# Seven sentences: 5 and 6 sit outside every pair's span below, which is where
# the length-matched control has to draw from.
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
N_SENTENCES = len(DOC_TEXT.split("\n"))


def record_for(head_id: str, tail_id: str, nodes=None):
    (record,) = document_pair_evidence(nodes or NODES, DOC_TEXT, [(head_id, tail_id)])
    return record


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


def test_evidence_is_the_interior_of_the_span_and_needs_no_ranking() -> None:
    record = record_for("m0", "m4")

    # Defined, not selected: the cue lexicon that used to rank these sentences
    # labels 79.3% of real pairs as cue-bearing, so it separated nothing.
    assert record.span == (0, 1, 2, 3, 4)
    assert record.protected == (0, 4)
    assert record.interior == (1, 2, 3)

    sets = counterfactual_sentence_ids(record, N_SENTENCES, arm=FULL_ARM)
    assert sets["base"] == (0, 1, 2, 3, 4, 5, 6)
    assert sets["masked"] == (0, 4, 5, 6)  # necessity: the interior is gone
    assert sets["retained"] == (0, 1, 2, 3, 4)  # sufficiency: the span alone
    assert necessity_scoreable(record, arm=FULL_ARM)


def test_both_directions_of_a_pair_intervene_on_the_same_sentences() -> None:
    forward = record_for("m0", "m4")
    backward = record_for("m4", "m0")

    # The interior of a span does not depend on which endpoint is the cause, so
    # the two directions must be scored on the same context; if they were not,
    # direction would be confounded with how much text the model saw.
    assert forward.interior == backward.interior
    assert forward.span == backward.span
    assert forward.substitutes == backward.substitutes
    assert set(pair_evidence_sidecar([forward, backward], arm=FULL_ARM)) == {
        "m0::m4",
        "m4::m0",
    }


def test_a_pair_with_no_interior_has_nothing_to_mask() -> None:
    same = record_for("m1", "m1b")
    adjacent = record_for("m0", "m1")

    for record in (same, adjacent):
        assert record.interior == ()
        assert not necessity_scoreable(record, arm=FULL_ARM)
        sets = counterfactual_sentence_ids(record, N_SENTENCES, arm=FULL_ARM)
        # Masking nothing must leave the document untouched rather than quietly
        # dropping a trigger sentence the pooling depends on.
        assert sets["masked"] == sets["base"]
        assert sets["retained"] == record.protected

    # These are the short distances, and the error profile puts 78.4% of causal
    # false positives on cross-sentence pairs, most of them long-distance.
    assert same.cross_sentence is False
    assert adjacent.cross_sentence is True


def test_the_control_intervenes_on_matched_length_sentences_outside_the_span() -> None:
    record = record_for("m0", "m4")
    assert record.cited(FULL_ARM) == record.interior
    assert record.cited(LENGTH_MATCHED_ARM) == record.substitutes
    # Sentence 1 has 7 tokens, 2 has 5, 3 has 4; only 5 and 6 lie outside the
    # span, so the control is one sentence short of the three it asked for.
    assert sentence_lengths(DOC_TEXT) == [6, 7, 5, 4, 6, 4, 8]
    assert record.substitutes == (5, 6)
    assert record.substitutes_requested == 3
    assert not set(record.substitutes) & set(record.span)

    controlled = counterfactual_sentence_ids(record, N_SENTENCES, arm=LENGTH_MATCHED_ARM)
    # The control must leave the pair's own interior in place, or it is
    # intervening on the evidence it exists to rule out.
    assert set(record.interior) <= set(controlled["masked"])
    assert not set(controlled["masked"]) & set(record.substitutes)
    assert not set(controlled["retained"]) & set(record.interior)


def test_an_unmatched_control_is_recorded_rather_than_padded() -> None:
    nodes = [mention("a", "attacked", 0), mention("b", "died", 2, event_type="Death")]
    text = "It fell.\nIt fell because rain came.\nPeople died."
    (record,) = document_pair_evidence(nodes, text, [("a", "b")])

    assert record.interior == (1,)
    assert record.substitutes == ()  # nothing outside the span to draw from
    assert record.substitutes_requested == 1
    assert not necessity_scoreable(record, arm=LENGTH_MATCHED_ARM)
    sidecar = pair_evidence_sidecar([record], arm=LENGTH_MATCHED_ARM)
    assert sidecar["a::b"]["control_matched"] is False


def test_remove_core_changes_only_the_objective_and_the_arms_move_one_axis() -> None:
    full = arm_flags(FULL_ARM)
    assert full == full.__class__(True, True, False)
    assert arm_flags(REMOVE_CORE_ARM) == full.__class__(False, False, False)
    assert arm_flags(NO_CONSTRAINT_ARM) == full.__class__(True, False, False)
    assert arm_flags(LENGTH_MATCHED_ARM) == full.__class__(True, True, True)

    record = record_for("m0", "m4")
    sets = counterfactual_sentence_ids(record, N_SENTENCES, arm=REMOVE_CORE_ARM)
    assert set(sets) == {"base"}  # no counterfactual forwards at all
    assert not necessity_scoreable(record, arm=REMOVE_CORE_ARM)


def test_an_unknown_arm_is_refused() -> None:
    with pytest.raises(ValueError, match="unknown A4 arm"):
        validate_a4_arm("full_v2")
    with pytest.raises(ValueError, match="unknown A4 arm"):
        pair_evidence_sidecar([], arm="ablation")


def test_a_timex_endpoint_is_intervened_on_by_the_same_path_as_any_other_pair() -> None:
    # Official scoring only reads temporal on a TIMEX endpoint, but the pair is
    # still in the candidate universe, and the evidence path must not branch on
    # it: a branch is exactly how training and inference stop agreeing.
    timex = mention("t0", "later", 4, event_type=TIMEX_EVENT_TYPE)
    nodes = [*NODES, timex]
    with_timex = record_for("m0", "t0", nodes)
    without = record_for("m0", "m4", nodes)

    assert with_timex.interior == without.interior
    assert with_timex.substitutes == without.substitutes
    assert counterfactual_sentence_ids(
        with_timex, N_SENTENCES, arm=FULL_ARM
    ) == counterfactual_sentence_ids(without, N_SENTENCES, arm=FULL_ARM)


def test_a_span_the_document_cannot_hold_is_refused() -> None:
    record = record_for("m0", "m4")
    with pytest.raises(ValueError, match="cannot hold the pair's span"):
        counterfactual_sentence_ids(record, 3, arm=FULL_ARM)


def test_the_revision_trains_on_a_balanced_row_set() -> None:
    records = [record_for("m0", "m4"), record_for("m0", "m3"), record_for("m1", "m4")]
    gold = [True, False, False]
    predicted = [True, True, True]

    # One gold positive and one of the two current false positives: trained on
    # base-predicted positives alone the revision sees ~80% gold-NONE rows and
    # collapses to always-NONE, which it measurably did.
    assert consistency_rows(records, gold, predicted, arm=FULL_ARM, cap=2) == ((0, 1), 1)
    # With room for everything the cap drops nothing.
    assert consistency_rows(records, gold, predicted, arm=FULL_ARM) == ((0, 1, 2), 0)
    # A gold positive that the base pass misses still trains the revision.
    assert consistency_rows(records, [True, False, False], [False, True, False],
                            arm=FULL_ARM) == ((0, 1), 0)
    # remove_core has no evidence stream, so it supervises nothing this way.
    assert consistency_rows(records, gold, predicted, arm=REMOVE_CORE_ARM) == ((), 0)
    with pytest.raises(ValueError, match="labels"):
        consistency_rows(records, [True], predicted, arm=FULL_ARM)
    with pytest.raises(ValueError, match="both halves"):
        consistency_rows(records, gold, predicted, arm=FULL_ARM, cap=1)


def test_the_mediator_registers_cross_sentence_false_positives_with_no_intervention() -> None:
    cross = record_for("m0", "m4")
    same = record_for("m1", "m1b")
    records = [cross, same]
    predicted = {("m0", "m4"): "CAUSE", ("m1", "m1b"): "CAUSE"}
    gold = dict.fromkeys(predicted, "NONE")

    report = context_dependence_report(records, predicted, gold)

    # The frozen causal chain registers this quantity, and it must be computable
    # with no counterfactual at all.
    assert report["cross_sentence_false_positives"] == 1
    assert report["false_positives"] == 2
    assert report["predicted_causal"] == 2
    assert report["pairs"] == 2
    # Nothing was measured, so nothing is claimed about context dependence.
    assert report["measured_cross_sentence_false_positives"] == 0
    assert report["context_independent_cross_sentence_false_positives"] == 0


def test_context_independence_is_measured_not_guessed_and_keeps_its_denominator() -> None:
    insensitive = record_for("m0", "m4")
    sensitive = record_for("m1", "m4")
    correct = record_for("m0", "m3")
    records = [insensitive, sensitive, correct]
    predicted = {
        ("m0", "m4"): "CAUSE",  # wrong, and unmoved by removing its interior
        ("m1", "m4"): "CAUSE",  # wrong, but it did read the context
        ("m0", "m3"): "CAUSE",  # right
    }
    gold = {("m0", "m4"): "NONE", ("m1", "m4"): "NONE", ("m0", "m3"): "CAUSE"}
    drops = {("m0", "m4"): 0.1, ("m1", "m4"): 3.0, ("m0", "m3"): 2.0}

    report = context_dependence_report(records, predicted, gold, logit_drop=drops)

    assert report["cross_sentence_false_positives"] == 2
    assert report["measured_cross_sentence_false_positives"] == 2
    assert report["context_independent_cross_sentence_false_positives"] == 1
    assert report["mean_false_positive_logit_drop"] == pytest.approx(1.55)
    # True positives travel alongside, so a drop in the count cannot be read as
    # progress when the model simply stopped using context everywhere.
    assert report["measured_true_positives"] == 1
    assert report["mean_true_positive_logit_drop"] == pytest.approx(2.0)


def test_the_mediator_refuses_a_pair_it_has_no_label_for() -> None:
    record = record_for("m0", "m4")
    with pytest.raises(ValueError, match="missing a prediction or a gold label"):
        context_dependence_report([record], {}, {("m0", "m4"): "NONE"})


def test_a_checkpoint_whose_mechanism_drifted_is_refused(tmp_path) -> None:
    config = pair_evidence_config(FULL_ARM)
    (tmp_path / CONFIG_FILE).write_text(json.dumps(config), encoding="utf-8")
    assert load_pair_evidence_config(tmp_path)["arm"] == FULL_ARM

    for field, value in (
        ("evidence_rule", "cue_ranked"),
        ("consistency_family", "temporal"),
        ("necessity_margin", 0.25),
        ("residual_rows", "gold_positive"),
        ("revision_training_rows", "base_predicted_positive"),
    ):
        (tmp_path / CONFIG_FILE).write_text(
            json.dumps({**config, field: value}), encoding="utf-8"
        )
        with pytest.raises(ValueError, match=f"mechanism drift on {field}"):
            load_pair_evidence_config(tmp_path)

    (tmp_path / CONFIG_FILE).write_text(json.dumps({"arm": FULL_ARM}), encoding="utf-8")
    with pytest.raises(ValueError, match="must contain exactly"):
        load_pair_evidence_config(tmp_path)

    (tmp_path / CONFIG_FILE).unlink()
    with pytest.raises(FileNotFoundError, match="arm identity is unknown"):
        load_pair_evidence_config(tmp_path)


def test_every_arm_has_a_config_and_all_four_are_covered() -> None:
    assert set(A4_ARMS) == {FULL_ARM, REMOVE_CORE_ARM, LENGTH_MATCHED_ARM, NO_CONSTRAINT_ARM}
    for arm in A4_ARMS:
        assert pair_evidence_config(arm)["arm"] == arm
        assert pair_evidence_config(arm)["evidence_rule"] == "span_interior"
        assert (
            pair_evidence_config(arm)["revision_training_rows"]
            == "balanced_gold_and_false_positive"
        )


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
    # Removing the interior costs the gold logit nothing and the span alone
    # loses it: both terms must fire on the one positive row.
    loss = sufficiency_necessity_loss(base, base, base - 3.0, target, scoreable=scoreable)
    assert loss.item() == pytest.approx(2.5 + 1.0)

    # The same tensors with no positive row score nothing at all.
    empty = sufficiency_necessity_loss(
        base, base, base - 3.0, torch.tensor([0, 0, -100]), scoreable=scoreable
    )
    assert empty.item() == 0.0

    # A pair with an empty interior keeps the sufficiency term and drops the
    # necessity term rather than absorbing a constant margin.
    partial = sufficiency_necessity_loss(
        base, base, base - 0.25, target, scoreable=torch.tensor([False, True, True])
    )
    assert partial.item() == 0.0
