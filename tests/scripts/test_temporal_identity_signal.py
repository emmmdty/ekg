"""Catch identity leakage, missing-date vetoes and split drift in the C5 audit."""

import copy
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def script():
    spec = importlib.util.spec_from_file_location(
        "report_temporal_identity_signal", ROOT / "scripts/report_temporal_identity_signal.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def document():
    return {
        "id": "d", "tokens": [["attack", "2020"], ["attack", "2021"],
                                  ["attack", "2021"]],
        "events": [
            {"id": "e1", "type": "Attack", "mention": [
                {"id": "a", "trigger_word": "attack", "sent_id": 0, "offset": [0, 1]},
                {"id": "b", "trigger_word": "attack", "sent_id": 1, "offset": [0, 1]}]},
            {"id": "e2", "type": "Attack", "mention": [
                {"id": "c", "trigger_word": "attack", "sent_id": 2, "offset": [0, 1]}]},
        ],
        "TIMEX": [{"id": f"t{i}", "type": "DATE", "mention": year,
                   "sent_id": i, "offset": [1, 2]}
                  for i, year in enumerate(("2020", "2021", "2021"))],
        "temporal_relations": {"BEFORE": [["e1", "e2"]]},
    }


def test_missing_and_ambiguous_dates_stay_unknown():
    d = document()
    d["TIMEX"] = [d["TIMEX"][0], {"id": "extra", "type": "DATE", "mention": "attack",
                               "sent_id": 0, "offset": [0, 1]},
                  {"id": "duration", "type": "DURATION", "mention": "2021",
                   "sent_id": 1, "offset": [1, 2]}]
    assert script().sentence_dates(d) == {0: None, 1: None, 2: None}


def test_date_surfaces_ignore_gold_identity_and_temporal_edges():
    d = document()
    changed = copy.deepcopy(d)
    changed["events"] = []
    changed["temporal_relations"] = {}
    module = script()
    assert module.sentence_dates(d) == {0: "2020", 1: "2021", 2: "2021"}
    assert module.sentence_dates(changed) == module.sentence_dates(d)


def test_date_disagreement_can_hurt_true_coreference():
    result = script().audit_document(document())
    bucket = result["pairs"]["all_same_type"]
    assert bucket["different_date_surface"] == {"coreferent": 1, "noncoreferent": 1}
    assert bucket["same_date_surface"] == {"coreferent": 0, "noncoreferent": 1}
    assert result["pairs"]["high_similarity_cross_sentence"] == bucket
    assert result["gold_before"]["same_type_mention_pairs"] == 2
    assert result["gold_before"]["identity_circularity"] is True


def test_unresolved_temporal_endpoint_is_rejected():
    d = document()
    d["temporal_relations"]["BEFORE"] = [["missing", "e2"]]
    with pytest.raises(ValueError, match="temporal endpoint"):
        script().audit_document(d)


def test_bad_timex_offsets_are_rejected():
    d = document()
    d["TIMEX"][0]["offset"] = [1, 10]
    with pytest.raises(ValueError, match="TIMEX offset"):
        script().sentence_dates(d)


def test_audit_rejects_dev_and_final_manifests():
    validate = script().validate_manifest
    for role in ("internal-dev", "final-valid"):
        with pytest.raises(ValueError, match="train-only"):
            validate({"dataset": "maven_ere", "split_role": role, "doc_ids": ["d"],
                      "doc_count": 1})
    with pytest.raises(ValueError, match="duplicate"):
        validate({"dataset": "maven_ere", "split_role": "train", "doc_ids": ["d", "d"],
                  "doc_count": 2})
