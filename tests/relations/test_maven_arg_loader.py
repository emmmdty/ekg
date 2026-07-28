"""Tests for the MAVEN-Arg loader against the bundled fixture."""

from __future__ import annotations

import json

import pytest

from ekg.relations.data.maven_arg import NONE_TYPE, load_maven_arg


def test_load_maven_arg_fixture(fixtures_dir) -> None:
    docs = list(load_maven_arg(fixtures_dir / "maven_arg" / "sample.jsonl"))
    assert [d.doc_id for d in docs] == ["adoc1", "adoc2"]

    doc = docs[0]
    # One node per event *mention*, so coreference stays a real clustering task.
    assert [n.event_id for n in doc.nodes] == ["adoc1::m1", "adoc1::m2", "adoc1::m3"]
    assert {n.event_type for n in doc.nodes} == {"Attacking", "Causation"}
    # Mention ids are namespaced exactly like the MAVEN-ERE loader, so canonical
    # nodes built here join straight onto the ERE id space used downstream.
    assert doc.clusters == {"EV1": ["adoc1::m1", "adoc1::m2"], "EV2": ["adoc1::m3"]}
    assert doc.gold_clusters() == [{"adoc1::m1", "adoc1::m2"}, {"adoc1::m3"}]


def test_arguments_resolve_inline_and_entity_refs(fixtures_dir) -> None:
    doc = next(iter(load_maven_arg(fixtures_dir / "maven_arg" / "sample.jsonl")))
    m1 = doc.nodes[0]
    # `Agent` is an entity reference, `Location` an inline span: both resolve to
    # surface text plus spans that slice back out of the document.
    assert m1.arguments == {"Agent": "Rebels", "Location": "outpost"}
    for role, value in m1.arguments.items():
        spans = m1.argument_evidence[role]
        assert [doc.doc_text[s.char_start : s.char_end] for s in spans] == value.split(" | ")
    # Event-level arguments are shared by every mention of that event.
    assert doc.nodes[1].arguments == m1.arguments


def test_trigger_evidence_slices_back_out_of_the_document(fixtures_dir) -> None:
    for doc in load_maven_arg(fixtures_dir / "maven_arg" / "sample.jsonl"):
        for node in doc.nodes:
            span = node.trigger_evidence[0]
            assert doc.doc_text[span.char_start : span.char_end] == node.trigger


def test_candidates_carry_gold_types_and_negative_triggers(fixtures_dir) -> None:
    doc = next(iter(load_maven_arg(fixtures_dir / "maven_arg" / "sample.jsonl")))
    by_id = {c.candidate_id: c for c in doc.candidates}
    assert by_id["adoc1::m1"].event_type == "Attacking"
    assert by_id["adoc1::m1"].event_id == "EV1"
    # Negative triggers are the official non-event candidates: the detection task
    # is a labelled decision over this same universe, not over gold spans only.
    assert by_id["adoc1::n1"].event_type == NONE_TYPE
    assert by_id["adoc1::n1"].event_id == ""
    assert len(doc.candidates) == 4


def test_offset_mismatch_is_fail_fast(tmp_path, fixtures_dir) -> None:
    record = json.loads((fixtures_dir / "maven_arg" / "sample.jsonl").read_text().splitlines()[0])
    record["events"][0]["mention"][0]["offset"] = [0, 6]  # now points at "Rebels"
    path = tmp_path / "broken.jsonl"
    path.write_text(json.dumps(record) + "\n")
    with pytest.raises(ValueError, match="offset"):
        list(load_maven_arg(path))
