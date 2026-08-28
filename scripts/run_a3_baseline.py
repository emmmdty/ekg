#!/usr/bin/env python
"""Validate and optionally execute one frozen A3 baseline/seed command.

Without ``--execute`` this is a CPU-only preflight that prints the exact command,
working directory, and expected outputs. With ``--execute`` it refuses an
existing run directory, checks the model/Python/GPU assumptions, records actual
argv and hashes, and then runs exactly one baseline job.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

from ekg.core.schema import RelationEdge, RelationType
from ekg.relations.maven_ere_official import (
    CAUSAL_SUBTYPES,
    TEMPORAL_SUBTYPES,
    empty_official_prediction,
    records_by_id,
    validate_official_predictions,
)

BASELINES = ("local_pair", "official_single", "official_joint")
SEEDS = (13, 17, 42)


class A3LaunchError(ValueError):
    """The preflight or requested execution does not match the frozen plan."""


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_plan(
    path: Path, expected_p1_hash: str, expected_plan_hash: str
) -> dict:
    actual_plan_hash = sha256_file(path)
    if actual_plan_hash != expected_plan_hash:
        raise A3LaunchError(
            f"A3 execution plan hash mismatch: expected {expected_plan_hash}, "
            f"got {actual_plan_hash}"
        )
    plan = json.loads(path.read_text(encoding="utf-8"))
    if plan.get("schema_version") != "ekg.a3_baseline_preflight.v1":
        raise A3LaunchError("A3 execution plan schema mismatch")
    if plan.get("status") != "pass":
        raise A3LaunchError("A3 preflight status is not pass")
    if plan.get("final_valid_accessed") is not False:
        raise A3LaunchError("A3 preflight does not prove final-valid non-access")
    if plan.get("p1_bundle_protocol_sha256") != expected_p1_hash:
        raise A3LaunchError("A3 plan P1 digest differs from command trust root")
    preflight = path.parent
    data_hashes = plan.get("hashes", {}).get("data", {})
    data_root = preflight / "data/MAVEN_ERE"
    actual_data_names = {path.name for path in data_root.iterdir() if path.is_file()}
    if actual_data_names != set(data_hashes):
        raise A3LaunchError("materialized A3 data file set differs from the plan")
    for name, expected in data_hashes.items():
        data_path = preflight / "data/MAVEN_ERE" / name
        if not data_path.is_file() or sha256_file(data_path) != expected:
            raise A3LaunchError(f"materialized A3 data hash mismatch: {name}")
    source_hashes = plan.get("hashes", {}).get("adapted_official_source", {})
    if not source_hashes:
        raise A3LaunchError("A3 plan has no adapted official-source hashes")
    actual_source_names = {
        path.relative_to(preflight / "source").as_posix()
        for path in (preflight / "source").rglob("*")
        if path.is_file()
    }
    if actual_source_names != set(source_hashes):
        raise A3LaunchError("materialized official source file set differs from the plan")
    for relative, expected in source_hashes.items():
        source_path = preflight / "source" / relative
        if not source_path.is_file() or sha256_file(source_path) != expected:
            raise A3LaunchError(f"materialized official source hash mismatch: {relative}")
    return plan


def _selected_command(
    plan: dict, *, baseline: str, seed: int, run_dir: Path
) -> tuple[Path, list[str], list[Path]]:
    entry = plan["commands"][baseline][str(seed)]
    replacements = {"run_dir": str(run_dir)}
    cwd_text = entry.get("cwd") or entry["cwd_template"].format(**replacements)
    argv = [part.format(**replacements) for part in entry["argv"]]
    raw_outputs = entry.get("expected_outputs") or [
        item.format(**replacements) for item in entry["expected_outputs_template"]
    ]
    return Path(cwd_text), argv, [Path(item) for item in raw_outputs]


def _hash_run_files(run_dir: Path) -> dict[str, str]:
    return {
        path.relative_to(run_dir).as_posix(): sha256_file(path)
        for path in sorted(run_dir.rglob("*"))
        if path.is_file() and path.name != "run_metadata.json"
    }


def _write_metadata(run_dir: Path, payload: dict) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "run_metadata.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _read_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line
    ]


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )


def _local_relation_payload(edges: list[RelationEdge]) -> dict:
    causal = {subtype: set() for subtype in CAUSAL_SUBTYPES}
    subevent: set[tuple[str, str]] = set()
    for edge in edges:
        head = edge.head_id.split("::", 1)[-1]
        tail = edge.tail_id.split("::", 1)[-1]
        if head == tail:
            raise A3LaunchError("local pair inference emitted a self relation")
        if edge.relation_type == RelationType.CAUSAL:
            if edge.subtype not in causal:
                raise A3LaunchError(f"unknown local causal subtype: {edge.subtype}")
            causal[edge.subtype].add((head, tail))
        elif edge.relation_type == RelationType.SUBEVENT:
            if edge.subtype != "SUBEVENT_OF":
                raise A3LaunchError(f"unknown local subevent subtype: {edge.subtype}")
            subevent.add((head, tail))
        else:
            raise A3LaunchError(
                f"formal local pair output contains inactive family {edge.relation_type.value}"
            )
    return {
        "temporal_relations": {subtype: [] for subtype in TEMPORAL_SUBTYPES},
        "causal_relations": {
            subtype: sorted(list(pair) for pair in causal[subtype])
            for subtype in CAUSAL_SUBTYPES
        },
        "subevent_relations": sorted(list(pair) for pair in subevent),
    }


def normalize_predictions(
    *,
    baseline: str,
    raw_path: Path,
    gold_path: Path,
    output: Path,
    candidate_digest: str,
) -> None:
    gold_records = _read_jsonl(gold_path)
    gold = records_by_id(gold_records, source=str(gold_path))
    if baseline == "local_pair":
        raw_by_id: dict[str, dict] = {}
        for row in _read_jsonl(raw_path):
            doc_id = row.get("doc_id")
            if not isinstance(doc_id, str) or doc_id in raw_by_id:
                raise A3LaunchError(f"invalid/duplicate local prediction document: {doc_id}")
            raw_by_id[doc_id] = row
        if set(raw_by_id) != set(gold):
            raise A3LaunchError("local prediction document set differs from internal-dev")
        predictions = []
        for record in gold_records:
            prediction = empty_official_prediction(record)
            edges = [
                RelationEdge.model_validate(item)
                for item in raw_by_id[record["id"]].get("edges", [])
            ]
            prediction.update(_local_relation_payload(edges))
            predictions.append(prediction)
    elif baseline == "official_single":
        raw = records_by_id(_read_jsonl(raw_path), source=str(raw_path))
        if set(raw) != set(gold):
            raise A3LaunchError("official-single document set differs from internal-dev")
        predictions = []
        for record in gold_records:
            prediction = empty_official_prediction(record)
            prediction["causal_relations"] = raw[record["id"]].get("causal_relations")
            predictions.append(prediction)
    else:
        raw = records_by_id(_read_jsonl(raw_path), source=str(raw_path))
        predictions = [raw[record["id"]] for record in gold_records]
    validate_official_predictions(
        gold,
        records_by_id(predictions, source=f"normalized {baseline}"),
        expected_candidate_digest=candidate_digest,
    )
    _write_jsonl(output, predictions)


def _prepare_official_workspace(preflight: Path, run_dir: Path) -> None:
    workspace_source = run_dir / "workspace/source"
    shutil.copytree(preflight / "source", workspace_source)
    data_link = workspace_source / "data/MAVEN_ERE"
    data_link.parent.mkdir(parents=True, exist_ok=True)
    data_link.symlink_to((preflight / "data/MAVEN_ERE").resolve(), target_is_directory=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--preflight",
        type=Path,
        default=Path("runs/stages/A3/a3-v6-baselines-r3/preflight"),
    )
    parser.add_argument("--p1-protocol-sha256", required=True)
    parser.add_argument("--plan-sha256", required=True)
    parser.add_argument("--baseline", choices=BASELINES, required=True)
    parser.add_argument("--seed", type=int, choices=SEEDS, required=True)
    parser.add_argument(
        "--run-dir",
        type=Path,
        help="override only for an isolated audit; default is the plan's stage layout",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="actually start the single long-running baseline job",
    )
    args = parser.parse_args()

    preflight = args.preflight.resolve()
    plan_path = preflight / "execution_plan.json"
    try:
        plan = _load_plan(plan_path, args.p1_protocol_sha256, args.plan_sha256)
    except (A3LaunchError, OSError, json.JSONDecodeError) as exc:
        raise SystemExit(str(exc)) from exc
    command_entry = plan["commands"][args.baseline][str(args.seed)]
    planned_run_dir = Path(command_entry["run_dir"])
    run_dir = args.run_dir.resolve() if args.run_dir else planned_run_dir
    cwd, argv, expected_outputs = _selected_command(
        plan,
        baseline=args.baseline,
        seed=args.seed,
        run_dir=run_dir,
    )

    print(f"[a3-launch] baseline={args.baseline} seed={args.seed}")
    print(f"[a3-launch] cwd={cwd}")
    print(f"[a3-launch] argv={json.dumps(argv)}")
    print(f"[a3-launch] expected_outputs={json.dumps([str(p) for p in expected_outputs])}")
    if not args.execute:
        print("[a3-launch] PRECHECK PASS; no process started (add --execute explicitly)")
        return 0

    planned_preflight = Path(plan["execution_environment"]["remote_preflight"])
    if preflight != planned_preflight:
        raise SystemExit(
            "--execute requires running from the planned remote preflight path: "
            f"expected {planned_preflight}, got {preflight}"
        )
    if run_dir.exists():
        raise SystemExit(f"refusing to overwrite immutable A3 run directory: {run_dir}")
    python = Path(argv[0])
    model_path = Path(plan["model_assumptions"]["path"])
    if not python.is_file():
        raise SystemExit(f"planned Python does not exist: {python}")
    if not model_path.exists():
        raise SystemExit(f"planned model path does not exist: {model_path}")
    gpu_check = subprocess.run(
        ("nvidia-smi", "--query-gpu=name,memory.total,memory.used", "--format=csv,noheader"),
        text=True,
        capture_output=True,
    )
    if gpu_check.returncode != 0 or not gpu_check.stdout.strip():
        raise SystemExit(f"GPU preflight failed: {gpu_check.stderr.strip()}")

    run_dir.mkdir(parents=True)
    if args.baseline.startswith("official_"):
        _prepare_official_workspace(preflight, run_dir)
    if not cwd.is_dir():
        raise SystemExit(f"planned working directory does not exist after setup: {cwd}")
    metadata = {
        "schema_version": "ekg.a3_baseline_run.v1",
        "status": "incomplete",
        "baseline": args.baseline,
        "seed": args.seed,
        "launcher_argv": list(sys.argv),
        "executed_argv": argv,
        "executed_commands": [{"role": "train", "cwd": str(cwd), "argv": argv}],
        "working_directory": str(cwd),
        "expected_outputs": [str(path) for path in expected_outputs],
        "p1_bundle_id": plan["p1_bundle_id"],
        "p1_bundle_protocol_sha256": args.p1_protocol_sha256,
        "preflight_plan_sha256": sha256_file(plan_path),
        "launcher_sha256": sha256_file(Path(__file__).resolve()),
        "gpu_preflight": gpu_check.stdout.strip().splitlines(),
        "final_valid_accessed": False,
        "exploratory": False,
    }
    _write_metadata(run_dir, metadata)
    log_path = run_dir / "launcher.log"
    with log_path.open("w", encoding="utf-8") as log:
        completed = subprocess.run(
            argv,
            cwd=cwd,
            stdout=log,
            stderr=subprocess.STDOUT,
            text=True,
        )
    returncodes = {"train": completed.returncode}
    missing = [str(path) for path in expected_outputs if not path.exists()]
    postprocess_error = None
    final_outputs = [run_dir / "official_predictions.jsonl", run_dir / "official_metrics.json"]
    if completed.returncode == 0 and not missing:
        try:
            repo = Path(plan["commands"]["local_pair"][str(args.seed)]["cwd"])
            python = Path(argv[0])
            if args.baseline == "local_pair":
                raw_path = run_dir / "edge_predictions.jsonl"
                inference_argv = [
                    str(python),
                    "-u",
                    "scripts/evaluate_relations.py",
                    "--config", "configs/relations/supervised_dump.yaml",
                    "--path", str(preflight / "data/MAVEN_ERE/valid.jsonl"),
                    "--checkpoint-path", str(run_dir / "checkpoint"),
                    "--dump-predictions", str(raw_path),
                    "--output", str(run_dir / "native_metrics.json"),
                ]
                metadata["executed_commands"].append(
                    {"role": "inference", "cwd": str(repo), "argv": inference_argv}
                )
                with log_path.open("a", encoding="utf-8") as log:
                    inference = subprocess.run(
                        inference_argv,
                        cwd=repo,
                        stdout=log,
                        stderr=subprocess.STDOUT,
                        text=True,
                    )
                returncodes["inference"] = inference.returncode
                if inference.returncode != 0:
                    raise A3LaunchError(
                        f"local-pair inference returned {inference.returncode}"
                    )
            else:
                raw_path = expected_outputs[-1]

            candidate_digest = plan["candidate_summaries"]["internal-dev"][
                "candidate_id_digest_sha256"
            ]
            normalize_predictions(
                baseline=args.baseline,
                raw_path=raw_path,
                gold_path=preflight / "data/MAVEN_ERE/valid.jsonl",
                output=final_outputs[0],
                candidate_digest=candidate_digest,
            )
            scorer_argv = [
                str(python),
                "-u",
                "scripts/score_maven_ere_official.py",
                "--evaluator", str(repo / "data/protocols/v6/tools/maven_ere_evaluate.py"),
                "--source-lock", str(repo / "data/protocols/v6/source_lock.json"),
                "--gold", str(preflight / "data/MAVEN_ERE/valid.jsonl"),
                "--pred", str(final_outputs[0]),
                "--candidate-digest", candidate_digest,
                "--output", str(final_outputs[1]),
            ]
            metadata["executed_commands"].append(
                {"role": "official_score", "cwd": str(repo), "argv": scorer_argv}
            )
            with log_path.open("a", encoding="utf-8") as log:
                scored = subprocess.run(
                    scorer_argv,
                    cwd=repo,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    text=True,
                )
            returncodes["official_score"] = scored.returncode
            if scored.returncode != 0:
                raise A3LaunchError(f"official scorer returned {scored.returncode}")
        except (A3LaunchError, ValueError, OSError) as exc:
            postprocess_error = str(exc)
    final_missing = [str(path) for path in final_outputs if not path.exists()]
    succeeded = (
        all(code == 0 for code in returncodes.values())
        and not missing
        and not final_missing
        and postprocess_error is None
    )
    metadata.update(
        {
            "status": "complete" if succeeded else "failed",
            "returncodes": returncodes,
            "missing_upstream_outputs": missing,
            "missing_final_outputs": final_missing,
            "postprocess_error": postprocess_error,
            "artifact_sha256": _hash_run_files(run_dir),
        }
    )
    _write_metadata(run_dir, metadata)
    if metadata["status"] != "complete":
        raise SystemExit(
            "A3 baseline failed: "
            f"returncodes={returncodes} missing={missing + final_missing} "
            f"postprocess={postprocess_error}"
        )
    print(f"[a3-launch] COMPLETE metadata={run_dir / 'run_metadata.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
