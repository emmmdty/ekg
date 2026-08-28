#!/usr/bin/env python
"""Run P1's pinned official-scorer gold-self and adversarial gates on CPU.

This reads final-valid gold only for protocol verification. It never evaluates a
model, and records both the access purpose and a zero confirmatory-evaluation
count in the v6 ledger.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path

from ekg.relations.maven_ere_official import (
    gold_to_official_prediction,
    records_by_id,
    validate_official_predictions,
)

EVALUATOR_SHA256 = "32919e86d98c6fafae6aa9505579e2c356caee12c32c1a8c719910acec359598"
FAMILIES = ("temporal", "causal", "subevent")

EXPECTED_ADVERSARIAL_F1 = {
    "empty": {
        "temporal_f1": 0.0,
        "causal_f1": 0.0,
        "subevent_f1": 0.0,
        "b_cubed_f1": 66.66666666666666,
        "ceaf_f1": 44.44444444444444,
        "muc_f1": 0.0,
        "blanc_f1": 40.0,
    },
    "reverse_causal": {
        "temporal_f1": 100.0,
        "causal_f1": 0.0,
        "subevent_f1": 100.0,
        "b_cubed_f1": 100.0,
        "ceaf_f1": 100.0,
        "muc_f1": 100.0,
        "blanc_f1": 100.0,
    },
    "coref_merge": {
        "temporal_f1": 100.0,
        "causal_f1": 100.0,
        "subevent_f1": 100.0,
        "b_cubed_f1": 66.66666666666666,
        "ceaf_f1": 44.44444444444444,
        "muc_f1": 80.0,
        "blanc_f1": 25.0,
    },
    "coref_split": {
        "temporal_f1": 100.0,
        "causal_f1": 100.0,
        "subevent_f1": 100.0,
        "b_cubed_f1": 66.66666666666666,
        "ceaf_f1": 44.44444444444444,
        "muc_f1": 0.0,
        "blanc_f1": 40.0,
    },
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_records(path: Path) -> dict[str, dict]:
    records = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line
    ]
    return records_by_id(records, source=str(path))


def _load_evaluator(path: Path):
    spec = importlib.util.spec_from_file_location("p1_maven_ere_evaluate", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import evaluator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _score(evaluator, gold: dict[str, dict], prediction: dict[str, dict]) -> dict[str, float]:
    validate_official_predictions(gold, prediction)
    result: dict[str, float] = {}
    for family in FAMILIES:
        result.update(evaluator.evaluate(gold, prediction, family))
    result.update(evaluator.evaluate_coreference(gold, prediction))
    return result


def _assert_expected(actual: dict[str, float], expected: dict[str, float], *, name: str) -> None:
    for key, target in expected.items():
        value = actual[key]
        if not math.isclose(value, target, abs_tol=1e-6):
            raise AssertionError(f"{name}.{key}: expected {target}, got {value}")


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(item, sort_keys=True) + "\n" for item in records),
        encoding="utf-8",
    )


def _record_access(output_dir: Path, *, gold: Path, fixtures: Path) -> None:
    ledger_path = output_dir.parent / "access_ledger.json"
    if ledger_path.exists():
        ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    else:
        ledger = {
            "schema_version": "ekg.final_valid_access.v1",
            "historical_final_access_disclosed": True,
            "v6_confirmatory_eval_count": 0,
            "entries": [],
        }
    new_entries = [
        {
            "asset": str(gold),
            "sha256": _sha256(gold),
            "purpose": "protocol_fixture",
            "operation": "official_evaluator_gold_self",
            "model_output": False,
        },
        {
            "asset": str(fixtures),
            "purpose": "protocol_fixture",
            "operation": "adversarial_scorer_fixtures",
            "model_output": False,
        },
    ]
    existing = {(item.get("asset"), item.get("operation")) for item in ledger["entries"]}
    ledger["entries"].extend(
        item
        for item in new_entries
        if (item["asset"], item["operation"]) not in existing
    )
    count = ledger.get("v6_confirmatory_eval_count")
    if not isinstance(count, int) or count < 0:
        raise ValueError("access ledger confirmatory count must be a non-negative integer")
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    ledger_path.write_text(json.dumps(ledger, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--evaluator",
        type=Path,
        default=Path("data/protocols/v6/tools/maven_ere_evaluate.py"),
    )
    parser.add_argument(
        "--gold",
        type=Path,
        default=Path("data/processed/maven_ere/valid.jsonl"),
    )
    parser.add_argument(
        "--fixtures",
        type=Path,
        default=Path("tests/fixtures/p1"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/protocols/v6/evaluator"),
    )
    args = parser.parse_args()

    evaluator_hash = _sha256(args.evaluator)
    if evaluator_hash != EVALUATOR_SHA256:
        raise SystemExit(
            f"evaluator hash mismatch: expected {EVALUATOR_SHA256}, got {evaluator_hash}"
        )
    evaluator = _load_evaluator(args.evaluator)

    gold = _load_records(args.gold)
    gold_prediction_records = [gold_to_official_prediction(gold[item]) for item in sorted(gold)]
    gold_prediction = {item["id"]: item for item in gold_prediction_records}
    population = validate_official_predictions(gold, gold_prediction)
    gold_scores = _score(evaluator, gold, gold_prediction)
    for key, value in gold_scores.items():
        is_metric = key.endswith(("_precision", "_recall", "_f1"))
        if is_metric and not math.isclose(value, 100.0, abs_tol=1e-4):
            raise AssertionError(f"gold-self {key} is not 100: {value}")

    fixture_gold_path = args.fixtures / "maven_ere_gold.jsonl"
    fixture_gold = _load_records(fixture_gold_path)
    adversarial: dict[str, dict[str, float]] = {}
    for name in EXPECTED_ADVERSARIAL_F1:
        path = args.fixtures / f"maven_ere_{name}_prediction.jsonl"
        prediction = _load_records(path)
        scores = _score(evaluator, fixture_gold, prediction)
        _assert_expected(scores, EXPECTED_ADVERSARIAL_F1[name], name=name)
        adversarial[name] = scores

    args.output_dir.mkdir(parents=True, exist_ok=True)
    _write_jsonl(args.output_dir / "gold_prediction.jsonl", gold_prediction_records)
    (args.output_dir / "gold_self_metrics.json").write_text(
        json.dumps(
            {
                "evaluator_sha256": evaluator_hash,
                "gold_sha256": _sha256(args.gold),
                "population": population,
                "scores": gold_scores,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (args.output_dir / "adversarial_metrics.json").write_text(
        json.dumps(
            {
                "fixture_gold_sha256": _sha256(fixture_gold_path),
                "expected_f1": EXPECTED_ADVERSARIAL_F1,
                "scores": adversarial,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    _record_access(args.output_dir, gold=args.gold, fixtures=args.fixtures)
    print(
        f"[p1-scorer] PASS: {len(gold)}-doc gold-self + "
        f"{len(adversarial)} adversarial fixtures; candidate={population['candidate_id_digest']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
