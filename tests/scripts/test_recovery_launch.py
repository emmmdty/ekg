"""A stale dependency or an occupied GPU must prevent launching a probe."""

import importlib.util
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
