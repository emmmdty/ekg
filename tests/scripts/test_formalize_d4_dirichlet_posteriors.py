import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]


def _load_script(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


_load_script("calibrate_d4_relation_posteriors")
_load_script("audit_d4_class_weight_correction")
_load_script("audit_d4_dirichlet_holdout")
formalize = _load_script("formalize_d4_dirichlet_posteriors")


def _training_metadata() -> dict:
    return {
        "checkpoint_sha256": {
            "by_family/causal/model.safetensors": "a" * 64,
        },
        "configuration": {
            "weight_alpha": "0.5",
            "neg_ratio": "inf",
            "official_mention_expansion": True,
        },
        "protocol_binding": {
            "candidate_summaries": {
                "train": {
                    "population_counts": {
                        "ordered_mention_pairs": 1000,
                        "positive_causal:CAUSE": 50,
                        "positive_causal:PRECONDITION": 150,
                    }
                }
            }
        },
    }


def _selection() -> tuple[np.ndarray, np.ndarray]:
    natural_rows = np.asarray(
        [[0.7, 0.2, 0.1], [0.2, 0.6, 0.2], [0.1, 0.2, 0.7]],
        dtype=np.float64,
    )
    raw_rows = np.square(natural_rows)
    raw_rows /= raw_rows.sum(axis=1, keepdims=True)
    probabilities = np.repeat(raw_rows, 100, axis=0)
    labels = np.concatenate(
        [
            np.repeat(np.arange(3), (70, 20, 10)),
            np.repeat(np.arange(3), (20, 60, 20)),
            np.repeat(np.arange(3), (10, 20, 70)),
        ]
    )
    return probabilities, labels


def _paths(root: Path) -> dict[str, Path]:
    names = (
        "source",
        "selection_manifest",
        "selection_posterior",
        "selection_metadata",
        "evaluation_posterior",
        "evaluation_metadata",
        "training_metadata",
    )
    paths = {name: root / f"{name}.json" for name in names}
    for path in paths.values():
        path.write_text("{}\n", encoding="utf-8")
    paths["output"] = root / "dirichlet.jsonl"
    paths["metadata_output"] = root / "dirichlet.metadata.json"
    return paths


def _posterior_rows() -> list[tuple[int, dict]]:
    return [
        (
            1,
            {
                "doc_id": "d1",
                "head_mention_id": "d1::m1",
                "tail_mention_id": "d1::m2",
                "p_none": 0.2,
                "p_cause": 0.7,
                "p_precondition": 0.1,
            },
        ),
        (
            2,
            {
                "doc_id": "d1",
                "head_mention_id": "d1::m2",
                "tail_mention_id": "d1::m1",
                "p_none": 0.7,
                "p_cause": 0.2,
                "p_precondition": 0.1,
            },
        ),
    ]


def _run(monkeypatch, paths: dict[str, Path]) -> dict:
    checkpoint = {"files": {"model.safetensors": "a" * 64}}

    def validate(*, metadata_path, **kwargs):
        manifest = "selection" if metadata_path == paths["selection_metadata"] else "evaluation"
        return {"inputs": {"checkpoint": checkpoint, "manifest": {"sha256": manifest}}}

    monkeypatch.setattr(formalize, "_validate_posterior_metadata", validate)
    monkeypatch.setattr(formalize, "_load_selection", lambda **kwargs: _selection())
    monkeypatch.setattr(formalize, "_load_object", lambda path: _training_metadata())
    monkeypatch.setattr(formalize, "_rows", lambda path: iter(_posterior_rows()))
    return formalize.formalize_fold(
        fold=1,
        source_path=paths["source"],
        selection_manifest_path=paths["selection_manifest"],
        selection_posterior_path=paths["selection_posterior"],
        selection_metadata_path=paths["selection_metadata"],
        evaluation_posterior_path=paths["evaluation_posterior"],
        evaluation_metadata_path=paths["evaluation_metadata"],
        training_metadata_path=paths["training_metadata"],
        output_path=paths["output"],
        metadata_output_path=paths["metadata_output"],
        expected_selection_documents=3,
        expected_selection_pairs=300,
        expected_evaluation_pairs=2,
    )


def test_formalize_fold_fits_selection_and_transforms_evaluation_without_gold(
    tmp_path: Path, monkeypatch
) -> None:
    paths = _paths(tmp_path)

    metadata = _run(monkeypatch, paths)

    assert metadata["evaluation"]["gold_accessed"] is False
    assert metadata["evaluation"]["ordered_mention_pairs"] == 2
    assert metadata["method"]["penalty"] is None
    assert metadata["method"]["iterations"] < 1000
    assert metadata["output"]["sha256"] == formalize.sha256_file(paths["output"])
    assert paths["metadata_output"].is_file()
    expected_fields = {
        "doc_id",
        "head_mention_id",
        "tail_mention_id",
        "p_none",
        "p_cause",
        "p_precondition",
    }
    for line in paths["output"].read_text(encoding="utf-8").splitlines():
        assert set(json.loads(line)) == expected_fields


def test_formalize_fold_refuses_to_overwrite_outputs(tmp_path: Path, monkeypatch) -> None:
    paths = _paths(tmp_path)
    paths["output"].write_text("occupied\n", encoding="utf-8")

    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        _run(monkeypatch, paths)
