"""P1 builder evidence gates reject the two independent-audit counterexamples."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[2]
_SCRIPT = _REPO / "scripts/build_p1_bundle.py"
_SPEC = importlib.util.spec_from_file_location("build_p1_bundle", _SCRIPT)
assert _SPEC and _SPEC.loader
builder = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(builder)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_minimal_fake_remote_pass_is_rejected() -> None:
    root = _REPO / "data/protocols/v6"
    baseline = _load(root / "baselines/smoke_summary.json")
    fake = {"status": "pass", "checkpoint_hashes": {"fake": "not-a-sha256"}}

    with pytest.raises(builder.P1EvidenceError, match="remote schema"):
        builder._validate_remote_smoke(_REPO, root, fake, baseline)


def test_current_remote_smoke_has_complete_cross_checked_evidence() -> None:
    root = _REPO / "data/protocols/v6"
    remote = _load(root / "remote_smoke.json")
    baseline = _load(root / "baselines/smoke_summary.json")

    builder._validate_remote_smoke(_REPO, root, remote, baseline)


def _passing_gate(extra: dict | None = None) -> dict:
    """A v2 gate whose recorded hashes cover the current P1 code paths."""
    gate = {
        "schema_version": "ekg.p1_local_gate.v2",
        "status": "pass",
        "tested_tree_sha256": "0" * 64,
        "tested_file_count": 163,
        "tested_file_sha256": {
            path: builder.sha256_file(_REPO / path) for path in builder.CODE_PATHS
        },
        "results": {
            name: {"returncode": 0} for name in ("pytest", "ruff", "ekg_smoke")
        },
    }
    gate.update(extra or {})
    return gate


def test_unrelated_repository_file_does_not_invalidate_the_gate() -> None:
    """An edit outside P1's code paths must not invalidate a protocol bundle.

    This is the r1..r5 failure mode: binding the whole src/tests/scripts tree made
    every unrelated edit a full trust-root rebuild.
    """
    gate = _passing_gate({"tested_file_count": 1, "tested_file_sha256_note": "stale tree"})
    gate["tested_file_sha256"]["scripts/some_unrelated_tool.py"] = "f" * 64

    builder._validate_local_gate(_REPO, gate)


def test_stale_p1_code_hash_is_rejected() -> None:
    gate = _passing_gate()
    gate["tested_file_sha256"]["scripts/build_p1_bundle.py"] = "a" * 64

    with pytest.raises(builder.P1EvidenceError, match="did not cover current"):
        builder._validate_local_gate(_REPO, gate)


def test_a3_execution_surface_is_not_part_of_the_protocol_trust_root() -> None:
    """Materializer/launcher are bound by the A3 plan hash, not by P1 identity."""
    assert "scripts/prepare_a3_baselines.py" not in builder.CODE_PATHS
    assert "scripts/run_a3_baseline.py" not in builder.CODE_PATHS


def test_superseded_v1_gate_schema_is_rejected() -> None:
    gate = _passing_gate({"schema_version": "ekg.p1_local_gate.v1"})

    with pytest.raises(builder.P1EvidenceError, match="local gate schema"):
        builder._validate_local_gate(_REPO, gate)


def test_tree_changed_during_gate_is_rejected() -> None:
    gate = _passing_gate({"tree_changed_during_gate": True})

    with pytest.raises(builder.P1EvidenceError, match="tree changed during local gate"):
        builder._validate_local_gate(_REPO, gate)
