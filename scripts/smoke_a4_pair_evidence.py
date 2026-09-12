#!/usr/bin/env python
"""Run the A4 smoke: every arm, a handful of documents, forward to reload.

What it proves is narrow and deliberate: that all four arms train, export,
reload and predict on the real encoder, that the counterfactual forwards stay
finite, that a freshly built head is the reproduction baseline until its
residual has learnt anything, and that the four arms label **one** candidate
population.  It proves nothing about whether the mechanism works -- that is
A4.3's job, on the frozen contract.

The documents come from the frozen manifests, subset in manifest order and
materialised into a source that holds exactly them, so the trainer's own
"source is not exactly train plus dev" guard still fires if the subset is
wrong.  Pass `--contract` once an A4.1 preflight exists and the bound code
hashes are re-verified here too.
"""

from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
from pathlib import Path

from ekg.core.protocol import load_manifest_ids
from ekg.core.stage_bundle import sha256_file
from ekg.relations.pair_evidence import A4_ARMS

ARTIFACTS = ("edges.jsonl", "evidence.json", "logits.json", "report.json")


class SmokeError(ValueError):
    """An A4 smoke input, checkpoint or export violates the contract."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise SmokeError(message)


def _load(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SmokeError(f"{path} must contain a JSON object")
    return payload


def _write(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _verify_contract(repo: Path, contract: Path) -> dict:
    payload = _load(contract)
    _require(payload.get("schema_version") == "ekg.a4_pair_evidence_preflight.v1", "schema")
    _require(payload.get("status") == "pass", "contract status")
    _require(payload.get("final_valid_accessed") is False, "contract final-valid access")
    for relative, expected in payload.get("code", {}).items():
        path = repo / relative
        _require(path.is_file(), f"missing bound code file: {relative}")
        _require(sha256_file(path) == expected, f"bound code hash drift: {relative}")
    return payload


def _subset(source: Path, ids: list[str], output: Path) -> None:
    """Keep exactly the wanted documents, in source order."""
    wanted = set(ids)
    selected = [
        line
        for line in source.read_text(encoding="utf-8").splitlines()
        if line and json.loads(line).get("id") in wanted
    ]
    _require(len(selected) == len(ids), f"smoke source covers {len(selected)} of {len(ids)}")
    output.write_text("\n".join(selected) + "\n", encoding="utf-8")


def _manifest(path: Path, ids: list[str]) -> Path:
    _write(path, {"schema_version": "ekg.a4_smoke_manifest.v1", "doc_ids": ids})
    return path


def _finite(values) -> bool:
    if isinstance(values, list):
        return all(_finite(item) for item in values)
    return isinstance(values, (int, float)) and math.isfinite(values)


def _baseline_equivalence(model: str) -> dict[str, object]:
    """A fresh head must equal the reproduction baseline, with or without evidence.

    The residual is zero-initialised, so the evidence stream cannot move a logit
    until training moves it -- which is what makes `full` and `remove_core`
    comparable at all.  Checked on the real device rather than only in the unit
    test, because that is where a dtype or device mismatch would show up.
    """
    import torch
    from transformers import AutoModel

    from ekg.relations.extractor.supervised import FAMILY_SUBTYPES
    from ekg.relations.pair_heads import LINEAR_HEAD, PAIR_EVIDENCE_HEAD, build_pair_head

    device = "cuda" if torch.cuda.is_available() else "cpu"
    hidden = AutoModel.from_pretrained(model).config.hidden_size
    counts = {family: len(subs) for family, subs in FAMILY_SUBTYPES.items()}
    torch.manual_seed(13)
    evidence_head = build_pair_head(
        PAIR_EVIDENCE_HEAD, hidden_size=hidden, subtype_counts=counts
    ).to(device)
    torch.manual_seed(13)
    baseline = build_pair_head(LINEAR_HEAD, hidden_size=hidden, subtype_counts=counts).to(device)
    evidence_head.eval()
    baseline.eval()
    feats = torch.randn(8, hidden * 4, device=device)
    dist_ids = torch.zeros(8, dtype=torch.long, device=device)
    with torch.no_grad():
        reference = baseline(feats, dist_ids)
        plain = evidence_head(feats, dist_ids)
        with_evidence = evidence_head(feats, dist_ids, torch.randn(8, hidden * 4, device=device))
    for family in counts:
        _require(
            torch.equal(plain[family], reference[family]),
            f"{family}: a fresh evidence head already differs from the baseline",
        )
        _require(
            torch.equal(with_evidence[family], reference[family]),
            f"{family}: the zero-initialised residual moved a logit at init",
        )
    return {
        "device": device,
        "hidden_size": hidden,
        "baseline_parameters": sum(p.numel() for p in baseline.parameters()),
        "evidence_parameters": sum(p.numel() for p in evidence_head.parameters()),
    }


def run(args: argparse.Namespace) -> dict:
    _require(not args.output.exists(), f"refusing to overwrite smoke output: {args.output}")
    contract = _verify_contract(args.repo, args.contract) if args.contract else None
    train_ids = load_manifest_ids(args.train_manifest)[: args.docs]
    dev_ids = load_manifest_ids(args.dev_manifest)[: args.docs]
    _require(not set(train_ids) & set(dev_ids), "smoke train and dev ids overlap")
    args.output.mkdir(parents=True)

    source = args.output / "smoke_source.jsonl"
    _subset(args.source, train_ids + dev_ids, source)
    gold = args.output / "smoke_dev.jsonl"
    _subset(args.source, dev_ids, gold)
    train_manifest = _manifest(args.output / "train_manifest.json", train_ids)
    dev_manifest = _manifest(args.output / "dev_manifest.json", dev_ids)

    arms: dict[str, dict] = {}
    populations: dict[str, int] = {}
    pair_keys: dict[str, list[str]] = {}
    for arm in A4_ARMS:
        root = args.output / arm
        checkpoint = root / "checkpoint"
        train = [
            sys.executable, "-u", "scripts/train_a4_pair_evidence.py",
            "--train", str(source),
            "--train-manifest", str(train_manifest),
            "--dev-manifest", str(dev_manifest),
            "--model", args.model,
            "--output", str(checkpoint),
            "--arm", arm,
            "--epochs", str(args.epochs),
            "--lr", str(args.lr),
            "--head-lr", str(args.head_lr),
            "--warmup-steps", "0",
            "--accum-steps", "2",
            "--max-length", str(args.max_length),
            "--consistency-weight", str(args.consistency_weight),
            "--seed", "13",
        ]
        evaluate = [
            sys.executable, "-u", "scripts/evaluate_a4_pair_evidence.py",
            "--gold", str(gold),
            "--checkpoint", str(checkpoint),
            "--max-length", str(args.max_length),
            "--edges-output", str(root / "edges.jsonl"),
            "--evidence-output", str(root / "evidence.json"),
            "--logits-output", str(root / "logits.json"),
            "--output", str(root / "report.json"),
        ]
        subprocess.run(train, cwd=args.repo, check=True)
        subprocess.run(evaluate, cwd=args.repo, check=True)
        for name in ARTIFACTS:
            _require((root / name).is_file(), f"{arm}: missing smoke output {name}")

        metadata = _load(checkpoint / "run_metadata.json")
        _require(metadata.get("status") == "complete", f"{arm}: training did not complete")
        losses = metadata.get("epoch_mean_loss")
        _require(
            isinstance(losses, list) and len(losses) == args.epochs and _finite(losses),
            f"{arm}: epoch losses are missing or non-finite: {losses}",
        )
        report = _load(root / "report.json")
        evidence = _load(root / "evidence.json")
        traces = _load(root / "logits.json")
        _require(report["arm"] == arm, f"{arm}: report carries arm {report['arm']!r}")
        _require(
            sorted(evidence) == sorted(dev_ids),
            f"{arm}: the evidence sidecar does not cover every evaluated document",
        )
        for trace in traces.values():
            for kind in ("base", "masked", "retained", "revised_probabilities"):
                _require(_finite(trace[kind]), f"{arm}: non-finite {kind} logits")
        populations[arm] = report["candidate_pairs"]
        pair_keys[arm] = sorted(
            f"{doc_id}::{key}" for doc_id, pairs in evidence.items() for key in pairs
        )
        arms[arm] = {
            "train_argv": train,
            "evaluate_argv": evaluate,
            "candidate_pairs": report["candidate_pairs"],
            "epoch_mean_loss": losses,
            "revised_rows": report["revised_rows"],
            "predicted_edges": report["predicted_edges"],
            "mediator": report["mediator"],
            "artifact_sha256": {name: sha256_file(root / name) for name in ARTIFACTS},
        }

    reference = pair_keys[A4_ARMS[0]]
    for arm in A4_ARMS[1:]:
        _require(
            pair_keys[arm] == reference,
            f"{arm}: labels a different candidate population than {A4_ARMS[0]}",
        )
    _require(len(set(populations.values())) == 1, f"candidate counts differ: {populations}")

    payload = {
        "schema_version": "ekg.a4_pair_evidence_smoke.v1",
        "status": "pass",
        "final_valid_accessed": False,
        "documents": {"train": len(train_ids), "dev": len(dev_ids)},
        "candidate_pairs": reference and populations[A4_ARMS[0]],
        "candidate_population_identical": True,
        "head_at_init": _baseline_equivalence(args.model),
        "contract_sha256": sha256_file(args.contract) if args.contract else None,
        "contract_status": contract["status"] if contract else "not_bound",
        "arms": arms,
    }
    _write(args.output / "smoke.json", payload)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--source", required=True, type=Path, help="MAVEN-ERE train jsonl")
    parser.add_argument("--train-manifest", required=True, type=Path)
    parser.add_argument("--dev-manifest", required=True, type=Path)
    parser.add_argument("--model", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--contract", type=Path, help="A4.1 preflight, once it exists")
    parser.add_argument("--docs", type=int, default=10)
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--lr", type=float, default=1e-5)
    parser.add_argument("--head-lr", type=float, default=1e-4)
    parser.add_argument("--max-length", type=int, default=512)
    parser.add_argument("--consistency-weight", type=float, default=1.0)
    args = parser.parse_args()
    args.repo = args.repo.resolve()
    payload = run(args)
    print(
        f"[a4-smoke] PASS {len(payload['arms'])} arms, "
        f"{payload['candidate_pairs']} candidates each, "
        f"device={payload['head_at_init']['device']}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
