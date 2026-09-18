#!/usr/bin/env python
"""Can the role-compatibility signal we already have pay C-11's price? (C-12)

C-11 turned the second design cycle into one number. Suppression *can* close the
gap -- vetoing the 213 genuinely wrong pairs in the >= 0.8 cross-sentence bucket
lifts `full` from 79.90115 to 84.64223 -- but the bucket holds 699 correct pairs
beside them, so a suppressor must be right about 41.5% of the time on what it
vetoes just to reach the anchor, against a 23.36% base rate.

That is checkable before any training, because `nodes/role_uncertainty.py`
already computes role compatibility without a model: `incompatible` fires when
some role has fillers on both sides that share no content token. So run the
existing signal as a suppressor over the same bucket and price it:

* **rule** -- veto exactly the pairs the incompatibility rule fires on;
* **ranking** -- veto the k pairs with the weakest role agreement (mean token
  Jaccard over the roles both sides filled), sweeping k. Pairs where no role is
  comparable rank last: the extractor declining to answer is not evidence.

Both are re-clustered and scored by the organisers' evaluator through C-11's
`score_veto`, so the numbers land on the same axis as the bound. No training, no
threshold fitted on anything -- this asks whether the signal is worth a GPU, and
a `verdict` of "do not train" is the expected kind of answer.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from report_coref_error_profile import _by_id, _load_evaluator  # noqa: E402
from report_coref_suppression_bound import bucket_pairs, score_veto  # noqa: E402

from ekg.core.io import read_jsonl  # noqa: E402
from ekg.nodes.predicted_arguments import apply_predicted_arguments  # noqa: E402
from ekg.nodes.role_uncertainty import ROLE_NAMES, _fillers, _tokens  # noqa: E402
from ekg.relations.data.maven_ere import _parse_document  # noqa: E402


def _bare(event_id: str) -> str:
    return event_id.split("::", 1)[1] if "::" in event_id else event_id


def load_nodes(gold_path: Path, arguments_path: Path) -> dict[str, object]:
    """Mention id -> EventNode carrying the extractor's predicted arguments."""
    docs = [_parse_document(record) for record in read_jsonl(gold_path)]
    apply_predicted_arguments(docs, arguments_path, allow_extra=True)
    nodes = {}
    for doc in docs:
        for node in doc.nodes:
            nodes[_bare(node.event_id)] = node
    return nodes


