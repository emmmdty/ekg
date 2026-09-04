#!/usr/bin/env python
"""Validate and optionally execute one frozen A3.6 recipe-accounting arm."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from ekg.core.stage_bundle import sha256_file


def _tree_hashes(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): sha256_file(path)
        for path in sorted(root.rglob("*"))
        if path.is_file() and path.name != "run_metadata.json"
    }


def _write_metadata(run_dir: Path, payload: dict) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "run_metadata.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--plan-sha256", required=True)
    parser.add_argument("--p1-protocol-sha256", required=True)
    parser.add_argument("--arm", required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()

    plan_path = args.plan.resolve()
    actual_plan_hash = sha256_file(plan_path)
    if actual_plan_hash != args.plan_sha256:
        raise SystemExit("recipe plan SHA-256 mismatch")
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    if plan.get("schema_version") != "ekg.a3_recipe_accounting.v1":
        raise SystemExit("recipe plan schema mismatch")
    if plan.get("status") != "pass" or plan.get("final_valid_accessed") is not False:
        raise SystemExit("recipe plan is not eligible")
    if plan.get("p1_bundle_protocol_sha256") != args.p1_protocol_sha256:
        raise SystemExit("recipe plan P1 hash mismatch")
    if args.arm not in plan.get("commands", {}):
        raise SystemExit(f"unknown recipe arm: {args.arm}")
    entry = plan["commands"][args.arm]
    cwd = Path(entry["cwd"])
    run_dir = Path(entry["run_dir"])
    print(f"[a3-recipe] arm={args.arm} cwd={cwd}")
    print(f"[a3-recipe] train_argv={json.dumps(entry['train_argv'])}")
    print(f"[a3-recipe] score_argv={json.dumps(entry['score_argv'])}")
    print(f"[a3-recipe] run_dir={run_dir}")
    if not args.execute:
        print("[a3-recipe] PRECHECK PASS; no process started")
        return 0

    expected_cwd = Path(plan["execution_environment"]["remote_repo_root"])
    expected_preflight = Path(plan["execution_environment"]["remote_preflight"])
    if cwd != expected_cwd or Path.cwd().resolve() != expected_cwd:
        raise SystemExit(f"execute requires cwd {expected_cwd}")
    if plan_path.parent != expected_preflight:
        raise SystemExit(f"execute requires plan under {expected_preflight}")
    if run_dir.exists():
        raise SystemExit(f"refusing to overwrite immutable run directory: {run_dir}")
    for relative, expected in plan["execution_surface"].items():
        path = cwd / relative
        if not path.is_file() or sha256_file(path) != expected:
            raise SystemExit(f"execution-surface hash mismatch: {relative}")
    data_root = expected_preflight / "data/MAVEN_ERE"
    actual_data = {path.name for path in data_root.iterdir() if path.is_file()}
    if actual_data != set(plan["data_hashes"]):
        raise SystemExit("materialized A3.6 data file set differs from the plan")
    for name, expected in plan["data_hashes"].items():
        if sha256_file(data_root / name) != expected:
            raise SystemExit(f"materialized A3.6 data hash mismatch: {name}")
    gpu = os.environ.get("CUDA_VISIBLE_DEVICES")
    if gpu is None or not gpu.isdigit():
        raise SystemExit("CUDA_VISIBLE_DEVICES must select exactly one numeric GPU")
    gpu_check = subprocess.run(
        (
            "nvidia-smi",
            f"--id={gpu}",
            "--query-gpu=index,name,memory.total,memory.used,utilization.gpu",
            "--format=csv,noheader",
        ),
        text=True,
        capture_output=True,
    )
    if gpu_check.returncode != 0 or not gpu_check.stdout.strip():
        raise SystemExit(f"GPU preflight failed: {gpu_check.stderr.strip()}")

    commit = subprocess.run(
        ("git", "rev-parse", "HEAD"), cwd=cwd, text=True, capture_output=True, check=True
    ).stdout.strip()
    metadata = {
        "schema_version": "ekg.a3_recipe_run.v1",
        "status": "incomplete",
        "arm": args.arm,
        "seed": entry["configuration"]["seed"],
        "commit": commit,
        "working_directory": str(cwd),
        "launcher_argv": list(sys.argv),
        "train_argv": entry["train_argv"],
        "score_argv": entry["score_argv"],
        "configuration": entry["configuration"],
        "p1_bundle_id": plan["p1_bundle_id"],
        "p1_bundle_protocol_sha256": args.p1_protocol_sha256,
        "recipe_plan_sha256": actual_plan_hash,
        "gpu": gpu_check.stdout.strip(),
        "final_valid_accessed": False,
        "exploratory": False,
    }
    _write_metadata(run_dir, metadata)
    returncodes = {}
    for role in ("train", "score"):
        completed = subprocess.run(entry[f"{role}_argv"], cwd=cwd)
        returncodes[role] = completed.returncode
        if completed.returncode != 0:
            break
    required = [
        run_dir / "checkpoint/run_metadata.json",
        run_dir / "checkpoint/heads.pt",
        run_dir / "official_predictions.jsonl",
        run_dir / "official_metrics.json",
    ]
    if entry["configuration"]["save_best_by_family"]:
        for family in ("causal", "subevent", "temporal"):
            required.extend(
                (
                    run_dir / f"checkpoint/by_family/{family}/heads.pt",
                    run_dir / f"checkpoint/by_family/{family}/selection.json",
                )
            )
    missing = [str(path) for path in required if not path.is_file()]
    succeeded = (
        set(returncodes) == {"train", "score"}
        and not any(returncodes.values())
        and not missing
    )
    metadata.update(
        {
            "status": "complete" if succeeded else "failed",
            "returncodes": returncodes,
            "missing_outputs": missing,
            "artifact_sha256": _tree_hashes(run_dir),
        }
    )
    _write_metadata(run_dir, metadata)
    if not succeeded:
        raise SystemExit(f"A3.6 arm failed: returncodes={returncodes} missing={missing}")
    print(f"[a3-recipe] COMPLETE metadata={run_dir / 'run_metadata.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
