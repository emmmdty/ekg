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
