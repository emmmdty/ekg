import random

import pytest

from ekg.relations.retrieval import retrieval_counts, sample_binary_pairs, top_k_pairs


def test_top_k_pairs_is_per_head_and_stable_on_ties() -> None:
    ids = ["a", "b", "c"]
    scores = {
        ("a", "b"): 0.5,
        ("a", "c"): 0.5,
        ("b", "a"): 0.1,
        ("b", "c"): 0.9,
        ("c", "a"): 0.7,
        ("c", "b"): 0.2,
    }

    assert top_k_pairs(ids, scores, 1) == {("a", "b"), ("b", "c"), ("c", "a")}


def test_top_k_pairs_rejects_incomplete_scores() -> None:
    with pytest.raises(ValueError, match="missing retrieval score"):
        top_k_pairs(["a", "b"], {}, 1)


def test_sample_binary_pairs_keeps_positives_and_is_deterministic() -> None:
    ids = ["a", "b", "c", "d"]
    gold = {("a", "b"), ("a", "c")}
    first = sample_binary_pairs(ids, gold, negative_ratio=2, rng=random.Random(13))
    second = sample_binary_pairs(ids, gold, negative_ratio=2, rng=random.Random(13))

    assert first == second
    pairs, labels = first
    labelled = dict(zip(pairs, labels, strict=True))
    assert labelled[("a", "b")] == labelled[("a", "c")] == 1
    assert sum(labels) == 2
    assert len(labels) == 6  # two positives + one capped negative per head


def test_retrieval_counts_separates_same_and_cross_sentence() -> None:
    ids = ["a", "b", "c"]
    gold = {("a", "b"), ("a", "c")}
    selected = {("a", "b"), ("b", "a"), ("c", "a")}

    counts = retrieval_counts(
        selected,
        gold,
        mention_ids=ids,
        sentence_by_id={"a": 0, "b": 0, "c": 1},
    )

    assert counts["retrieved_gold"] == 1
    assert counts["retrieved_same_gold"] == 1
    assert counts["retrieved_cross_gold"] == 0
    assert counts["recall"] == pytest.approx(0.5)
    assert counts["compression"] == pytest.approx(0.5)
