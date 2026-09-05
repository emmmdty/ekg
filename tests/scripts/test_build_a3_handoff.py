from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "build_a3_handoff", ROOT / "scripts/build_a3_handoff.py"
)
assert SPEC and SPEC.loader
handoff = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(handoff)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload) + "\n", encoding="utf-8")


def test_validate_arm_rejects_final_valid_access(tmp_path: Path) -> None:
    arm = "local_recipe"
    run = tmp_path / arm / "seed-13"
    _write_json(run / "official_predictions.jsonl", {"id": "d1"})
    _write_json(run / "score.log", {})
    metrics = {
        "hashes": {
            "predictions": handoff.sha256_file(run / "official_predictions.jsonl"),
            "gold": "a" * 64,
        },
        "population": {"candidate_id_digest": "b" * 64},
        "scores": {name: 1.0 for name in handoff.SCORES},
    }
    _write_json(run / "official_metrics.json", metrics)
    _write_json(
        run / "checkpoint/run_metadata.json",
        {
            "status": "complete",
            "protocol_binding": {
                "final_valid_accessed": False,
                "p1_bundle_protocol_sha256": "c" * 64,
            },
        },
    )
    artifacts = {
        relative: handoff.sha256_file(run / relative)
        for relative in ("official_metrics.json", "official_predictions.jsonl", "score.log")
    }
    command = {
        "configuration": {"seed": 13},
        "train_argv": ["train"],
        "score_argv": ["score"],
    }
    _write_json(
        run / "run_metadata.json",
        {
            "status": "complete",
            "returncodes": {"train": 0, "score": 0},
            "exploratory": False,
            "final_valid_accessed": True,
            "seed": 13,
            "configuration": command["configuration"],
            "train_argv": command["train_argv"],
            "score_argv": command["score_argv"],
            "recipe_plan_sha256": "d" * 64,
            "p1_bundle_protocol_sha256": "c" * 64,
            "artifact_sha256": artifacts,
        },
    )
    plan = {
        "commands": {arm: command},
        "data_hashes": {"valid.jsonl": "a" * 64},
        "candidate_summaries": {
            "internal-dev": {"candidate_id_digest_sha256": "b" * 64}
        },
    }

    with pytest.raises(handoff.A3HandoffError, match="final-valid"):
        handoff.validate_arm(
            arm,
            root=tmp_path,
            plan=plan,
            plan_sha256="d" * 64,
            p1_sha256="c" * 64,
        )
