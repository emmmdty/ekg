"""Windowed span location — the CPU-testable half of the GPU encoding path."""

from __future__ import annotations

import pytest

from ekg.nodes.encoding import locate_span_token

# Two overlapping windows over the same text; (0, 0) entries are special tokens.
WINDOWS = [
    [(0, 0), (0, 6), (7, 15), (16, 19), (20, 27), (0, 0)],
    [(0, 0), (16, 19), (20, 27), (28, 30), (31, 35), (0, 0)],
]


def test_locates_the_token_covering_the_offset() -> None:
    assert locate_span_token(WINDOWS, 7) == (0, 2)
    assert locate_span_token(WINDOWS, 31) == (1, 4)


def test_any_offset_inside_a_token_maps_to_that_token() -> None:
    # The span's first character is what anchors it, wherever inside the token.
    assert locate_span_token(WINDOWS, 8) == locate_span_token(WINDOWS, 7)


def test_overlapping_windows_pick_the_one_with_more_context() -> None:
    # Offset 20 appears at token 4 of window 0 (centrality 1) and token 2 of
    # window 1 (centrality 2): the better-contextualised copy wins.
    assert locate_span_token(WINDOWS, 20) == (1, 2)


def test_special_tokens_never_match() -> None:
    # Offset 0 must land on the real first token, not on a (0, 0) special token.
    assert locate_span_token(WINDOWS, 0) == (0, 1)


def test_uncovered_offset_is_fail_fast() -> None:
    with pytest.raises(ValueError, match="not covered"):
        locate_span_token(WINDOWS, 900)
