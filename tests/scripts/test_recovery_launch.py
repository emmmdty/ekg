"""A stale dependency or an occupied GPU must prevent launching a probe."""

import importlib.util
import json
from pathlib import Path

import pytest

from ekg.core.stage_bundle import sha256_file


def launcher():
    path = Path(__file__).resolve().parents[2] / "scripts/launch_recovery_validation.py"
    spec = importlib.util.spec_from_file_location("recovery_launcher", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_preflight_rejects_drift_and_overwriting_existing_outputs(tmp_path):
    dependency = tmp_path / "manifest.json"
    dependency.write_text("frozen")
    job = {"seed": 13, "inputs": {"manifest.json": sha256_file(dependency)},
           "models": {}, "outputs": ["new/output.json"]}
    check = launcher().check_files
    check(tmp_path, job)
    dependency.write_text("changed")
    with pytest.raises(ValueError, match="hash"):
        check(tmp_path, job)
    job["inputs"]["manifest.json"] = sha256_file(dependency)
    (tmp_path / "new").mkdir()
    (tmp_path / "new/output.json").touch()
    with pytest.raises(FileExistsError):
        check(tmp_path, job)


def test_gpu_must_be_empty_even_if_current_utilization_is_zero():
    check = launcher().check_gpu_rows
    check("0, GPU-zero, 100, 0\n1, GPU-one, 0, 0\n", "", 0)
    with pytest.raises(ValueError, match="occupied"):
        check("0, GPU-zero, 100, 0\n", "GPU-zero, 456\n", 0)
    with pytest.raises(ValueError, match="occupied"):
        check("0, GPU-zero, 17000, 0\n", "", 0)
    with pytest.raises(ValueError, match="unknown"):
        check("0, GPU-zero, 100, 0\n", "", 1)


def test_formal_job_requires_successful_smoke_from_the_same_plan(tmp_path):
    check = launcher().check_dependencies
    plan = {"jobs": {"smoke": {"status_output": "smoke.json"}}}
    job = {"depends_on": ["smoke"]}
    with pytest.raises(FileNotFoundError):
        check(tmp_path, plan, job, "frozen")
    status = {"status": "complete", "seed": 13, "plan_sha256": "different",
              "artifact_sha256": {}}
    (tmp_path / "smoke.json").write_text(json.dumps(status))
    with pytest.raises(ValueError, match="smoke"):
        check(tmp_path, plan, job, "frozen")
    status["plan_sha256"] = "frozen"
    (tmp_path / "smoke.json").write_text(json.dumps(status))
    check(tmp_path, plan, job, "frozen")


def test_factuality_pooling_rejects_wrong_head_or_changed_labels(tmp_path):
    path = Path(__file__).resolve().parents[2] / "scripts/collect_recovery_factuality.py"
    spec = importlib.util.spec_from_file_location("recovery_collector", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    labels = tmp_path / "evaluation_labels.json"
    labels.write_text('{"m": "Uu"}')
    metadata = {"status": "complete", "seed": 13, "head_name": "linear", "pooling": "cls",
                "fold": 1, "cv_sha256": "cv", "source_sha256": "source",
                "final_valid_accessed": False, "selection_uses_evaluation": False,
                "artifact_sha256": {"evaluation_labels.json": sha256_file(labels)}}
    (tmp_path / "run_metadata.json").write_text(json.dumps(metadata))
    module.validate_run(tmp_path, "linear", 1, "cv", "source")
    with pytest.raises(ValueError):
        module.validate_run(tmp_path, "tanh5", 1, "cv", "source")
    labels.write_text('{"m": "CT+"}')
    with pytest.raises(ValueError, match="hash"):
        module.validate_run(tmp_path, "linear", 1, "cv", "source")
