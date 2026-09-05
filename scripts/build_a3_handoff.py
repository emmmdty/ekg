#!/usr/bin/env python
"""Validate A3.6 recipe accounting and build the immutable failed handoff."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ekg.core.stage_bundle import (
    create_stage_bundle,
    sha256_file,
    validate_stage_bundle,
)

ARMS = (
    "local_recipe",
    "rates_only",
    "rates_coref",
    "rates_coref_family_selection",
)
SCORES = ("causal_f1", "subevent_f1", "temporal_f1")
LOCAL_HASH_CATEGORIES = ("data", "manifests", "candidate", "evaluator", "config", "code")


class A3HandoffError(ValueError):
    """A recipe arm cannot support the claimed A3 handoff."""


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise A3HandoffError(message)


def _relative(path: Path, repo: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo.resolve()))
    except ValueError as exc:
        raise A3HandoffError(f"path is outside repository: {path}") from exc


def validate_arm(
    arm: str,
    *,
    root: Path,
    plan: dict,
    plan_sha256: str,
    p1_sha256: str,
) -> tuple[dict, dict]:
    run_dir = root / arm / "seed-13"
    metadata_path = run_dir / "run_metadata.json"
    metadata = _load(metadata_path)
    metrics = _load(run_dir / "official_metrics.json")
    checkpoint_metadata = _load(run_dir / "checkpoint/run_metadata.json")
    expected = plan["commands"][arm]

    _require(metadata.get("status") == "complete", f"{arm}: run is incomplete")
    _require(metadata.get("returncodes") == {"train": 0, "score": 0}, f"{arm}: rc")
    _require(metadata.get("exploratory") is False, f"{arm}: exploratory")
    _require(metadata.get("final_valid_accessed") is False, f"{arm}: final-valid")
    _require(metadata.get("seed") == 13, f"{arm}: seed")
    _require(metadata.get("configuration") == expected["configuration"], f"{arm}: config")
    _require(metadata.get("train_argv") == expected["train_argv"], f"{arm}: train argv")
    _require(metadata.get("score_argv") == expected["score_argv"], f"{arm}: score argv")
    _require(metadata.get("recipe_plan_sha256") == plan_sha256, f"{arm}: plan binding")
    _require(metadata.get("p1_bundle_protocol_sha256") == p1_sha256, f"{arm}: P1 binding")
    _require(checkpoint_metadata.get("status") == "complete", f"{arm}: checkpoint status")
    binding = checkpoint_metadata.get("protocol_binding", {})
    _require(binding.get("final_valid_accessed") is False, f"{arm}: checkpoint final-valid")
    _require(binding.get("p1_bundle_protocol_sha256") == p1_sha256, f"{arm}: checkpoint P1")

    artifact_hashes = metadata.get("artifact_sha256", {})
    for relative in (
        "official_metrics.json",
        "official_predictions.jsonl",
        "score.log",
    ):
        path = run_dir / relative
        _require(path.is_file(), f"{arm}: missing {relative}")
        _require(
            artifact_hashes.get(relative) == sha256_file(path),
            f"{arm}: hash mismatch for {relative}",
        )
    _require(
        (run_dir / "checkpoint/run_metadata.json").is_file(),
        f"{arm}: missing checkpoint/run_metadata.json",
    )
    hashes = metrics.get("hashes", {})
    _require(
        hashes.get("predictions") == sha256_file(run_dir / "official_predictions.jsonl"),
        f"{arm}: scorer prediction hash",
    )
    _require(hashes.get("gold") == plan["data_hashes"]["valid.jsonl"], f"{arm}: gold")
    _require(
        metrics.get("population", {}).get("candidate_id_digest")
        == plan["candidate_summaries"]["internal-dev"]["candidate_id_digest_sha256"],
        f"{arm}: candidate population",
    )
    _require(set(SCORES) <= metrics.get("scores", {}).keys(), f"{arm}: score roster")
    return metadata, metrics


def build_handoff(args: argparse.Namespace) -> str:
    repo = args.repo.resolve()
    root = args.accounting_root.resolve()
    output = args.output.resolve()
    _require(not output.exists(), f"refusing to overwrite immutable bundle: {output}")
    plan_sha256 = sha256_file(args.plan)
    _require(plan_sha256 == args.plan_sha256, "recipe plan trust root mismatch")
    _require(sha256_file(args.p1_bundle / "protocol.json") == args.p1_sha256, "P1 mismatch")
    plan = _load(args.plan)
    _require(set(plan.get("commands", {})) == set(ARMS), "arm roster drift")
    _require(plan.get("final_valid_accessed") is False, "plan accessed final-valid")

    metadata_by_arm: dict[str, dict] = {}
    metrics_by_arm: dict[str, dict] = {}
    for arm in ARMS:
        metadata_by_arm[arm], metrics_by_arm[arm] = validate_arm(
            arm,
            root=root,
            plan=plan,
            plan_sha256=plan_sha256,
            p1_sha256=args.p1_sha256,
        )

    populations = [metrics_by_arm[arm]["population"] for arm in ARMS]
    _require(all(item == populations[0] for item in populations), "population drift across arms")
    scorer_hashes = [metrics_by_arm[arm]["hashes"] for arm in ARMS]
    for key in ("evaluator", "gold", "source_lock"):
        _require(len({item[key] for item in scorer_hashes}) == 1, f"{key} drift across arms")

    anchor = max(ARMS, key=lambda arm: metrics_by_arm[arm]["scores"]["causal_f1"])
    score_by_arm = {
        arm: {name: metrics_by_arm[arm]["scores"][name] for name in SCORES}
        for arm in ARMS
    }
    deltas = {
        f"{current}_minus_{previous}": {
            name: score_by_arm[current][name] - score_by_arm[previous][name]
            for name in SCORES
        }
        for previous, current in zip(ARMS[:-1], ARMS[1:], strict=True)
    }
    anchor_dir = root / anchor / "seed-13"
    predictions = _read_jsonl(anchor_dir / "official_predictions.jsonl")

    hashes = {
        "data": {
            _relative(args.gold, repo): sha256_file(args.gold),
        },
        "manifests": {
            relative: sha256_file(repo / relative)
            for relative in (
                "data/protocols/v6/manifests/maven_ere_train.json",
                "data/protocols/v6/manifests/maven_ere_internal-dev.json",
            )
        },
        "candidate": {
            "data/protocols/v6/ch2_candidate_protocol.json": sha256_file(
                repo / "data/protocols/v6/ch2_candidate_protocol.json"
            ),
        },
        "evaluator": {
            "data/protocols/v6/tools/maven_ere_evaluate.py": sha256_file(
                repo / "data/protocols/v6/tools/maven_ere_evaluate.py"
            ),
        },
        "config": {
            _relative(args.plan, repo): plan_sha256,
            "data/protocols/v6/access_ledger.json": sha256_file(
                repo / "data/protocols/v6/access_ledger.json"
            ),
            "data/protocols/v6/source_lock.json": sha256_file(
                repo / "data/protocols/v6/source_lock.json"
            ),
        },
        "code": {
            **plan["execution_surface"],
            "scripts/build_a3_handoff.py": sha256_file(repo / "scripts/build_a3_handoff.py"),
            "src/ekg/core/stage_bundle.py": sha256_file(repo / "src/ekg/core/stage_bundle.py"),
        },
        "checkpoint": {
            "/data/TJK/ekg/runs/stages/A3/a3-v6-recipe-accounting-r16/"
            f"{arm}/seed-13/{relative}": digest
            for arm in ARMS
            for relative, digest in metadata_by_arm[arm]["artifact_sha256"].items()
            if relative.startswith("checkpoint/")
        },
    }
    remote_evidence = {
        _relative(root / arm / "seed-13/run_metadata.json", repo): sha256_file(
            root / arm / "seed-13/run_metadata.json"
        )
        for arm in ARMS
    }
    metrics = {
        "schema_version": "ekg.a3_recipe_handoff_metrics.v1",
        "status": "failed",
        "score_scale": "percentage points",
        "score_by_arm": score_by_arm,
        "single_variable_deltas": deltas,
        "fallback_anchor": anchor,
        "fallback_reason": (
            "highest official internal-dev causal F1 under the P1 primary-anchor rule; "
            "recipe gains receive no method-contribution credit"
        ),
        "guardrail_observation": (
            "the fallback anchor improves causal and temporal versus local_recipe but lowers "
            "subevent F1"
        ),
        "validation": {
            "arms_complete": True,
            "single_seed": 13,
            "single_variable_plan_exact": True,
            "shared_population_exact": True,
            "official_evaluator_exact": True,
            "final_valid_accessed": False,
            "local_remote_selected_artifact_hashes_exact": True,
        },
    }
    status = {
        "status": "failed",
        "global_protocol_status": "pass",
        "phase_status": "failed",
        "next_entry_status": "pass",
        "primary_anchor_selection_rule": (
            "highest internal-dev causal micro-F1 among eligible A3.6 recipe arms; "
            "ties follow frozen arm order"
        ),
        "primary_anchor": anchor,
        "historical_final_access_disclosed": True,
        "final_valid_access_ledger": "data/protocols/v6/access_ledger.json",
        "v6_confirmatory_eval_count": 0,
        "exploratory": False,
        "upstream_bundle_ids": [args.p1_bundle.name],
        "executed": True,
        "remaining_condition": (
            "A3 old mechanism family is closed; R1 may consume this fallback for prospective "
            "power and decide whether a new A4 family is admissible"
        ),
    }
    population = populations[0]
    create_stage_bundle(
        output,
        phase="A3",
        predictions=predictions,
        metrics=metrics,
        status=status,
        hashes=hashes,
        expected_ids=[record["id"] for record in predictions],
        candidate_id_digest=population["candidate_id_digest"],
        population_counts={
            key: value for key, value in population.items() if key != "candidate_id_digest"
        },
        local_hash_categories=LOCAL_HASH_CATEGORIES,
        remote_evidence_sha256=remote_evidence,
        protocol_extra={
            "p1_bundle_protocol_sha256": args.p1_sha256,
            "recipe_plan_sha256": plan_sha256,
            "execution_commit": metadata_by_arm[ARMS[0]]["commit"],
            "checkpoint_host": "gpu-4090",
            "checkpoint_root": "/data/TJK/ekg/runs/stages/A3/a3-v6-recipe-accounting-r16",
            "checkpoint_transferred": False,
            "final_valid_accessed": False,
        },
    )
    protocol_sha256 = sha256_file(output / "protocol.json")
    validate_stage_bundle(
        output,
        evidence_root=repo,
        expected_protocol_sha256=protocol_sha256,
        known_upstream_bundle_ids={args.p1_bundle.name},
    )
    return protocol_sha256


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--accounting-root", required=True, type=Path)
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--plan-sha256", required=True)
    parser.add_argument("--p1-bundle", required=True, type=Path)
    parser.add_argument("--p1-sha256", required=True)
    parser.add_argument("--gold", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    digest = build_handoff(args)
    print(f"[a3-handoff] failed handoff validated: {args.output} protocol={digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
