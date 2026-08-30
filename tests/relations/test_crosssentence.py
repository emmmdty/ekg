"""Tests for the between-trigger probe (pure CPU, no model)."""

from __future__ import annotations

import pytest

from ekg.relations.crosssentence import (
    CAUSAL_CUES,
    ORDERING_CUES,
    MentionSpan,
    between_tokens,
    document_order,
    find_cues,
)

SENTENCES = [
    ["The", "dam", "burst", "because", "the", "rain", "never", "stopped", "."],
    ["Engineers", "had", "warned", "of", "it", "."],
    ["As", "a", "result", "the", "village", "flooded", "overnight", "."],
]


def test_document_order_ignores_the_gold_cause_effect_ordering() -> None:
    burst = MentionSpan(0, 2, 3)
    flooded = MentionSpan(2, 5, 6)
    # Gold stores (cause, effect); the effect is often written first, so reading
    # order has to be recomputed rather than assumed.
    assert document_order(flooded, burst) == (burst, flooded)
    assert document_order(burst, flooded) == (burst, flooded)


def test_same_sentence_between_is_just_the_separating_tokens() -> None:
    burst = MentionSpan(0, 2, 3)
    stopped = MentionSpan(0, 7, 8)
    assert between_tokens(SENTENCES, burst, stopped) == [
        "because", "the", "rain", "never",
    ]


def test_cross_sentence_between_splices_tail_middle_head() -> None:
    burst = MentionSpan(0, 2, 3)
    flooded = MentionSpan(2, 5, 6)
    tokens = between_tokens(SENTENCES, burst, flooded)
    # tail of sentence 0 after "burst", all of sentence 1, head of sentence 2.
    assert tokens[:5] == ["because", "the", "rain", "never", "stopped"]
    assert "warned" in tokens
    assert tokens[-5:] == ["As", "a", "result", "the", "village"]
    # The second trigger itself is excluded -- "between" is strict.
    assert "flooded" not in tokens


def test_reversed_arguments_give_the_same_span() -> None:
    burst = MentionSpan(0, 2, 3)
    flooded = MentionSpan(2, 5, 6)
    assert between_tokens(SENTENCES, burst, flooded) == between_tokens(
        SENTENCES, flooded, burst
    )


def test_adjacent_mentions_give_an_empty_span_not_a_negative_slice() -> None:
    first = MentionSpan(1, 2, 3)
    second = MentionSpan(1, 3, 4)
    assert between_tokens(SENTENCES, first, second) == []


def test_out_of_range_sentence_is_rejected() -> None:
    with pytest.raises(IndexError, match="outside"):
        between_tokens(SENTENCES, MentionSpan(0, 0, 1), MentionSpan(9, 0, 1))
    with pytest.raises(ValueError, match="invalid mention span"):
        MentionSpan(0, 3, 3)


def test_cues_match_multiword_runs_case_insensitively() -> None:
    burst = MentionSpan(0, 2, 3)
    flooded = MentionSpan(2, 5, 6)
    tokens = between_tokens(SENTENCES, burst, flooded)
    found = find_cues(tokens, CAUSAL_CUES)
    assert "because" in found
    # "As a result" is capitalised in the text and split across three tokens.
    assert "as a result" in found
    # Ordering markers are a separate list so they cannot inflate the causal cell.
    assert find_cues(tokens, ORDERING_CUES) == []


def test_a_cue_must_be_contiguous() -> None:
    # "as ... a ... result" scattered is not the connective.
    assert find_cues(["as", "the", "a", "big", "result"], CAUSAL_CUES) == []
    assert find_cues(["as", "a", "result"], CAUSAL_CUES) == ["as a result"]
