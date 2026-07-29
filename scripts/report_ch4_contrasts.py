#!/usr/bin/env python
"""Ch4: is a difference between two graphs bigger than the noise it sits in?

The propagation table is full of small numbers -- repair buys +0.0011 MRR,
purification buys −0.0000 -- and Phases A–D established that graph-side
interventions on SeDGPL land at that scale routinely. Reporting them without an
interval invites reading noise as an effect, in either direction.

Multi-seed retraining is the thorough answer and is Phase H's job (a seed costs
~2.5h). This is the answer available for free and it is the right one for *this*
comparison anyway: every arm answers the identical 1908 instances with the
identical model, so the arms are paired and the only sampling variation left is
which queries the valid split happens to contain. A paired bootstrap over
instances measures exactly that, and it is strictly tighter than an unpaired
interval on each arm's MRR separately.

What it cannot cover: training randomness (one fit, seed 209) and perturbation
sampling (one draw per amplitude). So an interval that excludes zero here means
"not explained by which queries we were given", not "would survive a reseed" --
stated rather than implied, because the two are routinely conflated.

    uv run python scripts/report_ch4_contrasts.py --ranks runs/cgep/ch4_propagation_ranks.json
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np


def _reciprocal_ranks(ranks: list[float], n_candidates: int) -> np.ndarray:
    """MRR's per-instance term, matching `cgep_metrics` on 0-based ranks.

    An unscorable instance is dumped as infinity (a guaranteed miss, which is
    what the calibrator needs) but charged as the *worst* rank by the metric, so
    it is clamped back here rather than silently contributing a different number
    to the two views.
    """
    worst = n_candidates - 1
    clamped = np.array([worst if math.isinf(r) else r for r in ranks], dtype=float)
    return 1.0 / (clamped + 1.0)


def paired_bootstrap(
    a: np.ndarray, b: np.ndarray, *, draws: int, seed: int
) -> dict[str, float]:
    """Percentile CI for ``mean(a) - mean(b)`` over resampled instances."""
    delta = a - b
    rng = np.random.default_rng(seed)
    index = rng.integers(0, len(delta), size=(draws, len(delta)))
    resampled = delta[index].mean(axis=1)
    return {
        "delta": float(delta.mean()),
        "ci_lo": float(np.percentile(resampled, 2.5)),
        "ci_hi": float(np.percentile(resampled, 97.5)),
        # Two-sided bootstrap p: how often the resampled effect crosses zero.
        # An exactly-zero difference lands on both tails, hence the clamp.
        "p_sign": float(min(1.0, 2 * min((resampled <= 0).mean(), (resampled >= 0).mean()))),
        "n_instances": int(len(delta)),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ranks", required=True, type=Path)
    parser.add_argument("--reference", default="gold",
                        help="arm every other arm is contrasted against")
    parser.add_argument("--contrasts", nargs="+", default=[],
                        help="extra pairs as A,B reported as mean(A) - mean(B). Comma, not "
                             "colon: arm names carry a '::selector' suffix")
    parser.add_argument("--arms", nargs="+", help="restrict the vs-reference table")
    parser.add_argument("--candidates", type=int, default=512,
                        help="candidate set size, for clamping unscorable instances")
    parser.add_argument("--draws", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=209)
    parser.add_argument("--output", type=Path, default=Path("runs/cgep/ch4_contrasts.json"))
    args = parser.parse_args()

    dump = json.loads(args.ranks.read_text(encoding="utf-8"))
    rr = {
        name: _reciprocal_ranks(entry["ranks"], args.candidates)
        for name, entry in dump.items()
    }

    pairs = [(name, args.reference) for name in (args.arms or dump) if name != args.reference]
    for spec in args.contrasts:
        left, _, right = spec.partition(",")
        if not right:
            raise SystemExit(f"contrast {spec!r} must be A,B")
        pairs.append((left, right))

    report: dict[str, dict] = {}
    print(f"{'contrast':60s}{'delta':>10}{'95% CI':>22}{'p':>8}")
    for left, right in pairs:
        for name in (left, right):
            if name not in rr:
                raise SystemExit(f"no arm {name!r} in {args.ranks}")
        result = paired_bootstrap(rr[left], rr[right], draws=args.draws, seed=args.seed)
        key = f"{left} - {right}"
        report[key] = result
        interval = f"[{result['ci_lo']:+.4f}, {result['ci_hi']:+.4f}]"
        print(f"{key:60s}{result['delta']:>+10.4f}{interval:>22}{result['p_sign']:>8.3f}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps({"draws": args.draws, "seed": args.seed, "contrasts": report}, indent=2),
        encoding="utf-8",
    )
    print(f"\n[contrasts] wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
