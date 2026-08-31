"""Pair-classification harness: the same-setting bridge between generative
edge lists and supervised pair classifiers (MAVEN-ERE convention: gold mentions
given, score per-pair labels). Load-bearing bits: mention order comes from text
position (the loader appends per event, not in reading order), hallucinated
mention ids are penalised *and* counted, and the window diagnostic separates
the structural recall ceiling from model misses.
"""

from __future__ import annotations

import pytest

from ekg.core.schema import EventNode, EvidenceSpan, RelationEdge, RelationType
from ekg.relations.data.maven_ere import RelationDocument, _parse_document
from ekg.relations.pairs import (
    CROSS_SENTENCE,
    SAME_SENTENCE,
    candidate_pairs,
    edges_to_pair_labels,
    gold_pair_labels,
    mention_order,
    pair_examples,
    pair_prf,
    window_recall_ceiling,
)


def _node(mid: str, sent: int, pos: int) -> EventNode:
    return EventNode(
        event_id=mid,
        event_type="E",
        doc_id="d1",
        trigger=mid,
        trigger_evidence=[
            EvidenceSpan(doc_id="d1", char_start=pos, char_end=pos + 1, sent_id=sent, text=mid)
        ],
    )


def _doc() -> RelationDocument:
    # textual order: m1 (s0,0) < m2 (s0,10) < m3 (s1,0) < m4 (s2,0);
    # nodes deliberately shuffled to prove order comes from spans, not the list
    nodes = [_node("m3", 1, 0), _node("m1", 0, 0), _node("m4", 2, 0), _node("m2", 0, 10)]
    gold = [
        RelationEdge(
            head_id="m1", tail_id="m2", relation_type=RelationType.COREFERENCE, directed=False
        ),
        RelationEdge(
            head_id="m1", tail_id="m3", relation_type=RelationType.TEMPORAL, subtype="BEFORE"
        ),
        RelationEdge(
            head_id="m1", tail_id="m4", relation_type=RelationType.CAUSAL, subtype="CAUSE"
        ),
    ]
    return RelationDocument(doc_id="d1", nodes=nodes, gold_edges=gold)


def test_mention_order_uses_text_position() -> None:
    order = mention_order(_doc())
    assert [m for m, _ in sorted(order.items(), key=lambda kv: kv[1])] == ["m1", "m2", "m3", "m4"]


def test_candidate_pairs_full_and_windowed() -> None:
    doc = _doc()
    assert len(candidate_pairs(doc)) == 12  # 4 * 3 ordered pairs
    near = candidate_pairs(doc, max_distance=1)
    assert len(near) == 6  # only textual neighbours, both directions
    assert ("m1", "m2") in near and ("m2", "m1") in near
    assert ("m1", "m3") not in near


def test_edges_to_pair_labels_dedups_by_confidence() -> None:
    edges = [
        RelationEdge(
            head_id="m1", tail_id="m3", relation_type=RelationType.TEMPORAL,
            subtype="OVERLAP", confidence=0.4,
        ),
        RelationEdge(
            head_id="m1", tail_id="m3", relation_type=RelationType.TEMPORAL,
            subtype="BEFORE", confidence=0.9,
        ),
    ]
    labels = edges_to_pair_labels(edges, family=RelationType.TEMPORAL)
    assert labels == {("m1", "m3"): "BEFORE"}


def test_pair_prf_perfect_and_hallucinated() -> None:
    doc = _doc()
    perfect = pair_prf(doc.gold_edges, doc)
    assert perfect["micro"]["f1"] == pytest.approx(1.0)
    assert perfect["coreference"]["f1"] == pytest.approx(1.0)
    assert perfect["diagnostics"]["hallucinated_pred_pairs"] == 0

    hallucinated = doc.gold_edges + [
        RelationEdge(
            head_id="m1", tail_id="ghost", relation_type=RelationType.CAUSAL, subtype="CAUSE"
        )
    ]
    res = pair_prf(hallucinated, doc)
    # the ghost pair is a false positive AND separately accounted
    assert res["diagnostics"]["hallucinated_pred_pairs"] == 1
    assert res["causal"]["precision"] == pytest.approx(0.5)
    assert res["causal"]["recall"] == pytest.approx(1.0)


def test_pair_prf_windowed_reports_structural_ceiling() -> None:
    doc = _doc()
    res = pair_prf(doc.gold_edges, doc, max_distance=2)
    # causal m1->m4 (distance 3) leaves the universe on both sides
    assert res["diagnostics"]["out_of_window_gold"] == 1
    assert res["causal"]["n_gold"] == 0
    assert res["temporal"]["f1"] == pytest.approx(1.0)


def test_window_recall_ceiling_counts_reachable_gold() -> None:
    doc = _doc()
    # window of 2 consecutive mentions: only the adjacent coref pair fits
    ceiling = window_recall_ceiling([doc], window_events=2)
    assert ceiling["reachable_gold"] == 1
    assert ceiling["total_gold"] == 3
    assert ceiling["ceiling"] == pytest.approx(1 / 3)
    # a window spanning the whole document reaches everything
    assert window_recall_ceiling([doc], window_events=4)["ceiling"] == pytest.approx(1.0)


