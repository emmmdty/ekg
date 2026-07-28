"""Event detection: candidate universe, micro-F1 scoring, lexicon baseline."""

from __future__ import annotations

import pytest

from ekg.nodes.detection import (
    LexiconEventDetector,
    TypedSpan,
    detection_prf,
    event_detectors,
)
from ekg.relations.data import load_maven_arg


@pytest.fixture
def arg_docs(fixtures_dir):
    return list(load_maven_arg(fixtures_dir / "maven_arg" / "sample.jsonl"))


def _gold_prediction(doc) -> dict[str, TypedSpan]:
    return {
        c.candidate_id: TypedSpan(c.candidate_id, c.event_type, 1.0)
        for c in doc.candidates
        if c.event_id
    }


def test_perfect_prediction_scores_one(arg_docs) -> None:
    doc = arg_docs[0]
    report = detection_prf(_gold_prediction(doc), doc.candidates)
    assert report["typed"]["f1"] == 1.0
    assert report["identification"]["f1"] == 1.0
    assert report["typed"]["n_gold"] == 3
    assert report["n_candidates"] == 4


def test_wrong_type_costs_typed_f1_but_not_identification(arg_docs) -> None:
    doc = arg_docs[0]
    predicted = _gold_prediction(doc)
    predicted["adoc1::m3"] = TypedSpan("adoc1::m3", "Motion", 0.6)
    report = detection_prf(predicted, doc.candidates)
    # The span is found (identification intact) but mislabelled: exactly the
    # error mode a span-only metric would hide.
    assert report["identification"]["f1"] == 1.0
    assert report["typed"]["tp"] == 2
    assert report["typed"]["precision"] == pytest.approx(2 / 3)


def test_firing_on_a_negative_trigger_is_a_false_positive(arg_docs) -> None:
    doc = arg_docs[0]
    predicted = _gold_prediction(doc)
    predicted["adoc1::n1"] = TypedSpan("adoc1::n1", "Attacking", 0.9)
    report = detection_prf(predicted, doc.candidates)
    assert report["typed"]["n_pred"] == 4
    assert report["typed"]["recall"] == 1.0
    assert report["typed"]["precision"] == pytest.approx(3 / 4)


def test_prediction_on_an_unknown_candidate_is_rejected(arg_docs) -> None:
    doc = arg_docs[0]
    predicted = {"adoc1::ghost": TypedSpan("adoc1::ghost", "Attacking", 0.9)}
    with pytest.raises(ValueError, match="unknown candidate"):
        detection_prf(predicted, doc.candidates)


def test_lexicon_detector_is_registered_and_memorizes_training_triggers(arg_docs) -> None:
    assert "lexicon" in event_detectors
    detector = event_detectors.create("lexicon")
    detector.fit(arg_docs)
    predicted = detector.detect(arg_docs[0])
    assert detection_prf(predicted, arg_docs[0].candidates)["typed"]["f1"] == 1.0
    # A negative trigger seen only as a negative stays unpredicted.
    assert "adoc1::n1" not in predicted


def test_lexicon_detector_abstains_on_unseen_triggers(arg_docs) -> None:
    detector = LexiconEventDetector()
    detector.fit(arg_docs[1:])  # only doc2 ("marched" / "downtown")
    assert detector.detect(arg_docs[0]) == {}


def test_lexicon_detector_round_trips_through_disk(arg_docs, tmp_path) -> None:
    detector = LexiconEventDetector()
    detector.fit(arg_docs)
    path = tmp_path / "lexicon.json"
    detector.save(path)
    # Reloading goes through the same `checkpoint_path` argument the neural
    # detector takes, so a config selects either one identically.
    reloaded = event_detectors.create("lexicon", checkpoint_path=str(path))
    assert reloaded.detect(arg_docs[0]) == detector.detect(arg_docs[0])


def test_unfitted_lexicon_detector_predicts_nothing(arg_docs) -> None:
    assert LexiconEventDetector().detect(arg_docs[0]) == {}
