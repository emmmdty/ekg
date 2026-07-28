"""Tests for structure-aware factuality detection (CPU paths)."""

from __future__ import annotations

import pytest

from ekg.core.schema import RelationEdge, RelationType
from ekg.factuality.detection import (
    STRUCTURE_FEATURE_NAMES,
    FactualityPrediction,
    LexiconFactualityDetector,
    StructureContext,
    factuality_detectors,
    structure_contexts,
)
from ekg.relations.data.maven_fact import load_maven_fact


@pytest.fixture
def docs(fixtures_dir):
    return list(load_maven_fact(fixtures_dir / "maven_fact" / "sample.jsonl"))


def test_structure_contexts_count_each_relation_role_separately(docs) -> None:
    doc = docs[0]
    contexts = structure_contexts(doc.mentions, doc.gold_edges)
    assert set(contexts) == {m.mention_id for m in doc.mentions}

    # m1 is the cause of m2, before m3, and the parent of m2.
    m1 = contexts["fdoc1::m1"]
    assert (m1.causal_out, m1.causal_in) == (1, 0)
    assert (m1.temporal_out, m1.temporal_in) == (1, 0)
    assert (m1.subevent_out, m1.subevent_in) == (1, 0)
    # m2 sees the same edges from the other side; direction must not be pooled,
    # because "is asserted as a cause" and "is asserted as an effect" are
    # different evidence about whether an event happened.
    m2 = contexts["fdoc1::m2"]
    assert (m2.causal_out, m2.causal_in) == (0, 1)
    assert (m2.subevent_out, m2.subevent_in) == (0, 1)


def test_structure_contexts_carry_coref_size_and_argument_count(docs) -> None:
    contexts = structure_contexts(docs[1].mentions, docs[1].gold_edges)
    # fdoc2's EV1 has two mentions, so both sit in a coreference cluster of 2.
    assert contexts["fdoc2::m1"].coref_degree == 1
    assert contexts["fdoc2::m2"].coref_degree == 1
    assert contexts["fdoc2::m3"].coref_degree == 0

    doc = docs[0]
    contexts = structure_contexts(doc.mentions, doc.gold_edges, nodes=doc.nodes)
    assert contexts["fdoc1::m1"].n_arguments == 2  # Agent, Location
    assert contexts["fdoc1::m2"].n_arguments == 0


def test_feature_vector_is_named_bounded_and_deterministic(docs) -> None:
    doc = docs[0]
    contexts = structure_contexts(doc.mentions, doc.gold_edges, nodes=doc.nodes)
    vector = contexts["fdoc1::m1"].as_vector()
    assert len(vector) == len(STRUCTURE_FEATURE_NAMES)
    # log1p-compressed counts: a hub mention cannot swamp the encoder features
    # it is concatenated with.
    assert all(0.0 <= v <= 5.0 for v in vector)
    assert vector == contexts["fdoc1::m1"].as_vector()


def test_empty_graph_gives_zero_context_not_a_missing_key(docs) -> None:
    doc = docs[0]
    contexts = structure_contexts(doc.mentions, [])
    assert set(contexts) == {m.mention_id for m in doc.mentions}
    zero = StructureContext(mention_id="fdoc1::m1")
    assert contexts["fdoc1::m1"].as_vector() == zero.as_vector()


def test_edges_on_unknown_mentions_are_ignored_not_fatal(docs) -> None:
    doc = docs[0]
    stray = RelationEdge(
        head_id="fdoc1::m1", tail_id="other::zz", relation_type=RelationType.CAUSAL
    )
    contexts = structure_contexts(doc.mentions, [*doc.gold_edges, stray])
    # A predicted graph may point at mentions outside the scored set; the
    # endpoint that *is* in the set still gets its edge counted.
    assert contexts["fdoc1::m1"].causal_out == 2


def test_lexicon_detector_memorizes_the_majority_label_per_trigger(docs) -> None:
    detector = LexiconFactualityDetector().fit(docs)
    predictions = detector.predict(docs[0])
    assert set(predictions) == {m.mention_id for m in docs[0].mentions}
    assert predictions["fdoc1::m2"].factuality == "CT-"
    assert isinstance(predictions["fdoc1::m2"], FactualityPrediction)
    assert 0.0 <= predictions["fdoc1::m2"].confidence <= 1.0


def test_lexicon_detector_backs_off_to_the_majority_class(docs) -> None:
    detector = LexiconFactualityDetector().fit(docs)
    # An unseen trigger must still get a prediction: the metrics refuse to score
    # a mention the system skipped, so abstention is not an option here.
    unseen = docs[0]
    detector.counts.pop("restrain")
    assert detector.predict(unseen)["fdoc1::m2"].factuality == "CT+"


def test_lexicon_detector_roundtrips_through_a_checkpoint(docs, tmp_path) -> None:
    path = tmp_path / "lexicon.json"
    LexiconFactualityDetector().fit(docs).save(path)
    reloaded = LexiconFactualityDetector(checkpoint_path=path)
    assert reloaded.predict(docs[0])["fdoc1::m2"].factuality == "CT-"


def test_detectors_are_registered(docs) -> None:
    assert "lexicon" in factuality_detectors
    assert "supervised" in factuality_detectors
    assert isinstance(factuality_detectors.create("lexicon"), LexiconFactualityDetector)
