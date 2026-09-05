"""Context-discriminative identity features: the train/score contract."""

from __future__ import annotations

import pytest

from ekg.core.schema import EventNode, EvidenceSpan
from ekg.nodes.discriminative import (
    ARGUMENT_POOLING_ORACLE,
    ARGUMENT_POOLING_PREDICTED,
    CONFUSABILITY,
    CONTEXT_POOLING,
    FEATURE_NAMES,
    argument_spans_and_counts,
    confusability_features,
    context_ranges_for,
    head_input_dim,
    pair_head_inputs,
    pool_argument_features,
    sentence_char_ranges,
    validate_components,
)


def _node(nid: str, trigger: str, sent: int, start: int, etype: str = "Attack") -> EventNode:
    return EventNode(
        event_id=nid,
        event_type=etype,
        doc_id="d",
        trigger=trigger,
        trigger_evidence=[
            EvidenceSpan(doc_id="d", char_start=start, char_end=start + len(trigger), sent_id=sent)
        ],
    )


def test_exact_trigger_pairs_are_named_explicitly() -> None:
    """51.8% of over-merges are exact-trigger pairs; the head must be able to see that."""
    order = {"a": 0, "b": 1}
    same = confusability_features(_node("a", "attack", 0, 0), _node("b", "attack", 3, 40), order)
    diff = confusability_features(_node("a", "attack", 0, 0), _node("b", "bombing", 3, 40), order)

    assert len(same) == len(FEATURE_NAMES) == 6
    assert same[FEATURE_NAMES.index("same_trigger_exact")] == 1.0
    assert diff[FEATURE_NAMES.index("same_trigger_exact")] == 0.0
    # ... and the pair that collapses the trigger representation is exactly the one
    # whose other features must carry the decision
    assert same[FEATURE_NAMES.index("same_sentence")] == 0.0
    assert same[FEATURE_NAMES.index("log_sentence_distance")] > 0


def test_case_and_type_are_normalised_the_same_way_both_sides() -> None:
    order = {"a": 0, "b": 1}
    feats = confusability_features(
        _node("a", "Attacked", 1, 0), _node("b", "attacked", 1, 20, etype="Bombing"), order
    )
    assert feats[FEATURE_NAMES.index("same_trigger_exact")] == 1.0
    assert feats[FEATURE_NAMES.index("same_event_type")] == 0.0
    assert feats[FEATURE_NAMES.index("same_sentence")] == 1.0


def test_sentence_ranges_cover_the_canonical_doc_text() -> None:
    text = "First one.\nSecond sentence here.\nThird."
    ranges = sentence_char_ranges(text)

    assert len(ranges) == 3
    assert [text[a:b] for a, b in ranges] == text.split("\n")


def test_context_range_falls_back_to_a_window_when_sent_id_is_missing() -> None:
    text = "aaa\nbbb"
    node = EventNode(
        event_id="n",
        event_type="Attack",
        doc_id="d",
        trigger="bbb",
        trigger_evidence=[EvidenceSpan(doc_id="d", char_start=4, char_end=7, sent_id=None)],
    )
    (start, end), = context_ranges_for([node], text)
    assert end > start  # never a zero-length range, which would pool nothing silently


def test_head_input_dim_tracks_each_component_independently() -> None:
    """Ablations switch the components separately, so the layout must too."""
    assert head_input_dim(768, ()) == 768 * 4
    assert head_input_dim(768, (CONTEXT_POOLING,)) == 768 * 8
    assert head_input_dim(768, (CONFUSABILITY,)) == 768 * 4 + len(FEATURE_NAMES)
    assert head_input_dim(768, (ARGUMENT_POOLING_ORACLE,)) == 768 * 8
    assert head_input_dim(768, (ARGUMENT_POOLING_PREDICTED,)) == 768 * 8


def test_argument_oracle_spans_are_deterministic_and_counted_per_mention() -> None:
    left = _node("a", "attack", 0, 10)
    right = _node("b", "attack", 1, 40)
    left.argument_evidence = {
        "Location": [EvidenceSpan(doc_id="d", char_start=30, char_end=35)],
        "Agent": [EvidenceSpan(doc_id="d", char_start=0, char_end=6)],
    }

    spans, counts = argument_spans_and_counts([left, right])

    assert spans == [(0, 6), (30, 35)]
    assert counts == [2, 0]


def test_argument_oracle_pooling_and_pair_layout_with_torch() -> None:
    torch = pytest.importorskip("torch")
    encoded = torch.tensor([[1.0, 3.0], [3.0, 5.0], [8.0, 10.0]])
    arguments = pool_argument_features(encoded, [2, 0, 1])
    assert arguments.tolist() == [[2.0, 4.0], [0.0, 0.0], [8.0, 10.0]]

    nodes = [_node("a", "attack", 0, 0), _node("b", "attack", 1, 20)]
    triggers = torch.ones((2, 2))
    inputs = pair_head_inputs(
        triggers,
        triggers,
        [("a", "b")],
        {node.event_id: node for node in nodes},
        {"a": 0, "b": 1},
        components=(ARGUMENT_POOLING_ORACLE,),
        arguments=arguments[:2],
    )
    assert inputs.shape == (1, head_input_dim(2, (ARGUMENT_POOLING_ORACLE,)))


def test_components_are_normalised_and_bad_ones_rejected() -> None:
    # order is canonical, so two spellings of the same ablation hash identically
    assert validate_components([CONFUSABILITY, CONTEXT_POOLING]) == (
        CONTEXT_POOLING,
        CONFUSABILITY,
    )
    with pytest.raises(ValueError, match="unknown"):
        validate_components(["bogus"])
    with pytest.raises(ValueError, match="duplicate"):
        validate_components([CONTEXT_POOLING, CONTEXT_POOLING])
    with pytest.raises(ValueError, match="one argument source"):
        validate_components([ARGUMENT_POOLING_ORACLE, ARGUMENT_POOLING_PREDICTED])
