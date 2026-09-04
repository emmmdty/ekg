#!/usr/bin/env python
"""Score predictions with MAVEN-ERE's **own** evaluator instead of ours.

Why this exists: our `evaluate_relation_pairs` and the official scorer do not
measure the same thing. The official one enumerates every ordered mention pair in
a document, expands each gold cluster-level relation to *all* mention pairs across
the two clusters, appends TIMEX ids for the temporal task, and micro-averages over
the positive labels only. Reporting our own numbers against figures from the
MAVEN-ERE paper is therefore not a like-for-like comparison -- this closes that
gap, and it is the only way left to do so: the CodaLab test server stopped
accepting submissions (2026-07-30, `Submissions have been disabled by admins`),
so **valid scored by the official script is the comparable number we can get**.

`evaluate.py` is the organisers' file and is restored at its P1-pinned path by
`scripts/fetch_p1_assets.py`. Override the path only for an explicit audit.

    curl -o /tmp/maven_evaluate.py \\
      https://raw.githubusercontent.com/THU-KEG/MAVEN-ERE/main/evaluate.py

Predictions must be in the official shape. Gold-self fixtures are produced by
`scripts/verify_p1_scorer.py`; `build_maven_ere_submission.py --from-labeled`
runs a model and is not a gold converter.

    uv run python scripts/score_maven_ere_official.py \\
        --evaluator data/protocols/v6/tools/maven_ere_evaluate.py \\
        --gold data/processed/maven_ere/valid.jsonl \\
        --pred runs/relations/valid_prediction.jsonl \\
        --candidate-digest <frozen-candidate-sha256>
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

from ekg.core.stage_bundle import sha256_file as _sha256
from ekg.relations.maven_ere_official import (
    OfficialProtocolError,
    records_by_id,
    validate_official_predictions,
)

_PINNED_EVALUATOR = Path("data/protocols/v6/tools/maven_ere_evaluate.py")


def _load_evaluator(path: Path):
    spec = importlib.util.spec_from_file_location("maven_ere_evaluate", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"cannot import an evaluator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _by_id(path: Path) -> dict[str, dict]:
    records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    try:
        return records_by_id(records, source=str(path))
    except OfficialProtocolError as exc:
        raise SystemExit(str(exc)) from exc


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--evaluator",
        type=Path,
        default=_PINNED_EVALUATOR,
        help=f"organisers' evaluate.py (default: {_PINNED_EVALUATOR})",
    )
    parser.add_argument(
        "--source-lock",
        type=Path,
        default=Path("data/protocols/v6/source_lock.json"),
        help="P1 source lock whose evaluator hash is mandatory",
    )
    parser.add_argument("--gold", required=True, type=Path, help="labelled split, e.g. valid.jsonl")
    parser.add_argument("--pred", required=True, type=Path, help="predictions in official shape")
    parser.add_argument("--output", type=Path, help="write the scores as JSON here")
    parser.add_argument(
        "--candidate-digest",
        required=True,
        help="expected frozen candidate population SHA-256; mismatch is fatal",
    )
    args = parser.parse_args()

    source_lock = json.loads(args.source_lock.read_text(encoding="utf-8"))
    expected_evaluator_hash = source_lock["evaluator"]["sha256"]
    evaluator_hash = _sha256(args.evaluator)
    if evaluator_hash != expected_evaluator_hash:
        raise SystemExit(
            "evaluator hash mismatch: "
            f"expected {expected_evaluator_hash}, got {evaluator_hash}"
        )
    evaluator = _load_evaluator(args.evaluator)
    gold, pred = _by_id(args.gold), _by_id(args.pred)
    try:
        population = validate_official_predictions(
            gold,
            pred,
            expected_candidate_digest=args.candidate_digest,
        )
    except OfficialProtocolError as exc:
        raise SystemExit(f"official protocol validation failed: {exc}") from exc

    result: dict[str, float] = {}
    for family in ("temporal", "causal", "subevent"):
        result.update(evaluator.evaluate(gold, pred, family))
    result.update(evaluator.evaluate_coreference(gold, pred))

    print(
        f"[score] {len(gold)} documents, official MAVEN-ERE protocol, "
        f"candidate_digest={population['candidate_id_digest']}"
    )
    for key, value in result.items():
        print(f"  {key:28s} {value:.2f}")

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        output = {
            "schema_version": "ekg.maven_ere_official_metrics.v2",
            "scores": result,
            "population": population,
            "hashes": {
                "evaluator": evaluator_hash,
                "gold": _sha256(args.gold),
                "predictions": _sha256(args.pred),
                "source_lock": _sha256(args.source_lock),
            },
            "command_argv": sys.argv,
        }
        args.output.write_text(
            json.dumps(output, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(f"[score] wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
