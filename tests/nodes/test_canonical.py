"""Uncertainty-aware canonicalization: merging, abstention, confidence, aggregation."""

from __future__ import annotations

import pytest

from ekg.core.calibration import IsotonicProbabilityCalibrator
from ekg.core.schema import EventNode, EvidenceSpan
from ekg.nodes.canonical import canonicalize
from ekg.nodes.coref import CorefPair
from ekg.nodes.metrics import merge_prf, mis_merge_report


def _node(node_id, trigger, start, *, arguments=None, event="E1") -> EventNode:
    return EventNode(
        event_id=node_id,
        event_type="Attacking",
        doc_id="d",
        trigger=trigger,
        trigger_evidence=[EvidenceSpan(doc_id="d", char_start=start, char_end=start + 1)],
        arguments=arguments or {},
        argument_evidence={
            role: [EvidenceSpan(doc_id="d", char_start=start, char_end=start + 1)]
            for role in (arguments or {})
        },
        metadata={"event": event},
    )


@pytest.fixture
def nodes() -> list[EventNode]:
    return [_node("a1", "attacked", 0), _node("a2", "assault", 10), _node("a3", "attack", 20)]


def test_merges_above_threshold_and_stops_below(nodes) -> None:
    scores = {("a1", "a2"): 0.9, ("a1", "a3"): 0.2, ("a2", "a3"): 0.1}
    result = canonicalize(nodes, scores, threshold=0.5)
    assert result.clusters() == [{"a1", "a2"}, {"a3"}]
    assert result.abstained_merges == []


def test_merged_confidence_is_the_weakest_accepted_link(nodes) -> None:
    # a3 joins the pair at average link (0.9 + 0.5) / 2 = 0.7, the weakest step.
    scores = {("a1", "a2"): 0.9, ("a1", "a3"): 0.9, ("a2", "a3"): 0.5}
    result = canonicalize(nodes, scores, threshold=0.5)
    assert result.clusters() == [{"a1", "a2", "a3"}]
    assert result.nodes[0].raw_confidence == pytest.approx(0.7)


def test_singleton_confidence_is_one_minus_its_strongest_external_link(nodes) -> None:
    scores = {("a1", "a2"): 0.9, ("a1", "a3"): 0.2, ("a2", "a3"): 0.1}
    result = canonicalize(nodes, scores, threshold=0.5)
    singleton = next(n for n in result.nodes if n.node_id == "a3")
    assert singleton.raw_confidence == pytest.approx(0.8)


def test_a_lone_mention_is_fully_confident() -> None:
    result = canonicalize([_node("a1", "attacked", 0)], {})
    assert result.nodes[0].raw_confidence == 1.0


def test_abstention_band_refuses_the_uncertain_merge_and_records_it(nodes) -> None:
    scores = {("a1", "a2"): 0.6, ("a1", "a3"): 0.1, ("a2", "a3"): 0.1}
    merged = canonicalize(nodes, scores, threshold=0.5)
    banded = canonicalize(nodes, scores, threshold=0.5, band=0.2)
    assert merged.clusters() == [{"a1", "a2"}, {"a3"}]
    assert banded.clusters() == [{"a1"}, {"a2"}, {"a3"}]
    assert banded.abstained_merges == [("a1", "a2", pytest.approx(0.6))]


def test_band_zero_records_no_abstention(nodes) -> None:
    scores = {("a1", "a2"): 0.5, ("a1", "a3"): 0.5, ("a2", "a3"): 0.5}
    assert canonicalize(nodes, scores, threshold=0.5, band=0.0).abstained_merges == []


def test_negative_band_is_fail_fast(nodes) -> None:
    with pytest.raises(ValueError, match="non-negative"):
        canonicalize(nodes, {}, band=-0.1)


def test_canonical_trigger_is_the_best_supported_mention(nodes) -> None:
    scores = {("a1", "a2"): 0.9, ("a1", "a3"): 0.9, ("a2", "a3"): 0.5}
    node = canonicalize(nodes, scores, threshold=0.5).nodes[0]
    assert node.canonical_trigger == "attacked"  # a1 carries the most link support
    assert len(node.evidence_spans) == 3  # every mention's evidence is kept


def test_conflicting_argument_fillers_are_kept_and_flagged() -> None:
    nodes = [
        _node("a1", "attacked", 0, arguments={"Agent": "Rebels", "Location": "outpost"}),
        _node("a2", "assault", 10, arguments={"Agent": "Militia", "Location": "outpost"}),
    ]
    node = canonicalize(nodes, {("a1", "a2"): 0.9}, threshold=0.5).nodes[0]
    assert node.arguments["Agent"] == "Rebels | Militia"
    assert node.arguments["Location"] == "outpost"
    assert node.conflicting_roles == ["Agent"]


def test_calibrator_maps_raw_confidence_to_node_confidence(nodes) -> None:
    calibrator = IsotonicProbabilityCalibrator().fit(
        [0.1, 0.4, 0.6, 0.9], [False, False, True, True]
    )
    scores = {("a1", "a2"): 0.9, ("a1", "a3"): 0.2, ("a2", "a3"): 0.1}
    result = canonicalize(nodes, scores, threshold=0.5, calibrator=calibrator)
    for node in result.nodes:
        assert node.node_confidence == calibrator.transform([node.raw_confidence])[0]


def test_projection_onto_the_frozen_schema_puts_extras_in_metadata(nodes) -> None:
    scores = {("a1", "a2"): 0.9, ("a1", "a3"): 0.2, ("a2", "a3"): 0.1}
    canonical = canonicalize(nodes, scores, threshold=0.5).nodes[0]
    event_node = canonical.to_event_node()
    assert isinstance(event_node, EventNode)
    assert event_node.confidence == canonical.node_confidence
    assert event_node.metadata["mention_cluster"] == "a1,a2"
    assert event_node.metadata["provenance"] == "nodes.canonical"


def test_empty_input_yields_no_nodes() -> None:
    assert canonicalize([], {}).nodes == []


def test_merge_prf_and_mis_merge_rate_see_the_wrong_join() -> None:
    cluster_of = {"a1": "E1", "a2": "E1", "a3": "E2"}
    perfect = merge_prf([{"a1", "a2"}, {"a3"}], cluster_of)
    assert perfect["f1"] == 1.0

    over_merged = [{"a1", "a2", "a3"}]
    prf = merge_prf(over_merged, cluster_of)
    assert prf["n_pred"] == 3 and prf["tp"] == 1
    report = mis_merge_report(over_merged, cluster_of, pairs=[])
    assert report["mis_merge_rate"] == pytest.approx(2 / 3)
    assert report["n_merges"] == 3


def test_hard_mis_merge_rate_has_its_own_denominator() -> None:
    cluster_of = {"a1": "E1", "a2": "E1", "a3": "E2"}
    hard = CorefPair("d", "a1", "a3", label=False, similarity=0.95)
    easy = CorefPair("d", "a2", "a3", label=False, similarity=0.1)
    report = mis_merge_report([{"a1", "a2", "a3"}], cluster_of, pairs=[hard, easy])
    assert report["n_hard_pairs"] == 1
    assert report["hard_mis_merge_rate"] == 1.0

    clean = mis_merge_report([{"a1", "a2"}, {"a3"}], cluster_of, pairs=[hard, easy])
    assert clean["hard_mis_merge_rate"] == 0.0
    assert clean["mis_merge_rate"] == 0.0
