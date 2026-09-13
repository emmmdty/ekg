#!/usr/bin/env python
"""Freeze and verify C5 argument-uncertainty inputs before any CUDA work starts.

Everything the pilot may read is pinned here and nothing else: the P1 trust
root, the R1 identity phase contract, the train source and its two manifests,
the frozen official evaluator, the content-addressed encoder, and the baselines
whose official coreference scores are recomputed rather than copied.  The
final-valid manifests are never opened.

The baselines are re-scored by running the frozen `score_maven_ere_official.py`
as a subprocess, not by a second scoring path in this file: two scorers are two
numbers for one protocol, which is the mistake `score_a3_arm.py` documents.

The registered negative control (`qwen3-argument-s13-r2`) sets the training
budget the proposed arms must match bit for bit, so `FROZEN_TRAINING` below is
read off that run's `coref_config.json` rather than chosen here.  The second
method family (Global-Local Topic via EasyECR) has not been reproduced yet;
under QR-001 v1.1.0 that does not block the phase, but the gap is recorded as
a status rather than silently omitted.
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

# Pinned by `docs/phases/PHASE_C5_argument_uncertainty.md`; a mismatch means the
# run would not be the experiment the contract froze.
EXPECTED_P1_PROTOCOL_SHA256 = (
    "1e31a9acef39261f776f7ed4069fd73f4531e8d12b55779bfc0fbd74c67f9655"
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

# Read off gpu-4090's `.../ch1/qwen3-argument-s13-r2/checkpoint/coref_config.json`
# plus that run's fixed endpoint epoch.  The contract requires arms 4-6 to match
# the registered control's budget bit for bit, so these are not tunables.
FROZEN_TRAINING = {
    "epochs": 10,
    "warmup_steps": 200,
    "lr": 2e-5,
    "head_lr": 2e-5,
    "accum_steps": 1,
    "max_length": 512,
}
# Inference side of the same pairing. The contract forbids sweeping either.
FROZEN_INFERENCE = {"threshold": 0.7, "band": 0.0, "endpoint_epoch": 10}

CODE_FILES = (
    "src/ekg/nodes/role_uncertainty.py",
    "src/ekg/nodes/discriminative.py",
    # The scorer decides the permutation arm's *inference* layout, so it is as
    # much part of the frozen mechanism as the trainer is.
    "src/ekg/nodes/coref.py",
    "scripts/train_coref_scorer.py",
    # Turns a checkpoint into official-shape coreference predictions, so it fixes
    # the inference protocol the arms are scored under.
    "scripts/build_maven_ere_submission.py",
    "scripts/prepare_c5_argument_uncertainty_preflight.py",
    "scripts/smoke_c5_argument_uncertainty.py",
    # The pilot driver runs under this contract, so it belongs inside the hash
    # set the contract binds -- D4 learnt this the expensive way.
    "scripts/run_c5_argument_uncertainty.py",
)

COREF_METRICS = ("muc", "b_cubed", "ceaf", "blanc")
ARMS = ("full", "remove_core", "permutation")


class PreflightError(ValueError):
    """A pinned C5 input, baseline or contract does not verify."""


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
    """The identity phase contract, as R1 and T024 both have to describe it."""
    protocol = _load(r1_protocol)
    phase = protocol.get("phase_contracts", {}).get("identity")
    _require(isinstance(phase, dict), "R1 protocol has no identity phase contract")
    path = repo / str(phase.get("path", ""))
    _require(path.is_file(), "C5 phase contract file is missing")
    _require(sha256_file(path) == phase.get("sha256"), "C5 phase contract hash drift")
    approved = _load(t024).get("approved_contracts", {}).get("identity")
    _require(isinstance(approved, dict), "T024 has no identity decision")
    _require(approved.get("state") == "frozen", "C5 is not frozen by T024")
    _require(approved.get("path") == phase.get("path"), "T024/R1 identity path mismatch")
    _require(approved.get("sha256") == phase.get("sha256"), "T024/R1 identity hash mismatch")
    return {
        "r1_protocol": sha256_file(r1_protocol),
        "t024": sha256_file(t024),
        "phase_contract": sha256_file(path),
    }


def _materialise_internal_dev(source: Path, manifest: Path, output: Path) -> dict:
    """Write the 291 internal-dev documents the pilot is scored on.

    In manifest order, so the file is reproducible from the manifest alone, and
    with the candidate population digest recomputed from the result: that digest
    is the one thing C5 may not move, so it is checked here rather than trusted.
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
    """Recompute one baseline's official coreference P/R/F1 with the frozen evaluator."""
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
    for metric in COREF_METRICS:
        for stat in ("precision", "recall", "f1"):
            _require(f"{metric}_{stat}" in scores, f"{name}: no {metric}_{stat}")
    return {
        "predictions_sha256": sha256_file(predictions),
        "metrics_sha256": sha256_file(output),
        "scores": {
            f"{metric}_{stat}": scores[f"{metric}_{stat}"]
            for metric in COREF_METRICS
            for stat in ("precision", "recall", "f1")
        },
    }


