#!/usr/bin/env python
"""Freeze the four-arm A3.6 official-recipe accounting matrix."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ekg.core.stage_bundle import sha256_file

ARMS = {
    "local_recipe": {
        "family_loss_rates": "temporal=1,causal=1,subevent=1",
        "coref_aux_rate": 0.0,
        "save_best_by_family": False,
    },
    "rates_only": {
        "family_loss_rates": "temporal=2,causal=4,subevent=4",
        "coref_aux_rate": 0.0,
        "save_best_by_family": False,
    },
    "rates_coref": {
        "family_loss_rates": "temporal=2,causal=4,subevent=4",
        "coref_aux_rate": 0.4,
        "save_best_by_family": False,
    },
    "rates_coref_family_selection": {
        "family_loss_rates": "temporal=2,causal=4,subevent=4",
        "coref_aux_rate": 0.4,
        "save_best_by_family": True,
    },
}
SEED = 13


def _train_argv(
    *,
    remote_repo: Path,
    remote_python: Path,
    model: str,
    p1_hash: str,
    run_dir: Path,
    spec: dict,
) -> list[str]:
    argv = [
        str(remote_python),
        "-u",
        "scripts/train_supervised_relations.py",
        "--train",
        str(remote_repo / "data/processed/maven_ere/train.jsonl"),
        "--train-manifest",
        str(remote_repo / "data/protocols/v6/manifests/maven_ere_train.json"),
        "--dev-manifest",
        str(remote_repo / "data/protocols/v6/manifests/maven_ere_internal-dev.json"),
        "--protocol-root",
        str(remote_repo / "data/protocols/v6"),
        "--repo-root",
        str(remote_repo),
        "--p1-protocol-sha256",
        p1_hash,
        "--official-mention-expansion",
        "--families",
        "causal",
        "subevent",
        "temporal",
        "--model",
        model,
        "--epochs",
        "50",
        "--lr",
        "1e-5",
        "--head-lr",
        "1e-4",
        "--warmup-steps",
        "200",
        "--accum-steps",
        "8",
        "--neg-ratio",
        "inf",
        "--weight-alpha",
        "0.5",
        "--dev-metric",
        "macro",
        "--seed",
        str(SEED),
        "--family-loss-rates",
        spec["family_loss_rates"],
        "--coref-aux-rate",
        str(spec["coref_aux_rate"]),
    ]
    if spec["save_best_by_family"]:
        argv.append("--save-best-by-family")
    argv.extend(("--output", str(run_dir / "checkpoint")))
    return argv


def _score_argv(
    *,
    remote_python: Path,
    remote_preflight: Path,
    candidate_digest: str,
    run_dir: Path,
    per_family: bool,
) -> list[str]:
    argv = [
        str(remote_python),
        "-u",
        "scripts/score_a3_arm.py",
        "--run-dir",
        str(run_dir),
        "--gold",
        str(remote_preflight / "data/MAVEN_ERE/valid.jsonl"),
        "--candidate-digest",
        candidate_digest,
    ]
    if per_family:
        argv.append("--per-family-checkpoints")
    return argv


def intended_differences(commands: dict[str, dict]) -> dict[str, dict]:
    """Return the three pre-registered recipe axes for matrix review."""
    return {
        arm: {
            "family_loss_rates": entry["configuration"]["family_loss_rates"],
            "coref_aux_rate": entry["configuration"]["coref_aux_rate"],
            "save_best_by_family": entry["configuration"]["save_best_by_family"],
        }
        for arm, entry in commands.items()
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--preflight", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--p1-protocol-sha256", required=True)
    args = parser.parse_args()

    repo = args.repo_root.resolve()
    preflight = args.preflight.resolve()
    output = args.output.resolve()
    if output.exists():
        raise SystemExit(f"refusing to overwrite frozen recipe plan: {output}")
    base_plan_path = preflight / "execution_plan.json"
    base = json.loads(base_plan_path.read_text(encoding="utf-8"))
    if base.get("schema_version") != "ekg.a3_baseline_preflight.v1":
        raise SystemExit("base A3 preflight schema mismatch")
    if base.get("status") != "pass" or base.get("final_valid_accessed") is not False:
        raise SystemExit("base A3 preflight is not eligible")
    if base.get("p1_bundle_protocol_sha256") != args.p1_protocol_sha256:
        raise SystemExit("base A3 preflight P1 hash mismatch")

    remote_repo = Path(base["execution_environment"]["remote_repo_root"])
    remote_preflight = Path(base["execution_environment"]["remote_preflight"])
    remote_python = Path(base["execution_environment"]["remote_python"])
    remote_stage = remote_preflight.parent
    candidate_digest = base["candidate_summaries"]["internal-dev"][
        "candidate_id_digest_sha256"
    ]
    commands = {}
    for arm, spec in ARMS.items():
        run_dir = remote_stage / arm / f"seed-{SEED}"
        commands[arm] = {
            "cwd": str(remote_repo),
            "run_dir": str(run_dir),
            "configuration": {"seed": SEED, **spec},
            "train_argv": _train_argv(
                remote_repo=remote_repo,
                remote_python=remote_python,
                model=base["model_assumptions"]["path"],
                p1_hash=args.p1_protocol_sha256,
                run_dir=run_dir,
                spec=spec,
            ),
            "score_argv": _score_argv(
                remote_python=remote_python,
                remote_preflight=remote_preflight,
                candidate_digest=candidate_digest,
                run_dir=run_dir,
                per_family=spec["save_best_by_family"],
            ),
        }

    plan = {
        "schema_version": "ekg.a3_recipe_accounting.v1",
        "status": "pass",
        "p1_bundle_id": base["p1_bundle_id"],
        "p1_bundle_protocol_sha256": args.p1_protocol_sha256,
        "base_preflight_sha256": sha256_file(base_plan_path),
        "final_valid_accessed": False,
        "candidate_summaries": base["candidate_summaries"],
        "data_hashes": base["hashes"]["data"],
        "model_assumptions": base["model_assumptions"],
        "execution_environment": base["execution_environment"],
        "execution_surface": {
            relative: sha256_file(repo / relative)
            for relative in (
                "scripts/train_supervised_relations.py",
                "scripts/score_a3_arm.py",
                "scripts/run_a3_recipe_arm.py",
                "configs/relations/supervised_dump.yaml",
                "scripts/score_maven_ere_official.py",
            )
        },
        "shared_configuration": {
            "seed": SEED,
            "epochs": 50,
            "lr": "1e-5",
            "head_lr": "1e-4",
            "warmup_steps": 200,
            "accum_steps": 8,
            "neg_ratio": "inf",
            "weight_alpha": "0.5",
            "dev_metric": "macro",
            "families": ["causal", "subevent", "temporal"],
            "official_mention_expansion": True,
        },
        "intended_differences": intended_differences(commands),
        "commands": commands,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"[a3-recipe-freeze] PASS plan={output} sha256={sha256_file(output)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
