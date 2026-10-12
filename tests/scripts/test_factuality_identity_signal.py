"""Keep the train-only factuality oracle distinct from event identity labels."""

import copy
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def script():
    spec = importlib.util.spec_from_file_location(
        "report_factuality_identity_signal", ROOT / "scripts/report_factuality_identity_signal.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def documents():
    ere = {"id": "d", "tokens": [["attack"], ["attack"], ["attack"]], "events": [
        {"id": "e1", "type": "Attack", "mention": [
            {"id": "a", "trigger_word": "attack", "sent_id": 0, "offset": [0, 1]},
            {"id": "b", "trigger_word": "attack", "sent_id": 1, "offset": [0, 1]}]},
        {"id": "e2", "type": "Attack", "mention": [
            {"id": "c", "trigger_word": "attack", "sent_id": 2, "offset": [0, 1]}]}]}
    fact = copy.deepcopy(ere)
    for event in fact["events"]:
        for mention in event["mention"]:
            mention["factuality"] = "CT+" if mention["id"] != "b" else "Uu"
    return ere, fact


def test_different_factuality_does_not_imply_different_identity():
    row = script().audit_document(*documents())
    assert row["pairs"]["all_same_type"]["CT+|Uu"] == {
        "coreferent": 1, "noncoreferent": 1}
    assert row["pairs"]["all_same_type"]["CT+|CT+"] == {
        "coreferent": 0, "noncoreferent": 1}
    assert row["mixed_label_gold_clusters"] == 1
    assert row["pairs"]["high_similarity_cross_sentence"] == row["pairs"]["all_same_type"]


def test_fact_cluster_identity_and_arguments_are_not_used():
    ere, fact = documents()
    before = script().audit_document(ere, fact)
    fact["events"][0]["id"] = "unrelated-fact-cluster"
    fact["events"][0]["arguments"] = [{"type": "Agent", "mentions": ["gold identity"]}]
    assert script().audit_document(ere, fact) == before


@pytest.mark.parametrize("drift", ["tokens", "offset", "type", "mention"])
def test_cross_dataset_drift_fails_fast(drift):
    ere, fact = documents()
    if drift == "tokens":
        fact["tokens"][0] = ["different"]
    elif drift == "offset":
        fact["events"][0]["mention"][0]["offset"] = [0, 2]
    elif drift == "type":
        fact["events"][0]["type"] = "Other"
    else:
        fact["events"][0]["mention"].pop()
    with pytest.raises(ValueError, match="alignment"):
        script().audit_document(ere, fact)


def test_duplicate_and_unknown_labels_are_rejected():
    ere, fact = documents()
    fact["events"][1]["mention"][0]["factuality"] = "not-a-label"
    with pytest.raises(ValueError, match="factuality label"):
        script().audit_document(ere, fact)
    ere, fact = documents()
    fact["events"][1]["mention"].append(copy.deepcopy(fact["events"][1]["mention"][0]))
    with pytest.raises(ValueError, match="duplicate mention"):
        script().audit_document(ere, fact)


def test_dev_and_final_manifests_are_rejected():
    for dataset in ("maven_fact", "maven_ere"):
        for role in ("internal-dev", "final-valid"):
            with pytest.raises(ValueError, match="train-only"):
                script().validate_manifest({"dataset": dataset, "split_role": role,
                                            "doc_ids": ["d"], "doc_count": 1}, dataset)


def test_observed_classes_are_used_instead_of_gold_factuality():
    row = script().audit_document(*documents(), observations={"a": "CT+", "b": "CT+", "c": "CT-"})
    assert row["label_source"] == "predicted_factuality"
    assert row["pairs"]["all_same_type"]["CT+|CT+"] == {
        "coreferent": 1, "noncoreferent": 0}
    assert row["pairs"]["all_same_type"]["CT+|CT-"] == {
        "coreferent": 0, "noncoreferent": 2}


def test_missing_observations_do_not_fall_back_to_gold():
    with pytest.raises(ValueError, match="observation coverage"):
        script().audit_document(*documents(), observations={"a": "CT+"})