def test_pair_examples_cover_universe_with_labels() -> None:
    doc = _doc()
    examples = pair_examples(doc)
    by_pair = {(e.head_id, e.tail_id): e for e in examples}
    assert len(examples) == 12
    assert by_pair[("m1", "m3")].labels == {"temporal": "BEFORE"}
    assert by_pair[("m1", "m2")].labels == {"coreference": "COREF"}
    # symmetric coref labels both directions; unrelated pairs carry no labels
    assert by_pair[("m2", "m1")].labels == {"coreference": "COREF"}
    assert by_pair[("m3", "m4")].labels == {}
    assert by_pair[("m1", "m4")].distance == 3
    assert by_pair[("m1", "m2")].position == SAME_SENTENCE
    assert by_pair[("m1", "m3")].position == CROSS_SENTENCE


def test_official_event_relation_expansion_labels_all_cluster_mention_pairs() -> None:
    doc = _doc()
    doc.representative = {"e1": "m1", "e2": "m4"}
    doc.clusters = {"e1": ("m1", "m2"), "e2": ("m3", "m4")}

    historical = gold_pair_labels(doc, family=RelationType.CAUSAL)
    official = gold_pair_labels(
        doc,
        family=RelationType.CAUSAL,
        expand_event_relations=True,
    )

    assert historical == {("m1", "m4"): "CAUSE"}
    assert official == {
        ("m1", "m3"): "CAUSE",
        ("m1", "m4"): "CAUSE",
        ("m2", "m3"): "CAUSE",
        ("m2", "m4"): "CAUSE",
    }
    rows = pair_examples(doc, expand_event_relations=True)
    by_pair = {(row.head_id, row.tail_id): row for row in rows}
    assert by_pair[("m2", "m3")].labels["causal"] == "CAUSE"


def test_timex_nodes_recover_temporal_gold_without_touching_causal_universe() -> None:
    """Official parity: temporal scores TIMEX endpoints, causal/subevent do not.

    Loading without TIMEX silently dropped every temporal relation with a TIMEX
    endpoint (39% of gold). Loading with TIMEX must recover them while leaving the
    causal/subevent candidate population byte-identical.
    """
    record = {
        "id": "doc-1",
        "tokens": [["a", "b", "c", "d"]],
        "events": [
            {
                "id": "EV1",
                "type": "Attack",
                "mention": [{"id": "m1", "trigger_word": "a", "sent_id": 0, "offset": [0, 1]}],
            },
            {
                "id": "EV2",
                "type": "Attack",
                "mention": [{"id": "m2", "trigger_word": "b", "sent_id": 0, "offset": [1, 2]}],
            },
        ],
        "TIMEX": [{"id": "TIME_1", "mention": "c", "type": "DATE", "sent_id": 0, "offset": [2, 3]}],
        "temporal_relations": {"BEFORE": [["EV1", "TIME_1"], ["EV1", "EV2"]]},
        "causal_relations": {"CAUSE": [["EV1", "EV2"]]},
        "subevent_relations": [],
    }

    without = _parse_document(record, include_timex=False)
    with_timex = _parse_document(record, include_timex=True)

    temporal_without = [
        e for e in without.gold_edges if e.relation_type is RelationType.TEMPORAL
    ]
    temporal_with = [
        e for e in with_timex.gold_edges if e.relation_type is RelationType.TEMPORAL
    ]
    assert len(temporal_without) == 1  # the TIMEX endpoint was unrepresentable
    assert len(temporal_with) == 2  # ... and is recovered

    rows = pair_examples(with_timex, expand_event_relations=True)
    causal_rows = [r for r in rows if "causal" not in r.ignored_families]
    assert len(causal_rows) == 2  # exactly the two event-event ordered pairs
    assert sum(1 for r in causal_rows if r.labels.get("causal") == "CAUSE") == 1
    # every pair touching the TIMEX is ignored for the non-temporal families rather
    # than counted as a negative; official excludes TIMEX from coreference too
    ignored = [r for r in rows if r.ignored_families]
    assert len(ignored) == 4
    assert all("temporal" not in r.ignored_families for r in ignored)
    assert all({"causal", "subevent"} <= r.ignored_families for r in ignored)


def test_loader_fails_fast_on_unresolvable_endpoint_when_timex_enabled() -> None:
    record = {
        "id": "doc-1",
        "tokens": [["a", "b"]],
        "events": [
            {
                "id": "EV1",
                "type": "Attack",
                "mention": [{"id": "m1", "trigger_word": "a", "sent_id": 0, "offset": [0, 1]}],
            }
        ],
        "TIMEX": [],
        "temporal_relations": {"BEFORE": [["EV1", "GHOST"]]},
    }
    with pytest.raises(ValueError, match="not resolvable"):
        _parse_document(record, include_timex=True)
