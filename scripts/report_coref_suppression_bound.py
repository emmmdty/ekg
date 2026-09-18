#!/usr/bin/env python
"""How much of C5's precision gap a trigger-similarity suppressor could ever close (H1).

`report_coref_error_profile.py` sized the gap and said where it lives: `full` is
1.084 MUC F1 below the joint anchor and **all** of it is precision (.756630 vs
.788430) because recall already overtook it (.846422 vs .832461). It also showed
the over-merged pairs concentrate at high trigger similarity -- 243/419 = 58.0%
at similarity >= 0.8 for `full` against 203/394 = 51.5% for the anchor. H1 asks
whether attaching role compatibility to the *suppression* side could therefore
recover the gap.

That question is decidable without training anything, because suppression can
only ever *split* predicted clusters. So bound it from above:

* **oracle** -- veto only the pairs in the bucket that are genuinely wrong
  (different gold events). No suppressor can do better: it is the bucket's
  entire precision mass with zero recall cost.
* **blind** -- veto every pair in the bucket, right or wrong. That is the same
  rule applied without the oracle's knowledge, and its recall loss is the price
  a real suppressor pays.

Both re-cluster each predicted cluster as the connected components of its
surviving pairs, then hand the result to the organisers' own scorer. A cluster
only splits when the vetoed pairs actually disconnect it, which is the point:
a fused cluster held together by *low*-similarity pairs is out of reach of any
bucket rule, however perfect.

The no-op row must reproduce the arm's recorded MUC F1 or the run aborts.

    uv run python scripts/report_coref_suppression_bound.py \
        --evaluator data/protocols/v6/tools/maven_ere_evaluate.py \
        --gold  runs/.../preflight-r2/data/MAVEN_ERE/internal-dev.jsonl \
        --pred  runs/.../pilot-r2/full/predictions.jsonl \
        --expect-muc-f1 79.9011532125206 \
        --anchor-muc-f1 80.98472 \
        --output runs/.../suppression-bound/full.json
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from itertools import combinations
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from report_coref_error_profile import (  # noqa: E402
    _by_id,
    _load_evaluator,
    official_clusterings,
)

from ekg.nodes.coref import trigger_similarity  # noqa: E402

# The bucket edges the error profile already reports on, so the two tables line
# up row for row. `None` is the no-op control that must reproduce the arm.
TAUS = (None, 1.0, 0.8, 0.6, 0.4, 0.2)


def _components(members: list[str], kept: list[tuple[str, str]]) -> list[list[str]]:
    parent = {m: m for m in members}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for a, b in kept:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb
    groups: dict[str, list[str]] = {}
    for m in members:
        groups.setdefault(find(m), []).append(m)
    return list(groups.values())


def suppress_document(
    gold_record: dict, pred_record: dict, *, tau: float | None, oracle: bool, cross_only: bool
) -> tuple[list[list[str]], int, int]:
    """Predicted clusters after vetoing the bucket; also (vetoed_wrong, vetoed_right)."""
    gold, predicted, mentions = official_clusterings(gold_record, pred_record)
    gold_of = {m: index for index, cluster in enumerate(gold) for m in cluster}

    clusters: list[list[str]] = []
    wrong = right = 0
    for cluster in predicted:
        if len(cluster) < 2:
            continue
        members = sorted(cluster)
        kept: list[tuple[str, str]] = []
        for a, b in combinations(members, 2):
            left, right_m = mentions[a], mentions[b]
            veto = tau is not None and trigger_similarity(left.trigger, right_m.trigger) >= tau
            if veto and cross_only and left.sent_id == right_m.sent_id:
                veto = False
            is_wrong = gold_of[a] != gold_of[b]
            if veto and oracle and not is_wrong:
                veto = False
            if veto:
                wrong += is_wrong
                right += not is_wrong
            else:
                kept.append((a, b))
        clusters.extend(sorted(g) for g in _components(members, kept) if len(g) > 1)
    return clusters, wrong, right


def run_config(
    evaluator, gold: dict[str, dict], pred: dict[str, dict], **kwargs
) -> dict:
    patched: dict[str, dict] = {}
    wrong = right = 0
    for doc_id, pred_record in pred.items():
        clusters, w, r = suppress_document(gold[doc_id], pred_record, **kwargs)
        patched[doc_id] = {**pred_record, "coreference": clusters}
        wrong += w
        right += r
    scores = evaluator.evaluate_coreference(gold, patched)
    return {
        **{k: v for k, v in kwargs.items()},
        "vetoed_wrong_pairs": wrong,
        "vetoed_correct_pairs": right,
        "muc_precision": scores["muc_precision"],
        "muc_recall": scores["muc_recall"],
        "muc_f1": scores["muc_f1"],
        "blanc_f1": scores["blanc_f1"],
    }


def bucket_pairs(
    gold: dict[str, dict], pred: dict[str, dict], *, tau: float, cross_only: bool
) -> list[tuple[str, str, str, bool]]:
    """Every predicted within-cluster pair in the bucket, tagged wrong/right."""
    found = []
    for doc_id, pred_record in pred.items():
        _, predicted, mentions = official_clusterings(gold[doc_id], pred_record)
        for cluster in predicted:
            if len(cluster) < 2:
                continue
            for a, b in combinations(sorted(cluster), 2):
                left, right = mentions[a], mentions[b]
                if trigger_similarity(left.trigger, right.trigger) < tau:
                    continue
                if cross_only and left.sent_id == right.sent_id:
                    continue
                found.append((doc_id, a, b, left.event_id != right.event_id))
    return found


def score_veto(
    evaluator, gold: dict[str, dict], pred: dict[str, dict], veto: set[tuple[str, str, str]]
) -> dict:
    """Re-cluster with exactly `veto` removed, then score with the official scorer."""
    patched: dict[str, dict] = {}
    for doc_id, pred_record in pred.items():
        _, predicted, _ = official_clusterings(gold[doc_id], pred_record)
        clusters: list[list[str]] = []
        for cluster in predicted:
            if len(cluster) < 2:
                continue
            members = sorted(cluster)
            kept = [
                (a, b)
                for a, b in combinations(members, 2)
                if (doc_id, a, b) not in veto
            ]
            clusters.extend(sorted(g) for g in _components(members, kept) if len(g) > 1)
        patched[doc_id] = {**pred_record, "coreference": clusters}
    scores = evaluator.evaluate_coreference(gold, patched)
    return {
        "muc_precision": scores["muc_precision"],
        "muc_recall": scores["muc_recall"],
        "muc_f1": scores["muc_f1"],
        "blanc_f1": scores["blanc_f1"],
    }


def false_veto_budget(
    evaluator, gold: dict[str, dict], pred: dict[str, dict], *, tau: float, cross_only: bool,
    draws: int,
) -> list[dict]:
    """What a suppressor may spend in wrong vetoes before the oracle gain is gone.

    The oracle catch is held fixed (every genuinely wrong pair in the bucket) and
    correct pairs are added to the veto at random. A real suppressor never gets
    the oracle catch, so this is still an upper bound -- but it prices the *other*
    half of the trade, which the blind rows leave unsized.
    """
    pairs = bucket_pairs(gold, pred, tau=tau, cross_only=cross_only)
    wrong = [(d, a, b) for d, a, b, is_wrong in pairs if is_wrong]
    right = [(d, a, b) for d, a, b, is_wrong in pairs if not is_wrong]
    rows = []
    for budget in (0, 25, 50, 100, 150, 200, 300, 400, len(right)):
        if budget > len(right):
            continue
        scored = []
        for draw in range(draws if budget else 1):
            rng = random.Random(13 + draw)
            veto = set(wrong) | set(rng.sample(right, budget))
            scored.append(score_veto(evaluator, gold, pred, veto)["muc_f1"])
        rows.append({
            "false_vetoes": budget,
            "of_correct_pairs": len(right),
            "wrong_vetoes": len(wrong),
            "muc_f1_mean": sum(scored) / len(scored),
            "muc_f1_min": min(scored),
            "muc_f1_max": max(scored),
        })
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evaluator", required=True, type=Path)
    parser.add_argument("--gold", required=True, type=Path)
    parser.add_argument("--pred", required=True, type=Path)
    parser.add_argument("--expect-muc-f1", required=True, type=float,
                        help="the arm's recorded MUC F1; the no-op row must reproduce it")
    parser.add_argument("--anchor-muc-f1", required=True, type=float,
                        help="the bar the bound is judged against")
    parser.add_argument("--budget-tau", type=float, default=0.8,
                        help="bucket the false-veto budget is priced on (default: HARD_SIMILARITY)")
    parser.add_argument("--budget-draws", type=int, default=5,
                        help="random draws per budget point")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    evaluator = _load_evaluator(args.evaluator)
    gold, pred = _by_id(args.gold), _by_id(args.pred)
    if set(gold) != set(pred):
        raise SystemExit(f"gold has {len(gold)} documents, prediction {len(pred)}; ids must match")

    rows = [
        run_config(evaluator, gold, pred, tau=tau, oracle=oracle, cross_only=cross_only)
        for tau in TAUS
        for oracle in (True, False)
        for cross_only in (True, False)
        if not (tau is None and (not oracle or not cross_only))  # one no-op row is enough
    ]

    no_op = rows[0]
    if abs(no_op["muc_f1"] - args.expect_muc_f1) > 1e-9:
        raise SystemExit(
            f"no-op row scores {no_op['muc_f1']} but the arm recorded {args.expect_muc_f1}"
        )
    print(f"[bound] ✔ no-op row reproduces the arm: MUC F1 {no_op['muc_f1']:.6f}")

    print(f"\n  {'bucket':>10} {'suppressor':>10} {'pairs':>9} "
          f"{'vetoed w/r':>14} {'MUC P':>8} {'MUC R':>8} {'MUC F1':>9} {'vs anchor':>10}")
    for row in rows:
        tau = "none" if row["tau"] is None else f">= {row['tau']:g}"
        kind = "oracle" if row["oracle"] else "blind"
        scope = "cross-sent" if row["cross_only"] else "any pair"
        print(f"  {tau:>10} {kind:>10} {scope:>9} "
              f"{row['vetoed_wrong_pairs']:>7}/{row['vetoed_correct_pairs']:<6} "
              f"{row['muc_precision']:>8.4f} {row['muc_recall']:>8.4f} {row['muc_f1']:>9.5f} "
              f"{row['muc_f1'] - args.anchor_muc_f1:>+10.3f}")

    budget_rows = false_veto_budget(
        evaluator, gold, pred, tau=args.budget_tau, cross_only=True, draws=args.budget_draws
    )
    print(f"\n  false-veto budget at similarity >= {args.budget_tau:g}, cross-sentence "
          f"(oracle catch held fixed at {budget_rows[0]['wrong_vetoes']} wrong pairs; "
          f"{budget_rows[0]['of_correct_pairs']} correct pairs in the bucket)")
    print(f"  {'false vetoes':>13} {'MUC F1 mean':>13} {'min':>9} {'max':>9} {'vs arm':>9} "
          f"{'vs anchor':>10}")
    for row in budget_rows:
        print(f"  {row['false_vetoes']:>13} {row['muc_f1_mean']:>13.5f} {row['muc_f1_min']:>9.5f} "
              f"{row['muc_f1_max']:>9.5f} {row['muc_f1_mean'] - args.expect_muc_f1:>+9.3f} "
              f"{row['muc_f1_mean'] - args.anchor_muc_f1:>+10.3f}")

    best = max(rows, key=lambda r: r["muc_f1"])
    reachable = best["muc_f1"] >= args.anchor_muc_f1
    print(f"\n[bound] ceiling {best['muc_f1']:.5f} at tau={best['tau']}, "
          f"{'oracle' if best['oracle'] else 'blind'}, "
          f"{'cross-sentence' if best['cross_only'] else 'any pair'} "
          f"=> anchor {args.anchor_muc_f1} is {'REACHABLE' if reachable else 'OUT OF REACH'}")

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(
                {
                    "expect_muc_f1": args.expect_muc_f1,
                    "anchor_muc_f1": args.anchor_muc_f1,
                    "anchor_reachable_by_suppression": reachable,
                    "ceiling": best,
                    "rows": rows,
                    "false_veto_budget": budget_rows,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        print(f"[bound] wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
