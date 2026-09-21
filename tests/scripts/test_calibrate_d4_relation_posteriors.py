import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "calibrate_d4_relation_posteriors",
    ROOT / "scripts/calibrate_d4_relation_posteriors.py",
)
assert SPEC is not None and SPEC.loader is not None
calibrate = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = calibrate
SPEC.loader.exec_module(calibrate)


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


def _write_posterior(path: Path, doc_id: str) -> None:
    rows = [
        {
            "doc_id": doc_id,
            "head_mention_id": f"{doc_id}::m1",
            "tail_mention_id": f"{doc_id}::m2",
            "p_none": 0.2,
            "p_cause": 0.7,
            "p_precondition": 0.1,
        },
        {
            "doc_id": doc_id,
            "head_mention_id": f"{doc_id}::m2",
            "tail_mention_id": f"{doc_id}::m1",
            "p_none": 0.4,
            "p_cause": 0.5,
            "p_precondition": 0.1,
        },
    ]
    path.write_text(
        "".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8"
    )


def _posterior_metadata(
    *,
    path: Path,
    posterior: Path,
    source: Path,
    manifest: Path,
    checkpoint_files: dict[str, str],
) -> None:
    _write_json(
        path,
        {
            "schema_version": "ekg.relation_causal_posteriors.v1",
            "class_order": list(calibrate.CLASSES),
            "gold_fields_present": False,
            "output_sha256": calibrate.sha256_file(posterior),
            "inputs": {
                "data": {"sha256": calibrate.sha256_file(source)},
                "manifest": {"sha256": calibrate.sha256_file(manifest)},
                "checkpoint": {"files": checkpoint_files},
            },
        },
    )


def _fixture(root: Path) -> dict[str, Path]:
    source = root / "source.jsonl"
    source.write_text(
        "".join(json.dumps(_record(doc_id)) + "\n" for doc_id in ("d1", "d2")),
        encoding="utf-8",
    )
    selection_manifest = root / "selection.json"
    evaluation_manifest = root / "evaluation.json"
    _write_json(selection_manifest, {"doc_ids": ["d1"]})
    _write_json(evaluation_manifest, {"doc_ids": ["d2"]})
    selection = root / "selection.jsonl"
    evaluation = root / "evaluation.jsonl"
    _write_posterior(selection, "d1")
    _write_posterior(evaluation, "d2")
    selection_metadata = root / "selection.metadata.json"
    evaluation_metadata = root / "evaluation.metadata.json"
    checkpoint_files = {"model.safetensors": "a" * 64}
    _posterior_metadata(
        path=selection_metadata,
        posterior=selection,
        source=source,
        manifest=selection_manifest,
        checkpoint_files=checkpoint_files,
    )
    _posterior_metadata(
        path=evaluation_metadata,
        posterior=evaluation,
        source=source,
        manifest=evaluation_manifest,
        checkpoint_files=checkpoint_files,
    )
    return {
        "source": source,
        "selection_manifest": selection_manifest,
        "selection": selection,
        "selection_metadata": selection_metadata,
        "evaluation": evaluation,
        "evaluation_metadata": evaluation_metadata,
        "output": root / "calibrated.jsonl",
        "metadata_output": root / "calibration.metadata.json",
    }


def _calibrate(paths: dict[str, Path]) -> dict:
    return calibrate.calibrate_fold(
        fold=1,
        source_path=paths["source"],
        selection_manifest_path=paths["selection_manifest"],
        selection_posterior_path=paths["selection"],
        selection_metadata_path=paths["selection_metadata"],
        evaluation_posterior_path=paths["evaluation"],
        evaluation_metadata_path=paths["evaluation_metadata"],
        output_path=paths["output"],
        metadata_output_path=paths["metadata_output"],
        expected_selection_documents=1,
        expected_selection_pairs=2,
        expected_evaluation_pairs=2,
    )


def test_calibrate_fold_fits_selection_only_and_preserves_evaluation_argmax(
    tmp_path: Path,
) -> None:
    paths = _fixture(tmp_path)

    metadata = _calibrate(paths)

    assert metadata["evaluation"]["gold_accessed"] is False
    assert metadata["evaluation"]["argmax_unchanged"] is True
    assert (
        metadata["evaluation"]["raw_prediction_counts"]
        == metadata["evaluation"]["calibrated_prediction_counts"]
    )
    assert metadata["selection"]["calibrated_metrics"]["nll"] < metadata[
        "selection"
    ]["raw_metrics"]["nll"]
    assert metadata["output"]["sha256"] == calibrate.sha256_file(paths["output"])
    for row in paths["output"].read_text(encoding="utf-8").splitlines():
        assert set(json.loads(row)) == calibrate.ROW_FIELDS


def test_calibrate_fold_rejects_checkpoint_drift(tmp_path: Path) -> None:
    paths = _fixture(tmp_path)
    metadata = json.loads(paths["evaluation_metadata"].read_text(encoding="utf-8"))
    metadata["inputs"]["checkpoint"]["files"] = {"model.safetensors": "b" * 64}
    _write_json(paths["evaluation_metadata"], metadata)

    with pytest.raises(ValueError, match="checkpoints differ"):
        _calibrate(paths)
