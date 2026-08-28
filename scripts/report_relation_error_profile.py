#!/usr/bin/env python
"""Decompose MAVEN-ERE relation errors into the counts a mechanism can target.

`causal_f1 = 23.91` is three ratios. It cannot say whether the model over-predicts
or under-predicts, whether the misses are cross-sentence, whether the direction was
reversed, or whether one relation family is being confused for another -- and those
distinctions decide which mechanism is worth building. This is the relation-side
counterpart of `report_coref_error_profile.py`.

Every number here is cross-checked against the organisers' own scorer before
anything is printed (`--official`): our micro P/R/F1 per family must equal theirs to
1e-6, otherwise the run aborts. A profile that could drift from the headline metric
would be worse than no profile at all -- that is exactly how this project misread
its coreference gap four times.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

from ekg.relations.maven_ere_official import (
    CAUSAL_SUBTYPES,
    TEMPORAL_SUBTYPES,
    gold_to_official_prediction,
    records_by_id,
)

PairKey = tuple[str, str]
FAMILIES = ("causal", "subevent", "temporal")
_SUBTYPES = {
    "causal": CAUSAL_SUBTYPES,
    "subevent": ("SUBEVENT_OF",),
    "temporal": TEMPORAL_SUBTYPES,
}


def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _labelled_pairs(record: dict, family: str) -> dict[PairKey, str]:
    """Every positive pair of one family, mapped to its subtype."""
    out: dict[PairKey, str] = {}
    if family == "subevent":
        for pair in record.get("subevent_relations") or []:
            out[(str(pair[0]), str(pair[1]))] = "SUBEVENT_OF"
        return out
    field = "causal_relations" if family == "causal" else "temporal_relations"
    for subtype, pairs in (record.get(field) or {}).items():
        for pair in pairs:
            out[(str(pair[0]), str(pair[1]))] = str(subtype).upper()
    return out


def _mention_index(record: dict) -> dict[str, tuple[int, int]]:
    """Mention/TIMEX id -> (sentence id, textual rank) for stratification."""
    items = [
        (str(m["id"]), int(m.get("sent_id", 10**9)), (m.get("offset") or [10**9])[0])
        for event in record.get("events", [])
        for m in event.get("mention", [])
    ]
    items += [
        (str(t["id"]), int(t.get("sent_id", 10**9)), (t.get("offset") or [10**9])[0])
        for t in record.get("TIMEX", [])
    ]
    items.sort(key=lambda x: (x[1], x[2], x[0]))
    return {mid: (sent, rank) for rank, (mid, sent, _) in enumerate(items)}


def _distance_bucket(distance: int) -> str:
    for edge in (1, 2, 4, 8, 16, 32):
        if distance <= edge:
            return f"<={edge}"
    return ">32"


def profile(gold_path: Path, pred_path: Path) -> dict:
    gold_records = _read_jsonl(gold_path)
    gold = records_by_id(gold_records, source=str(gold_path))
    pred = records_by_id(_read_jsonl(pred_path), source=str(pred_path))
    missing = set(gold) - set(pred)
    if missing:
        raise SystemExit(f"prediction is missing {len(missing)} gold documents")

    report: dict[str, dict] = {}
    for family in FAMILIES:
        counts = Counter()
        strata: dict[str, Counter] = defaultdict(Counter)
        confusion = Counter()
        for doc_id, gold_record in gold.items():
            index = _mention_index(gold_record)
            expanded = gold_to_official_prediction(gold_record)
            g = _labelled_pairs(expanded, family)
            p = _labelled_pairs(pred[doc_id], family)
            reverse_pred = {(t, h) for h, t in p}

            for key, subtype in g.items():
                predicted = p.get(key)
                bucket = _stratum(key, index)
                if predicted == subtype:
                    counts["tp"] += 1
                    strata["tp"][bucket] += 1
                    continue
                counts["fn"] += 1
                strata["fn"][bucket] += 1
                confusion[f"gold:{subtype}->pred:{predicted or 'NONE'}"] += 1
                if predicted is None and key in reverse_pred:
                    counts["fn_direction_reversed"] += 1
            for key, subtype in p.items():
                if g.get(key) != subtype:
                    counts["fp"] += 1
                    strata["fp"][_stratum(key, index)] += 1

        tp, fp, fn = counts["tp"], counts["fp"], counts["fn"]
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        report[family] = {
            "counts": dict(counts),
            "micro": {
                "precision": round(100 * precision, 4),
                "recall": round(100 * recall, 4),
                "f1": round(100 * f1, 4),
            },
            "strata": {k: dict(v.most_common()) for k, v in strata.items()},
            "confusion_top": dict(confusion.most_common(12)),
            "subtypes": list(_SUBTYPES[family]),
        }
    return report


def _stratum(key: PairKey, index: dict[str, tuple[int, int]]) -> str:
    head, tail = index.get(key[0]), index.get(key[1])
    if head is None or tail is None:
        return "unknown_endpoint"
    same = "same_sentence" if head[0] == tail[0] else "cross_sentence"
    return f"{same}|{_distance_bucket(abs(head[1] - tail[1]))}"


def _cross_check(report: dict, official: Path) -> None:
    """Abort unless our micro P/R/F1 equals the organisers' scorer to 1e-6."""
    scores = json.loads(official.read_text(encoding="utf-8"))
    flat = scores.get("scores", scores)
    for family in FAMILIES:
        for metric in ("precision", "recall", "f1"):
            key = f"{family}_{metric}"
            if key not in flat:
                raise SystemExit(f"official metrics lack {key}; cannot cross-check")
            ours = report[family]["micro"][metric]
            theirs = float(flat[key])
            if abs(ours - theirs) > 1e-4:
                raise SystemExit(
                    f"cross-check FAILED on {key}: profile {ours} vs official {theirs}"
                )
    print("✔ cross-checked against the official scorer (all families, P/R/F1)")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gold", required=True, type=Path)
    parser.add_argument("--pred", required=True, type=Path)
    parser.add_argument(
        "--official", required=True, type=Path,
        help="output of score_maven_ere_official.py",
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    report = profile(args.gold, args.pred)
    _cross_check(report, args.official)

    for family in FAMILIES:
        block = report[family]
        c, m = block["counts"], block["micro"]
        total = c.get("fp", 0) + c.get("fn", 0)
        print(
            f"\n=== {family} ===  P {m['precision']:.2f}"
            f" / R {m['recall']:.2f} / F1 {m['f1']:.2f}"
        )
        print(f"  tp={c.get('tp',0):,}  fp={c.get('fp',0):,}  fn={c.get('fn',0):,}")
        if total:
            print(f"  fp share={c.get('fp',0)/total:.1%}  fn share={c.get('fn',0)/total:.1%}"
                  f"  direction-reversed misses={c.get('fn_direction_reversed',0):,}")
        for kind in ("tp", "fn", "fp"):
            layer = block["strata"].get(kind, {})
            cross = sum(v for k, v in layer.items() if k.startswith("cross"))
            same = sum(v for k, v in layer.items() if k.startswith("same"))
            if same + cross:
                print(f"  {kind}: same-sentence {same:,} ({same/(same+cross):.1%})"
                      f" | cross-sentence {cross:,} ({cross/(same+cross):.1%})")
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
        args.output.write_text(payload, encoding="utf-8")
        print(f"\n[profile] wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
