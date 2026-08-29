#!/usr/bin/env python
"""How much of MAVEN-FACT's headline metric is actually measurable?

`macro_f1 = .4823` is one number over five classes whose supports differ by three
orders of magnitude (CT+ 16,868 vs Uu 20). Before designing a mechanism it is worth
knowing what a *difference* in that number can mean: this script reports, for the
frozen valid split,

  1. the document-cluster bootstrap CI of macro-F1 and of several restrictions of it, and
  2. the *paired* minimum detectable effect: inject a known improvement of k rare-class
     instances and find the smallest k whose paired CI excludes zero.

The two are very different and conflating them is a trap. The absolute CI (~±0.043 here)
says how uncertain one system's score is; the paired MDE (~5 instances, ~+0.016 here)
says how small a difference *between two systems scored on the same instances* is still
detectable, and is far more sensitive because the two systems' errors are correlated.

Practical consequence: a same-protocol re-run of a baseline can be compared with power,
while a comparison against a published number on a different split cannot be — the
pairing is exactly what is lost. Cf. Card et al., "With Little Power Comes Great
Responsibility" (EMNLP 2020), which recommends reporting the minimum detectable effect.
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


def _class_f1s(keys, gold, pred, classes) -> list[float]:
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
    return scores


def _macro(keys, gold, pred, classes) -> float:
    scores = _class_f1s(keys, gold, pred, classes)
    return sum(scores) / len(scores)


def _paired_delta(gold, pred_a, pred_b, keys, by_doc, samples, classes) -> dict:
    """B − A on the same instances, with a document-cluster bootstrap CI.

    This is the comparison the phase contract's decision rule is written on: the
    two systems make errors on the *same* mentions, so the paired interval is
    far narrower than either system's absolute CI. Reporting the two point
    estimates and eyeballing the gap is the mistake this replaces.
    """
    point = _macro(keys, gold, pred_b, classes) - _macro(keys, gold, pred_a, classes)
    deltas = sorted(
        _macro([x for d in s for x in by_doc[d]], gold, pred_b, classes)
        - _macro([x for d in s for x in by_doc[d]], gold, pred_a, classes)
        for s in samples
    )
    lo = deltas[int(0.025 * len(deltas))]
    hi = deltas[int(0.975 * len(deltas))]
    return {"delta": point, "ci_low": lo, "ci_high": hi, "b_wins": lo > 0, "b_loses": hi < 0}


def _paired_mde(gold, pred, by_doc, samples, steps) -> list[dict]:
    """Smallest injected improvement whose paired document-cluster CI excludes zero."""
    import random

    keys = list(gold)
    fixable = [k for k in keys if gold[k] in ("PS-", "Uu") and pred[k] != gold[k]]
    random.Random(13).shuffle(fixable)
    rows = []
    for k in steps:
        if k > len(fixable):
            break
        improved = dict(pred)
        for key in fixable[:k]:
            improved[key] = gold[key]
        point = _macro(keys, gold, improved, CLASSES) - _macro(keys, gold, pred, CLASSES)
        deltas = sorted(
            _macro([x for d in s for x in by_doc[d]], gold, improved, CLASSES)
            - _macro([x for d in s for x in by_doc[d]], gold, pred, CLASSES)
            for s in samples
        )
        lo = deltas[int(0.025 * len(deltas))]
        hi = deltas[int(0.975 * len(deltas))]
        rows.append(
            {"instances_fixed": k, "delta": point, "ci_low": lo, "ci_high": hi, "detected": lo > 0}
        )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gold", required=True, type=Path, help="MAVEN-FACT valid jsonl")
    parser.add_argument("--predicted-labels", required=True, type=Path)
    parser.add_argument(
        "--predicted-labels-b",
        type=Path,
        help=(
            "a second system's label dump over the same mentions; turns on the paired "
            "document-cluster bootstrap of (B - A), which is the axis the D3 decision "
            "rule is written on"
        ),
    )
    parser.add_argument("--resamples", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=13)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    from ekg.relations.data.maven_fact import load_maven_fact

    pred = json.loads(args.predicted_labels.read_text(encoding="utf-8"))
    pred_b = (
        json.loads(args.predicted_labels_b.read_text(encoding="utf-8"))
        if args.predicted_labels_b
        else None
    )
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
    if pred_b is not None:
        # Pairing is the whole point: comparing two systems scored on different
        # mention sets would silently turn a paired test into an unpaired one.
        missing = [k for k in gold if k not in pred_b]
        if missing:
            raise SystemExit(
                f"{args.predicted_labels_b} is missing {len(missing)} of the "
                f"{len(gold)} mentions system A predicted; the comparison would not be paired"
            )

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
        # A variant can score exactly 0 (e.g. a system that only ever predicts
        # CT+ scores 0 on `non_ctplus`); the relative column is undefined there
        # and must not take the whole report down with it.
        relative = f"{half / point:>9.1%}" if point else f"{'--':>9}"
        print(f"{name:<24}{point:>9.4f}{half:>15.4f}{relative}")

    if pred_b is not None:
        print("\n--- paired A vs B on the same mentions (B - A) ---")
        print(f"A = {args.predicted_labels}")
        print(f"B = {args.predicted_labels_b}")
        print(f"{'metric':<24}{'A':>9}{'B':>9}{'delta':>10}{'ci_low':>10}{'ci_high':>10}{'':>8}")
        print("-" * 80)
        comparison: dict[str, object] = {}
        for name, classes in VARIANTS.items():
            row = _paired_delta(gold, pred, pred_b, keys, by_doc, samples, classes)
            verdict = "B>A" if row["b_wins"] else ("B<A" if row["b_loses"] else "tie")
            comparison[name] = row
            print(
                f"{name:<24}{_macro(keys, gold, pred, classes):>9.4f}"
                f"{_macro(keys, gold, pred_b, classes):>9.4f}"
                f"{row['delta']:>10.4f}{row['ci_low']:>10.4f}{row['ci_high']:>10.4f}{verdict:>8}"
            )
        # Per class, because a macro win carried entirely by CT+ is not a win,
        # and a class the anchor scores non-zero must not collapse to zero.
        a_f1 = _class_f1s(keys, gold, pred, CLASSES)
        b_f1 = _class_f1s(keys, gold, pred_b, CLASSES)
        print(f"\n{'class':<8}{'n':>8}{'A F1':>9}{'B F1':>9}{'delta':>9}")
        print("-" * 43)
        for cls, a, b in zip(CLASSES, a_f1, b_f1, strict=True):
            print(f"{cls:<8}{support[cls]:>8}{a:>9.4f}{b:>9.4f}{b - a:>9.4f}")
        collapsed = [c for c, a, b in zip(CLASSES, a_f1, b_f1, strict=True) if a > 0 and b == 0]
        if collapsed:
            print(f"\n*** rare-class guardrail: B collapsed {collapsed} to zero F1 ***")
        report["paired_comparison"] = {
            "system_a": str(args.predicted_labels),
            "system_b": str(args.predicted_labels_b),
            "variants": comparison,
            "per_class_f1_a": dict(zip(CLASSES, a_f1, strict=True)),
            "per_class_f1_b": dict(zip(CLASSES, b_f1, strict=True)),
            "collapsed_classes": collapsed,
        }

    print("\n--- paired minimum detectable effect (same instances, both systems) ---")
    print(f"{'instances fixed':>16}{'delta':>10}{'ci_low':>10}{'ci_high':>10}{'detected':>10}")
    mde_rows = _paired_mde(gold, pred, by_doc, samples, (1, 2, 3, 5, 8, 12, 16, 20, 30))
    for row in mde_rows:
        print(
            f"{row['instances_fixed']:>16}{row['delta']:>10.4f}"
            f"{row['ci_low']:>10.4f}{row['ci_high']:>10.4f}"
            f"{'yes' if row['detected'] else 'no':>10}"
        )
    detected = [r for r in mde_rows if r["detected"]]
    if detected:
        first = detected[0]
        print(
            f"\nMDE = {first['instances_fixed']} rare-class instances "
            f"(delta macro-F1 ~ {first['delta']:.4f})"
        )
    report["paired_mde"] = mde_rows

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
        args.output.write_text(payload, encoding="utf-8")
        print(f"\n[metric-power] wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
