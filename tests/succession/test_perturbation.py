"""Controlled construction errors: exact amplitudes, and one provable zero.

Each generator has to do precisely what it claims and nothing else — a
perturbation that quietly also deleted edges would make the attribution it
exists to support meaningless.
"""

from __future__ import annotations

import pytest

from ekg.core.schema import RelationEdge, RelationType
from ekg.succession.data.cgep import topology_triples
from ekg.succession.perturbation import (
    SPLIT_SUFFIX,
    add_edges,
    drop_edges,
    graph_perturbations,
    merge_nodes,
    scramble_temporal,
    split_nodes,
)

_NODES = {"docA": [f"docA::m{i}" for i in range(1, 7)]}


def _edge(head: str, tail: str, kind: RelationType, subtype: str) -> RelationEdge:
    return RelationEdge(
        head_id=f"docA::{head}", tail_id=f"docA::{tail}",
        relation_type=kind, subtype=subtype,
    )


def _graph() -> dict[str, list[RelationEdge]]:
    return {
        "docA": [
            _edge("m1", "m2", RelationType.CAUSAL, "CAUSE"),
            _edge("m2", "m3", RelationType.CAUSAL, "PRECONDITION"),
            _edge("m3", "m4", RelationType.SUBEVENT, "SUBEVENT_OF"),
            _edge("m4", "m5", RelationType.CAUSAL, "CAUSE"),
            _edge("m1", "m5", RelationType.TEMPORAL, "BEFORE"),
            _edge("m2", "m6", RelationType.TEMPORAL, "CONTAINS"),
        ]
    }


def _topology(graphs) -> set[tuple[str, str, str]]:
    return {t for edges in graphs.values() for t in topology_triples(edges)}


def test_drop_edges_removes_an_exact_count_of_topology_edges_only() -> None:
    graphs = _graph()
    result = drop_edges(graphs, rate=None, exact=2, seed=1)

    assert result.stats == {"eligible": 4.0, "dropped": 2.0}
    assert len(_topology(result.edges_by_doc)) == 2
    # The two temporal edges are untouched: this control must not remove mass
    # the intervention it matches never touched.
    temporal = [e for e in result.edges_by_doc["docA"] if e.relation_type is RelationType.TEMPORAL]
    assert len(temporal) == 2


def test_drop_edges_honours_a_subtype_filter() -> None:
    """Matching a causal repair must leave subevent edges alone."""
    graphs = _graph()
    result = drop_edges(graphs, rate=1.0, subtypes=("CAUSE", "PRECONDITION"), seed=1)

    assert result.stats["eligible"] == 3.0
    assert _topology(result.edges_by_doc) == {("docA::m3", "SUBEVENT_OF", "docA::m4")}


def test_drop_edges_rejects_both_or_neither_amplitude() -> None:
    with pytest.raises(ValueError):
        drop_edges(_graph(), rate=0.5, exact=2)
    with pytest.raises(ValueError):
        drop_edges(_graph())


def test_add_edges_fabricates_pairs_that_had_no_relation() -> None:
    graphs = _graph()
    existing = {frozenset((e.head_id, e.tail_id)) for e in graphs["docA"]}

    result = add_edges(graphs, _NODES, exact=3, seed=7)

    assert result.stats["added"] == 3.0
    new = result.edges_by_doc["docA"][len(graphs["docA"]) :]
    assert len(new) == 3
    assert all(frozenset((e.head_id, e.tail_id)) not in existing for e in new)
    assert all(e.relation_type is RelationType.CAUSAL for e in new)


def test_merge_nodes_reattaches_edges_and_drops_self_loops() -> None:
    graphs = {"docA": [_edge("m1", "m2", RelationType.CAUSAL, "CAUSE")]}

    result = merge_nodes(graphs, {"docA": ["docA::m1", "docA::m2"]}, exact=1, seed=3)

    assert result.stats["merged_nodes"] == 1.0
    # m1 and m2 became one event, so the edge between them is a self-loop.
    assert result.stats["self_loops_dropped"] == 1.0
    assert result.edges_by_doc["docA"] == []


def test_merge_nodes_keeps_every_other_relation_pointing_at_the_survivor() -> None:
    graphs = {
        "docA": [
            _edge("m1", "m2", RelationType.CAUSAL, "CAUSE"),
            _edge("m3", "m4", RelationType.CAUSAL, "CAUSE"),
        ]
    }
    result = merge_nodes(graphs, {"docA": ["docA::m1", "docA::m3"]}, exact=1, seed=3)

    survivors = {(e.head_id, e.tail_id) for e in result.edges_by_doc["docA"]}
    # No relation was lost, but one of them now describes a different event.
    assert len(survivors) == 2
    assert ("docA::m1", "docA::m2") in survivors or ("docA::m3", "docA::m4") in survivors


def test_split_nodes_moves_edges_onto_a_clone_the_gold_frame_cannot_see() -> None:
    graphs = _graph()
    result = split_nodes(graphs, _NODES, rate=1.0, share=1.0, seed=5)

    assert result.stats["split_nodes"] == 6.0
    endpoints = {e.head_id for e in result.edges_by_doc["docA"]} | {
        e.tail_id for e in result.edges_by_doc["docA"]
    }
    assert endpoints and all(node.endswith(SPLIT_SUFFIX) for node in endpoints)
    assert len(result.edges_by_doc["docA"]) == len(graphs["docA"])  # nothing deleted


def test_scramble_temporal_cannot_touch_ecg_topology() -> None:
    """The structural zero: temporal edits are invisible to the successor reader."""
    graphs = _graph()
    before = _topology(graphs)

    result = scramble_temporal(graphs, rate=1.0, seed=11)

    assert result.stats == {"eligible": 2.0, "reversed": 2.0}
    assert _topology(result.edges_by_doc) == before
    reversed_pairs = {
        (e.head_id, e.tail_id)
        for e in result.edges_by_doc["docA"]
        if e.relation_type is RelationType.TEMPORAL
    }
    assert reversed_pairs == {("docA::m5", "docA::m1"), ("docA::m6", "docA::m2")}


@pytest.mark.parametrize("name", ["drop_edges", "add_edges", "merge_nodes", "split_nodes"])
def test_sweep_points_are_nested(name: str) -> None:
    """A larger amplitude must touch a superset, or the curve measures luck.

    Checked on the surviving topology: a bigger deletion can only remove more,
    a bigger insertion can only add more, and both coreference errors can only
    rewire more. Without nesting, two sweep points differ by which random subset
    was drawn as well as by how many -- which is exactly the confound the sweep
    exists to remove.
    """
    graphs = _graph()
    small, large = (
        graph_perturbations.create(
            name, edges_by_doc=graphs, nodes_by_doc=_NODES, rate=rate, seed=4
        )
        for rate in (0.25, 0.75)
    )
    intact = _topology(graphs)
    changed_small = intact.symmetric_difference(_topology(small.edges_by_doc))
    changed_large = intact.symmetric_difference(_topology(large.edges_by_doc))

    assert changed_small <= changed_large


def test_registry_dispatches_every_generator_uniformly() -> None:
    for name in ("drop_edges", "add_edges", "merge_nodes", "split_nodes", "scramble_temporal"):
        result = graph_perturbations.create(
            name, edges_by_doc=_graph(), nodes_by_doc=_NODES, rate=0.5, seed=2
        )
        assert set(result.edges_by_doc) == {"docA"}
        assert "eligible" in result.stats
