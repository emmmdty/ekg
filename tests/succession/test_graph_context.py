"""Swapping the graph context under a fixed CGEP problem (Ch4 error propagation).

The design only isolates graph quality if three things hold: gold in, gold out
(so the `gold` arm *is* the published baseline rather than a re-derivation); the
answer never reaches the prompt, whatever the constructed graph says; and the
instance set never changes, so the MRRs stay comparable.
"""

from __future__ import annotations

import pytest

from ekg.core.schema import EventNode, EvidenceSpan, RelationEdge, RelationType
from ekg.relations.data.maven_ere import RelationDocument
from ekg.succession.data.cgep import build_cgep
from ekg.succession.graph_context import swap_graph_context

# The ALPHA topology of test_cgep_build / test_reconstruction. Its one query edge
# is m2 -CAUSE-> m4 ("arrest": out-degree 0, in-degree 1).
_TOPOLOGY = [
    ("m1", "m2", RelationType.CAUSAL, "CAUSE"),
    ("m2", "m3", RelationType.CAUSAL, "PRECONDITION"),
    ("m2", "m4", RelationType.CAUSAL, "CAUSE"),
    ("m3", "m5", RelationType.SUBEVENT, "SUBEVENT_OF"),
    ("m1", "m5", RelationType.CAUSAL, "CAUSE"),
]
_TRIGGERS = ["attack", "riot", "march", "arrest", "trial"]


def _node(key: str, trigger: str, sent_id: int) -> EventNode:
    return EventNode(
        event_id=f"docA::{key}",
        event_type=f"Type_{trigger}",
        doc_id="docA",
        trigger=trigger,
        trigger_evidence=[
            EvidenceSpan(doc_id="docA", char_start=0, char_end=len(trigger),
                         sent_id=sent_id, text=trigger)
        ],
    )


def _edge(head: str, tail: str, kind: RelationType, subtype: str) -> RelationEdge:
    return RelationEdge(
        head_id=f"docA::{head}", tail_id=f"docA::{tail}",
        relation_type=kind, subtype=subtype,
    )


def _document() -> RelationDocument:
    keys = [f"m{i}" for i in range(1, 6)]
    nodes = [_node(k, t, i) for i, (k, t) in enumerate(zip(keys, _TRIGGERS, strict=True))]
    edges = [_edge(h, t, k, s) for h, t, k, s in _TOPOLOGY]
    edges.append(_edge("m1", "m3", RelationType.TEMPORAL, "BEFORE"))  # out of topology
    return RelationDocument(
        doc_id="docA", nodes=nodes, gold_edges=edges,
        doc_text="\n".join(f"sentence {i} mentions {t}" for i, t in enumerate(_TRIGGERS)),
        representative={f"E{i}": n.event_id for i, n in enumerate(nodes)},
    )


def _instances(doc: RelationDocument):
    instances, _ = build_cgep([doc], n_candidates=4)
    return instances


def test_gold_in_gold_out_is_byte_identical() -> None:
    """The `gold` arm must reproduce `build_cgep`, edge order included.

    Order is load-bearing: SeDGPL's budget keeps the *first* 20 edges in stored
    order, so a reordering would silently change the baseline this table is
    compared against.
    """
    doc = _document()
    instances = _instances(doc)
    swap = swap_graph_context(instances, {doc.doc_id: doc.gold_edges})

    assert [i.edges for i in swap.instances] == [i.edges for i in instances]
    assert swap.stats["template_recall"] == pytest.approx(1.0)
    assert swap.stats["template_precision"] == pytest.approx(1.0)
    # Exactly one blocked edge per instance: the query edge itself, which touches
    # the gold successor by definition.
    assert swap.stats["mean_leak_blocked"] == pytest.approx(1.0)
    assert swap.reachable == (True,)


def test_constructed_edge_touching_the_answer_is_blocked() -> None:
    """A predicted edge into the gold successor must not print the answer token."""
    doc = _document()
    instances = _instances(doc)
    # m1 -CAUSE-> m4 is a *new* edge into the gold successor m4.
    constructed = [*doc.gold_edges, _edge("m1", "m4", RelationType.CAUSAL, "CAUSE")]

    swap = swap_graph_context(instances, {doc.doc_id: constructed})

    gold_index = instances[0].gold_index
    assert all(gold_index not in (h, t) for h, _, t in swap.instances[0].template_edges)
    assert swap.stats["mean_leak_blocked"] == pytest.approx(2.0)


def test_edges_outside_the_gold_node_frame_are_dropped_not_added() -> None:
    doc = _document()
    instances = _instances(doc)
    stranger = RelationEdge(
        head_id="docA::m1", tail_id="docA::m99",
        relation_type=RelationType.CAUSAL, subtype="CAUSE",
    )

    swap = swap_graph_context(instances, {doc.doc_id: [*doc.gold_edges, stranger]})

    assert swap.instances[0].edges == instances[0].edges
    assert swap.stats["mean_out_of_frame"] == pytest.approx(1.0)


def test_missing_query_edge_marks_the_instance_unreachable() -> None:
    doc = _document()
    instances = _instances(doc)
    query_pair = ("docA::m2", "docA::m4")
    without_query = [e for e in doc.gold_edges if (e.head_id, e.tail_id) != query_pair]

    swap = swap_graph_context(instances, {doc.doc_id: without_query})

    assert swap.reachable == (False,)
    assert swap.stats["reachability_rate"] == pytest.approx(0.0)


def test_instances_survive_an_empty_graph_rather_than_being_dropped() -> None:
    """An extractor that returned nothing has still been asked the question."""
    doc = _document()
    instances = _instances(doc)

    swap = swap_graph_context(instances, {})

    assert len(swap.instances) == len(instances)
    assert swap.instances[0].template_edges == ()
    assert swap.instances[0].query_edge == instances[0].query_edge
    assert swap.instances[0].candidates == instances[0].candidates
    assert swap.instances[0].label == instances[0].label
    assert swap.stats["frac_empty_template"] == pytest.approx(1.0)


def test_temporal_only_edges_never_enter_the_template() -> None:
    """The orthogonality Phase B's first probe got wrong, as an executable check."""
    doc = _document()
    instances = _instances(doc)
    extra_temporal = [
        _edge("m4", "m1", RelationType.TEMPORAL, "BEFORE"),
        _edge("m5", "m2", RelationType.TEMPORAL, "CONTAINS"),
    ]

    swap = swap_graph_context(instances, {doc.doc_id: [*doc.gold_edges, *extra_temporal]})

    assert swap.instances[0].edges == instances[0].edges
