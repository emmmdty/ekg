"""Context-discriminative identity features: the train/score contract."""

from __future__ import annotations

from ekg.core.schema import EventNode, EvidenceSpan
from ekg.nodes.discriminative import (
    FEATURE_NAMES,
    confusability_features,
    context_ranges_for,
    head_input_dim,
    sentence_char_ranges,
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


def test_head_input_dim_matches_the_declared_layout() -> None:
    assert head_input_dim(768, context_discriminative=False) == 768 * 4
    assert head_input_dim(768, context_discriminative=True) == 768 * 8 + len(FEATURE_NAMES)
