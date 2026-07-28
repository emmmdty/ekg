"""Tests for factuality-driven graph purification."""

from __future__ import annotations

import pytest

from ekg.core.schema import EventGraph, EventNode, RelationEdge, RelationType
from ekg.factuality.purification import (
    DEFAULT_POLICY,
    PurificationPolicy,
    purification_report,
    purify_graph,
    random_drop_control,
)


def _graph() -> EventGraph:
    nodes = {
        f"m{i}": EventNode(event_id=f"m{i}", event_type="Attacking", doc_id="d1")
        for i in range(1, 5)
    }
    edges = [
        RelationEdge(head_id="m1", tail_id="m2", relation_type=RelationType.CAUSAL),
        RelationEdge(head_id="m2", tail_id="m3", relation_type=RelationType.TEMPORAL),
        RelationEdge(head_id="m1", tail_id="m4", relation_type=RelationType.SUBEVENT),
    ]
    return EventGraph(nodes=nodes, edges=edges)


def test_counterfactual_nodes_are_dropped_with_their_edges() -> None:
    # m2 is CT-: asserted *not* to have happened, so it and both edges touching
    # it leave the graph.
    result = purify_graph(_graph(), {"m1": "CT+", "m2": "CT-", "m3": "CT+", "m4": "CT+"})
    assert set(result.graph.nodes) == {"m1", "m3", "m4"}
    assert [(e.head_id, e.tail_id) for e in result.graph.edges] == [("m1", "m4")]
    assert result.dropped_nodes == ("m2",)
    assert result.n_dropped_edges == 2


def test_uncertain_nodes_are_downweighted_not_dropped() -> None:
    result = purify_graph(_graph(), {"m1": "CT+", "m2": "Uu", "m3": "PS-", "m4": "CT+"})
    # Nothing is removed: uncertainty is not counter-evidence.
    assert set(result.graph.nodes) == {"m1", "m2", "m3", "m4"}
    assert result.dropped_nodes == ()
    # Edges touching a downweighted node carry a reduced confidence, and the
    # weight of the *lower*-confidence endpoint wins.
    by_pair = {(e.head_id, e.tail_id): e for e in result.graph.edges}
    assert by_pair[("m1", "m2")].confidence == pytest.approx(DEFAULT_POLICY.weights["Uu"])
    assert by_pair[("m2", "m3")].confidence == pytest.approx(
        min(DEFAULT_POLICY.weights["Uu"], DEFAULT_POLICY.weights["PS-"])
    )
    assert by_pair[("m1", "m4")].confidence == pytest.approx(1.0)


def test_every_decision_is_traceable() -> None:
    result = purify_graph(_graph(), {"m1": "CT+", "m2": "CT-", "m3": "Uu", "m4": "CT+"})
    # A purification that cannot say *why* it removed something is not auditable,
    # so each affected node carries its label and action.
    assert result.trace["m2"] == {"label": "CT-", "action": "drop"}
    assert result.trace["m3"] == {"label": "Uu", "action": "downweight"}
    assert "m1" not in result.trace  # untouched nodes add no noise


def test_unlabelled_nodes_are_left_alone() -> None:
    # A node the detector never scored must not be silently dropped: absence of
    # a factuality label is not evidence against the event.
    result = purify_graph(_graph(), {"m1": "CT+"})
    assert set(result.graph.nodes) == {"m1", "m2", "m3", "m4"}
    assert result.dropped_nodes == ()


def test_policy_is_configurable_and_validated() -> None:
    strict = PurificationPolicy(drop_labels=frozenset({"CT-", "PS-"}), weights={"Uu": 0.5})
    result = purify_graph(_graph(), {"m1": "CT+", "m2": "PS-", "m3": "CT+", "m4": "CT+"}, strict)
    assert result.dropped_nodes == ("m2",)

    with pytest.raises(ValueError, match="unknown factuality label"):
        PurificationPolicy(drop_labels=frozenset({"CT?"}))
    with pytest.raises(ValueError, match="weight"):
        PurificationPolicy(weights={"Uu": 1.5})


def test_report_quantifies_the_change_in_both_directions() -> None:
    graph = _graph()
    labels = {"m1": "CT+", "m2": "CT-", "m3": "Uu", "m4": "CT+"}
    report = purification_report(graph, purify_graph(graph, labels))
    assert report["n_nodes_before"] == 4
    assert report["n_nodes_after"] == 3
    assert report["n_edges_before"] == 3
    assert report["n_edges_after"] == 1
    assert report["node_retention"] == pytest.approx(0.75)
    assert report["edge_retention"] == pytest.approx(1 / 3)
    # Consistency diagnostics before and after, so a purification that removed
    # violations and one that merely removed edges are distinguishable.
    assert "consistency_before" in report
    assert "consistency_after" in report


def test_random_control_isolates_the_shrinkage_confound() -> None:
    graph = _graph()
    control = random_drop_control(graph, n_drop=1, trials=3)
    # Deleting one node blindly still removes edges, which is the whole point:
    # the control says how much "fewer violations" comes for free.
    assert control["n_edges"] < len(graph.edges)
    assert "causal_cyclic_scc" in control


def test_report_carries_the_control_whenever_nodes_were_dropped() -> None:
    graph = _graph()
    labels = {"m1": "CT+", "m2": "CT-", "m3": "CT+", "m4": "CT+"}
    report = purification_report(graph, purify_graph(graph, labels), control_trials=3)
    # Same number of nodes removed as the purification removed, so the two
    # sides of the comparison are matched on size.
    assert report["random_control"]["n_edges"] > 0

    # No nodes dropped -> nothing to control for, and no misleading empty entry.
    nothing = purify_graph(graph, {"m1": "CT+"})
    assert purification_report(graph, nothing)["random_control"] == {}


def test_default_policy_keeps_factual_and_probable_events() -> None:
    assert DEFAULT_POLICY.drop_labels == frozenset({"CT-"})
    assert DEFAULT_POLICY.weights["CT+"] == 1.0
    assert DEFAULT_POLICY.weights["PS+"] == 1.0
    assert 0.0 < DEFAULT_POLICY.weights["PS-"] < 1.0
    assert 0.0 < DEFAULT_POLICY.weights["Uu"] < 1.0
