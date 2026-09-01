#!/usr/bin/env python
"""Assemble and validate P1's auditable four-file handoff bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import subprocess
from pathlib import Path

from ekg.core.stage_bundle import (
    create_stage_bundle,
    is_sha256,
    sha256_file,
    validate_stage_bundle,
)
from ekg.relations.maven_ere_official import (
    records_by_id,
    validate_official_predictions,
)

CODE_PATHS = (
    "src/ekg/core/stage_bundle.py",
    # The A3.2 mechanism lives here and decides what the trainer optimises, so a
    # bundle that pinned the trainer but not this file would claim to fix the
    # code behind a number it does not actually cover.
    "src/ekg/relations/balance.py",
    "src/ekg/relations/data/maven_ere.py",
    "src/ekg/relations/extractor/supervised.py",
    "src/ekg/relations/maven_ere_official.py",
    "src/ekg/relations/objective_registry.py",
    "src/ekg/relations/objectives.py",
    "src/ekg/relations/pair_heads.py",
    "src/ekg/relations/pairs.py",
    "src/ekg/relations/prototype.py",
    "scripts/build_p1_bundle.py",
    "scripts/fetch_p1_assets.py",
    "scripts/freeze_v6_protocol.py",
    "scripts/run_p1_baseline_smokes.py",
    "scripts/run_p1_local_gate.py",
    "scripts/score_maven_ere_official.py",
    "scripts/train_supervised_relations.py",
    "scripts/verify_p1_scorer.py",
    "scripts/build_maven_ere_submission.py",
    "scripts/evaluate_relation_pairs.py",
)

# A3 的 materializer/launcher 是执行面，不是协议身份：它们由 execution_plan.json 的
# plan SHA-256 与每个 run 的 launcher_sha256 绑定。放进 CODE_PATHS 会让一次路径修复
# 作废整个 P1 信任根（r1..r5 即由此而来），且不增加任何科研上的约束力。

LOCAL_HASH_CATEGORIES = ("data", "manifests", "candidate", "evaluator", "config", "code")
EXPECTED_BASELINES = {"local_pair", "official_single", "official_joint"}
EXPECTED_REMOTE_RUNS = {"ten_document", "longest_internal_dev"}


class P1EvidenceError(ValueError):
    """A P1 input claims PASS without the evidence required to support it."""


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _canonical_hash(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise P1EvidenceError(message)


def _relative_to_repo(path: Path, repo: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo.resolve()))
    except ValueError as exc:
        raise P1EvidenceError(f"evidence path is outside repository: {path}") from exc


def _check_file_hash(path: Path, expected: object, *, label: str) -> None:
    _require(is_sha256(expected), f"{label} is not a SHA-256 digest")
    _require(path.is_file(), f"{label} file is missing: {path}")
    actual = sha256_file(path)
    _require(actual == expected, f"{label} hash mismatch: expected {expected}, got {actual}")


def _validate_registry(repo: Path, root: Path, registry: dict) -> None:
    _require(registry.get("schema_version") == "ekg.protocol_registry.v1", "registry schema")
    for relative, digest in registry.get("source_sha256", {}).items():
        _check_file_hash(repo / relative, digest, label=f"source {relative}")
    manifests = registry.get("manifest_sha256")
    _require(isinstance(manifests, dict) and len(manifests) == 6, "six manifests required")
    for relative, digest in manifests.items():
        _check_file_hash(root / relative, digest, label=f"manifest {relative}")
    for key, relative in (
        ("support_counts_sha256", "support_counts.json"),
        ("candidate_protocol_sha256", "ch2_candidate_protocol.json"),
        ("shared_id_namespace_sha256", "shared_id_namespace.json"),
        ("preregistration_sha256", "preregistration.json"),
        ("access_ledger_sha256", "access_ledger.json"),
    ):
        _check_file_hash(root / relative, registry.get(key), label=key)


def _validate_source_lock(repo: Path, source_lock: dict) -> None:
    _require(source_lock.get("schema_version") == "ekg.external_source_lock.v1", "source lock")
    evaluator = source_lock.get("evaluator")
    _require(isinstance(evaluator, dict), "source lock evaluator missing")
    _check_file_hash(repo / evaluator["local_path"], evaluator.get("sha256"), label="evaluator")
    _require((repo / source_lock["license_path"]).is_file(), "source license missing")
    for patch in source_lock.get("patches", []):
        _check_file_hash(repo / patch["path"], patch.get("sha256"), label=patch["path"])
    checkout = repo / source_lock["local_checkout"]
    commit = subprocess.run(
        ("git", "rev-parse", "HEAD"),
        cwd=checkout,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    ).stdout.strip()
    _require(commit == source_lock.get("commit"), "source checkout commit drift")


def _validate_evaluator_assets(
    root: Path,
    registry: dict,
    source_lock: dict,
    candidate: dict,
    gold_self: dict,
    adversarial: dict,
) -> None:
    _require(
        gold_self.get("evaluator_sha256") == source_lock["evaluator"]["sha256"],
        "gold-self evaluator hash drift",
    )
    valid_source = "data/processed/maven_ere/valid.jsonl"
    _require(
        gold_self.get("gold_sha256") == registry["source_sha256"][valid_source],
        "gold-self source hash drift",
    )
    final_candidate = candidate.get("final-valid", {})
    _require(
        gold_self.get("population", {}).get("candidate_id_digest")
        == final_candidate.get("candidate_id_digest_sha256"),
        "gold-self candidate digest drift",
    )
    expected_population = final_candidate.get("population_counts", {})
    actual_population = gold_self.get("population", {})
    _require(actual_population.get("documents") == expected_population.get("documents"), "docs")
    _require(
        actual_population.get("event_mentions") == expected_population.get("event_mentions"),
        "gold-self event mention population drift",
    )
    _require(
        actual_population.get("relation_pairs")
        == expected_population.get("ordered_mention_pairs"),
        "gold-self pair population drift",
    )
    scores = gold_self.get("scores")
    required_f1 = {
        "temporal_f1",
        "causal_f1",
        "subevent_f1",
        "b_cubed_f1",
        "ceaf_f1",
        "muc_f1",
        "blanc_f1",
    }
    _require(isinstance(scores, dict) and required_f1 <= scores.keys(), "gold-self F1 keys")
    _require(
        all(math.isclose(float(scores[key]), 100.0, abs_tol=1e-4) for key in required_f1),
        "gold-self F1 is not all 100",
    )
    expected = adversarial.get("expected_f1")
    actual = adversarial.get("scores")
    _require(isinstance(expected, dict) and set(expected) == {
        "empty", "reverse_causal", "coref_merge", "coref_split"
    }, "adversarial fixture roster")
    _require(isinstance(actual, dict) and set(actual) == set(expected), "adversarial scores")
    for fixture, expected_scores in expected.items():
        for metric, value in expected_scores.items():
            _require(
                math.isclose(float(actual[fixture][metric]), float(value), abs_tol=1e-6),
                f"adversarial mismatch: {fixture}.{metric}",
            )


def _validate_local_gate(repo: Path, local_gate: dict) -> None:
    """The three commands passed on a tree whose P1 code equals what we hash now.

    Deliberately not asserted: that every unrelated repository file is unchanged. The
    tested tree is recorded as provenance, but binding it would let any edit anywhere
    invalidate a protocol bundle whose evidence did not move.
    """
    _require(local_gate.get("schema_version") == "ekg.p1_local_gate.v2", "local gate schema")
    _require(local_gate.get("status") == "pass", "local gate status")
    _require(not local_gate.get("tree_changed_during_gate"), "tree changed during local gate")
    results = local_gate.get("results")
    _require(
        isinstance(results, dict) and set(results) == {"pytest", "ruff", "ekg_smoke"},
        "local gate roster",
    )
    _require(all(item.get("returncode") == 0 for item in results.values()), "local command failed")
    _require(is_sha256(local_gate.get("tested_tree_sha256", "")), "local gate tree digest")
    tested = local_gate.get("tested_file_sha256")
    _require(isinstance(tested, dict) and tested, "local gate file hashes")
    for path in CODE_PATHS:
        _require(
            tested.get(path) == sha256_file(repo / path),
            f"local gate did not cover current {path}",
        )


def _validate_baselines(repo: Path, root: Path, baseline: dict, source_lock: dict) -> None:
    _require(baseline.get("schema_version") == "ekg.p1_baseline_smoke.v1", "baseline schema")
    _require(len(baseline.get("fixture_doc_ids", [])) == 10, "baseline fixture size")
    _require(baseline.get("source_commit") == source_lock.get("commit"), "baseline source")
    _require(
        baseline.get("source_lock_sha256") == sha256_file(root / "source_lock.json"),
        "baseline source-lock hash drift",
    )
    _check_file_hash(
        root / "baselines/fixture/gold.jsonl",
        baseline.get("fixture_gold_sha256"),
        label="baseline fixture gold",
    )
    _check_file_hash(
        root / "baselines/fixture/test.jsonl",
        baseline.get("fixture_test_sha256"),
        label="baseline fixture test",
    )
    smokes = baseline.get("smokes")
    _require(isinstance(smokes, dict) and set(smokes) == EXPECTED_BASELINES, "baseline roster")
    gold = records_by_id(
        _read_jsonl(root / "baselines/fixture/gold.jsonl"),
        source="baseline fixture gold",
    )
    for name, smoke in smokes.items():
        _require(smoke.get("status") == "pass", f"{name} status")
        _require(smoke.get("schema_only") is True, f"{name} schema boundary")
        _require(smoke.get("model_execution") is False, f"{name} model boundary")
        assumptions = smoke.get("input_assumptions")
        _require(isinstance(assumptions, dict) and assumptions, f"{name} input assumptions")
        prediction_path = root / f"baselines/{name}/predictions.jsonl"
        _check_file_hash(prediction_path, smoke.get("prediction_sha256"), label=name)
        prediction = records_by_id(_read_jsonl(prediction_path), source=name)
        validation = validate_official_predictions(
            gold,
            prediction,
            expected_candidate_digest=baseline["candidate_id_digest"],
        )
        _require(validation == smoke.get("validation"), f"{name} validation drift")


def _validate_remote_smoke(repo: Path, root: Path, remote: dict, baseline: dict) -> None:
    _require(remote.get("schema_version") == "ekg.p1_remote_smoke.v1", "remote schema")
    _require(remote.get("status") == "pass", "remote status")
    _require(remote.get("scientific_scores_produced") is False, "remote score boundary")
    _require(remote.get("final_valid_accessed") is False, "remote final-valid access")
    server = remote.get("server", {})
    _require(server.get("alias") == "gpu-4090", "remote server alias")
    _require(server.get("working_directory") == "/data/TJK/ekg", "remote working dir")
    _require(server.get("worktree_clean") is True, "remote worktree was dirty")
    _require(bool(re.fullmatch(r"[0-9a-f]{40}", str(server.get("git_commit")))), "remote commit")
    runtime = remote.get("runtime", {})
    _require(runtime.get("python") == ".venv/bin/python", "remote python")
    _require(runtime.get("cuda_available") is True, "remote CUDA unavailable")
    gpu = remote.get("gpu", {})
    _require(gpu.get("visible_device") == 0, "remote GPU index")
    _require("RTX 4090" in str(gpu.get("name")), "remote GPU model")
    _require(
        isinstance(gpu.get("memory_total_mib"), int) and gpu["memory_total_mib"] > 20000,
        "remote memory",
    )
    checkpoint_path = remote.get("checkpoint", {}).get("path")
    checkpoint_hashes = remote.get("checkpoint_hashes")
    _require(isinstance(checkpoint_path, str) and checkpoint_path, "remote checkpoint path")
    _require(
        isinstance(checkpoint_hashes, dict) and len(checkpoint_hashes) >= 3,
        "remote checkpoint hashes",
    )
    for path, digest in checkpoint_hashes.items():
        _require(path.startswith(f"{checkpoint_path}/"), "checkpoint hash path drift")
        _require(is_sha256(digest), f"invalid remote checkpoint hash: {path}")

    provenance = remote.get("command_provenance", {})
    _require(provenance.get("executed_command_available") is False, "old argv boundary")
    _require(provenance.get("working_directory") == server["working_directory"], "command cwd")
    commands = provenance.get("reproduction_commands")
    wall_times = provenance.get("wall_time_seconds")
    _require(isinstance(commands, dict) and set(commands) == EXPECTED_REMOTE_RUNS, "commands")
    _require(isinstance(wall_times, dict) and set(wall_times) == EXPECTED_REMOTE_RUNS, "wall times")
    for name, command in commands.items():
        _require(
            isinstance(command, list) and all(isinstance(item, str) for item in command),
            f"{name} command",
        )
        _require(".venv/bin/python" in command, f"{name} remote python command")
        _require("scripts/build_maven_ere_submission.py" in command, f"{name} entrypoint")
        _require(float(wall_times[name]) > 0, f"{name} wall time")

    expected_inputs = {
        "ten_document_fixture": root / "baselines/fixture/test.jsonl",
        "longest_internal_dev_fixture": root / "baselines/fixture/longest_test.jsonl",
    }
    for name, expected_path in expected_inputs.items():
        item = remote.get("inputs", {}).get(name, {})
        _require((repo / item.get("path", "")).resolve() == expected_path.resolve(), f"{name} path")
        _check_file_hash(expected_path, item.get("sha256"), label=name)

    inference = remote.get("inference", {})
    _require(inference.get("coreference_predictor") == "lexical", "remote coref")
    _require(inference.get("relation_predictor") == "supervised", "remote relation")
    _require(inference.get("relation_threshold") == 0.7, "remote threshold")
    gold_paths = {
        "ten_document": root / "baselines/fixture/gold.jsonl",
        "longest_internal_dev": root / "baselines/fixture/longest_gold.jsonl",
    }
    for name, gold_path in gold_paths.items():
        run = inference.get(name, {})
        _require(run.get("return_code") == 0, f"{name} return code")
        _require(run.get("skipped_documents") == 0, f"{name} skipped documents")
        prediction_path = repo / run.get("prediction_path", "")
        log_path = repo / run.get("log_path", "")
        _check_file_hash(prediction_path, run.get("prediction_sha256"), label=f"{name} prediction")
        _check_file_hash(log_path, run.get("log_sha256"), label=f"{name} log")
        log = log_path.read_text(encoding="utf-8")
        _require("SKIPPED" not in log, f"{name} log contains a skipped document")
        gold = records_by_id(_read_jsonl(gold_path), source=f"{name} gold")
        prediction = records_by_id(_read_jsonl(prediction_path), source=f"{name} prediction")
        validation = validate_official_predictions(
            gold,
            prediction,
            expected_candidate_digest=run.get("candidate_id_digest"),
        )
        _require(validation["documents"] == run.get("documents"), f"{name} documents")
        _require(validation["event_mentions"] == run.get("event_mentions"), f"{name} mentions")
        _require(validation["relation_pairs"] == run.get("candidate_pairs"), f"{name} pairs")
    _require(
        inference["ten_document"]["candidate_id_digest"] == baseline["candidate_id_digest"],
        "remote fixture candidate digest drift",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol-root", type=Path, default=Path("data/protocols/v6"))
    # 默认跟随 registry 选中的 bundle：写死版本号会在每次 supersede 后变成过期地雷。
    parser.add_argument("--bundle", type=Path, default=None)
    parser.add_argument(
        "--remote-smoke",
        type=Path,
        default=Path("data/protocols/v6/remote_smoke.json"),
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="validate the registry-selected existing bundle without writing anything",
    )
    args = parser.parse_args()
    repo = Path.cwd().resolve()
    root = args.protocol_root
    registry = _load(root / "registry.json")
    source_lock = _load(root / "source_lock.json")
    preregistration = _load(root / "preregistration.json")
    candidate = _load(root / "ch2_candidate_protocol.json")
    gold_self = _load(root / "evaluator/gold_self_metrics.json")
    adversarial = _load(root / "evaluator/adversarial_metrics.json")
    baseline = _load(root / "baselines/smoke_summary.json")
    local_gate = _load(root / "local_gate.json")
    access_ledger = _load(root / "access_ledger.json")

    _validate_registry(repo, root, registry)
    _validate_source_lock(repo, source_lock)
    _validate_evaluator_assets(
        root,
        registry,
        source_lock,
        candidate,
        gold_self,
        adversarial,
    )
    _validate_local_gate(repo, local_gate)
    _validate_baselines(repo, root, baseline, source_lock)
    _require(
        access_ledger.get("schema_version") == "ekg.final_valid_access.v1",
        "access ledger schema",
    )
    _require(
        access_ledger.get("historical_final_access_disclosed") is True,
        "historical final access was not disclosed",
    )
    _require(
        access_ledger.get("v6_confirmatory_eval_count") == 0,
        "P1 requires zero confirmatory final-valid evaluations",
    )

    if args.bundle is None:
        args.bundle = repo / "runs/stages/P1" / registry["p1_bundle_id"]

    remote = _load(args.remote_smoke) if args.remote_smoke.exists() else None
    if remote is not None:
        _validate_remote_smoke(repo, root, remote, baseline)
    remote_pass = remote is not None

    if args.validate_only:
        selected_bundle = repo / "runs/stages/P1" / registry["p1_bundle_id"]
        _require(
            args.bundle.resolve() == selected_bundle.resolve(),
            "--bundle does not match registry p1_bundle_id",
        )
        validate_stage_bundle(
            args.bundle,
            evidence_root=repo,
            expected_protocol_sha256=registry["p1_bundle_protocol_sha256"],
            known_upstream_bundle_ids=set(),
        )
        print(f"[p1-bundle] PASS existing bundle validation: {args.bundle}")
        return 0

    _require(not args.bundle.exists(), f"refusing to overwrite existing bundle: {args.bundle}")

    global_checks = {
        "six_manifests_frozen": True,
        "gold_self_all_f1_100": True,
        "four_adversarial_fixtures": True,
        "candidate_digest_matches_scorer": True,
        "local_gate_current_and_pass": True,
        "external_hashes_recomputed": True,
        "confirmatory_eval_count_zero": True,
    }
    baseline_checks = {
        name: item["status"] == "pass" and item["schema_only"] is True
        for name, item in baseline["smokes"].items()
    }
    a3_entry = "pass" if remote_pass else "conditional"
    phase_status = "pass" if remote_pass else "conditional"
    predictions_by_baseline = {
        name: {
            record["id"]: record
            for record in (
                json.loads(line)
                for line in (root / f"baselines/{name}/predictions.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
                if line
            )
        }
        for name in baseline_checks
    }
    fixture_ids = baseline["fixture_doc_ids"]
    predictions = [
        {
            "id": doc_id,
            "baseline_schema_outputs_present": {
                name: doc_id in records for name, records in predictions_by_baseline.items()
            },
            "schema_only": True,
        }
        for doc_id in fixture_ids
    ]
    code_hashes = {path: sha256_file(repo / path) for path in CODE_PATHS}
    root_relative = _relative_to_repo(root, repo)
    manifest_hashes = {
        f"{root_relative}/{path}": digest
        for path, digest in registry["manifest_sha256"].items()
    }
    candidate_hashes = {
        f"{root_relative}/ch2_candidate_protocol.json": registry[
            "candidate_protocol_sha256"
        ],
        f"{root_relative}/baselines/fixture/gold.jsonl": baseline[
            "fixture_gold_sha256"
        ],
        f"{root_relative}/baselines/fixture/test.jsonl": baseline[
            "fixture_test_sha256"
        ],
    }
    evaluator_hashes = {
        source_lock["evaluator"]["local_path"]: source_lock["evaluator"]["sha256"],
        f"{root_relative}/evaluator/gold_self_metrics.json": sha256_file(
            root / "evaluator/gold_self_metrics.json"
        ),
        f"{root_relative}/evaluator/adversarial_metrics.json": sha256_file(
            root / "evaluator/adversarial_metrics.json"
        ),
        f"{root_relative}/evaluator/gold_prediction.jsonl": sha256_file(
            root / "evaluator/gold_prediction.jsonl"
        ),
    }
    config_paths = [
        "preregistration.json",
        "access_ledger.json",
        "source_lock.json",
        "support_counts.json",
        "shared_id_namespace.json",
        "local_gate.json",
        "baselines/smoke_summary.json",
    ]
    for name in EXPECTED_BASELINES:
        config_paths.extend(
            (f"baselines/{name}/smoke.json", f"baselines/{name}/predictions.jsonl")
        )
    config_hashes = {
        f"{root_relative}/{path}": sha256_file(root / path) for path in config_paths
    }
    checkpoint_hashes = remote["checkpoint_hashes"] if remote else {}
    hashes = {
        "data": registry["source_sha256"],
        "manifests": manifest_hashes,
        "candidate": candidate_hashes,
        "evaluator": evaluator_hashes,
        "config": config_hashes,
        "code": code_hashes,
        "checkpoint": checkpoint_hashes,
    }
    metrics = {
        "schema_version": "ekg.p1_metrics.v1",
        "global_checks": global_checks,
        "baseline_schema_checks": baseline_checks,
        "gold_self_scores": gold_self["scores"],
        "adversarial_expected_f1": adversarial["expected_f1"],
        "local_gate": {
            name: item["returncode"] for name, item in local_gate["results"].items()
        },
        "remote_checkpoint_smoke": remote,
        "scientific_scores_produced": False,
    }
    status = {
        "status": phase_status,
        "global_protocol_status": "pass",
        "phase_status": phase_status,
        "next_entry_status": a3_entry,
        "a3_entry_status": a3_entry,
        "primary_anchor_selection_rule": preregistration["primary_anchor_selection_rule"],
        "primary_anchor": None,
        "historical_final_access_disclosed": True,
        "final_valid_access_ledger": str(root / "access_ledger.json"),
        "v6_confirmatory_eval_count": 0,
        "exploratory": False,
        "upstream_bundle_ids": [],
        "executed": True,
        "schema_smoke_is_baseline_evidence": False,
        "remaining_condition": None if remote_pass else "P1.6 4090 checkpoint forward smoke",
    }
    create_stage_bundle(
        args.bundle,
        phase="P1",
        predictions=predictions,
        metrics=metrics,
        status=status,
        hashes=hashes,
        expected_ids=fixture_ids,
        candidate_id_digest=baseline["candidate_id_digest"],
        population_counts=baseline["population_counts"],
        local_hash_categories=LOCAL_HASH_CATEGORIES,
        remote_evidence_sha256=(
            {f"{root_relative}/remote_smoke.json": sha256_file(args.remote_smoke)}
            if remote
            else {}
        ),
        protocol_extra={
            "seed": None,
            "historical_final_access_disclosed": True,
            "v6_confirmatory_eval_count": 0,
            "source_lock_sha256": sha256_file(root / "source_lock.json"),
            "candidate_protocol_sha256": registry["candidate_protocol_sha256"],
            "access_ledger_sha256": registry["access_ledger_sha256"],
            "code_state_digest_sha256": _canonical_hash(code_hashes),
            "remote_smoke_required_for_a3": True,
        },
    )
    protocol_sha256 = sha256_file(args.bundle / "protocol.json")
    validate_stage_bundle(
        args.bundle,
        evidence_root=repo,
        expected_protocol_sha256=protocol_sha256,
        known_upstream_bundle_ids=set(),
    )
    registry["global_protocol_status"] = "pass"
    registry["a3_entry_status"] = a3_entry
    registry["p1_bundle_id"] = args.bundle.name
    registry["p1_bundle_protocol_sha256"] = protocol_sha256
    (root / "registry.json").write_text(
        json.dumps(registry, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        f"[p1-bundle] PASS validation; global_protocol_status=pass "
        f"a3_entry_status={a3_entry} bundle={args.bundle}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
