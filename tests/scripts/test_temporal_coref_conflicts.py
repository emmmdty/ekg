"""Gold identity evaluates frozen predictions; it never creates temporal input."""

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def script(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    spec = importlib.util.spec_from_file_location(
        "report_temporal_coref_conflicts", ROOT / "scripts/report_temporal_coref_conflicts.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def gold():
    return {"id": "d", "TIMEX": [{"id": "time"}], "events": [
        {"id": "e1", "type": "Attack", "mention": [
            {"id": "a", "trigger_word": "attack", "sent_id": 0},
            {"id": "b", "trigger_word": "attack", "sent_id": 1}]},
        {"id": "e2", "type": "Attack", "mention": [
            {"id": "c", "trigger_word": "attack", "sent_id": 2}]},
    ]}


def prediction():
    return {"id": "d", "coreference": [["a", "b", "c"]],
            "temporal_relations": {"BEFORE": [["a", "b"], ["c", "a"], ["b", "time"]]}}


def test_predicted_before_conflicts_include_correct_and_incorrect_merges(monkeypatch):
    result = script(monkeypatch).audit_conflicts(gold(), prediction())
    assert result["merged_pairs"] == {"gold_same": 1, "gold_different": 2}
    assert result["before_conflicts"] == {"gold_same": 1, "gold_different": 1}
    assert result["high_similarity_cross_sentence_before"] == result["before_conflicts"]


def test_gold_clusters_do_not_create_predicted_before(monkeypatch):
    pred = prediction()
    pred["temporal_relations"]["BEFORE"] = []
    result = script(monkeypatch).audit_conflicts(gold(), pred)
    assert result["before_conflicts"] == {"gold_same": 0, "gold_different": 0}


def test_unknown_temporal_prediction_endpoint_fails(monkeypatch):
    pred = prediction()
    pred["temporal_relations"]["BEFORE"] = [["a", "unknown"]]
    with pytest.raises(ValueError, match="temporal endpoint"):
        script(monkeypatch).audit_conflicts(gold(), pred)


def test_reversed_and_duplicate_before_edges_do_not_double_count(monkeypatch):
    pred = prediction()
    pred["temporal_relations"]["BEFORE"] = [["a", "c"], ["c", "a"], ["a", "c"]]
    assert script(monkeypatch).audit_conflicts(gold(), pred)["before_conflicts"] == {
        "gold_same": 0, "gold_different": 1}
