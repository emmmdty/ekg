#!/usr/bin/env python
"""How much of MAVEN-FACT's headline metric is actually measurable?

`macro_f1 = .4823` is one number over five classes whose supports differ by three
orders of magnitude (CT+ 16,868 vs Uu 20). Before designing a mechanism it is worth
knowing what a *difference* in that number can mean: this script reports, for the
frozen valid split,

  1. how much macro-F1 moves when a single instance of each class flips, and
  2. the document-cluster bootstrap CI of macro-F1 and of several restrictions of it.

A method whose reported gain is smaller than the CI half-width has not been shown to
differ from the baseline on this split, however plausible its mechanism.
"""

from __future__ import annotations

import argparse
import json
import random
from collections import Counter, defaultdict
from pathlib import Path

CLASSES = ("CT+", "PS+", "CT-", "PS-", "Uu")
VARIANTS = {
    "five_class_official": CLASSES,
    "drop_rare_classes": ("CT+", "PS+", "CT-"),
    "non_ctplus": ("PS+", "CT-", "PS-"),
    "supported_only": ("PS+", "CT-"),
}


def _macro(keys, gold, pred, classes) -> float:
    tp, fp, fn = Counter(), Counter(), Counter()
    for key in keys:
        g, p = gold[key], pred[key]
        if g == p:
            tp[g] += 1
        else:
            fp[p] += 1
            fn[g] += 1
    scores = []
    for cls in classes:
        precision = tp[cls] / (tp[cls] + fp[cls]) if tp[cls] + fp[cls] else 0.0
        recall = tp[cls] / (tp[cls] + fn[cls]) if tp[cls] + fn[cls] else 0.0
        scores.append(2 * precision * recall / (precision + recall) if precision + recall else 0.0)
    return sum(scores) / len(scores)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gold", required=True, type=Path, help="MAVEN-FACT valid jsonl")
    parser.add_argument("--predicted-labels", required=True, type=Path)
    parser.add_argument("--resamples", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=13)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    from ekg.relations.data.maven_fact import load_maven_fact

    pred = json.loads(args.predicted_labels.read_text(encoding="utf-8"))
    gold: dict[str, str] = {}
    by_doc: dict[str, list[str]] = defaultdict(list)
    for doc in load_maven_fact(args.gold):
        for mention in doc.mentions:
            key = mention.mention_id
            if key not in pred:
                key = f"{doc.doc_id}::{mention.mention_id}"
            if key not in pred:
                continue
            gold[key] = mention.factuality
            by_doc[doc.doc_id].append(key)
    if not gold:
        raise SystemExit("no mention IDs matched between gold and the prediction dump")

    keys = list(gold)
    support = Counter(gold.values())
    rng = random.Random(args.seed)
    docs = list(by_doc)
    samples = [rng.choices(docs, k=len(docs)) for _ in range(args.resamples)]

    report: dict[str, object] = {
        "n_mentions": len(keys),
        "n_documents": len(docs),
        "support": dict(support),
        "resamples": args.resamples,
        "variants": {},
    }
    print(f"{'metric':<24}{'point':>9}{'ci_half_width':>15}{'relative':>10}")
    print("-" * 58)
    for name, classes in VARIANTS.items():
        point = _macro(keys, gold, pred, classes)
        values = sorted(
            _macro([k for d in s for k in by_doc[d]], gold, pred, classes) for s in samples
        )
        lo = values[int(0.025 * len(values))]
        hi = values[int(0.975 * len(values))]
        half = (hi - lo) / 2
        report["variants"][name] = {
            "classes": list(classes),
            "point": point,
            "ci_low": lo,
            "ci_high": hi,
            "half_width": half,
        }
        print(f"{name:<24}{point:>9.4f}{half:>15.4f}{half / point:>9.1%}")

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
        args.output.write_text(payload, encoding="utf-8")
        print(f"\n[metric-power] wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
