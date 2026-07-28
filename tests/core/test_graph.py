"""Tests for graph primitives and consistency diagnostics."""

from __future__ import annotations

import signal
from collections.abc import Iterator
from contextlib import contextmanager

import pytest

from ekg.core.eval import consistency_report
from ekg.core.graph import (
    close_pairs,
    coreference_clusters,
    find_cycles,
    is_acyclic,
    transitive_closure_pairs,
)
from ekg.core.schema import EventGraph, EventNode, RelationEdge, RelationType


def _node(eid: str) -> EventNode:
    return EventNode(event_id=eid, event_type="E", doc_id="d")


def _causal(h: str, t: str) -> RelationEdge:
    return RelationEdge(head_id=h, tail_id=t, relation_type=RelationType.CAUSAL, subtype="CAUSE")


def _coref(h: str, t: str) -> RelationEdge:
    return RelationEdge(
        head_id=h, tail_id=t, relation_type=RelationType.COREFERENCE, directed=False
    )


def _temporal(h: str, t: str) -> RelationEdge:
    return RelationEdge(
        head_id=h,
        tail_id=t,
        relation_type=RelationType.TEMPORAL,
        subtype="BEFORE",
    )


def _graph(edges: list[RelationEdge]) -> EventGraph:
    ids = {e.head_id for e in edges} | {e.tail_id for e in edges}
    return EventGraph(nodes={i: _node(i) for i in ids}, edges=edges)


@contextmanager
def _deadline(seconds: int) -> Iterator[None]:
    """Fail (instead of hanging) if the block runs longer than `seconds`."""

    def _fire(signum: int, frame: object) -> None:
        pytest.fail(f"did not finish within {seconds}s — complexity regression")

    previous = signal.signal(signal.SIGALRM, _fire)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous)


def test_coreference_clusters_connected_components() -> None:
    g = _graph([_coref("a", "b"), _coref("b", "c"), _coref("x", "y")])
    clusters = {frozenset(c) for c in coreference_clusters(g)}
    assert frozenset({"a", "b", "c"}) in clusters
    assert frozenset({"x", "y"}) in clusters


def test_causal_cycle_detection() -> None:
    cyclic = _graph([_causal("a", "b"), _causal("b", "a")])
    assert not is_acyclic(cyclic, RelationType.CAUSAL)
    assert len(find_cycles(cyclic, RelationType.CAUSAL)) >= 1

    acyclic = _graph([_causal("a", "b"), _causal("b", "c")])
    assert is_acyclic(acyclic, RelationType.CAUSAL)


def test_consistency_report_flags_causal_cycle() -> None:
    report = consistency_report(_graph([_causal("a", "b"), _causal("b", "a")]))
    assert report["causal_cyclic_scc"] >= 1.0


def _complete_causal_graph(n: int) -> EventGraph:
    """Every ordered pair as a causal edge — one strongly connected component."""
    ids = [f"e{i}" for i in range(n)]
    return _graph([_causal(h, t) for h in ids for t in ids if h != t])


def test_consistency_report_counts_cyclic_sccs_not_simple_cycles() -> None:
    # A complete digraph on 10 nodes is a single SCC covering all 90 edges, but
    # it contains 1,112,073 distinct simple cycles. The diagnostic must report
    # the SCC structure, not enumerate cycles.
    report = consistency_report(_complete_causal_graph(10))
    assert report["causal_cyclic_scc"] == 1.0
    assert report["causal_cyclic_edges"] == 90.0


def test_consistency_report_stays_tractable_on_dense_graph() -> None:
    """Complexity regression sentinel: the report must be O(V+E), not exponential.

    Enumerating simple cycles on a dense graph is super-exponential (25 nodes is
    astronomically beyond 10's 1.1M), which is what exhausted 44GB of RAM on the
    real MAVEN dump. A wall-clock deadline is the honest assertion here: the
    failure mode being guarded against is non-termination, not a wrong value.
    """
    graph = _complete_causal_graph(25)
    with _deadline(seconds=10):
        report = consistency_report(graph)
    assert report["causal_cyclic_scc"] == 1.0
    assert report["causal_cyclic_edges"] == 600.0


def test_close_pairs_chain() -> None:
    assert close_pairs([("a", "b"), ("b", "c")]) == {("a", "b"), ("b", "c"), ("a", "c")}


def test_close_pairs_empty() -> None:
    assert close_pairs([]) == set()


def test_close_pairs_diamond_adds_only_implied() -> None:
    pairs = [("a", "b"), ("a", "c"), ("b", "d"), ("c", "d")]
    closed = close_pairs(pairs)
    assert ("a", "d") in closed  # implied through both b and c
    assert closed == set(pairs) | {("a", "d")}


def test_close_pairs_cycle_omits_reflexive_pairs() -> None:
    assert close_pairs([("a", "b"), ("b", "a")]) == {("a", "b"), ("b", "a")}


def test_transitive_closure_pairs_cycle_omits_reflexive_pairs() -> None:
    graph = _graph([_temporal("a", "b"), _temporal("b", "a")])
    assert transitive_closure_pairs(graph, RelationType.TEMPORAL, {"BEFORE"}) == {
        ("a", "b"),
        ("b", "a"),
    }
