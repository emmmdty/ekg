#!/usr/bin/env python
"""Freeze and verify A4 pair-evidence inputs before any CUDA work starts.

Everything the pilot may read is pinned here and nothing else: the P1 trust
root, the A3 failed handoff, the R1 relation phase contract, the train source
and its two manifests, the frozen evaluator, the content-addressed encoder, and
the two same-protocol baselines whose official scores are recomputed rather
than copied.  The final-valid manifests are never opened.

The baselines are re-scored by running the frozen `score_maven_ere_official.py`
as a subprocess, not by a second scoring path in this file: two scorers are two
numbers for one protocol, which is the mistake `score_a3_arm.py` documents.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from ekg.core.protocol import load_manifest_ids
from ekg.core.stage_bundle import model_content_digest, sha256_file
from ekg.relations.maven_ere_official import candidate_population_digest

# Pinned by `docs/phases/PHASE_A4_pair_evidence.md`; a mismatch means the run
# would not be the experiment the contract froze.
EXPECTED_P1_PROTOCOL_SHA256 = (
    "1e31a9acef39261f776f7ed4069fd73f4531e8d12b55779bfc0fbd74c67f9655"
)
EXPECTED_A3_PROTOCOL_SHA256 = (
    "c187bf03978674edd29ac209658ccb62d457b744a209e864a0fef0e9eee9359e"
)
EXPECTED_SOURCE_SHA256 = "6a5519fe7c30448690adb13d49217c50d474fc57480eae10aecb29df7eb638b7"
EXPECTED_TRAIN_MANIFEST_SHA256 = (
    "47d19cc9a17e38259bfbb7f9206c675c7362f41252d23f414ea6cfd46015ca68"
)
EXPECTED_DEV_MANIFEST_SHA256 = (
    "f5457b302be57663f8e618d977c492909c3210682804cb486bd67ccc8c171b5f"
)
EXPECTED_CANDIDATE_DIGEST = "15a3b1a548625624642130190b39411e6346866ff8594c2af2020cfbdac10910"
EXPECTED_EVALUATOR_SHA256 = (
    "32919e86d98c6fafae6aa9505579e2c356caee12c32c1a8c719910acec359598"
)
EXPECTED_MODEL_SHA256 = "71be7419a60dcce0fc276654c8f9213b41f8def71a0c3465d7fed2352c961ea9"

# Frozen by A4.3; the preflight refuses anything else so a pilot cannot be
# launched under a budget the contract never approved.
FROZEN_TRAINING = {
    "epochs": 50,
    "warmup_steps": 200,
    "lr": 1e-5,
    "head_lr": 1e-4,
    "accum_steps": 8,
    "max_length": 512,
}

CODE_FILES = (
    "src/ekg/relations/pair_evidence.py",
    "src/ekg/relations/pair_heads.py",
    "scripts/train_a4_pair_evidence.py",
    "scripts/evaluate_a4_pair_evidence.py",
    "scripts/prepare_a4_pair_evidence_preflight.py",
    "scripts/smoke_a4_pair_evidence.py",
    # The pilot driver runs under this contract, so it belongs inside the hash
    # set the contract binds -- D4 learnt this the expensive way.
    "scripts/run_a4_pair_evidence.py",
)

FAMILIES = ("causal", "subevent", "temporal")


class PreflightError(ValueError):
    """A pinned A4 input, baseline or contract does not verify."""


def _load(path: Path) -> dict:
    if not path.is_file():
        raise PreflightError(f"missing JSON input: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise PreflightError(f"{path} must contain a JSON object")
    return payload


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise PreflightError(message)


def _read_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line
    ]


def _validate_contract(repo: Path, r1_protocol: Path, t024: Path) -> dict[str, str]:
    """The relation phase contract, as R1 and T024 both have to describe it."""
    protocol = _load(r1_protocol)
    phase = protocol.get("phase_contracts", {}).get("relation")
    _require(isinstance(phase, dict), "R1 protocol has no relation phase contract")
    path = repo / str(phase.get("path", ""))
    _require(path.is_file(), "A4 phase contract file is missing")
    _require(sha256_file(path) == phase.get("sha256"), "A4 phase contract hash drift")
    approved = _load(t024).get("approved_contracts", {}).get("relation")
    _require(isinstance(approved, dict), "T024 has no relation decision")
    _require(approved.get("state") == "frozen", "A4 is not frozen by T024")
    _require(approved.get("path") == phase.get("path"), "T024/R1 relation path mismatch")
    _require(approved.get("sha256") == phase.get("sha256"), "T024/R1 relation hash mismatch")
    return {
        "r1_protocol": sha256_file(r1_protocol),
        "t024": sha256_file(t024),
        "phase_contract": sha256_file(path),
    }


def _materialise_internal_dev(source: Path, manifest: Path, output: Path) -> dict:
    """Write the 291 internal-dev documents the pilot is scored on.

    In manifest order, so the file is reproducible from the manifest alone, and
    with the candidate population digest recomputed from the result: that digest
    is the one thing A4 may not move, so it is checked here rather than trusted.
    """
    wanted = load_manifest_ids(manifest)
    records = {str(record["id"]): record for record in _read_jsonl(source)}
    missing = [doc_id for doc_id in wanted if doc_id not in records]
    _require(not missing, f"source misses {len(missing)} internal-dev documents")
    selected = [records[doc_id] for doc_id in wanted]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in selected),
        encoding="utf-8",
    )
    digest, counts = candidate_population_digest({str(r["id"]): r for r in selected})
    _require(
        digest == EXPECTED_CANDIDATE_DIGEST,
        f"internal-dev candidate digest drift: {digest}",
    )
    return {
        "path": str(output),
        "sha256": sha256_file(output),
        "documents": len(selected),
        "candidate_id_digest": digest,
        "population_counts": counts,
    }


def _score_baseline(
    repo: Path, name: str, predictions: Path, gold: Path, evaluator: Path, output: Path
) -> dict:
    """Recompute one baseline's official P/R/F1 with the frozen evaluator."""
    _require(predictions.is_file(), f"{name}: missing official predictions {predictions}")
    argv = [
        sys.executable, "-u", "scripts/score_maven_ere_official.py",
        "--evaluator", str(evaluator),
        "--gold", str(gold),
        "--pred", str(predictions),
        "--candidate-digest", EXPECTED_CANDIDATE_DIGEST,
        "--output", str(output),
    ]
    completed = subprocess.run(argv, cwd=repo, text=True, capture_output=True)
    if completed.returncode != 0:
        raise PreflightError(
            f"{name}: official scoring failed\n{completed.stdout}\n{completed.stderr}"
        )
    scores = _load(output).get("scores", {})
    for family in FAMILIES:
        for metric in ("precision", "recall", "f1"):
            _require(f"{family}_{metric}" in scores, f"{name}: no {family}_{metric}")
    return {
        "predictions_sha256": sha256_file(predictions),
        "metrics_sha256": sha256_file(output),
        "scores": {
            f"{family}_{metric}": scores[f"{family}_{metric}"]
            for family in FAMILIES
            for metric in ("precision", "recall", "f1")
        },
    }


