#!/usr/bin/env python
"""Why does cross-sentence causal recall stall at ~25 F1?

`docs/results/PHASE_A.md` has the shape of the problem already: window encoding
lifted cross-sentence causal from 19.99 to 24.11, and **three further rounds of
optimisation moved it by under a point** while same-sentence sits at 38.07. The
same file rules out the structural suspect -- only 3.3% of gold causal pairs
straddle an encoder window -- and concludes the remaining gap "must be found
somewhere other than window splitting".

This is the next hypothesis, measured before anything is built on it. The pair
head reads two pooled trigger vectors, their product, their difference and a
distance bucket. Nothing in that feature points at the text *between* the two
triggers, which for a cross-sentence pair is where the discourse connective
lives. If the model already recovers cue-bearing pairs better than cue-less
ones, it is finding the cue anyway and this hypothesis is dead; if recall is
flat across that contrast, a pair-specific context representation has something
real to recover.

Gold pairs are enumerated through `gold_to_official_prediction`, the same
expansion the official scorer uses, so "missed" here means missed by the
number we report -- not by some private re-derivation of the candidate set.

    .venv/bin/python scripts/report_relation_crosssentence_profile.py \
        --gold runs/stages/A3/.../preflight/data/MAVEN_ERE/valid.jsonl \
        --pred runs/stages/A3/reproduction_base/seed-13/official_predictions.jsonl
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from ekg.relations.crosssentence import (
    CAUSAL_CUES,
    ORDERING_CUES,
    MentionSpan,
    between_tokens,
    find_cues,
)
from ekg.relations.maven_ere_official import gold_to_official_prediction


def read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def mention_spans(record: dict) -> dict[str, MentionSpan]:
    spans: dict[str, MentionSpan] = {}
    for event in record.get("events", []):
        for mention in event.get("mention", []):
            start, end = mention["offset"]
            spans[str(mention["id"])] = MentionSpan(int(mention["sent_id"]), start, end)
    return spans


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gold", required=True, type=Path)
    parser.add_argument("--pred", required=True, type=Path)
    parser.add_argument("--limit", type=int, help="first N documents (verification run)")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    records = read_jsonl(args.gold)
    if args.limit:
        records = records[: args.limit]
    predictions = {str(r["id"]): r for r in read_jsonl(args.pred)}
    missing = [str(r["id"]) for r in records if str(r["id"]) not in predictions]
    if missing:
        raise SystemExit(f"prediction file is missing {len(missing)} of {len(records)} documents")

    # cell -> [n_gold, n_recovered]
    cells: dict[tuple[str, str], list[int]] = {}
    distance: dict[int, list[int]] = {}
    cue_counts: Counter[str] = Counter()
    n_pairs = 0

    for record in records:
        spans = mention_spans(record)
        sentences = record["tokens"]
        gold = gold_to_official_prediction(record)["causal_relations"]
        predicted_by_subtype = {
            subtype: {tuple(pair) for pair in pairs}
            for subtype, pairs in (
                predictions[str(record["id"])].get("causal_relations") or {}
            ).items()
        }
        for subtype, pairs in gold.items():
            emitted = predicted_by_subtype.get(subtype, set())
            for pair in pairs:
                head, tail = str(pair[0]), str(pair[1])
                if head not in spans or tail not in spans:
                    raise SystemExit(f"{record['id']}: gold pair references unknown mention")
                a, b = spans[head], spans[tail]
                n_pairs += 1
                position = "same" if a.sent_id == b.sent_id else "cross"
                tokens = between_tokens(sentences, a, b)
                causal = find_cues(tokens, CAUSAL_CUES)
                ordering = find_cues(tokens, ORDERING_CUES)
                cue = "causal_cue" if causal else ("ordering_cue" if ordering else "no_cue")
                cue_counts.update(causal)
                recovered = int(tuple(pair) in emitted)
                cell = cells.setdefault((position, cue), [0, 0])
                cell[0] += 1
                cell[1] += recovered
                bucket = min(abs(a.sent_id - b.sent_id), 6)
                row = distance.setdefault(bucket, [0, 0])
                row[0] += 1
                row[1] += recovered

    print(f"{len(records)} documents, {n_pairs} gold causal mention-pairs\n")
    print(f"{'位置':<8}{'线索':<14}{'gold':>8}{'召回数':>8}{'recall':>9}")
    print("-" * 47)
    for position in ("same", "cross"):
        for cue in ("causal_cue", "ordering_cue", "no_cue"):
            n, hit = cells.get((position, cue), [0, 0])
            if n:
                print(f"{position:<8}{cue:<14}{n:>8}{hit:>8}{hit / n:>9.4f}")
    print("-" * 47)
    cue_names = ("causal_cue", "ordering_cue", "no_cue")
    for position in ("same", "cross"):
        n = sum(cells.get((position, c), [0, 0])[0] for c in cue_names)
        hit = sum(cells.get((position, c), [0, 0])[1] for c in cue_names)
        if n:
            print(f"{position:<8}{'(全部)':<14}{n:>8}{hit:>8}{hit / n:>9.4f}")

    print(f"\n{'句距':>6}{'gold':>9}{'召回数':>8}{'recall':>9}")
    for bucket in sorted(distance):
        n, hit = distance[bucket]
        label = f"{bucket}" if bucket < 6 else "6+"
        print(f"{label:>6}{n:>9}{hit:>8}{hit / n:>9.4f}")

    print("\n最常见的因果线索词:", cue_counts.most_common(8))

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(
                {
                    "n_documents": len(records),
                    "n_gold_pairs": n_pairs,
                    "cells": {f"{p}|{c}": v for (p, c), v in cells.items()},
                    "distance": {str(k): v for k, v in distance.items()},
                    "cue_counts": dict(cue_counts),
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        print(f"\n[crosssentence] wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
