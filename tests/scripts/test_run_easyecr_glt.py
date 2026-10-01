from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_SCRIPT = _ROOT / "scripts" / "run_easyecr_glt.py"
_SPEC = importlib.util.spec_from_file_location("run_easyecr_glt", _SCRIPT)
assert _SPEC is not None and _SPEC.loader is not None
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
_validate_preflight = _MODULE._validate_preflight
_model_conf = _MODULE._model_conf
_configure_upstream_tempdir = _MODULE._configure_upstream_tempdir


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_validate_preflight_accepts_only_hashed_unlabeled_inputs(tmp_path: Path) -> None:
    paths = {
        "train": tmp_path / "train.jsonl",
        "selection_dev": tmp_path / "selection-valid.jsonl",
        "evaluation_test": tmp_path / "evaluation-test.jsonl",
    }
    for name, path in paths.items():
        path.write_text(f'{{"id": "{name}"}}\n', encoding="utf-8")
    report = {
        "schema_version": "ekg.easyecr_glt_preflight.v2",
        "p1_protocol_sha256": _MODULE.EXPECTED_P1_PROTOCOL_SHA256,
        "evaluation_gold_access": False,
        "split_counts": {"evaluation": 291, "selection_dev": 291, "training": 2331},
        "artifact_sha256": {name: _sha256(path) for name, path in paths.items()},
    }
    preflight = tmp_path / "preflight.json"
    preflight.write_text(json.dumps(report), encoding="utf-8")

    assert _validate_preflight(preflight) == {
        "train": paths["train"],
        "selection": paths["selection_dev"],
        "evaluation": paths["evaluation_test"],
    }


def test_model_configuration_freezes_seed_13_and_single_gpu_trainer(tmp_path: Path) -> None:
    trainer = _MODULE._trainer_parameters(tmp_path, smoke=False)
    conf = _model_conf(
        doc_encoder=tmp_path / "longformer",
        mention_encoder=tmp_path / "bert",
        trainer_parameters=trainer,
    )

    assert conf["seed"] == 13
    assert trainer["devices"] == 1
    assert trainer["max_epochs"] == 30


def test_upstream_tempdir_is_run_local_and_overrides_the_global_hard_code(tmp_path: Path) -> None:
    previous = tempfile.tempdir
    try:
        temporary_directory = _configure_upstream_tempdir(tmp_path / "run")
        assert temporary_directory == tmp_path / "run" / "temporary"
        assert temporary_directory.is_dir()
        assert tempfile.tempdir == str(temporary_directory)
    finally:
        tempfile.tempdir = previous
