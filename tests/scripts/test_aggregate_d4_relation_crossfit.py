import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "aggregate_d4_relation_crossfit",
    ROOT / "scripts/aggregate_d4_relation_crossfit.py",
)
assert SPEC is not None and SPEC.loader is not None
aggregate = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = aggregate
SPEC.loader.exec_module(aggregate)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _record(doc_id: str) -> dict:
    return {
        "id": doc_id,
        "tokens": [["a", "b"]],
        "sentences": ["a b"],
        "events": [
            {
                "id": "e1",
                "type": "A",
                "mention": [
                    {
                        "id": "m1",
                        "sent_id": 0,
                        "offset": [0, 1],
                        "trigger_word": "a",
                    }
                ],
            },
            {
                "id": "e2",
                "type": "B",
                "mention": [
                    {
                        "id": "m2",
                        "sent_id": 0,
                        "offset": [1, 2],
                        "trigger_word": "b",
                    }
                ],
            },
        ],
        "causal_relations": {"CAUSE": [["e1", "e2"]], "PRECONDITION": []},
        "temporal_relations": {},
        "subevent_relations": [],
    }


def _fixture(
    root: Path,
    *,
    weak: bool = False,
    leaked_field: bool = False,
) -> tuple[Path, Path]:
    source = root / "data" / "train.jsonl"
    source.parent.mkdir(parents=True)
    records = [_record(f"d{fold}") for fold in range(1, 6)]
    source.write_text(
        "".join(json.dumps(record) + "\n" for record in records),
        encoding="utf-8",
    )
    stage = root / "runs" / "stages" / "R1" / "fixture"
    folds = []
    manifests: dict[int, Path] = {}
    for fold in range(1, 6):
        manifest = stage / "manifests" / f"fold-{fold}.json"
        _write_json(manifest, {"doc_ids": [f"d{fold}"]})
        manifests[fold] = manifest
        folds.append(
            {
                "fold": fold,
                "seed": 13,
                "manifests": {
                    "evaluation": {
                        "path": str(manifest.relative_to(root)),
                        "sha256": aggregate.sha256_file(manifest),
                        "documents": 1,
                    }
                },
                "expected_output": {
                    "path": (
                        f"relation_crossfit/fold-{fold}/causal_posteriors.jsonl"
                    ),
                    "documents": 1,
                    "ordered_mention_pairs": 2,
                },
            }
        )
    plan = stage / "d4_crossfit_plan.json"
    _write_json(
        plan,
        {
            "schema_version": "r1-v62-d4-crossfit-plan-v2",
            "inputs": {
                "ere_train": {
                    "path": str(source.relative_to(root)),
                    "sha256": aggregate.sha256_file(source),
                }
            },
            "folds": folds,
        },
    )
    plan_hash = aggregate.sha256_file(plan)

    for fold in range(1, 6):
        doc_id = f"d{fold}"
        run_dir = stage / "relation_crossfit" / f"fold-{fold}"
        run_dir.mkdir(parents=True)
        posterior_path = run_dir / "causal_posteriors.jsonl"
        if weak:
            positive = (0.5, 0.5, 0.0)
            negative = (0.5, 0.5, 0.0)
        else:
            positive = (0.05, 0.9, 0.05)
            negative = (0.9, 0.05, 0.05)
        rows = []
        for head, tail, probabilities in (
            ("m1", "m2", positive),
            ("m2", "m1", negative),
        ):
            row = {
                "doc_id": doc_id,
                "head_mention_id": f"{doc_id}::{head}",
                "tail_mention_id": f"{doc_id}::{tail}",
                "p_none": probabilities[0],
                "p_cause": probabilities[1],
                "p_precondition": probabilities[2],
            }
            if leaked_field:
                row["gold_label"] = "CAUSE" if head == "m1" else "NONE"
            rows.append(row)
        posterior_path.write_text(
            "".join(json.dumps(row) + "\n" for row in rows),
            encoding="utf-8",
        )
        posterior_hash = aggregate.sha256_file(posterior_path)
        posterior_metadata_path = run_dir / "causal_posteriors.metadata.json"
        _write_json(
            posterior_metadata_path,
            {
                "schema_version": "ekg.relation_causal_posteriors.v1",
                "gold_fields_present": False,
                "class_order": list(aggregate.CLASSES),
                "documents": 1,
                "ordered_mention_pairs": 2,
                "output_sha256": posterior_hash,
            },
        )
        manifest = manifests[fold]
        _write_json(
            run_dir / "run_metadata.json",
            {
                "status": "complete",
                "fold": fold,
                "seed": 13,
                "commit": "fixture",
                "plan_sha256": plan_hash,
                "source_sha256": aggregate.sha256_file(source),
                "manifest_sha256": {
                    "evaluation": aggregate.sha256_file(manifest)
                },
                "selection_uses_evaluation": False,
                "final_valid_accessed": False,
                "train_argv": ["train"],
                "dump_argv": ["dump", str(manifest.resolve())],
                "posterior": {
                    "documents": 1,
                    "ordered_mention_pairs": 2,
                    "sha256": posterior_hash,
                },
                "artifacts_sha256": {
                    "causal_posteriors.jsonl": posterior_hash,
                    "causal_posteriors.metadata.json": aggregate.sha256_file(
                        posterior_metadata_path
                    ),
                },
            },
        )
    return root, plan