def pair_evidence(head, tail) -> tuple[bool, float | None]:
    """(`incompatible`, mean token Jaccard over comparable roles or None).

    Mirrors `incompatible_role_merges` for the flag; the agreement score only
    averages roles where both sides actually produced a filler, so a pair the
    extractor said nothing about scores `None` rather than a misleading zero.
    """
    incompatible = False
    agreements: list[float] = []
    for role in ROLE_NAMES:
        left, right = _fillers(head, role), _fillers(tail, role)
        if not left or not right:
            continue
        left_tokens, right_tokens = _tokens(left), _tokens(right)
        union = left_tokens | right_tokens
        agreements.append(len(left_tokens & right_tokens) / len(union) if union else 0.0)
        if not (left_tokens & right_tokens):
            incompatible = True
    return incompatible, (sum(agreements) / len(agreements) if agreements else None)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evaluator", required=True, type=Path)
    parser.add_argument("--gold", required=True, type=Path)
    parser.add_argument("--pred", required=True, type=Path)
    parser.add_argument("--arguments", required=True, type=Path,
                        help="the extractor artifact the arm was trained and scored with")
    parser.add_argument("--tau", type=float, default=0.8,
                        help="bucket edge (default: HARD_SIMILARITY)")
    parser.add_argument("--arm-muc-f1", required=True, type=float)
    parser.add_argument("--anchor-muc-f1", required=True, type=float)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    evaluator = _load_evaluator(args.evaluator)
    gold, pred = _by_id(args.gold), _by_id(args.pred)
    nodes = load_nodes(args.gold, args.arguments)

    pairs = bucket_pairs(gold, pred, tau=args.tau, cross_only=True)
    missing = [m for _, a, b, _ in pairs for m in (a, b) if m not in nodes]
    if missing:
        raise SystemExit(f"{len(missing)} bucket mentions have no node, e.g. {missing[0]}")

    scored = []
    for doc_id, a, b, is_wrong in pairs:
        incompatible, agreement = pair_evidence(nodes[a], nodes[b])
        scored.append(
            {"pair": (doc_id, a, b), "wrong": is_wrong,
             "incompatible": incompatible, "agreement": agreement}
        )
    n_wrong = sum(row["wrong"] for row in scored)
    base_rate = n_wrong / len(scored)
    print(f"[signal] bucket >= {args.tau:g}, cross-sentence: {len(scored)} pairs, "
          f"{n_wrong} wrong, base rate {base_rate:.4f}")

    rows = []

    fired = [row for row in scored if row["incompatible"]]
    if fired:
        caught = sum(row["wrong"] for row in fired)
        muc = score_veto(evaluator, gold, pred, {row["pair"] for row in fired})
        rows.append({"rule": "incompatible", "vetoed": len(fired), "wrong_caught": caught,
                     "precision": caught / len(fired), "recall_of_wrong": caught / n_wrong,
                     **muc})
    else:
        rows.append({"rule": "incompatible", "vetoed": 0, "wrong_caught": 0,
                     "precision": 0.0, "recall_of_wrong": 0.0})

    # Weakest agreement first; "no comparable role" is not evidence, so it sorts last.
    order = sorted(scored, key=lambda row: (row["agreement"] is None, row["agreement"] or 0.0))
    for k in (50, 100, 200, 300, 400, 513, 700, len(order)):
        if k > len(order):
            continue
        chosen = order[:k]
        caught = sum(row["wrong"] for row in chosen)
        muc = score_veto(evaluator, gold, pred, {row["pair"] for row in chosen})
        rows.append({"rule": f"weakest-agreement@{k}", "vetoed": k, "wrong_caught": caught,
                     "precision": caught / k, "recall_of_wrong": caught / n_wrong, **muc})

    print(f"\n  {'suppressor':>24} {'vetoed':>7} {'wrong':>6} {'precision':>10} "
          f"{'MUC F1':>9} {'vs arm':>8} {'vs anchor':>10}")
    for row in rows:
        if "muc_f1" not in row:
            print(f"  {row['rule']:>24} {row['vetoed']:>7} {row['wrong_caught']:>6} "
                  f"{row['precision']:>10.4f} {'--':>9} {'--':>8} {'--':>10}")
            continue
        print(f"  {row['rule']:>24} {row['vetoed']:>7} {row['wrong_caught']:>6} "
              f"{row['precision']:>10.4f} {row['muc_f1']:>9.5f} "
              f"{row['muc_f1'] - args.arm_muc_f1:>+8.3f} "
              f"{row['muc_f1'] - args.anchor_muc_f1:>+10.3f}")

    achievable = [row for row in rows if "muc_f1" in row]
    best = max(achievable, key=lambda row: row["muc_f1"])
    beats_arm = best["muc_f1"] > args.arm_muc_f1
    reaches_anchor = best["muc_f1"] >= args.anchor_muc_f1
    verdict = (
        "train" if reaches_anchor
        else "do not train: the existing signal cannot pay C-11's price"
    )
    print(f"\n[signal] best {best['rule']} -> MUC F1 {best['muc_f1']:.5f} "
          f"(precision {best['precision']:.4f} vs base rate {base_rate:.4f}); "
          f"beats the arm: {beats_arm}; reaches the anchor: {reaches_anchor}")
    print(f"[signal] verdict: {verdict}")

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps({"bucket_pairs": len(scored), "wrong_pairs": n_wrong,
                        "base_rate": base_rate, "arm_muc_f1": args.arm_muc_f1,
                        "anchor_muc_f1": args.anchor_muc_f1, "best": best,
                        "beats_arm": beats_arm, "reaches_anchor": reaches_anchor,
                        "verdict": verdict, "rows": rows}, indent=2),
            encoding="utf-8",
        )
        print(f"[signal] wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