def prepare(args: argparse.Namespace) -> dict:
    _require(not args.output.exists(), f"refusing to overwrite preflight: {args.output}")
    _require(args.seed == 13, "A4 is authorized only for seed 13")
    for name, expected in FROZEN_TRAINING.items():
        actual = getattr(args, name)
        _require(actual == expected, f"A4 {name} is frozen to {expected}, got {actual}")
    _require(
        sha256_file(args.p1_protocol) == EXPECTED_P1_PROTOCOL_SHA256, "P1 trust root drift"
    )
    _require(
        sha256_file(args.a3_protocol) == EXPECTED_A3_PROTOCOL_SHA256, "A3 handoff drift"
    )
    _require(sha256_file(args.source) == EXPECTED_SOURCE_SHA256, "MAVEN-ERE train source drift")
    _require(
        sha256_file(args.train_manifest) == EXPECTED_TRAIN_MANIFEST_SHA256,
        "train manifest drift",
    )
    _require(
        sha256_file(args.dev_manifest) == EXPECTED_DEV_MANIFEST_SHA256,
        "internal-dev manifest drift",
    )
    _require(sha256_file(args.evaluator) == EXPECTED_EVALUATOR_SHA256, "evaluator drift")
    train_ids = load_manifest_ids(args.train_manifest)
    dev_ids = load_manifest_ids(args.dev_manifest)
    _require(not set(train_ids) & set(dev_ids), "train and internal-dev manifests overlap")
    _require(args.model.is_dir(), f"missing model directory: {args.model}")
    model_digest = model_content_digest(args.model)
    _require(model_digest == EXPECTED_MODEL_SHA256, f"encoder content drift: {model_digest}")

    contracts = _validate_contract(args.repo, args.r1_protocol, args.t024)
    root = args.output.parent
    gold = _materialise_internal_dev(
        args.source, args.dev_manifest, root / "data/MAVEN_ERE/internal-dev.jsonl"
    )
    baselines = {
        "a3_fallback": _score_baseline(
            args.repo,
            "a3_fallback",
            args.fallback_predictions,
            Path(gold["path"]),
            args.evaluator,
            root / "baselines/a3_fallback.metrics.json",
        ),
        "taco_adaptation": _score_baseline(
            args.repo,
            "taco_adaptation",
            args.taco_predictions,
            Path(gold["path"]),
            args.evaluator,
            root / "baselines/taco_adaptation.metrics.json",
        ),
    }
    protocol = {
        "schema_version": "ekg.a4_pair_evidence_preflight.v1",
        "status": "pass",
        "seed": args.seed,
        "final_valid_accessed": False,
        "source": {"path": str(args.source), "sha256": EXPECTED_SOURCE_SHA256},
        "manifests": {
            "train": {
                "path": str(args.train_manifest),
                "sha256": EXPECTED_TRAIN_MANIFEST_SHA256,
                "documents": len(train_ids),
            },
            "internal_dev": {
                "path": str(args.dev_manifest),
                "sha256": EXPECTED_DEV_MANIFEST_SHA256,
                "documents": len(dev_ids),
            },
        },
        "internal_dev_gold": gold,
        "trust_roots": {
            "p1_protocol_sha256": EXPECTED_P1_PROTOCOL_SHA256,
            "a3_protocol_sha256": EXPECTED_A3_PROTOCOL_SHA256,
        },
        "contracts": contracts,
        "evaluator": {"path": str(args.evaluator), "sha256": EXPECTED_EVALUATOR_SHA256},
        "model": {"path": str(args.model), "content_sha256": model_digest},
        "baselines": baselines,
        "training": {
            "arms": ["full", "remove_core", "length_matched", "no_constraint"],
            **FROZEN_TRAINING,
            "consistency_weight": args.consistency_weight,
            "negatives": "all",
            "selection": "internal-dev, per family; the candidate universe is never pruned",
        },
        "code": {path: sha256_file(args.repo / path) for path in CODE_FILES},
        "final_valid_ledger": "not opened; A4 reads train and internal-dev only",
    }
    args.output.write_text(json.dumps(protocol, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return protocol


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--train-manifest", required=True, type=Path)
    parser.add_argument("--dev-manifest", required=True, type=Path)
    parser.add_argument("--p1-protocol", required=True, type=Path)
    parser.add_argument("--a3-protocol", required=True, type=Path)
    parser.add_argument("--r1-protocol", required=True, type=Path)
    parser.add_argument("--t024", required=True, type=Path)
    parser.add_argument("--fallback-predictions", required=True, type=Path)
    parser.add_argument("--taco-predictions", required=True, type=Path)
    parser.add_argument("--model", required=True, type=Path)
    parser.add_argument(
        "--evaluator", type=Path, default=Path("data/protocols/v6/tools/maven_ere_evaluate.py")
    )
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--seed", type=int, default=13)
    parser.add_argument("--epochs", type=int, default=FROZEN_TRAINING["epochs"])
    parser.add_argument("--warmup-steps", type=int, default=FROZEN_TRAINING["warmup_steps"])
    parser.add_argument("--lr", type=float, default=FROZEN_TRAINING["lr"])
    parser.add_argument("--head-lr", type=float, default=FROZEN_TRAINING["head_lr"])
    parser.add_argument("--accum-steps", type=int, default=FROZEN_TRAINING["accum_steps"])
    parser.add_argument("--max-length", type=int, default=FROZEN_TRAINING["max_length"])
    parser.add_argument("--consistency-weight", type=float, default=1.0)
    args = parser.parse_args()
    args.repo = args.repo.resolve()
    for name in (
        "source", "train_manifest", "dev_manifest", "p1_protocol", "a3_protocol",
        "r1_protocol", "t024", "fallback_predictions", "taco_predictions", "model",
        "evaluator",
    ):
        setattr(args, name, getattr(args, name).resolve())
    protocol = prepare(args)
    print(
        f"[a4-preflight] PASS {args.output} code_files={len(protocol['code'])} "
        f"candidate_digest={protocol['internal_dev_gold']['candidate_id_digest']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
