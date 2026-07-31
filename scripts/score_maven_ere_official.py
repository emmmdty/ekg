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

`evaluate.py` is the organisers' file and is deliberately **not vendored** into
this repo; pass its path. Fetch it once with:

    curl -o /tmp/maven_evaluate.py \\
      https://raw.githubusercontent.com/THU-KEG/MAVEN-ERE/main/evaluate.py

Predictions must be in the official shape, which
`scripts/build_maven_ere_submission.py --from-labeled` produces from a labelled
split. Verified 2026-07-30 by feeding gold back through that shape: this script
returned 100.0 on all four metrics.

    uv run python scripts/score_maven_ere_official.py \\
        --evaluator /tmp/maven_evaluate.py \\
        --gold data/processed/maven_ere/valid.jsonl \\
        --pred runs/relations/valid_prediction.jsonl
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path


def _load_evaluator(path: Path):
    spec = importlib.util.spec_from_file_location("maven_ere_evaluate", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"cannot import an evaluator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _by_id(path: Path) -> dict[str, dict]:
    records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    by_id = {r["id"]: r for r in records}
    if len(by_id) != len(records):
        raise SystemExit(
            f"{path} has {len(records)} lines but only {len(by_id)} unique ids -- "
            "a truncated or concatenated file, not a valid prediction set"
        )
    return by_id


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evaluator", required=True, type=Path,
                        help="path to the organisers' evaluate.py (not vendored here)")
    parser.add_argument("--gold", required=True, type=Path, help="labelled split, e.g. valid.jsonl")
    parser.add_argument("--pred", required=True, type=Path, help="predictions in official shape")
    parser.add_argument("--output", type=Path, help="write the scores as JSON here")
    args = parser.parse_args()

    evaluator = _load_evaluator(args.evaluator)
    gold, pred = _by_id(args.gold), _by_id(args.pred)
    missing = set(gold) - set(pred)
    if missing:
        # Scored as all-NONE by the official code, which silently costs recall.
        print(f"[score] ⚠️ {len(missing)} gold documents have no prediction; they count as misses")
    scored = {k: v for k, v in gold.items() if k in pred}

    result: dict[str, float] = {}
    for family in ("temporal", "causal", "subevent"):
        result.update(evaluator.evaluate(scored, pred, family))
    result.update(evaluator.evaluate_coreference(scored, pred))

    print(f"[score] {len(scored)} documents, official MAVEN-ERE protocol")
    for key, value in result.items():
        print(f"  {key:28s} {value:.2f}")

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(f"[score] wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
