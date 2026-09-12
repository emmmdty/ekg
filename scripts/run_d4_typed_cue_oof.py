#!/usr/bin/env python
"""Drive the D4 seed-13 five-fold OOF pilot over the three frozen arms.

Every knob comes from the immutable preflight contract rather than this file's
defaults, so the pilot cannot drift from what the preflight verified.  Each
fold trains on its own train/selection manifests and predicts only its own
evaluation manifest; the per-fold training source is materialised from the
train and selection ids alone, which makes an evaluation document structurally
unreachable from a trainer rather than merely unused by it.

Folds are independent, so ``--folds`` lets one shard per card run a subset and
``--aggregate`` pools afterwards.  Pooling is a separate invocation on purpose:
sharing it with the shards would race, and the coverage assertion it carries is
the one that has to hold over all five folds at once.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from ekg.core.protocol import load_manifest_ids
from ekg.core.stage_bundle import sha256_file
from ekg.factuality.metrics import factuality_report
from ekg.factuality.typed_cues import structured_confusion_report
from ekg.relations.data.maven_fact import load_maven_fact

ARMS = ("full", "remove_core", "permutation")
EXPECTED_DOCUMENTS = 2913
EXPECTED_MENTIONS = 73939


class PilotError(ValueError):
    """A D4 pilot input, fold or export violates the frozen contract."""


def _load(path: Path) -> dict:
    if not path.is_file():
        raise PilotError(f"missing JSON input: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise PilotError(f"{path} must contain a JSON object")
    return payload


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise PilotError(message)


def _write(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _verify_contract(repo: Path, contract: Path) -> dict:
    payload = _load(contract)
    _require(payload.get("schema_version") == "ekg.d4_typed_cue_preflight.v1", "contract schema")
    _require(payload.get("status") == "pass", "contract status")
    _require(payload.get("seed") == 13, "contract seed")
    _require(payload.get("final_valid_accessed") is False, "contract final-valid access")
    _require(tuple(payload["training"]["arms"]) == ARMS, "contract arm set")
    for relative, expected in payload.get("code", {}).items():
        path = repo / relative
        _require(path.is_file(), f"missing bound code file: {relative}")
        _require(sha256_file(path) == expected, f"bound code hash drift: {relative}")
    return payload


def _fold_rows(repo: Path, contract: dict) -> dict[int, dict]:
    cv = _load(Path(contract["cv"]["path"]))
    _require(sha256_file(Path(contract["cv"]["path"])) == contract["cv"]["sha256"], "CV hash drift")
    rows: dict[int, dict] = {}
    for row in cv["folds"]:
        manifests = {}
        for role in ("train", "selection_dev", "evaluation"):
            path = repo / row[role]["path"]
            _require(sha256_file(path) == row[role]["sha256"], f"fold {row['fold']} {role} drift")
            manifests[role] = path
        rows[int(row["fold"])] = manifests
    _require(sorted(rows) == [1, 2, 3, 4, 5], "CV does not carry five folds")
    return rows


def _training_source(source: Path, ids: set[str], output: Path) -> None:
    selected = [
        line
        for line in source.read_text(encoding="utf-8").splitlines()
        if line and json.loads(line).get("id") in ids
    ]
    _require(len(selected) == len(ids), "training source does not cover train+selection")
    output.write_text("\n".join(selected) + "\n", encoding="utf-8")


def _run_arm(
    repo: Path, contract: dict, manifests: dict, arm: str, root: Path, training_source: Path
) -> dict:
    training = contract["training"]
    checkpoint = root / "checkpoint"
    train = [
        sys.executable, "-u", "scripts/train_d4_typed_cue.py",
        "--train", str(training_source),
        "--train-manifest", str(manifests["train"]),
        "--selection-manifest", str(manifests["selection_dev"]),
        "--model", str(Path(contract["model"]["path"])),
        "--output", str(checkpoint),
        "--arm", arm,
        "--epochs", str(training["epochs"]),
        "--lr", str(training["lr"]),
        "--alpha", str(training["alpha"]),
        "--cue-weight", str(training["cue_weight"]),
        "--max-length", str(training["max_length"]),
        "--stride", str(training["stride"]),
        "--seed", str(contract["seed"]),
        "--permutation-seed", str(training["permutation_seed"]),
    ]
    evaluate = [
        sys.executable, "-u", "scripts/evaluate_d4_typed_cue.py",
        "--source", str(Path(contract["source"]["path"])),
        "--checkpoint", str(checkpoint),
        "--manifest", str(manifests["evaluation"]),
        "--arm", arm,
        "--max-length", str(training["max_length"]),
        "--stride", str(training["stride"]),
        "--permutation-seed", str(training["permutation_seed"]),
        "--labels-output", str(root / "labels.json"),
        "--sidecar-output", str(root / "typed_cues.json"),
        "--probabilities-output", str(root / "decision_trace.json"),
        "--output", str(root / "report.json"),
    ]
    subprocess.run(train, cwd=repo, check=True)
    subprocess.run(evaluate, cwd=repo, check=True)
    artifacts = ("labels.json", "typed_cues.json", "decision_trace.json", "report.json")
    for name in artifacts:
        _require((root / name).is_file(), f"{arm}: missing pilot output {name}")
    labels = _load(root / "labels.json")
    cues = _load(root / "typed_cues.json")
    trace = _load(root / "decision_trace.json")
    _require(
        set(labels) == set(cues) == set(trace),
        f"{arm}: labels, cues and trace do not cover the same mentions",
    )
    return {
        "train_argv": train,
        "evaluate_argv": evaluate,
        "mentions": len(labels),
        "artifact_sha256": {name: sha256_file(root / name) for name in artifacts},
    }


def run_fold(
    repo: Path, contract: dict, fold: int, manifests: dict, output: Path, contract_sha256: str
) -> dict:
    _require(not output.exists(), f"refusing to overwrite fold output: {output}")
    evaluation_ids = set(load_manifest_ids(manifests["evaluation"]))
    training_ids = set(load_manifest_ids(manifests["train"])) | set(
        load_manifest_ids(manifests["selection_dev"])
    )
    _require(not (evaluation_ids & training_ids), f"fold {fold}: evaluation leaks into training")
    output.mkdir(parents=True)
    # Written once per fold and shared by the three arms: they train on exactly
    # the same documents by construction, and the file is ~100 MB.
    training_source = output / "training_source.jsonl"
    _training_source(Path(contract["source"]["path"]), training_ids, training_source)
    arms: dict[str, dict] = {}
    for arm in ARMS:
        root = output / arm
        root.mkdir(parents=True)
        arms[arm] = _run_arm(repo, contract, manifests, arm, root, training_source)
    payload = {
        "schema_version": "ekg.d4_typed_cue_pilot_fold.v1",
        "status": "complete",
        "fold": fold,
        "seed": contract["seed"],
        "final_valid_accessed": False,
        "contract_sha256": contract_sha256,
        "evaluation_documents": len(evaluation_ids),
        "manifest_sha256": {role: sha256_file(path) for role, path in manifests.items()},
        "training_source_sha256": sha256_file(training_source),
        "arms": arms,
    }
    _write(output / "fold.json", payload)
    return payload


def aggregate(contract: dict, output: Path) -> dict:
    documents = list(load_maven_fact(Path(contract["source"]["path"])))
    gold = {m.mention_id: m.factuality for doc in documents for m in doc.mentions}
    _require(len(documents) == EXPECTED_DOCUMENTS, f"source holds {len(documents)} documents")
    _require(len(gold) == EXPECTED_MENTIONS, f"source holds {len(gold)} mentions")
    pooled: dict[str, dict] = {}
    for arm in ARMS:
        labels: dict[str, str] = {}
        folds: list[dict] = []
        for fold in range(1, 6):
            fold_root = output / f"fold-{fold}"
            state = _load(fold_root / "fold.json")
            _require(state.get("status") == "complete", f"fold {fold} is not complete")
            _require(state.get("final_valid_accessed") is False, f"fold {fold} touched final-valid")
            _require(state.get("seed") == contract["seed"], f"fold {fold} ran another seed")
            arm_labels = _load(fold_root / arm / "labels.json")
            overlap = labels.keys() & arm_labels.keys()
            _require(not overlap, f"{arm}: fold {fold} repeats {len(overlap)} mentions")
            labels.update(arm_labels)
            folds.append(
                {
                    "fold": fold,
                    "mentions": len(arm_labels),
                    "artifact_sha256": state["arms"][arm]["artifact_sha256"],
                }
            )
        missing, extra = gold.keys() - labels.keys(), labels.keys() - gold.keys()
        _require(
            not missing and not extra,
            f"{arm}: OOF coverage missing={len(missing)} extra={len(extra)}",
        )
        pooled[arm] = {
            "folds": folds,
            "mentions": len(labels),
            "report": factuality_report(labels, gold),
            "structured_confusion": structured_confusion_report(labels, gold),
        }
    cv = _load(Path(contract["cv"]["path"]))
    evaluation_documents: set[str] = set()
    for row in cv["folds"]:
        fold_ids = set(load_manifest_ids(Path(row["evaluation"]["path"])))
        repeated = evaluation_documents & fold_ids
        _require(not repeated, f"fold {row['fold']}: {len(repeated)} documents evaluated twice")
        evaluation_documents |= fold_ids
    _require(
        len(evaluation_documents) == EXPECTED_DOCUMENTS,
        f"OOF covers {len(evaluation_documents)} of {EXPECTED_DOCUMENTS} documents",
    )
    _require(
        {doc.doc_id for doc in documents} == evaluation_documents,
        "the five evaluation folds do not reconstruct the source document set",
    )
    summary = {
        "schema_version": "ekg.d4_typed_cue_pilot_summary.v1",
        "status": "pass",
        "seed": contract["seed"],
        "final_valid_accessed": False,
        "documents": len(documents),
        "mentions": len(gold),
        "source_sha256": contract["source"]["sha256"],
        "cv_sha256": contract["cv"]["sha256"],
        "model_content_sha256": contract["model"]["content_sha256"],
        "contract_sha256": _load(output / "fold-1" / "fold.json")["contract_sha256"],
        "arms": pooled,
    }
    _write(output / "pilot_summary.json", summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--contract", required=True, type=Path)
    parser.add_argument("--seed", type=int, default=13)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--folds", default="1,2,3,4,5")
    parser.add_argument("--aggregate", action="store_true")
    args = parser.parse_args()
    args.repo = args.repo.resolve()
    contract_path = args.contract.resolve()
    contract = _verify_contract(args.repo, contract_path)
    contract_sha256 = sha256_file(contract_path)
    _require(args.seed == 13, "D4 is authorized only for seed 13")

    if args.aggregate:
        summary = aggregate(contract, args.output)
        scores = {arm: round(v["report"]["macro_f1"], 6) for arm, v in summary["arms"].items()}
        print(f"[d4-pilot] PASS pooled macro-F1 {scores}", flush=True)
        return 0

    rows = _fold_rows(args.repo, contract)
    wanted = [int(value) for value in args.folds.split(",") if value.strip()]
    _require(all(fold in rows for fold in wanted), f"unknown folds in {args.folds!r}")
    for fold in wanted:
        state = run_fold(
            args.repo, contract, fold, rows[fold], args.output / f"fold-{fold}", contract_sha256
        )
        print(f"[d4-pilot] fold {fold} complete, arms={len(state['arms'])}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
