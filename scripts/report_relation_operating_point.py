#!/usr/bin/env python
"""Is Ch2's causal gap a *working point* problem or a discriminative one?

The reproduction base emits causal edges at P 22.15 / R 54.02 while the frozen
primary anchor sits at P 34.37 / R 32.05 (`docs/results/PHASE_A.md`). Same
split, same candidate population, same evaluator: we are not uniformly worse, we
are standing somewhere else on the precision/recall curve -- emitting roughly
2.4x as many causal edges as there are gold ones.

Two very different situations produce that picture, and they call for opposite
mechanisms:

- a **working point** problem: the scores separate, we are just cutting them in
  the wrong place. A mechanism that moves the operating point per family can
  then recover F1;
- a **discriminative** problem: the score distribution does not separate, every
  cut is bad, and no re-weighting will help.

This decides which, training nothing: it re-cuts the *already emitted* edges at
a grid of confidence thresholds, re-normalises to the official prediction shape
and re-scores with MAVEN-ERE's own `evaluate.py`. Dropping a causal edge never
changes the temporal score, so one pass per threshold yields all three curves.

⚠️ The sweep is a **diagnostic, not a method**. The phase contract rules out
gains that come from re-cutting alone ("固定权重/网格/只改 best-checkpoint 选择
不算新方法"), and PHASE_A has seen a *plateau* here before under an older
protocol -- which is exactly why it has to be re-measured on this run rather
than extrapolated. What the curve buys is the design question: how much headroom
the working point holds, and for which family.

    .venv/bin/python scripts/report_relation_operating_point.py \
        --edges runs/stages/A3/reproduction_base/seed-13/edge_predictions.jsonl \
        --checkpoint runs/stages/A3/reproduction_base/seed-13/checkpoint \
        --gold runs/stages/A3/a3-v6-baselines-r10/preflight/data/MAVEN_ERE/valid.jsonl \
        --candidate-digest <frozen digest> --output runs/stages/A3/operating_point.json
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from run_a3_baseline import normalize_predictions  # noqa: E402

from ekg.relations.extractor.supervised import checkpoint_active_families  # noqa: E402

FAMILIES = ("causal", "subevent", "temporal")
DEFAULT_THRESHOLDS = (0.0, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70, 0.80, 0.90)


def read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def filtered_edges(rows: list[dict], threshold: float) -> tuple[list[dict], dict[str, int]]:
    """Drop every emitted edge whose confidence is below `threshold`.

    The dump only holds edges the model already decided to emit, so this can
    only move the cut *up*. That is the direction of interest: the diagnosis is
    an excess of false positives, not a shortage of candidates.
    """
    kept: list[dict] = []
    counts = dict.fromkeys(FAMILIES, 0)
    for row in rows:
        edges = [e for e in row.get("edges", []) if e.get("confidence", 1.0) >= threshold]
        for edge in edges:
            family = edge["relation_type"]
            if family in counts:
                counts[family] += 1
        kept.append({"doc_id": row["doc_id"], "edges": edges})
    return kept, counts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--edges", required=True, type=Path, help="edge_predictions.jsonl")
    parser.add_argument("--checkpoint", required=True, type=Path, help="the run's checkpoint dir")
    parser.add_argument("--gold", required=True, type=Path, help="internal-dev valid.jsonl")
    parser.add_argument("--candidate-digest", required=True)
    parser.add_argument(
        "--evaluator", type=Path, default=Path("data/protocols/v6/tools/maven_ere_evaluate.py")
    )
    parser.add_argument(
        "--source-lock", type=Path, default=Path("data/protocols/v6/source_lock.json")
    )
    parser.add_argument("--thresholds", type=float, nargs="*", default=list(DEFAULT_THRESHOLDS))
    parser.add_argument("--workdir", type=Path, default=Path("runs/stages/A3/operating_point"))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    rows = read_jsonl(args.edges)
    active = checkpoint_active_families(args.checkpoint)
    print(f"{len(rows)} documents, active families {active}")

    results: list[dict] = []
    for threshold in args.thresholds:
        kept, counts = filtered_edges(rows, threshold)
        stem = f"tau_{threshold:.2f}".replace(".", "p")
        raw_path = args.workdir / f"{stem}_edges.jsonl"
        official_path = args.workdir / f"{stem}_official.jsonl"
        metrics_path = args.workdir / f"{stem}_metrics.json"
        write_jsonl(raw_path, kept)
        normalize_predictions(
            baseline="local_pair",
            raw_path=raw_path,
            gold_path=args.gold,
            output=official_path,
            candidate_digest=args.candidate_digest,
            active_families=active,
        )
        completed = subprocess.run(
            [
                sys.executable, "-u", "scripts/score_maven_ere_official.py",
                "--evaluator", str(args.evaluator),
                "--source-lock", str(args.source_lock),
                "--gold", str(args.gold),
                "--pred", str(official_path),
                "--candidate-digest", args.candidate_digest,
                "--output", str(metrics_path),
            ],
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0:
            raise SystemExit(
                f"official scorer failed at tau={threshold}: {completed.stdout[-800:]}"
            )
        scores = json.loads(metrics_path.read_text(encoding="utf-8"))["scores"]
        results.append(
            {
                "threshold": threshold,
                "edges_kept": counts,
                **{
                    f"{fam}_{key}": scores[f"{fam}_{key}"]
                    for fam in FAMILIES
                    for key in ("precision", "recall", "f1")
                },
            }
        )
        print(
            f"tau={threshold:.2f}  "
            + "  ".join(
                f"{fam[:4]} P{scores[f'{fam}_precision']:5.2f} R{scores[f'{fam}_recall']:5.2f} "
                f"F{scores[f'{fam}_f1']:5.2f}"
                for fam in FAMILIES
            ),
            flush=True,
        )

    print()
    for fam in FAMILIES:
        best = max(results, key=lambda r: r[f"{fam}_f1"])
        base = results[0]
        print(
            f"{fam:<9} base F1 {base[f'{fam}_f1']:6.2f} (tau {base['threshold']:.2f})  ->  "
            f"best F1 {best[f'{fam}_f1']:6.2f} at tau {best['threshold']:.2f}  "
            f"headroom {best[f'{fam}_f1'] - base[f'{fam}_f1']:+.2f}"
        )

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps({"edges": str(args.edges), "sweep": results}, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"\n[operating-point] wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
