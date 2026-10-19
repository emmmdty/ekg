"""Direction, subtype and absence must not be double-counted as one mechanism."""

import importlib.util
import json
from copy import deepcopy
from pathlib import Path

import pytest

from ekg.relations.maven_ere_official import (
    OfficialProtocolError,
    empty_official_prediction,
)

spec = importlib.util.spec_from_file_location(
    "report_a4_direction_errors",
    Path(__file__).resolve().parents[2] / "scripts/report_a4_direction_errors.py",
)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


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


@pytest.mark.parametrize(
    ("subtype", "pair", "kind"),
    [
        ("PRECONDITION", ["a", "c"], "same_direction_wrong_subtype"),
        ("CAUSE", ["c", "a"], "reverse_only_same_subtype"),
        ("PRECONDITION", ["c", "a"], "reverse_only_wrong_subtype"),
    ],
)
def test_wrong_edges_partition_false_positives_and_false_negatives(subtype, pair, kind):
    gold, pred = fixture()
    pred["causal_relations"][subtype] = [pair]
    report = module.profile({"d": gold}, {"d": pred})
    total = report["total"]
    assert total["gold_positive"] == 4  # Cartesian expansion, not one event edge
    assert total["predicted_positive"] == 1
    assert total["true_positive"] == 0
    assert total["false_negative"][kind] == 1
    assert total["false_negative"]["neither_direction_positive"] == 3
    assert sum(total["false_negative"].values()) == 4
    assert total["false_positive"][kind] == 1
    assert sum(total["false_positive"].values()) == 1
    assert sum(map(sum, report["confusion"])) == 12


def test_subtype_error_with_reverse_edge_keeps_overlap_but_one_primary_bucket():
    gold, pred = fixture()
    pred["causal_relations"]["PRECONDITION"] = [["a", "c"]]
    pred["causal_relations"]["CAUSE"] = [["c", "a"]]
    total = module.profile({"d": gold}, {"d": pred})["total"]
    assert total["false_negative"]["same_direction_wrong_subtype"] == 1
    assert total["false_negative"]["reverse_only_same_subtype"] == 0
    assert total["fn_with_any_reverse_prediction"] == 1
    assert sum(total["false_negative"].values()) == 4
    assert sum(total["false_positive"].values()) == 2


def test_correct_edge_and_unannotated_edge_preserve_native_confusion():
    gold, pred = fixture()
    pred["causal_relations"]["CAUSE"] = [["a", "c"], ["a", "b"]]
    report = module.profile({"d": gold}, {"d": pred})
    assert report["total"]["true_positive"] == 1
    assert report["total"]["false_positive"]["neither_direction_positive"] == 1
    assert report["confusion"] == [[7, 0, 1], [0, 0, 0], [3, 0, 1]]
    assert report["diagnostic_only"] is True


def test_missing_document_and_changed_candidate_population_fail():
    gold, pred = fixture()
    with pytest.raises(OfficialProtocolError, match="document IDs differ"):
        module.profile({"d": gold}, {})
    with pytest.raises(OfficialProtocolError, match="candidate population digest mismatch"):
        module.profile({"d": gold}, {"d": pred}, expected_candidate_digest="wrong")


def test_overlapping_gold_subtypes_are_rejected_instead_of_overwritten():
    gold, pred = fixture()
    gold["causal_relations"]["PRECONDITION"] = [["e1", "e2"]]
    with pytest.raises(OfficialProtocolError, match="causal"):
        module.profile({"d": gold}, {"d": pred})


def test_bidirectional_annotations_do_not_make_a_true_positive_a_direction_error():
    gold, pred = fixture()
    gold["causal_relations"]["CAUSE"].append(["e2", "e1"])
    pred["causal_relations"]["CAUSE"] = [["a", "c"], ["c", "a"]]
    original = deepcopy(pred)
    total = module.profile({"d": gold}, {"d": pred})["total"]
    assert total["true_positive"] == 2
    assert sum(total["false_positive"].values()) == 0
    assert sum(total["false_negative"].values()) == 6
    assert pred == original


def test_command_rejects_sealed_manifest_before_reading_gold(tmp_path, monkeypatch):
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"split_role": "final-valid", "doc_ids": ["d"]}))
    monkeypatch.setattr("sys.argv", [
        "report_a4_direction_errors.py", "--gold", str(tmp_path / "absent-gold.jsonl"),
        "--pred", str(tmp_path / "absent-pred.jsonl"), "--manifest", str(manifest),
        "--candidate-digest", "unused", "--output", str(tmp_path / "out.json"),
    ])
    with pytest.raises(SystemExit, match="train or internal-dev"):
        module.main()