def _aggregate(monkeypatch, root: Path, plan: Path) -> dict:
    monkeypatch.setattr(aggregate, "_git_commit", lambda repo: "fixture")
    return aggregate.aggregate_quality(
        repo=root,
        plan_path=plan,
        expected_documents=5,
        expected_mentions=10,
        expected_pairs=10,
    )


def _add_calibrated_artifacts(root: Path, plan: Path) -> Path:
    plan_payload = json.loads(plan.read_text(encoding="utf-8"))
    for row in plan_payload["folds"]:
        fold = row["fold"]
        run_dir = plan.parent / "relation_crossfit" / f"fold-{fold}"
        raw_path = run_dir / "causal_posteriors.jsonl"
        raw_metadata_path = run_dir / "causal_posteriors.metadata.json"
        calibrated_path = run_dir / "calibrated_causal_posteriors.jsonl"
        calibrated_path.write_bytes(raw_path.read_bytes())
        selection_posterior = run_dir / "selection_causal_posteriors.jsonl"
        selection_metadata = run_dir / "selection_causal_posteriors.metadata.json"
        selection_posterior.write_text("selection\n", encoding="utf-8")
        _write_json(selection_metadata, {"fixture": True})
        selection_manifest = root / row["manifests"]["evaluation"]["path"]
        row["manifests"]["selection_dev"] = {
            "path": str(selection_manifest.relative_to(root)),
            "sha256": aggregate.sha256_file(selection_manifest),
        }
        _write_json(
            run_dir / "temperature_calibration.metadata.json",
            {
                "schema_version": "ekg.d4_temperature_calibration.v1",
                "fold": fold,
                "class_order": list(aggregate.CLASSES),
                "gold_fields_present": False,
                "method": {
                    "name": "scalar_temperature_scaling",
                    "formula": "softmax(log(p) / T)",
                    "fit_objective": "unweighted multiclass NLL on selection-dev",
                    "temperature": 1.0,
                },
                "evaluation": {
                    "gold_accessed": False,
                    "argmax_unchanged": True,
                    "ordered_mention_pairs": 2,
                    "raw_prediction_counts": {"NONE": 1, "CAUSE": 1},
                    "calibrated_prediction_counts": {"NONE": 1, "CAUSE": 1},
                },
                "inputs": {
                    "selection_manifest": {
                        "sha256": aggregate.sha256_file(selection_manifest)
                    },
                    "selection_posterior": {
                        "path": str(selection_posterior),
                        "sha256": aggregate.sha256_file(selection_posterior),
                    },
                    "selection_metadata": {
                        "path": str(selection_metadata),
                        "sha256": aggregate.sha256_file(selection_metadata),
                    },
                    "evaluation_posterior": {
                        "sha256": aggregate.sha256_file(raw_path)
                    },
                    "evaluation_metadata": {
                        "sha256": aggregate.sha256_file(raw_metadata_path)
                    },
                },
                "output": {
                    "path": str(calibrated_path),
                    "sha256": aggregate.sha256_file(calibrated_path),
                },
            },
        )
    _write_json(plan, plan_payload)
    plan_hash = aggregate.sha256_file(plan)
    for fold in range(1, 6):
        run_metadata = plan.parent / f"relation_crossfit/fold-{fold}/run_metadata.json"
        payload = json.loads(run_metadata.read_text(encoding="utf-8"))
        payload["plan_sha256"] = plan_hash
        _write_json(run_metadata, payload)
    raw_quality_report = plan.parent / "quality_report.json"
    _write_json(
        raw_quality_report,
        {
            "schema_version": "ekg.d4_relation_crossfit_quality.v1",
            "status": "quality_gate_failed",
            "gate": {
                "causal_f1_pass": True,
                "multiclass_brier_pass": False,
            },
        },
    )
    return raw_quality_report


