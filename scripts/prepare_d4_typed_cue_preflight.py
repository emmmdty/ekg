#!/usr/bin/env python
"""Freeze and verify D4 typed-cue inputs before any CUDA work starts.

The preflight deliberately reads only the accepted train-derived factuality OOF
baseline, its five-fold manifests, the frozen D4 contract and the content-pinned
encoder.  It never opens a final-valid manifest or result.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ekg.core.protocol import load_manifest_ids
from ekg.core.stage_bundle import model_content_digest, sha256_file
from ekg.factuality.metrics import factuality_report
from ekg.relations.data.maven_fact import load_maven_fact

EXPECTED_OOF_SUMMARY_SHA256 = "21e7e50596aa773f54037b95146c37838c68c250e579ae955b2730db6fe88165"
EXPECTED_OOF_ACCEPTANCE_SHA256 = "7de7177f9eb4e837c5c4eb8ff6822d103a9b0cb022065bf1d2ae34ce367e58af"
EXPECTED_MODEL_SHA256 = "71be7419a60dcce0fc276654c8f9213b41f8def71a0c3465d7fed2352c961ea9"
CODE_FILES = (
    "src/ekg/factuality/detection.py",
    "src/ekg/factuality/typed_cues.py",
    "scripts/train_d4_typed_cue.py",
    "scripts/evaluate_d4_typed_cue.py",
    "scripts/prepare_d4_typed_cue_preflight.py",
    "scripts/smoke_d4_typed_cue.py",
)


class PreflightError(ValueError):
    """A pinned D4 input, baseline or contract does not verify."""


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


def _resolve(root: Path, value: object, field: str) -> Path:
    if not isinstance(value, str) or not value:
        raise PreflightError(f"{field} has no path")
    path = Path(value)
    return path if path.is_absolute() else root / path


def _validate_cv(repo: Path, cv_path: Path, source: Path) -> dict:
    cv = _load(cv_path)
    _require(cv.get("schema_version") == "ekg.r1_factuality_cv.v1", "unexpected CV schema")
    _require(cv.get("status") == "pass", "factuality CV is not pass")
    _require(cv.get("config", {}).get("final_valid_accessed") is False, "CV accessed final-valid")
    _require(cv.get("source", {}).get("sha256") == sha256_file(source), "source hash drift")
    _require(cv.get("source", {}).get("documents") == 2913, "unexpected source document count")
    folds = cv.get("folds")
    _require(isinstance(folds, list) and len(folds) == 5, "CV does not have five folds")
    seen_evaluation: set[str] = set()
    for row in folds:
        _require(isinstance(row, dict), "invalid CV fold")
        ids_by_role: dict[str, set[str]] = {}
        for role in ("train", "selection_dev", "evaluation"):
            entry = row.get(role)
            _require(isinstance(entry, dict), f"fold {row.get('fold')}: missing {role}")
            path = repo / str(entry.get("path", ""))
            _require(path.is_file(), f"fold {row.get('fold')}: missing {role} manifest")
            _require(
                sha256_file(path) == entry.get("sha256"),
                f"fold {row.get('fold')}: {role} manifest hash drift",
            )
            ids = load_manifest_ids(path)
            _require(len(ids) == entry.get("doc_count"), f"fold {row.get('fold')}: {role} count")
            ids_by_role[role] = set(ids)
        _require(
            not (ids_by_role["train"] & ids_by_role["selection_dev"]),
            f"fold {row.get('fold')}: train/selection overlap",
        )
        _require(
            not (ids_by_role["train"] & ids_by_role["evaluation"]),
            f"fold {row.get('fold')}: train/evaluation overlap",
        )
        _require(
            not (ids_by_role["selection_dev"] & ids_by_role["evaluation"]),
            f"fold {row.get('fold')}: selection/evaluation overlap",
        )
        _require(
            sum(map(len, ids_by_role.values())) == 2913,
            f"fold {row.get('fold')}: does not cover source",
        )
        _require(
            not (seen_evaluation & ids_by_role["evaluation"]),
            "evaluation documents repeat across folds",
        )
        seen_evaluation.update(ids_by_role["evaluation"])
    _require(len(seen_evaluation) == 2913, "OOF evaluation does not cover source")
    return cv


def _validate_contract(repo: Path, r1_protocol: Path, t024: Path) -> dict[str, str]:
    protocol = _load(r1_protocol)
    phase = protocol.get("phase_contracts", {}).get("factuality")
    _require(isinstance(phase, dict), "R1 protocol has no factuality phase contract")
    path = repo / str(phase.get("path", ""))
    _require(path.is_file(), "D4 phase contract file is missing")
    _require(sha256_file(path) == phase.get("sha256"), "D4 phase contract hash drift")
    t024_payload = _load(t024)
    approved = t024_payload.get("approved_contracts", {}).get("factuality")
    _require(isinstance(approved, dict), "T024 has no factuality decision")
    _require(approved.get("state") == "frozen", "D4 is not frozen by T024")
    _require(approved.get("path") == phase.get("path"), "T024/R1 factuality path mismatch")
    _require(approved.get("sha256") == phase.get("sha256"), "T024/R1 factuality hash mismatch")
    return {
        "r1_protocol": sha256_file(r1_protocol),
        "t024": sha256_file(t024),
        "phase_contract": sha256_file(path),
    }


def _validate_baselines(root: Path, source: Path) -> dict:
    summary_path = root / "oof_summary.json"
    acceptance_path = root / "acceptance.json"
    _require(sha256_file(summary_path) == EXPECTED_OOF_SUMMARY_SHA256, "OOF summary hash drift")
    _require(
        sha256_file(acceptance_path) == EXPECTED_OOF_ACCEPTANCE_SHA256,
        "OOF acceptance hash drift",
    )
    summary = _load(summary_path)
    acceptance = _load(acceptance_path)
    _require(summary.get("status") == "pass", "OOF summary is not pass")
    _require(summary.get("final_valid_accessed") is False, "OOF summary accessed final-valid")
    _require(acceptance.get("status") == "pass", "OOF acceptance is not pass")
    _require(acceptance.get("final_valid_accessed") is False, "OOF acceptance accessed final-valid")
    docs = list(load_maven_fact(source))
    gold = {mention.mention_id: mention.factuality for doc in docs for mention in doc.mentions}
    verified: dict[str, dict] = {}
    for name in ("cls", "dynamic_multi"):
        entry = summary.get("baselines", {}).get(name)
        _require(isinstance(entry, dict), f"OOF summary has no {name} baseline")
        labels = entry.get("labels")
        _require(isinstance(labels, dict), f"{name} baseline has no labels identity")
        labels_path = _resolve(root, labels.get("path"), f"{name} labels")
        _require(labels_path.is_file(), f"missing {name} OOF labels")
        _require(sha256_file(labels_path) == labels.get("sha256"), f"{name} labels hash drift")
        predicted = _load(labels_path)
        _require(set(predicted) == set(gold), f"{name} OOF mention coverage")
        recomputed = factuality_report(predicted, gold)
        _require(recomputed == entry.get("report"), f"{name} OOF report drift")
        verified[name] = {
            "labels_path": str(labels_path),
            "labels_sha256": sha256_file(labels_path),
            "report": recomputed,
        }
    return {
        "summary_sha256": sha256_file(summary_path),
        "acceptance_sha256": sha256_file(acceptance_path),
        "baselines": verified,
    }


def prepare(args: argparse.Namespace) -> dict:
    _require(not args.output.exists(), f"refusing to overwrite preflight: {args.output}")
    _require(args.seed == 13, "D4 is authorized only for seed 13")
    _require(args.epochs == 12, "D4 epoch budget is frozen to the OOF baseline budget")
    _require(args.lr == 2e-5, "D4 learning rate is frozen to the OOF baseline budget")
    _require(args.alpha == 0.5, "D4 class-weight alpha is frozen")
    _require(args.max_length == 128 and args.stride == 64, "D4 sequence settings are frozen")
    _require(args.model.is_dir(), f"missing model directory: {args.model}")
    model_digest = model_content_digest(args.model)
    _require(model_digest == EXPECTED_MODEL_SHA256, "RoBERTa content hash drift")
    _validate_cv(args.repo, args.cv, args.source)
    contracts = _validate_contract(args.repo, args.r1_protocol, args.t024)
    baselines = _validate_baselines(args.accepted_oof_root, args.source)
    code = {path: sha256_file(args.repo / path) for path in CODE_FILES}
    protocol = {
        "schema_version": "ekg.d4_typed_cue_preflight.v1",
        "status": "pass",
        "seed": args.seed,
        "final_valid_accessed": False,
        "source": {"path": str(args.source), "sha256": sha256_file(args.source)},
        "cv": {"path": str(args.cv), "sha256": sha256_file(args.cv), "folds": 5},
        "contracts": contracts,
        "accepted_oof": baselines,
        "model": {"path": str(args.model), "content_sha256": model_digest},
        "training": {
            "arms": ["full", "remove_core", "permutation"],
            "epochs": args.epochs,
            "lr": args.lr,
            "alpha": args.alpha,
            "cue_weight": args.cue_weight,
            "max_length": args.max_length,
            "stride": args.stride,
            "use_structure": False,
            "permutation_seed": args.permutation_seed,
            "selection": "selection-dev only; evaluation is unread by each trainer",
        },
        "code": code,
        "final_valid_ledger": "not opened; D4 pilot is pooled train-derived OOF only",
    }
    args.output.parent.mkdir(parents=True, exist_ok=False)
    args.output.write_text(json.dumps(protocol, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return protocol


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--cv", required=True, type=Path)
    parser.add_argument("--r1-protocol", required=True, type=Path)
    parser.add_argument("--t024", required=True, type=Path)
    parser.add_argument("--accepted-oof-root", required=True, type=Path)
    parser.add_argument("--model", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--seed", type=int, default=13)
    parser.add_argument("--epochs", type=int, default=12)
    parser.add_argument("--lr", type=float, default=2e-5)
    parser.add_argument("--alpha", type=float, default=0.5)
    parser.add_argument("--cue-weight", type=float, default=1.0)
    parser.add_argument("--max-length", type=int, default=128)
    parser.add_argument("--stride", type=int, default=64)
    parser.add_argument("--permutation-seed", type=int, default=13)
    args = parser.parse_args()
    args.repo = args.repo.resolve()
    for name in ("source", "cv", "r1_protocol", "t024", "accepted_oof_root", "model"):
        setattr(args, name, getattr(args, name).resolve())
    protocol = prepare(args)
    print(f"[d4-preflight] PASS {args.output} code_files={len(protocol['code'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
