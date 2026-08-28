"""The CodaLab submission builder's output shape.

Every assertion here mirrors something read off the official scorer
(`THU-KEG/MAVEN-ERE/evaluate.py`); each is a way the submission could score zero
while looking fine. Verified end-to-end on 2026-07-30 by feeding gold back
through this format: the official script returned 100.0 on all four metrics.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from ekg.core.schema import RelationEdge, RelationType

_SPEC = importlib.util.spec_from_file_location(
    "build_maven_ere_submission",
    Path(__file__).resolve().parents[2] / "scripts" / "build_maven_ere_submission.py",
)
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)  # type: ignore[union-attr]

CAUSAL_SUBTYPES = _MODULE.CAUSAL_SUBTYPES
TEMPORAL_SUBTYPES = _MODULE.TEMPORAL_SUBTYPES
relation_payload = _MODULE.relation_payload
strip_to_test_shape = _MODULE.strip_to_test_shape
enforce_no_skipped_relations = _MODULE.enforce_no_skipped_relations


def _edge(head: str, tail: str, kind: RelationType, subtype: str, conf: float) -> RelationEdge:
    return RelationEdge(
        head_id=f"docA::{head}", tail_id=f"docA::{tail}",
        relation_type=kind, subtype=subtype, directed=True, confidence=conf,
    )


def test_every_subtype_key_is_present_even_when_empty() -> None:
    """A missing key reads as "no prediction" for that whole subtype."""
    payload = relation_payload([], threshold=0.5)

    assert set(payload["temporal_relations"]) == set(TEMPORAL_SUBTYPES)
    assert set(payload["causal_relations"]) == set(CAUSAL_SUBTYPES)
    assert payload["subevent_relations"] == []


def test_ids_are_bare_and_direction_is_preserved() -> None:
    """The scorer keys on `m1 + m2` with bare mention ids, both directions apart."""
    payload = relation_payload(
        [_edge("m1", "m2", RelationType.CAUSAL, "CAUSE", 0.9)], threshold=0.5
    )

    assert payload["causal_relations"]["CAUSE"] == [["m1", "m2"]]
    # Not mirrored: (m2, m1) is a different, unpredicted pair.
    assert ["m2", "m1"] not in payload["causal_relations"]["CAUSE"]


def test_threshold_drops_low_confidence_edges() -> None:
    edges = [
        _edge("m1", "m2", RelationType.CAUSAL, "CAUSE", 0.9),
        _edge("m3", "m4", RelationType.CAUSAL, "CAUSE", 0.4),
    ]

    payload = relation_payload(edges, threshold=0.7)

    assert payload["causal_relations"]["CAUSE"] == [["m1", "m2"]]


def test_subevent_is_a_flat_list_not_a_dict() -> None:
    payload = relation_payload(
        [_edge("m1", "m2", RelationType.SUBEVENT, "SUBEVENT_OF", 0.9)], threshold=0.5
    )

    assert payload["subevent_relations"] == [["m1", "m2"]]


def test_coreference_propagation_expands_across_clusters_without_self_pairs() -> None:
    """Gold is expanded to every cross-cluster mention pair, so propagation mirrors it.

    The self-pair guard matters: the scorer only enumerates `m1 != m2`, so an
    (m, m) pair would raise a KeyError on its side rather than score zero.
    """
    payload = relation_payload(
        [_edge("m1", "m3", RelationType.CAUSAL, "CAUSE", 0.9)],
        threshold=0.5,
        clusters=[["m1", "m2"], ["m3", "m4"]],
    )

    assert payload["causal_relations"]["CAUSE"] == [
        ["m1", "m3"], ["m1", "m4"], ["m2", "m3"], ["m2", "m4"]
    ]

    same = relation_payload(
        [_edge("m1", "m2", RelationType.CAUSAL, "CAUSE", 0.9)],
        threshold=0.5,
        clusters=[["m1", "m2"]],
    )
    assert all(a != b for a, b in same["causal_relations"]["CAUSE"])


def test_coreference_edges_never_leak_into_the_relation_fields() -> None:
    payload = relation_payload(
        [_edge("m1", "m2", RelationType.COREFERENCE, "", 0.9)], threshold=0.5
    )

    assert payload["subevent_relations"] == []
    assert all(not v for v in payload["temporal_relations"].values())
    assert all(not v for v in payload["causal_relations"].values())


def test_strip_to_test_shape_flattens_clusters_and_drops_labels() -> None:
    record = {
        "id": "docA",
        "tokens": [["a", "b"]],
        "sentences": ["a b"],
        "events": [
            {"id": "E0", "type": "Attack", "type_id": 7,
             "mention": [{"id": "m1", "trigger_word": "a"}, {"id": "m2", "trigger_word": "b"}]}
        ],
        "TIMEX": [{"id": "t1"}],
        "temporal_relations": {"BEFORE": [["E0", "E0"]]},
        "causal_relations": {"CAUSE": []},
        "subevent_relations": [],
    }

    stripped = strip_to_test_shape(record)

    assert [m["id"] for m in stripped["event_mentions"]] == ["m1", "m2"]
    # The type moves from the cluster down onto each mention, as the test file has it.
    assert {m["type"] for m in stripped["event_mentions"]} == {"Attack"}
    assert stripped["TIMEX"] == [{"id": "t1"}]
    assert "events" not in stripped
    assert not any(k.endswith("_relations") for k in stripped)


def test_skipped_relations_are_exploratory_only() -> None:
    failures = [("docA", "unlocatable trigger")]

    with pytest.raises(SystemExit, match="confirmation output is invalid"):
        enforce_no_skipped_relations(failures, allow_skipped=False)

    enforce_no_skipped_relations(failures, allow_skipped=True)
