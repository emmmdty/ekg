#!/usr/bin/env python
"""Operating-point sweep for canonicalization: threshold x abstention band.

Pair scores do not depend on the threshold or the band, so `CachingScorer`
computes them once per document and every later cell reads the cache: the sweep
costs **one** scoring pass, not one per cell. That is the difference between
minutes and an hour once the scorer is the neural one.

Reports, per cell, the numbers that trade against each other: coreference
CoNLL/MUC, the mis-merge rate overall and on the hard subset, the coref-family
FNR (Phase B's ruler) with its precision, and how many merges the band refused.
There is no single best cell — the band buys precision with recall, and the
table is what makes that price visible.

    .venv/bin/python scripts/sweep_canonical_nodes.py \
        --arg data/processed/maven_arg/valid.jsonl \
        --ere data/processed/maven_ere/valid.jsonl \
        --scorer supervised --scorer-path runs/nodes/coref_supervised \
        --out runs/canonical_nodes_sweep.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from build_canonical_nodes import run

from ekg.nodes.coref import coreference_scorers
from ekg.relations.data import load_maven_arg, load_maven_ere


class CachingScorer:
    """Scores each document once; later cells read the cache.

    Keyed by document id — the candidate pair set is a function of the document's
    mentions, which the sweep never varies.
    """

    def __init__(self, inner) -> None:
        self.inner = inner
        self.cache: dict[str, dict[tuple[str, str], float]] = {}
        self.misses = 0

    def score(self, nodes, pairs, doc_text=""):
        doc_id = nodes[0].doc_id if nodes else ""
        if doc_id not in self.cache:
            self.misses += 1
            self.cache[doc_id] = self.inner.score(nodes, pairs, doc_text)
        return self.cache[doc_id]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arg", required=True, type=Path)
    parser.add_argument("--ere", required=True, type=Path)
    parser.add_argument("--scorer", default="lexical")
    parser.add_argument("--scorer-path", default=None)
    parser.add_argument("--cal-ratio", type=float, default=0.3)
    parser.add_argument("--thresholds", default="0.3,0.5,0.7,0.9")
    parser.add_argument("--bands", default="0.0,0.05,0.1")
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    arg_docs = list(load_maven_arg(args.arg))
    ere_docs = list(load_maven_ere(args.ere))
    scorer = CachingScorer(
        coreference_scorers.create(
            args.scorer, **({"checkpoint_path": args.scorer_path} if args.scorer_path else {})
        )
    )

    header = (
        f"{'thr':>5} {'band':>5} {'MUC':>6} {'CoNLL':>6} {'misM':>6} "
        f"{'hardM':>6} {'cFNR':>6} {'cP':>6} {'cF1':>6} {'ECE':>7} {'abst':>6}"
    )
    print(header, flush=True)
    print("-" * len(header), flush=True)

    cells = []
    for threshold in (float(t) for t in args.thresholds.split(",")):
        for band in (float(b) for b in args.bands.split(",")):
            report, _ = run(
                arg_docs,
                ere_docs,
                scorer_name=args.scorer,
                scorer_path=args.scorer_path,
                threshold=threshold,
                band=band,
                cal_ratio=args.cal_ratio,
                scorer=scorer,
            )
            coref = report["coreference"]
            merge = report["mis_merge"]
            family = report["coref_family_fnr"]
            prf = family["coreference_prf"]
            cells.append(report)
            print(
                f"{threshold:5.2f} {band:5.2f} {coref['muc_f1']:6.3f} {coref['conll_f1']:6.3f} "
                f"{merge['mis_merge_rate']:6.3f} {merge['hard_mis_merge_rate']:6.3f} "
                f"{family['by_type']['coreference']['fnr']:6.3f} {prf['precision']:6.3f} "
                f"{prf['f1']:6.3f} {report['confidence']['ece_calibrated']:7.4f} "
                f"{report['abstained_merges']:6d}",
                flush=True,
            )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(cells, indent=2, default=float))
    print(f"wrote {len(cells)} cells to {args.out}; scored {scorer.misses} documents once each")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
