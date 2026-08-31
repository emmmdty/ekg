"""Pure candidate-retrieval helpers for document-level event relations."""

from __future__ import annotations

import random
from collections import defaultdict
from collections.abc import Mapping, Sequence

PairKey = tuple[str, str]

__all__ = [
    "PairKey",
    "retrieval_counts",
    "sample_binary_pairs",
    "top_k_pairs",
]


def top_k_pairs(
    mention_ids: Sequence[str],
    scores: Mapping[PairKey, float],
    k: int,
) -> set[PairKey]:
    """Select the highest-scoring ``k`` tails per head with stable tie-breaking."""
    if k <= 0:
        raise ValueError(f"k must be positive, got {k}")
    if len(set(mention_ids)) != len(mention_ids):
        raise ValueError("mention_ids must be unique")
    selected: set[PairKey] = set()
    for head in mention_ids:
        candidates = []
        for tail in mention_ids:
            if head == tail:
                continue
            pair = (head, tail)
            if pair not in scores:
                raise ValueError(f"missing retrieval score for {pair}")
            candidates.append((float(scores[pair]), tail))
        candidates.sort(key=lambda item: (-item[0], item[1]))
        selected.update((head, tail) for _, tail in candidates[:k])
    return selected


def sample_binary_pairs(
    mention_ids: Sequence[str],
    gold_pairs: set[PairKey],
    *,
    negative_ratio: int,
    rng: random.Random,
) -> tuple[list[PairKey], list[int]]:
    """Keep every positive and sample bounded within-document negatives per head."""
    if negative_ratio <= 0:
        raise ValueError(f"negative_ratio must be positive, got {negative_ratio}")
    known = set(mention_ids)
    if any(head not in known or tail not in known or head == tail for head, tail in gold_pairs):
        raise ValueError("gold_pairs must be non-self pairs over mention_ids")

    positive_by_head: dict[str, set[str]] = defaultdict(set)
    for head, tail in gold_pairs:
        positive_by_head[head].add(tail)

    examples: list[tuple[PairKey, int]] = []
    for head in mention_ids:
        positives = sorted(positive_by_head.get(head, set()))
        examples.extend(((head, tail), 1) for tail in positives)
        negatives = sorted(
            tail for tail in mention_ids if tail != head and tail not in positive_by_head[head]
        )
        if negatives:
            wanted = min(len(negatives), max(1, negative_ratio * len(positives)))
            examples.extend(((head, tail), 0) for tail in rng.sample(negatives, wanted))
    examples.sort(key=lambda item: item[0])
    return [pair for pair, _ in examples], [label for _, label in examples]


def retrieval_counts(
    selected: set[PairKey],
    gold_pairs: set[PairKey],
    *,
    mention_ids: Sequence[str],
    sentence_by_id: Mapping[str, int],
) -> dict[str, int | float]:
    """Return micro-aggregatable recall and compression counts."""
    known = set(mention_ids)
    universe = {(head, tail) for head in mention_ids for tail in mention_ids if head != tail}
    if not selected <= universe:
        raise ValueError("selected pairs fall outside the mention-pair universe")
    if not gold_pairs <= universe:
        raise ValueError("gold pairs fall outside the mention-pair universe")
    if set(sentence_by_id) != known:
        raise ValueError("sentence_by_id must cover exactly mention_ids")

    same_gold = {
        pair for pair in gold_pairs if sentence_by_id[pair[0]] == sentence_by_id[pair[1]]
    }
    cross_gold = gold_pairs - same_gold
    return {
        "gold": len(gold_pairs),
        "retrieved_gold": len(selected & gold_pairs),
        "same_gold": len(same_gold),
        "retrieved_same_gold": len(selected & same_gold),
        "cross_gold": len(cross_gold),
        "retrieved_cross_gold": len(selected & cross_gold),
        "selected": len(selected),
        "universe": len(universe),
        "recall": len(selected & gold_pairs) / len(gold_pairs) if gold_pairs else 0.0,
        "compression": 1.0 - len(selected) / len(universe) if universe else 0.0,
    }
