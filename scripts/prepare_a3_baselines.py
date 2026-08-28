#!/usr/bin/env python
"""Materialize the immutable, train/internal-dev-only A3 baseline preflight.

No model is loaded and no GPU is used. The output is an isolated copy of the
pinned official source, the exact two P1 split files expected by that source,
an unlabeled-shape internal-dev test file, and an execution plan for all three
required baselines. Final-valid is deliberately neither read nor materialized.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

from ekg.core.stage_bundle import StageBundleError, is_sha256, validate_stage_bundle
from ekg.relations.maven_ere_official import (
    frozen_candidate_protocol,
    records_by_id,
)

SEEDS = (13, 17, 42)
ROBERTA_BASE_MODEL_ID = "FacebookAI/roberta-base"
# Content digest of the pinned snapshot (SHA-256 over the canonical map of each
# file's SHA-256), NOT an upstream Git revision. The server already held a complete
# roberta-base snapshot with no revision metadata; claiming an unverified upstream
# commit would be a provenance we never checked. A content digest is strictly
# stronger for the property the protocol needs -- every run used byte-identical
# weights -- and anyone can recompute it from the directory.
ROBERTA_BASE_REVISION = "71be7419a60dcce0fc276654c8f9213b41f8def71a0c3465d7fed2352c961ea9"
DEFAULT_ROBERTA_BASE_PATH = (
    f"/data/TJK/models/local/roberta-base/{ROBERTA_BASE_REVISION}"
)


class A3PreflightError(ValueError):
    """A frozen A3 input or materialized artifact is not trustworthy."""


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_json(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise A3PreflightError(f"{path} must contain a JSON object")
    return payload


def _read_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line
    ]


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )


def _test_shape(record: dict) -> dict:
    mentions = [
        {**mention, "type": event.get("type", "Unknown"), "type_id": event.get("type_id")}
        for event in record.get("events", [])
        for mention in event.get("mention", [])
    ]
    return {
        "id": record["id"],
        "title": record.get("title", ""),
        "tokens": record.get("tokens", []),
        "sentences": record.get("sentences", []),
        "event_mentions": mentions,
        "TIMEX": record.get("TIMEX", []),
    }


def _source_files(root: Path) -> list[Path]:
    return [
        path
        for path in sorted(root.rglob("*"))
        if path.is_file()
        and ".git" not in path.parts
        and "__pycache__" not in path.parts
        and "output" not in path.parts
    ]


def _tree_hashes(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): sha256_file(path)
        for path in _source_files(root)
    }


def _adapt_model_path(source: Path, model_path: str) -> list[dict]:
    """Change only upstream hard-coded model identifiers in the isolated copy."""
    replacement = json.dumps(model_path)
    targets = (
        (source / "causal/main.py", '"roberta-base"'),
        (source / "utils/model.py", '"roberta-base"'),
        (source / "joint/main.py", '"/data/MODELS/roberta-base"'),
        (source / "joint/src/model.py", '"/data/MODELS/roberta-base"'),
    )
    changes = []
    for path, original in targets:
        text = path.read_text(encoding="utf-8")
        occurrences = text.count(original)
        if occurrences == 0:
            raise A3PreflightError(
                f"expected model-path literal {original} is absent from {path}"
            )
        before = sha256_file(path)
        path.write_text(text.replace(original, replacement), encoding="utf-8")
        changes.append(
            {
                "path": path.relative_to(source).as_posix(),
                "scope": "model identifier/path only; architecture and training unchanged",
                "original_literal": original,
                "replacement_literal": replacement,
                "occurrences": occurrences,
                "before_sha256": before,
                "after_sha256": sha256_file(path),
            }
        )
    return changes


def _select_protocol_records(
    *, repo: Path, protocol_root: Path, expected_p1_hash: str
) -> tuple[dict[str, list[dict]], dict]:
    registry = _load_json(protocol_root / "registry.json")
    if not is_sha256(expected_p1_hash):
        raise A3PreflightError("--p1-protocol-sha256 must be a SHA-256 digest")
    if registry.get("p1_bundle_protocol_sha256") != expected_p1_hash:
        raise A3PreflightError("registry P1 digest differs from command trust root")
    if registry.get("global_protocol_status") != "pass":
        raise A3PreflightError("P1 global protocol status is not pass")
    if registry.get("a3_entry_status") != "pass":
        raise A3PreflightError("P1 A3 entry status is not pass")
    bundle = repo / "runs/stages/P1" / str(registry.get("p1_bundle_id"))
    try:
        validate_stage_bundle(
            bundle,
            evidence_root=repo,
            expected_protocol_sha256=expected_p1_hash,
            known_upstream_bundle_ids=set(),
        )
    except StageBundleError as exc:
        raise A3PreflightError(f"P1 bundle validation failed: {exc}") from exc

    source_rel = "data/processed/maven_ere/train.jsonl"
    source = repo / source_rel
    source_hash = sha256_file(source)
    if registry.get("source_sha256", {}).get(source_rel) != source_hash:
        raise A3PreflightError("MAVEN-ERE train source hash mismatch")
    raw = records_by_id(_read_jsonl(source), source=str(source))
    candidate_path = protocol_root / "ch2_candidate_protocol.json"
    if sha256_file(candidate_path) != registry.get("candidate_protocol_sha256"):
        raise A3PreflightError("Ch2 candidate protocol hash mismatch")
    frozen_candidates = _load_json(candidate_path)

    selected: dict[str, list[dict]] = {}
    seen: set[str] = set()
    manifest_hashes = registry.get("manifest_sha256", {})
    for role in ("train", "internal-dev"):
        relative = f"manifests/maven_ere_{role}.json"
        path = protocol_root / relative
        if sha256_file(path) != manifest_hashes.get(relative):
            raise A3PreflightError(f"{role} manifest hash mismatch")
        manifest = _load_json(path)
        if manifest.get("dataset") != "maven_ere" or manifest.get("split_role") != role:
            raise A3PreflightError(f"{role} manifest identity mismatch")
        if manifest.get("source_path") != source_rel:
            raise A3PreflightError(f"{role} manifest source path mismatch")
        if manifest.get("source_sha256") != source_hash:
            raise A3PreflightError(f"{role} manifest source hash mismatch")
        ids = manifest.get("doc_ids")
        if not isinstance(ids, list) or len(ids) != len(set(ids)):
            raise A3PreflightError(f"{role} manifest IDs are missing or duplicated")
        if manifest.get("doc_count") != len(ids):
            raise A3PreflightError(f"{role} manifest doc_count mismatch")
        if seen & set(ids):
            raise A3PreflightError("train and internal-dev manifests overlap")
        if set(ids) - raw.keys():
            raise A3PreflightError(f"{role} manifest references missing source documents")
        seen.update(ids)
        records = [raw[item] for item in ids]
        if frozen_candidate_protocol(records) != frozen_candidates.get(role):
            raise A3PreflightError(f"{role} candidate or label population drift")
        selected[role] = records
    if seen != set(raw):
        raise A3PreflightError("train/internal-dev do not exactly partition source")
    return selected, registry


def _official_source_check(repo: Path, protocol_root: Path) -> tuple[Path, dict]:
    lock = _load_json(protocol_root / "source_lock.json")
    source = repo / lock["local_checkout"]
    commit = subprocess.run(
        ("git", "rev-parse", "HEAD"),
        cwd=source,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    ).stdout.strip()
    if commit != lock.get("commit"):
        raise A3PreflightError("official source checkout commit mismatch")
    if sha256_file(repo / lock["license_path"]) != sha256_file(source / "LICENSE"):
        raise A3PreflightError("official source license file mismatch")
    for patch in lock.get("patches", []):
        if sha256_file(repo / patch["path"]) != patch.get("sha256"):
            raise A3PreflightError(f"official compatibility patch hash mismatch: {patch['path']}")
    return source, lock


def _commands(
    *,
    remote_repo: Path,
    remote_preflight: Path,
    python: Path,
    model_path: str,
    p1_hash: str,
) -> dict:
    common_local = [
        str(python),
        "-u",
        "scripts/train_supervised_relations.py",
        "--train", str(remote_repo / "data/processed/maven_ere/train.jsonl"),
        "--train-manifest",
        str(remote_repo / "data/protocols/v6/manifests/maven_ere_train.json"),
        "--dev-manifest",
        str(remote_repo / "data/protocols/v6/manifests/maven_ere_internal-dev.json"),
        "--protocol-root", str(remote_repo / "data/protocols/v6"),
        "--repo-root", str(remote_repo),
        "--p1-protocol-sha256", p1_hash,
        "--official-mention-expansion",
        "--families", "causal", "subevent", "temporal",
        "--model", model_path,
        "--epochs", "3",
        "--lr", "1e-5",
        "--head-lr", "1e-4",
        "--warmup-steps", "200",
        "--accum-steps", "8",
        "--neg-ratio", "inf",
        "--weight-alpha", "0.0",
        "--dev-metric", "macro",
    ]
    commands: dict[str, dict[str, dict]] = {
        name: {} for name in ("local_pair", "official_single", "official_joint")
    }
    for seed in SEEDS:
        local_run = remote_preflight.parent / f"local_pair/seed-{seed}"
        commands["local_pair"][str(seed)] = {
            "run_dir": str(local_run),
            "cwd": str(remote_repo),
            "argv": [
                *common_local,
                "--seed", str(seed),
                "--output", "{run_dir}/checkpoint",
            ],
            "expected_outputs_template": [
                "{run_dir}/checkpoint/run_metadata.json",
                "{run_dir}/checkpoint/heads.pt",
            ],
        }
        single_run = remote_preflight.parent / f"official_single/seed-{seed}"
        commands["official_single"][str(seed)] = {
            "run_dir": str(single_run),
            "cwd_template": "{run_dir}/workspace/source/causal",
            "argv": [
                str(python), "-u", "main.py",
                "--seed", str(seed),
                "--eval_steps", "500",
                "--epochs", "50",
                "--batch_size", "4",
            ],
            "expected_outputs_template": [
                "{run_dir}/workspace/source/causal/output/"
                f"{seed}/maven_ignore_none_False_None/best",
                "{run_dir}/workspace/source/causal/output/"
                f"{seed}/maven_ignore_none_False_None/test_prediction.jsonl",
            ],
        }
        joint_run = remote_preflight.parent / f"official_joint/seed-{seed}"
        commands["official_joint"][str(seed)] = {
            "run_dir": str(joint_run),
            "cwd_template": "{run_dir}/workspace/source/joint",
            "argv": [
                str(python), "-u", "main.py",
                "--seed", str(seed),
                "--eval_steps", "200",
                "--epochs", "100",
                "--lr", "3e-4",
                "--bert_lr", "2e-5",
                "--accumulation_steps", "4",
                "--batch_size", "8",
            ],
            "expected_outputs_template": [
                "{run_dir}/workspace/source/joint/output/"
                f"{seed}/MAVEN-ERE/best_CAUSAL",
                "{run_dir}/workspace/source/joint/output/"
                f"{seed}/MAVEN-ERE/best_SUBEVENT",
                "{run_dir}/workspace/source/joint/output/"
                f"{seed}/MAVEN-ERE/test_prediction.jsonl",
            ],
        }
    return commands


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--protocol-root", type=Path, default=Path("data/protocols/v6")
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("runs/stages/A3/a3-v6-baselines-r3/preflight"),
    )
    parser.add_argument("--p1-protocol-sha256", required=True)
    parser.add_argument("--model-path", default=DEFAULT_ROBERTA_BASE_PATH)
    parser.add_argument("--model-id", default=ROBERTA_BASE_MODEL_ID)
    parser.add_argument("--model-revision", default=ROBERTA_BASE_REVISION)
    parser.add_argument("--remote-repo-root", type=Path, default=Path("/data/TJK/ekg"))
    parser.add_argument(
        "--remote-python", type=Path, default=Path("/data/TJK/ekg/.venv/bin/python")
    )
    args = parser.parse_args()

    repo = args.repo_root.resolve()
    protocol_root = (
        args.protocol_root.resolve()
        if args.protocol_root.is_absolute()
        else (repo / args.protocol_root).resolve()
    )
    output = args.output.resolve() if args.output.is_absolute() else (repo / args.output).resolve()
    try:
        output_relative = output.relative_to(repo)
    except ValueError as exc:
        raise SystemExit("--output must be inside --repo-root") from exc
    if output.exists():
        raise SystemExit(f"refusing to overwrite immutable A3 preflight: {output}")
    if Path(args.model_path).name != args.model_revision:
        raise SystemExit("--model-path must end in the exact --model-revision")

    try:
        selected, registry = _select_protocol_records(
            repo=repo,
            protocol_root=protocol_root,
            expected_p1_hash=args.p1_protocol_sha256,
        )
        official_source, source_lock = _official_source_check(repo, protocol_root)
        output.mkdir(parents=True)
        copied_source = output / "source"
        shutil.copytree(
            official_source,
            copied_source,
            ignore=shutil.ignore_patterns(".git", "__pycache__", "output", "*.pyc"),
        )
        adaptations = _adapt_model_path(copied_source, args.model_path)
        data_dir = output / "data/MAVEN_ERE"
        _write_jsonl(data_dir / "train.jsonl", selected["train"])
        _write_jsonl(data_dir / "valid.jsonl", selected["internal-dev"])
        _write_jsonl(
            data_dir / "test.jsonl",
            [_test_shape(record) for record in selected["internal-dev"]],
        )
    except (A3PreflightError, OSError, subprocess.CalledProcessError) as exc:
        if output.exists():
            shutil.rmtree(output)
        raise SystemExit(str(exc)) from exc

    data_hashes = {
        path.name: sha256_file(path) for path in sorted((output / "data/MAVEN_ERE").iterdir())
    }
    remote_preflight = args.remote_repo_root / output_relative
    # 执行面（materializer/launcher）按 plan 粒度留痕，不进 P1 信任根：改动只产生新的
    # plan SHA-256，不作废协议。launcher 另在每个 run 的 run_metadata.json 里记录自身哈希。
    execution_surface = {
        relative: sha256_file(repo / relative)
        for relative in (
            "scripts/prepare_a3_baselines.py",
            "scripts/run_a3_baseline.py",
            # The inference config selects the consistency mode and the loader's
            # TIMEX setting: both change what the baseline predicts, so it belongs
            # in the plan's hash rather than travelling unverified.
            "configs/relations/supervised_dump.yaml",
        )
    }
    plan = {
        "schema_version": "ekg.a3_baseline_preflight.v1",
        "status": "pass",
        "p1_bundle_id": registry["p1_bundle_id"],
        "p1_bundle_protocol_sha256": args.p1_protocol_sha256,
        "final_valid_accessed": False,
        "split_roles": {
            "train.jsonl": "P1 train (2622 documents)",
            "valid.jsonl": "P1 internal-dev (291 documents; checkpoint selection only)",
            "test.jsonl": "same P1 internal-dev IDs in unlabeled official test shape",
        },
        "candidate_summaries": {
            role: frozen_candidate_protocol(records) for role, records in selected.items()
        },
        "hashes": {
            "data": data_hashes,
            "adapted_official_source": _tree_hashes(copied_source),
            "source_lock": sha256_file(protocol_root / "source_lock.json"),
        },
        "official_source": {
            "commit": source_lock["commit"],
            "license": source_lock["license"],
            "compatibility_patches": source_lock["patches"],
            "model_path_adaptations": adaptations,
        },
        "model_assumptions": {
            "path": args.model_path,
            "model_id": args.model_id,
            "revision": args.model_revision,
            "revision_kind": "local_content_digest",
            "must_exist_before_execute": True,
            "closed_api_required": False,
        },
        "execution_surface": execution_surface,
        "execution_environment": {
            "remote_repo_root": str(args.remote_repo_root),
            "remote_preflight": str(remote_preflight),
            "remote_python": str(args.remote_python),
        },
        "commands": _commands(
            remote_repo=args.remote_repo_root,
            remote_preflight=remote_preflight,
            python=args.remote_python,
            model_path=args.model_path,
            p1_hash=args.p1_protocol_sha256,
        ),
    }
    plan_path = output / "execution_plan.json"
    plan_path.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    plan_hash = sha256_file(plan_path)
    print(
        f"[a3-preflight] PASS: {len(selected['train'])} train + "
        f"{len(selected['internal-dev'])} internal-dev; final-valid not accessed; "
        f"plan={plan_path} plan_sha256={plan_hash}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
