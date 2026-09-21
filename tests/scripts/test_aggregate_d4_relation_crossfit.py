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
