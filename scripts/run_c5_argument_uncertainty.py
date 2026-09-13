#!/usr/bin/env python
"""Drive the C5 seed-13 pilot over the three frozen arms.

Every knob comes from the immutable preflight contract rather than this file's
defaults, so the pilot cannot drift from what the preflight verified.  Each arm
trains on the train manifest with one component switch changed, predicts the
whole 291-document internal-dev mention population, and is scored by the
organisers' own `evaluate.py` -- the same path the anchor and the registered
negative control went through.

The three arms differ by exactly one thing each:

* `full`         -- the role-compatibility residual;
* `remove_core`  -- no residual, same corpus and budget;
* `permutation`  -- the residual reading vectors shuffled inside document x
                    event type, which is the negative control.

`remove_core` still passes `--argument-predictions`: that flag selects the
corpus as well as the annotation, and the arms have to share one pair
population.

Arms are independent, so `--arms` lets one card run a subset and `--aggregate`
pools afterwards.  Pooling is a separate invocation on purpose: it carries the
assertions that have to hold across all three arms at once -- one candidate
population, one evaluator, one seed.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from ekg.core.stage_bundle import sha256_file

ARMS = ("full", "remove_core", "permutation")
# What each arm hands the trainer. The tuple is the whole difference between them.
ARM_FLAGS: dict[str, tuple[str, ...]] = {
    "full": ("--components", "role_compatibility"),
    "remove_core": (),
    "permutation": ("--components", "role_compatibility", "--permute-role-features"),
}


class PilotError(ValueError):
    """A C5 pilot input, arm or export violates the frozen contract."""


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
        payload.get("schema_version") == "ekg.c5_argument_uncertainty_preflight.v1",
        "contract schema",
    )
    _require(payload.get("status") == "pass", "contract status")
    _require(payload.get("seed") == 13, "contract seed")
    _require(payload.get("final_valid_accessed") is False, "contract final-valid access")
    _require(tuple(payload["training"]["arms"]) == ARMS, "contract arm set")
    for relative, expected in payload.get("code", {}).items():
        path = repo / relative
        _require(path.is_file(), f"missing bound code file: {relative}")
        _require(sha256_file(path) == expected, f"bound code hash drift: {relative}")
    for field in ("source", "evaluator", "argument_predictions"):
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


def _coverage(gold: Path, predictions: Path) -> dict:
    """Every gold mention appears in exactly one predicted cluster.

    The official scorer fills singletons silently, so a dropped mention would
    score rather than fail.  C5's gate is a coverage gate, so it is counted here
    against the gold population instead of being inferred from the metrics.
    """
    wanted: dict[str, set[str]] = {}
    for line in gold.read_text(encoding="utf-8").splitlines():
        if not line:
            continue
        record = json.loads(line)
        mentions = {
            str(mention["id"])
            for event in record.get("events", [])
            for mention in event.get("mention", [])
        }
        mentions |= {str(m["id"]) for m in record.get("TIMEX", [])}
        mentions |= {str(m["id"]) for m in record.get("event_mentions", [])}
        wanted[str(record["id"])] = mentions

    seen: dict[str, list[str]] = {doc: [] for doc in wanted}
    for line in predictions.read_text(encoding="utf-8").splitlines():
        if not line:
            continue
        record = json.loads(line)
        doc_id = str(record["id"])
        _require(doc_id in wanted, f"prediction for an unknown document: {doc_id}")
        for cluster in record.get("coreference", []):
            seen[doc_id].extend(str(m) for m in cluster)

    duplicated, unknown, missing = 0, 0, 0
    for doc_id, mentions in wanted.items():
        predicted = seen[doc_id]
        duplicated += len(predicted) - len(set(predicted))
        unknown += len(set(predicted) - mentions)
        missing += len(mentions - set(predicted))
    total = sum(len(m) for m in wanted.values())
    # Singletons are legitimately absent from the clusters, so `missing` is not
    # an error by itself; duplicates and strangers always are.
    _require(duplicated == 0, f"{duplicated} mentions appear in more than one cluster")
    _require(unknown == 0, f"{unknown} predicted mentions are not in the gold population")
    return {
        "documents": len(wanted),
        "gold_mentions": total,
        "clustered_mentions": total - missing,
        "singletons": missing,
        "duplicated": duplicated,
        "unknown": unknown,
    }


def run_arm(repo: Path, contract: dict, arm: str, output: Path, contract_sha256: str) -> dict:
    _require(not output.exists(), f"refusing to overwrite arm output: {output}")
    training = contract["training"]
    gold = Path(contract["internal_dev_gold"]["path"])
    output.mkdir(parents=True)
    checkpoint = output / "checkpoint"
    train = [
        sys.executable, "-u", "scripts/train_coref_scorer.py",
        "--train", str(Path(contract["source"]["path"])),
        "--train-manifest", str(Path(contract["manifests"]["train"]["path"])),
        "--dev-manifest", str(Path(contract["manifests"]["internal_dev"]["path"])),
        "--model", str(Path(contract["model"]["path"])),
        "--output", str(checkpoint),
        "--argument-predictions", str(Path(contract["argument_predictions"]["path"])),
        "--epochs", str(training["epochs"]),
        "--lr", str(training["lr"]),
        "--head-lr", str(training["head_lr"]),
        "--warmup-steps", str(training["warmup_steps"]),
        "--accum-steps", str(training["accum_steps"]),
        "--max-length", str(training["max_length"]),
        "--seed", str(contract["seed"]),
        "--save-every-epoch",
        *ARM_FLAGS[arm],
    ]
    subprocess.run(train, cwd=repo, check=True)

    # Fixed endpoint epoch, as the contract froze it: no epoch is selected on
    # internal-dev, so the arms cannot be compared at different budgets.
    endpoint = checkpoint / "epochs" / f"epoch-{training['endpoint_epoch']}"
    _require(endpoint.is_dir(), f"{arm}: missing frozen endpoint checkpoint {endpoint}")

    predictions = output / "predictions.jsonl"
    predict = [
        sys.executable, "-u", "scripts/build_maven_ere_submission.py",
        "--test", str(gold),
        "--from-labeled",
        "--coref-predictor", "supervised",
        "--coref-checkpoint", str(endpoint),
        "--coref-threshold", str(training["threshold"]),
        "--coref-band", str(training["band"]),
        "--relation-predictor", "none",
        "--output", str(predictions),
    ]
    subprocess.run(predict, cwd=repo, check=True)
    _require(predictions.is_file(), f"{arm}: predictions were not written")
    coverage = _coverage(gold, predictions)

    metrics = output / "official_metrics.json"
    subprocess.run(
        [
            sys.executable, "-u", "scripts/score_maven_ere_official.py",
            "--evaluator", str(Path(contract["evaluator"]["path"])),
            "--gold", str(gold),
            "--pred", str(predictions),
            "--candidate-digest", contract["internal_dev_gold"]["candidate_id_digest"],
            "--output", str(metrics),
        ],
        cwd=repo,
        check=True,
    )
    scores = _load(metrics)["scores"]
    payload = {
        "schema_version": "ekg.c5_argument_uncertainty_pilot_arm.v1",
        "status": "complete",
        "arm": arm,
        "seed": contract["seed"],
        "final_valid_accessed": False,
        "contract_sha256": contract_sha256,
        "candidate_id_digest": contract["internal_dev_gold"]["candidate_id_digest"],
        "official_scores": scores,
        "coverage": coverage,
        "artifacts": {
            "predictions_sha256": sha256_file(predictions),
            "metrics_sha256": sha256_file(metrics),
        },
    }
    _write(output / "status.json", payload)
    return payload


def aggregate(output: Path, contract: dict, contract_sha256: str) -> dict:
    arms = {}
    for arm in ARMS:
        status = output / arm / "status.json"
        _require(status.is_file(), f"missing arm status: {status}")
        arms[arm] = _load(status)
    digests = {arm["candidate_id_digest"] for arm in arms.values()}
    _require(len(digests) == 1, f"arms disagree on the candidate population: {digests}")
    _require(
        digests.pop() == contract["internal_dev_gold"]["candidate_id_digest"],
        "arms scored a population the contract did not freeze",
    )
    _require(
        {arm["contract_sha256"] for arm in arms.values()} == {contract_sha256},
        "arms ran under different contracts",
    )
    _require(
        {arm["seed"] for arm in arms.values()} == {contract["seed"]},
        "arms ran under different seeds",
    )
    coverages = {arm: payload["coverage"]["gold_mentions"] for arm, payload in arms.items()}
    _require(len(set(coverages.values())) == 1, f"arms saw different mentions: {coverages}")

    anchor = contract["baselines"]["official_joint"]["scores"]["muc_f1"]
    control = contract["baselines"]["qwen3_argument_pooling"]["scores"]["muc_f1"]
    full_muc = arms["full"]["official_scores"]["muc_f1"]
    payload = {
        "schema_version": "ekg.c5_argument_uncertainty_pilot.v1",
        "seed": contract["seed"],
        "final_valid_accessed": False,
        "contract_sha256": contract_sha256,
        "arms": {arm: payload["official_scores"] for arm, payload in arms.items()},
        "coverage": {arm: payload["coverage"] for arm, payload in arms.items()},
        "gate": {
            # Reported, never enforced here: the promotion decision belongs to
            # the results page, and a driver that judged itself could not be
            # trusted to report a failure.
            "official_joint_muc_f1": anchor,
            "registered_control_muc_f1": control,
            "full_muc_f1": full_muc,
            "above_anchor": full_muc > anchor,
            "above_registered_control": full_muc > control,
        },
    }
    _write(output / "pilot.json", payload)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--contract", required=True, type=Path)
    parser.add_argument("--seed", type=int, default=13)
    parser.add_argument("--arms", nargs="*", default=list(ARMS), choices=list(ARMS))
    parser.add_argument(
        "--aggregate", action="store_true",
        help="pool arms already run and write pilot.json; runs no training",
    )
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    args.repo = args.repo.resolve()
    args.contract = args.contract.resolve()
    args.output = args.output.resolve()

    _require(args.seed == 13, "C5 is authorized only for seed 13")
    contract = verify_contract(args.repo, args.contract)
    contract_sha256 = sha256_file(args.contract)

    if args.aggregate:
        payload = aggregate(args.output, contract, contract_sha256)
        print(f"[c5-pilot] aggregated {len(payload['arms'])} arms -> {args.output}/pilot.json")
        return 0

    for arm in args.arms:
        result = run_arm(args.repo, contract, arm, args.output / arm, contract_sha256)
        print(
            f"[c5-pilot] {arm} muc_f1={result['official_scores']['muc_f1']:.4f} "
            f"coverage={result['coverage']['gold_mentions']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