def prepare(args: argparse.Namespace) -> dict:
    _require(not args.output.exists(), f"refusing to overwrite preflight: {args.output}")
    _require(args.seed == 13, "C5 is authorized only for seed 13")
    for name, expected in FROZEN_TRAINING.items():
        actual = getattr(args, name)
        _require(actual == expected, f"C5 {name} is frozen to {expected}, got {actual}")
    _require(
        sha256_file(args.p1_protocol) == EXPECTED_P1_PROTOCOL_SHA256, "P1 trust root drift"
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
        "official_joint": _score_baseline(
            args.repo,
            "official_joint",
            args.anchor_predictions,
            Path(gold["path"]),
            args.evaluator,
            root / "baselines/official_joint.metrics.json",
        ),
        "qwen3_argument_pooling": _score_baseline(
            args.repo,
            "qwen3_argument_pooling",
            args.negative_control_predictions,
            Path(gold["path"]),
            args.evaluator,
            root / "baselines/qwen3_argument_pooling.metrics.json",
        ),
    }
    # The registered control must stay below the anchor; if it ever scored above
    # it, it would not be the "naive pooling loses MUC" control C5 reasons from.
    anchor_muc = baselines["official_joint"]["scores"]["muc_f1"]
    control_muc = baselines["qwen3_argument_pooling"]["scores"]["muc_f1"]
    _require(
        control_muc < anchor_muc,
        f"registered negative control is not below the anchor: {control_muc} >= {anchor_muc}",
    )

    if args.global_local_predictions is not None:
        baselines["global_local_topic"] = {
            "fidelity": "(b) transparent adaptation; see BASELINE_ROSTER.md 1.1",
            **_score_baseline(
                args.repo,
                "global_local_topic",
                args.global_local_predictions,
                Path(gold["path"]),
                args.evaluator,
                root / "baselines/global_local_topic.metrics.json",
            ),
        }
    else:
        # QR-001 v1.1.0 made baseline breadth a reporting requirement rather than
        # an admission gate, so the gap is declared instead of blocking -- but it
        # is declared, not omitted.
        baselines["global_local_topic"] = {
            "status": "not_reproduced",
            "obstacle": (
                "EasyECR conditionally_runnable (PHASE_R1.md 22); KBP 2017 needs an LDC "
                "licence, so fidelity path is FR-016 (b). Pass --global-local-predictions "
                "once C-2b closes."
            ),
        }

    protocol = {
        "schema_version": "ekg.c5_argument_uncertainty_preflight.v1",
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
        "trust_roots": {"p1_protocol_sha256": EXPECTED_P1_PROTOCOL_SHA256},
        "contracts": contracts,
        "evaluator": {"path": str(args.evaluator), "sha256": EXPECTED_EVALUATOR_SHA256},
        "model": {"path": str(args.model), "content_sha256": model_digest},
        "argument_predictions": {
            "path": str(args.argument_predictions),
            "sha256": sha256_file(args.argument_predictions),
        },
        "baselines": baselines,
        "training": {
            "arms": list(ARMS),
            **FROZEN_TRAINING,
            **FROZEN_INFERENCE,
            "component": "role_compatibility",
            "budget_source": "matched to qwen3-argument-s13-r2 coref_config.json",
            "selection": "fixed endpoint epoch; no threshold or epoch sweep",
        },
        "code": {path: sha256_file(args.repo / path) for path in CODE_FILES},
        "final_valid_ledger": "not opened; C5 reads train and internal-dev only",
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
    parser.add_argument("--r1-protocol", required=True, type=Path)
    parser.add_argument("--t024", required=True, type=Path)
    parser.add_argument(
        "--anchor-predictions", required=True, type=Path,
        help="official-joint official-shape coreference predictions, for independent replay",
    )
    parser.add_argument(
        "--negative-control-predictions", required=True, type=Path,
        help="qwen3-argument-s13-r2 predictions, the registered negative control",
    )
    parser.add_argument(
        "--global-local-predictions", type=Path, default=None,
        help="Global-Local Topic via EasyECR; omit until C-2b closes and it is recorded absent",
    )
    parser.add_argument(
        "--argument-predictions", required=True, type=Path,
        help="complete mention-local argument prediction JSONL the arms read",
    )
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
    args = parser.parse_args()
    args.repo = args.repo.resolve()
    for name in (
        "source", "train_manifest", "dev_manifest", "p1_protocol", "r1_protocol",
        "t024", "anchor_predictions", "negative_control_predictions",
        "argument_predictions", "model", "evaluator", "output",
    ):
        setattr(args, name, getattr(args, name).resolve())
    if args.global_local_predictions is not None:
        args.global_local_predictions = args.global_local_predictions.resolve()

    protocol = prepare(args)
    print(
        f"[c5-preflight] {protocol['status'].upper()} {args.output} "
        f"code_files={len(CODE_FILES)} candidate_digest={EXPECTED_CANDIDATE_DIGEST}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
