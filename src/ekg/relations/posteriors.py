"""Validation and serialization for deployable relation posterior sidecars."""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping, Sequence

Pair = tuple[str, str]
CAUSAL_POSTERIOR_FIELDS = ("p_none", "p_cause", "p_precondition")

__all__ = ["CAUSAL_POSTERIOR_FIELDS", "causal_posterior_rows"]


def causal_posterior_rows(
    doc_id: str,
    pairs: Iterable[Pair],
    scores: Mapping[Pair, Sequence[float]],
    *,
    tolerance: float = 1e-6,
) -> list[dict[str, object]]:
    """Validate exhaustive causal scores and return deterministic JSON rows."""
    ordered_pairs = list(pairs)
    if len(ordered_pairs) != len(set(ordered_pairs)):
        raise ValueError(f"{doc_id}: duplicate candidate pairs")
    if any(head == tail for head, tail in ordered_pairs):
        raise ValueError(f"{doc_id}: self-pair in candidate universe")

    expected = set(ordered_pairs)
    actual = set(scores)
    if expected != actual:
        raise ValueError(
            f"{doc_id}: posterior pair coverage mismatch: "
            f"missing={len(expected - actual)} extra={len(actual - expected)}"
        )

    rows: list[dict[str, object]] = []
    for head, tail in ordered_pairs:
        values = tuple(float(value) for value in scores[(head, tail)])
        if len(values) != len(CAUSAL_POSTERIOR_FIELDS):
            raise ValueError(f"{doc_id}/{head}/{tail}: expected three causal probabilities")
        if not all(math.isfinite(value) for value in values):
            raise ValueError(f"{doc_id}/{head}/{tail}: non-finite causal probability")
        if not all(0.0 <= value <= 1.0 for value in values):
            raise ValueError(f"{doc_id}/{head}/{tail}: causal probability outside [0, 1]")
        if abs(sum(values) - 1.0) > tolerance:
            raise ValueError(f"{doc_id}/{head}/{tail}: causal probabilities do not sum to 1")
        row: dict[str, object] = {
            "doc_id": doc_id,
            "head_mention_id": head,
            "tail_mention_id": tail,
        }
        row.update(zip(CAUSAL_POSTERIOR_FIELDS, values, strict=True))
        rows.append(row)
    return rows
