"""Tests for factuality metrics: macro-F1 discipline and evidence span scoring."""

from __future__ import annotations

import pytest

from ekg.factuality.metrics import (
    MAJORITY_LABEL,
    evidence_span_prf,
    factuality_report,
    majority_baseline_report,
)
from ekg.relations.data.maven_fact import FACTUALITY_LABELS


def test_report_covers_every_class_even_when_never_predicted() -> None:
    gold = {"a": "CT+", "b": "CT+", "c": "PS+", "d": "Uu"}
    predicted = dict.fromkeys(gold, "CT+")
    report = factuality_report(predicted, gold)

    assert set(report["per_class"]) == set(FACTUALITY_LABELS)
    # A class the system never predicts scores 0, it does not vanish from the
    # average — that is the whole point of macro over micro here.
    assert report["per_class"]["PS+"]["f1"] == 0.0
    assert report["per_class"]["PS-"]["n_gold"] == 0
    assert report["macro_f1"] == pytest.approx(
        sum(report["per_class"][c]["f1"] for c in FACTUALITY_LABELS) / len(FACTUALITY_LABELS)
    )


def test_accuracy_is_reported_but_macro_f1_is_the_headline() -> None:
    # 3 of 4 correct by predicting the majority class only.
    gold = {"a": "CT+", "b": "CT+", "c": "CT+", "d": "PS+"}
    report = factuality_report(dict.fromkeys(gold, "CT+"), gold)
    assert report["accuracy"] == pytest.approx(0.75)
    # High accuracy, near-worthless macro-F1: 1 class at f1>0, 4 classes at 0.
    assert report["macro_f1"] == pytest.approx(2 * 0.75 * 1.0 / 1.75 / 5)


def test_majority_baseline_is_the_floor_macro_f1_must_beat() -> None:
    gold = {f"m{i}": "CT+" for i in range(19)} | {"m19": "PS+"}
    baseline = majority_baseline_report(gold)
    assert MAJORITY_LABEL == "CT+"
    assert baseline["accuracy"] == pytest.approx(0.95)
    assert baseline["macro_f1"] < 0.2
    # Identical to predicting the majority label everywhere, by construction.
    assert baseline == factuality_report(dict.fromkeys(gold, MAJORITY_LABEL), gold)


def test_perfect_prediction_scores_one() -> None:
    gold = {"a": "CT+", "b": "PS+", "c": "CT-", "d": "PS-", "e": "Uu"}
    report = factuality_report(dict(gold), gold)
    assert report["macro_f1"] == pytest.approx(1.0)
    assert report["accuracy"] == pytest.approx(1.0)


def test_missing_or_unknown_predictions_are_fail_fast() -> None:
    gold = {"a": "CT+", "b": "PS+"}
    with pytest.raises(ValueError, match="without a prediction"):
        factuality_report({"a": "CT+"}, gold)
    with pytest.raises(ValueError, match="unknown mention"):
        factuality_report({"a": "CT+", "b": "PS+", "zz": "CT+"}, gold)
    with pytest.raises(ValueError, match="label"):
        factuality_report({"a": "CT+", "b": "MAYBE"}, gold)


def test_evidence_span_prf_scores_exact_spans() -> None:
    gold = {"a": {(0, 3), (4, 9)}, "b": {(2, 5)}, "c": set()}
    predicted = {"a": {(0, 3), (10, 12)}, "b": {(2, 5)}, "c": {(1, 2)}}
    prf = evidence_span_prf(predicted, gold)
    # tp = (0,3) and (2,5); n_pred = 4; n_gold = 3.
    assert (prf["tp"], prf["n_pred"], prf["n_gold"]) == (2, 4, 3)
    assert prf["precision"] == pytest.approx(0.5)
    assert prf["recall"] == pytest.approx(2 / 3)


def test_evidence_span_prf_denominator_is_annotated_mentions_only() -> None:
    # Only 843 of 17,780 valid mentions carry evidence; scoring over all of them
    # would divide by the wrong number, so the report says how many contributed.
    gold = {"a": {(0, 3)}, "b": set(), "c": set()}
    prf = evidence_span_prf({"a": {(0, 3)}, "b": set(), "c": set()}, gold)
    assert prf["n_gold"] == 1
    assert prf["n_mentions_with_evidence"] == 1
    assert prf["f1"] == pytest.approx(1.0)
