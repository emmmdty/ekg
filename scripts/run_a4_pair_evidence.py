#!/usr/bin/env python
"""Drive the A4 seed-13 pilot over the four frozen arms.

Every knob comes from the immutable preflight contract rather than this file's
defaults, so the pilot cannot drift from what the preflight verified.  Each arm
trains on the train manifest, selects on internal-dev per family, predicts the
whole candidate universe, and is scored by the organisers' own `evaluate.py`
through the same normaliser the A3 baselines went through.

Arms are independent, so `--arms` lets one card run a subset and `--aggregate`
pools afterwards.  Pooling is a separate invocation on purpose: it carries the
assertions that have to hold across all four arms at once -- one candidate
population, one evaluator, one seed.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from run_a3_baseline import normalize_predictions  # noqa: E402

from ekg.core.stage_bundle import sha256_file  # noqa: E402
from ekg.relations.pair_evidence import A4_ARMS  # noqa: E402

FAMILIES = ("causal", "subevent", "temporal")
ARTIFACTS = ("edges.jsonl", "evidence.json", "logits.json", "report.json")


class PilotError(ValueError):
    """An A4 pilot input, arm or export violates the frozen contract."""


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


def verify_contract(repo: Path, contract: Path) -> dict:
    payload = _load(contract)
    _require(
        payload.get("schema_version") == "ekg.a4_pair_evidence_preflight.v1", "contract schema"
    )
    _require(payload.get("status") == "pass", "contract status")
    _require(payload.get("seed") == 13, "contract seed")
    _require(payload.get("final_valid_accessed") is False, "contract final-valid access")
    _require(tuple(payload["training"]["arms"]) == A4_ARMS, "contract arm set")
    for relative, expected in payload.get("code", {}).items():
        path = repo / relative
        _require(path.is_file(), f"missing bound code file: {relative}")
        _require(sha256_file(path) == expected, f"bound code hash drift: {relative}")
    for field in ("source", "evaluator"):
        entry = payload[field]
        path = Path(entry["path"])
        _require(path.is_file(), f"contract {field} is missing: {path}")
        _require(sha256_file(path) == entry["sha256"], f"contract {field} hash drift")
    gold = Path(payload["internal_dev_gold"]["path"])
    _require(gold.is_file(), f"internal-dev gold is missing: {gold}")
    _require(
        sha256_file(gold) == payload["internal_dev_gold"]["sha256"],
        "internal-dev gold hash drift",
    )
    return payload


def run_arm(repo: Path, contract: dict, arm: str, output: Path, contract_sha256: str) -> dict:
    _require(not output.exists(), f"refusing to overwrite arm output: {output}")
    training = contract["training"]
    gold = Path(contract["internal_dev_gold"]["path"])
    output.mkdir(parents=True)
    checkpoint = output / "checkpoint"
    train = [
        sys.executable, "-u", "scripts/train_a4_pair_evidence.py",
        "--train", str(Path(contract["source"]["path"])),
        "--train-manifest", str(Path(contract["manifests"]["train"]["path"])),
        "--dev-manifest", str(Path(contract["manifests"]["internal_dev"]["path"])),
        "--model", str(Path(contract["model"]["path"])),
        "--output", str(checkpoint),
        "--arm", arm,
        "--epochs", str(training["epochs"]),
        "--lr", str(training["lr"]),
        "--head-lr", str(training["head_lr"]),
        "--warmup-steps", str(training["warmup_steps"]),
        "--accum-steps", str(training["accum_steps"]),
        "--max-length", str(training["max_length"]),
        "--consistency-weight", str(training["consistency_weight"]),
        "--seed", str(contract["seed"]),
    ]
    subprocess.run(train, cwd=repo, check=True)

    # Per-family checkpoint selection: each family is predicted from the epoch
    # selected for it, then only that family's edges are kept.
    family_edges: dict[str, Path] = {}
    for family in FAMILIES:
        selected = checkpoint / "by_family" / family
        selection = selected / "selection.json"
        _require(
            (selected / "heads.pt").is_file() and selection.is_file(),
            f"{arm}: missing selected {family} checkpoint under {selected}",
        )
        _require(
            _load(selection).get("family") == family,
            f"{arm}: selection metadata mismatch under {selected}",
        )
        root = output / family
        evaluate = [
            sys.executable, "-u", "scripts/evaluate_a4_pair_evidence.py",
            "--gold", str(gold),
            "--checkpoint", str(selected),
            "--max-length", str(training["max_length"]),
            "--edges-output", str(root / "edges.jsonl"),
            "--evidence-output", str(root / "evidence.json"),
            "--logits-output", str(root / "logits.json"),
            "--output", str(root / "report.json"),
        ]
        subprocess.run(evaluate, cwd=repo, check=True)
        for name in ARTIFACTS:
            _require((root / name).is_file(), f"{arm}/{family}: missing pilot output {name}")
        family_edges[family] = root / "edges.jsonl"

    merged = output / "edge_predictions.jsonl"
    _merge_family_edges(family_edges, merged)
    official = output / "official_predictions.jsonl"
    normalize_predictions(
        baseline="local_pair",
        raw_path=merged,
        gold_path=gold,
        output=official,
        candidate_digest=contract["internal_dev_gold"]["candidate_id_digest"],
        active_families=FAMILIES,
    )
    metrics = output / "official_metrics.json"
    subprocess.run(
        [
            sys.executable, "-u", "scripts/score_maven_ere_official.py",
            "--evaluator", str(Path(contract["evaluator"]["path"])),
            "--gold", str(gold),
            "--pred", str(official),
            "--candidate-digest", contract["internal_dev_gold"]["candidate_id_digest"],
            "--output", str(metrics),
        ],
        cwd=repo,
        check=True,
    )
    scores = _load(metrics)["scores"]
    reports = {family: _load(output / family / "report.json") for family in FAMILIES}
    payload = {
        "schema_version": "ekg.a4_pair_evidence_pilot_arm.v1",
        "status": "complete",
        "arm": arm,
        "seed": contract["seed"],
        "final_valid_accessed": False,
        "contract_sha256": contract_sha256,
        "candidate_id_digest": contract["internal_dev_gold"]["candidate_id_digest"],
        "official_scores": scores,
        "mediator": reports["causal"]["mediator"],
        "revised_rows": reports["causal"]["revised_rows"],
        "candidate_pairs": reports["causal"]["candidate_pairs"],
        "train_argv": train,
        "artifact_sha256": {
            "edge_predictions.jsonl": sha256_file(merged),
            "official_predictions.jsonl": sha256_file(official),
            "official_metrics.json": sha256_file(metrics),
            **{
                f"{family}/{name}": sha256_file(output / family / name)
                for family in FAMILIES
                for name in ARTIFACTS
            },
        },
    }
    _write(output / "arm.json", payload)
    return payload


def _merge_family_edges(family_paths: dict[str, Path], output: Path) -> None:
    """Keep only each family's own edges, from the checkpoint selected for it.

    Every checkpoint carries all three heads, so taking every edge from one of
    them would not be per-family selection at all.
    """
    records = {
        family: [
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line
        ]
        for family, path in family_paths.items()
    }
    reference = [row["doc_id"] for row in records[FAMILIES[0]]]
    for family in FAMILIES[1:]:
        _require(
            [row["doc_id"] for row in records[family]] == reference,
            f"{family} prediction document order/set differs",
        )
    indexed = {
        family: {row["doc_id"]: row for row in rows} for family, rows in records.items()
    }
    merged = [
        {
            "doc_id": doc_id,
            "edges": [
                edge
                for family in FAMILIES
                for edge in indexed[family][doc_id]["edges"]
                if edge["relation_type"] == family
            ],
        }
        for doc_id in reference
    ]
    output.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in merged),
        encoding="utf-8",
    )


def aggregate(contract: dict, output: Path) -> dict:
    arms: dict[str, dict] = {}
    for arm in A4_ARMS:
        state = _load(output / arm / "arm.json")
        _require(state.get("status") == "complete", f"{arm} is not complete")
        _require(state.get("seed") == contract["seed"], f"{arm} ran another seed")
        _require(state.get("final_valid_accessed") is False, f"{arm} touched final-valid")
        _require(
            state.get("candidate_id_digest")
            == contract["internal_dev_gold"]["candidate_id_digest"],
            f"{arm} scored another candidate population",
        )
        arms[arm] = state
    populations = {arm: state["candidate_pairs"] for arm, state in arms.items()}
    _require(len(set(populations.values())) == 1, f"candidate counts differ: {populations}")
    summary = {
        "schema_version": "ekg.a4_pair_evidence_pilot_summary.v1",
        "status": "pass",
        "seed": contract["seed"],
        "final_valid_accessed": False,
        "candidate_id_digest": contract["internal_dev_gold"]["candidate_id_digest"],
        "candidate_pairs": populations[A4_ARMS[0]],
        "contract_sha256": arms[A4_ARMS[0]]["contract_sha256"],
        "baselines": contract["baselines"],
        "arms": {
            arm: {
                "official_scores": state["official_scores"],
                "mediator": state["mediator"],
                "revised_rows": state["revised_rows"],
                "artifact_sha256": state["artifact_sha256"],
            }
            for arm, state in arms.items()
        },
    }
    _write(output / "pilot_summary.json", summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--contract", required=True, type=Path)
    parser.add_argument("--seed", type=int, default=13)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--arms", default=",".join(A4_ARMS))
    parser.add_argument("--aggregate", action="store_true")
    args = parser.parse_args()
    args.repo = args.repo.resolve()
    contract_path = args.contract.resolve()
    contract = verify_contract(args.repo, contract_path)
    _require(args.seed == 13, "A4 is authorized only for seed 13")

    if args.aggregate:
        summary = aggregate(contract, args.output)
        causal = {
            arm: round(state["official_scores"]["causal_f1"], 4)
            for arm, state in summary["arms"].items()
        }
        print(f"[a4-pilot] PASS official causal F1 {causal}", flush=True)
        return 0

    wanted = [value.strip() for value in args.arms.split(",") if value.strip()]
    _require(all(arm in A4_ARMS for arm in wanted), f"unknown arms in {args.arms!r}")
    for arm in wanted:
        state = run_arm(
            args.repo, contract, arm, args.output / arm, sha256_file(contract_path)
        )
        print(
            f"[a4-pilot] {arm} complete, causal F1 "
            f"{state['official_scores']['causal_f1']:.4f}",
            flush=True,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
