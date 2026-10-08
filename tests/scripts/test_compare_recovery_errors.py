"""Recovery must distinguish fixing errors from merely exchanging them."""

import importlib.util
from copy import deepcopy
from pathlib import Path

import pytest

from ekg.relations.maven_ere_official import (
    OfficialProtocolError,
    empty_official_prediction,
)

spec = importlib.util.spec_from_file_location(
    "compare_recovery_errors", Path(__file__).resolve().parents[2]
    / "scripts/compare_recovery_errors.py",
)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
compare = module.compare


def fixture():
    gold = {
        "id": "d",
        "events": [
            {"id": "e1", "mention": [{"id": "a"}, {"id": "b"}]},
            {"id": "e2", "mention": [{"id": "c"}, {"id": "d"}]},
        ],
        "causal_relations": {"CAUSE": [["e1", "e2"]], "PRECONDITION": []},
    }
    return gold, empty_official_prediction(gold)


def test_coref_recovery_counts_transitive_errors_and_regressions():
    gold, control = fixture()
    control["coreference"] = [["a", "b", "c"]]
    candidate = deepcopy(control)
    candidate["coreference"] = [["a", "b"], ["c", "d"]]
    report = compare({"d": gold}, {"d": control}, {"d": candidate}, family="coreference")
    # The control loses c-d and falsely joins both a-c and b-c.
    assert report["total"] == {
        "recovered_positives": 1, "lost_positives": 0,
        "removed_false_positives": 2, "added_false_positives": 0,
        "control_true_positives": 1, "candidate_true_positives": 2,
        "control_false_positives": 2, "candidate_false_positives": 0,
        "gold_positives": 2,
    }


def test_causal_wrong_subtype_is_both_false_positive_and_missed_positive():
    gold, control = fixture()
    control["causal_relations"]["PRECONDITION"] = [["a", "c"]]
    candidate = deepcopy(control)
    candidate["causal_relations"] = {"CAUSE": [["a", "c"]], "PRECONDITION": []}
    report = compare({"d": gold}, {"d": control}, {"d": candidate}, family="causal")
    assert report["total"]["recovered_positives"] == 1
    assert report["total"]["removed_false_positives"] == 1
    assert report["total"]["gold_positives"] == 4  # event-to-mention expansion


def test_missing_document_cannot_be_reported_as_recovery():
    gold, control = fixture()
    with pytest.raises(OfficialProtocolError, match="document IDs differ"):
        compare({"d": gold}, {"d": control}, {}, family="coreference")