def test_aggregate_quality_passes_exact_coverage_f1_and_brier(
    tmp_path: Path, monkeypatch
) -> None:
    root, plan = _fixture(tmp_path)

    report = _aggregate(monkeypatch, root, plan)

    assert report["status"] == "quality_gate_passed"
    assert report["coverage"] == {
        "documents": 5,
        "mentions": 10,
        "ordered_mention_pairs": 10,
    }
    assert report["pooled_metrics"]["causal_positive"]["f1"] == 1.0
    brier = report["pooled_metrics"]["multiclass_brier"]
    assert brier["model"] < brier["evaluation_prevalence_no_skill"]
    assert report["gate"] == {
        "coverage_pass": True,
        "no_gold_fields_pass": True,
        "causal_f1_pass": True,
        "multiclass_brier_pass": True,
        "passed": True,
    }


def test_aggregate_quality_writes_a_negative_scientific_result(
    tmp_path: Path, monkeypatch
) -> None:
    root, plan = _fixture(tmp_path, weak=True)

    report = _aggregate(monkeypatch, root, plan)

    assert report["status"] == "quality_gate_failed"
    assert report["scientific_result"] is True
    assert report["pooled_metrics"]["causal_positive"]["f1"] == 0.0
    assert report["gate"]["causal_f1_pass"] is False
    assert report["gate"]["multiclass_brier_pass"] is False


def test_aggregate_quality_rejects_a_gold_field_in_posterior(
    tmp_path: Path, monkeypatch
) -> None:
    root, plan = _fixture(tmp_path, leaked_field=True)

    with pytest.raises(aggregate.D4QualityError, match="posterior row fields drifted"):
        _aggregate(monkeypatch, root, plan)


def test_aggregate_quality_rejects_incomplete_fold(tmp_path: Path, monkeypatch) -> None:
    root, plan = _fixture(tmp_path)
    run_metadata = plan.parent / "relation_crossfit/fold-3/run_metadata.json"
    payload = json.loads(run_metadata.read_text(encoding="utf-8"))
    payload["status"] = "failed"
    _write_json(run_metadata, payload)

    with pytest.raises(aggregate.D4QualityError, match="fold 3: run is not complete"):
        _aggregate(monkeypatch, root, plan)


def test_aggregate_quality_validates_calibrated_provenance(
    tmp_path: Path, monkeypatch
) -> None:
    root, plan = _fixture(tmp_path)
    raw_quality_report = _add_calibrated_artifacts(root, plan)
    monkeypatch.setattr(aggregate, "_git_commit", lambda repo: "fixture")

    report = aggregate.aggregate_quality(
        repo=root,
        plan_path=plan,
        expected_documents=5,
        expected_mentions=10,
        expected_pairs=10,
        calibrated=True,
        raw_quality_report=raw_quality_report,
    )

    assert report["schema_version"].endswith("calibrated_quality.v1")
    assert report["calibration"]["evaluation_gold_used_for_fit"] is False
    assert [fold["temperature"] for fold in report["folds"]] == [1.0] * 5
