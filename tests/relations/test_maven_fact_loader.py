"""Tests for the MAVEN-FACT loader against the bundled fixture."""

from __future__ import annotations

import json

import pytest

from ekg.core.schema import RelationType
from ekg.relations.data.maven_fact import (
    FACTUALITY_LABELS,
    factuality_distribution,
    load_maven_fact,
)


def test_load_maven_fact_fixture(fixtures_dir) -> None:
    docs = list(load_maven_fact(fixtures_dir / "maven_fact" / "sample.jsonl"))
    assert [d.doc_id for d in docs] == ["fdoc1", "fdoc2"]

    doc = docs[0]
    # One record per event *mention*: factuality is annotated per mention, not
    # per event, so a multi-mention event can disagree with itself.
    assert [m.mention_id for m in doc.mentions] == ["fdoc1::m1", "fdoc1::m2", "fdoc1::m3"]
    assert [m.factuality for m in doc.mentions] == ["CT+", "CT-", "PS+"]
    # Mention ids are namespaced exactly like the MAVEN-ERE/Arg loaders, so these
    # join onto the same id space the predicted graph uses.
    assert [n.event_id for n in doc.nodes] == [m.mention_id for m in doc.mentions]


def test_labels_cover_the_official_five_classes() -> None:
    assert FACTUALITY_LABELS == ("CT+", "PS+", "CT-", "PS-", "Uu")


def test_trigger_span_slices_back_out_of_the_document(fixtures_dir) -> None:
    for doc in load_maven_fact(fixtures_dir / "maven_fact" / "sample.jsonl"):
        for mention in doc.mentions:
            span = mention.span
            assert doc.doc_text[span.char_start : span.char_end] == mention.trigger
            # `sent_id` is kept alongside the character offsets because the
            # released offsets are token-based and only meaningful with it.
            assert span.sent_id is not None


def test_evidence_spans_slice_back_and_mismatches_are_counted(fixtures_dir) -> None:
    docs = list(load_maven_fact(fixtures_dir / "maven_fact" / "sample.jsonl"))
    by_id = {m.mention_id: m for d in docs for m in d.mentions}

    restrain = by_id["fdoc1::m2"]
    assert [s.text for s in restrain.evidence] == ["was", "powerless", "to"]
    for span in restrain.evidence:
        assert docs[0].doc_text[span.char_start : span.char_end] == span.text
    assert docs[0].evidence_mismatches == 0

    # The released data mis-indexes a small number of evidence words (24/5,997 in
    # train, 6/1,296 in valid). Those are dropped and counted, never stored as a
    # span pointing at the wrong token.
    assert by_id["fdoc2::m1"].evidence == []
    assert docs[1].evidence_mismatches == 1


def test_arguments_use_character_offsets_and_are_shared_by_mentions(fixtures_dir) -> None:
    doc = next(iter(load_maven_fact(fixtures_dir / "maven_fact" / "sample.jsonl")))
    node = doc.nodes[0]
    # Argument offsets are *characters* on the same records whose mentions use
    # token offsets, so the loader checks each convention separately.
    assert node.arguments == {"Agent": "Rebels | them", "Location": "outpost"}
    for role, value in node.arguments.items():
        spans = node.argument_evidence[role]
        assert [doc.doc_text[s.char_start : s.char_end] for s in spans] == value.split(" | ")


def test_argument_offset_mismatch_is_fail_fast(tmp_path, fixtures_dir) -> None:
    record = json.loads((fixtures_dir / "maven_fact" / "sample.jsonl").read_text().splitlines()[0])
    record["events"][0]["arguments"][0]["mentions"][0]["offset"] = [0, 3]
    path = tmp_path / "broken.jsonl"
    path.write_text(json.dumps(record) + "\n")
    with pytest.raises(ValueError, match="argument"):
        list(load_maven_fact(path))


def test_relations_attach_to_representative_mentions(fixtures_dir) -> None:
    doc = next(iter(load_maven_fact(fixtures_dir / "maven_fact" / "sample.jsonl")))
    keys = {(e.relation_type, e.subtype, e.head_id, e.tail_id) for e in doc.gold_edges}
    assert (RelationType.CAUSAL, "CAUSE", "fdoc1::m1", "fdoc1::m2") in keys
    assert (RelationType.TEMPORAL, "BEFORE", "fdoc1::m1", "fdoc1::m3") in keys
    assert (RelationType.SUBEVENT, "SUBEVENT_OF", "fdoc1::m1", "fdoc1::m2") in keys


def test_coreference_edges_link_mentions_of_one_event(fixtures_dir) -> None:
    doc = list(load_maven_fact(fixtures_dir / "maven_fact" / "sample.jsonl"))[1]
    coref = [e for e in doc.gold_edges if e.relation_type is RelationType.COREFERENCE]
    assert [(e.head_id, e.tail_id) for e in coref] == [("fdoc2::m1", "fdoc2::m2")]


def test_factuality_distribution_counts_every_label(fixtures_dir) -> None:
    docs = list(load_maven_fact(fixtures_dir / "maven_fact" / "sample.jsonl"))
    counts = factuality_distribution(docs)
    assert counts == {"CT+": 2, "PS+": 1, "CT-": 1, "PS-": 1, "Uu": 1}
    # Every label is present as a key even at zero, so a report never silently
    # omits a class it scored.
    assert set(counts) == set(FACTUALITY_LABELS)


def test_trigger_offset_mismatch_is_fail_fast(tmp_path, fixtures_dir) -> None:
    record = json.loads((fixtures_dir / "maven_fact" / "sample.jsonl").read_text().splitlines()[0])
    record["events"][0]["mention"][0]["offset"] = [0, 1]  # now points at "Rebels"
    path = tmp_path / "broken.jsonl"
    path.write_text(json.dumps(record) + "\n")
    with pytest.raises(ValueError, match="offset"):
        list(load_maven_fact(path))


def test_unknown_factuality_label_is_fail_fast(tmp_path, fixtures_dir) -> None:
    record = json.loads((fixtures_dir / "maven_fact" / "sample.jsonl").read_text().splitlines()[0])
    record["events"][0]["mention"][0]["factuality"] = "CT?"
    path = tmp_path / "broken.jsonl"
    path.write_text(json.dumps(record) + "\n")
    with pytest.raises(ValueError, match="factuality"):
        list(load_maven_fact(path))


def test_document_is_the_token_join_and_disagreement_raises(tmp_path, fixtures_dir) -> None:
    record = json.loads((fixtures_dir / "maven_fact" / "sample.jsonl").read_text().splitlines()[0])
    record["document"] = record["document"].replace("dawn", "dusk")
    path = tmp_path / "broken.jsonl"
    path.write_text(json.dumps(record) + "\n")
    with pytest.raises(ValueError, match="document"):
        list(load_maven_fact(path))
