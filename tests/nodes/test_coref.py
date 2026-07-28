"""Coreference candidate pairs, hard negatives, and the lexical baseline."""

from __future__ import annotations

import pytest

from ekg.core.schema import EventNode, EvidenceSpan
from ekg.nodes.coref import (
    CorefPair,
    LexicalCoreferenceScorer,
    candidate_coref_pairs,
    cluster_of_nodes,
    coreference_scorers,
    labelled_coref_pairs,
    sample_training_pairs,
    trigger_similarity,
)
from ekg.relations.data import load_maven_arg


def _node(node_id: str, trigger: str, event_type: str, start: int, event: str) -> EventNode:
    return EventNode(
        event_id=node_id,
        event_type=event_type,
        doc_id="d",
        trigger=trigger,
        trigger_evidence=[EvidenceSpan(doc_id="d", char_start=start, char_end=start + 1)],
        metadata={"event": event},
    )


@pytest.fixture
def nodes() -> list[EventNode]:
    # Two Attacking mentions of the SAME event, one Attacking mention of a
    # DIFFERENT event with a near-identical trigger (the hard negative), and one
    # unrelated type.
    return [
        _node("a1", "attacked", "Attacking", 0, "E1"),
        _node("a2", "assault", "Attacking", 10, "E1"),
        _node("a3", "attack", "Attacking", 20, "E2"),
        _node("d1", "died", "Death", 30, "E3"),
    ]


def test_candidate_pairs_are_same_type_and_textually_ordered(nodes) -> None:
    pairs = candidate_coref_pairs(nodes)
    assert pairs == [("a1", "a2"), ("a1", "a3"), ("a2", "a3")]
    # Dropping the same-type restriction adds the cross-type pairs.
    assert len(candidate_coref_pairs(nodes, same_type_only=False)) == 6


def test_same_type_restriction_never_drops_a_gold_pair(fixtures_dir) -> None:
    # A MAVEN event carries a single type, so restricting to same-type pairs is
    # lossless under gold typing — assert it instead of assuming it.
    for doc in load_maven_arg(fixtures_dir / "maven_arg" / "sample.jsonl"):
        cluster_of = cluster_of_nodes(doc.nodes)
        restricted = labelled_coref_pairs(doc.nodes, cluster_of)
        unrestricted = labelled_coref_pairs(doc.nodes, cluster_of, same_type_only=False)
        assert sum(p.label for p in restricted) == sum(p.label for p in unrestricted)


def test_hard_negative_is_the_similar_trigger_of_another_event(nodes) -> None:
    pairs = {p.key(): p for p in labelled_coref_pairs(nodes, cluster_of_nodes(nodes))}
    assert pairs[("a1", "a2")].label is True
    assert pairs[("a1", "a3")].label is False
    # "attacked" vs "attack" is lexically near-identical: a hard negative.
    assert pairs[("a1", "a3")].hard is True
    # "assault" vs "attack" shares the type but not the surface: an easy one.
    assert pairs[("a2", "a3")].hard is False


def test_a_positive_pair_is_never_hard(nodes) -> None:
    assert all(not p.hard for p in labelled_coref_pairs(nodes, cluster_of_nodes(nodes)) if p.label)


def test_trigger_similarity_is_case_insensitive() -> None:
    assert trigger_similarity("Attacked", "attacked") == 1.0


def test_sampling_keeps_every_positive_and_enriches_hard_negatives() -> None:
    pairs = [CorefPair("d", f"p{i}", f"q{i}", True, 0.5) for i in range(10)]
    pairs += [CorefPair("d", f"h{i}", f"k{i}", False, 0.95) for i in range(50)]
    pairs += [CorefPair("d", f"e{i}", f"f{i}", False, 0.1) for i in range(500)]

    sampled = sample_training_pairs(pairs, neg_ratio=10.0, hard_fraction=0.5, seed=1)
    assert sum(p.label for p in sampled) == 10
    assert sum(p.hard for p in sampled) == 50  # capped by the pool, budget was 50
    assert len(sampled) == 10 + 100


def test_sampling_spends_the_remainder_on_easy_when_hard_runs_out() -> None:
    pairs = [CorefPair("d", "p", "q", True, 0.5)]
    pairs += [CorefPair("d", f"e{i}", f"f{i}", False, 0.1) for i in range(100)]
    sampled = sample_training_pairs(pairs, neg_ratio=10.0, hard_fraction=0.9, seed=1)
    assert len(sampled) == 11


def test_sampling_is_deterministic_for_a_seed() -> None:
    pairs = [CorefPair("d", f"e{i}", f"f{i}", i < 5, 0.1) for i in range(200)]
    assert sample_training_pairs(pairs, seed=7) == sample_training_pairs(pairs, seed=7)


def test_lexical_scorer_is_registered_and_scores_surface_similarity(nodes) -> None:
    assert "lexical" in coreference_scorers
    scorer = coreference_scorers.create("lexical")
    assert isinstance(scorer, LexicalCoreferenceScorer)
    scores = scorer.score(nodes, candidate_coref_pairs(nodes))
    # The baseline ranks the hard negative ABOVE the true merge — precisely why
    # similar-event discrimination needs more than trigger matching.
    assert scores[("a1", "a3")] > scores[("a1", "a2")]


def test_supervised_scorer_instantiates_without_torch() -> None:
    assert "supervised" in coreference_scorers
    coreference_scorers.create("supervised")


def test_cluster_of_nodes_rejects_a_node_without_gold() -> None:
    node = EventNode(event_id="x", event_type="T", doc_id="d")
    with pytest.raises(ValueError, match="no gold event"):
        cluster_of_nodes([node])
