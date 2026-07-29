#!/usr/bin/env python
"""Ch4 goal 3: the analytic error budget against the measured construction loss.

`core.calibration.propagation` composes a construction-stage reachability budget
with a reasoning-stage coverage budget under one total risk `alpha_total`, via
the union bound ``P(miss) <= P(unreachable) + P(reasoning miss | reachable)``.
Until now that composition was only ever exercised against a *synthetic*
reachability mask (`succession.cross_stage.induce_reachability`), because no
extractor produced a non-degenerate constructed ECG. Phase A's does, so this
reads the real per-query ranks and reachability dumped by
`evaluate_cgep_propagation.py` and asks the budget the question it exists for.

The first thing it reports is not a coverage number but a **feasibility floor**:
whatever the allocation, composed coverage can never exceed the reachable rate,
so any ``alpha_total`` below the measured unreachability is unattainable by
construction. A budget table that omits that floor would show three methods
"failing" where in fact no method could succeed.

A fifth method sits beside the four `compare_cross_stage_methods` returns.
`cs_crp_cond` certifies the unreachability rate ``u`` from held-out outcomes and
then *tightens* it with the construction stage's CRC bound ``alpha_edge``, taking
the minimum of the two. That is sound only while the reachability loss is
produced by the admission stage ``alpha_edge`` bounds. Here it is not -- the loss
comes from **extraction**, which no CRC bound covers -- so the tightening asserts
an upper bound that does not hold and the recycler under-covers. Running the
budget against measured rather than synthetic loss is what makes that visible, so
``cs_crp_measured`` (the same recycler with the tightening dropped) is reported
next to it rather than the library being quietly changed.

    uv run python scripts/report_ch4_budget.py --ranks runs/cgep/ch4_propagation_ranks.json
"""

from __future__ import annotations

import argparse
import json
import math
import random
from pathlib import Path

from ekg.core.calibration.propagation import (
    allocate_budget_conditional,
    compare_cross_stage_methods,
    run_cross_stage,
)

_METHODS = ("naive", "bonferroni", "cs_crp", "cs_crp_cond", "cs_crp_measured")
_DEFAULT_ALPHAS = (0.1, 0.2, 0.3, 0.4, 0.5)


def _split(n: int, cal_ratio: float, seed: int) -> tuple[list[int], list[int]]:
    order = list(range(n))
    random.Random(seed).shuffle(order)
    cut = int(n * cal_ratio)
    return order[:cut], order[cut:]


def budget_curve(
    ranks: list[float],
    reachable: list[bool],
    *,
    alphas: tuple[float, ...],
    cal_ratio: float,
    seed: int,
) -> dict:
    """Composed coverage per method across `alphas`, plus the feasibility floor."""
    cal, test = _split(len(ranks), cal_ratio, seed)
    reach_test = [reachable[i] for i in test]
    reach_cal = [reachable[i] for i in cal]
    masked = [ranks[i] if reachable[i] else math.inf for i in test]
    cal_ranks = [ranks[i] for i in cal if reachable[i]]

    rows: list[dict[str, float]] = []
    for alpha in alphas:
        results = compare_cross_stage_methods(
            reach_test, masked, cal_ranks, alpha_total=alpha, cal_reachable=reach_cal
        )
        # The recycler without the CRC tightening: here the reachability loss is
        # extraction's, which alpha_edge does not bound (see the module docstring).
        measured = allocate_budget_conditional(reach_cal, alpha, alpha_edge=None)
        results["cs_crp_measured"] = run_cross_stage(
            reach_test, masked, cal_ranks,
            alpha_total=alpha, alpha_pred=measured.alpha_pred, reasoning="aci",
        )
        row: dict[str, float] = {
            "u_certified": measured.alpha_edge,
            "alpha_total": alpha,
            "target": 1.0 - alpha,
            # The ceiling: an unreachable gold answer is a miss no calibrator can
            # cover, so this bounds every method in the row from above.
            "reachable_rate_test": sum(reach_test) / len(reach_test),
            "feasible": float(1.0 - alpha <= sum(reach_test) / len(reach_test)),
        }
        for method in _METHODS:
            row[f"{method}_coverage"] = results[method].composed_coverage
            row[f"{method}_set_size"] = results[method].mean_set_size
        rows.append(row)
    unreachable_cal = 1.0 - (sum(reach_cal) / len(reach_cal) if reach_cal else 0.0)
    return {
        "n_cal": len(cal),
        "n_test": len(test),
        "unreachability_cal": unreachable_cal,
        # Below this total budget the composition is infeasible whatever the split.
        "min_feasible_alpha_total": 1.0 - sum(reach_test) / len(reach_test),
        "curve": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ranks", required=True, type=Path,
                        help="the --ranks-output file of evaluate_cgep_propagation.py")
    parser.add_argument("--alphas", type=float, nargs="+", default=list(_DEFAULT_ALPHAS))
    parser.add_argument("--arms", nargs="+", help="only these arms (default: all)")
    parser.add_argument("--cal-ratio", type=float, default=0.5)
    parser.add_argument("--seed", type=int, default=209)
    parser.add_argument("--output", type=Path, default=Path("runs/cgep/ch4_budget.json"))
    args = parser.parse_args()

    dump = json.loads(args.ranks.read_text(encoding="utf-8"))
    wanted = args.arms or list(dump)
    alphas = tuple(args.alphas)

    report: dict[str, dict] = {}
    for name in wanted:
        if name not in dump:
            raise SystemExit(f"no arm {name!r} in {args.ranks}; have {sorted(dump)}")
        entry = dump[name]
        ranks = [math.inf if r is None else float(r) for r in entry["ranks"]]
        report[name] = budget_curve(
            ranks, list(entry["reachable"]),
            alphas=alphas, cal_ratio=args.cal_ratio, seed=args.seed,
        )
        floor = report[name]["min_feasible_alpha_total"]
        print(f"\n{name}   min feasible alpha_total = {floor:.4f}")
        print(f"{'alpha':>7}{'target':>8}{'feas':>6}"
              + "".join(f"{m:>17}" for m in _METHODS))
        for row in report[name]["curve"]:
            print(
                f"{row['alpha_total']:>7.2f}{row['target']:>8.2f}"
                f"{'y' if row['feasible'] else 'n':>6}"
                + "".join(f"{row[f'{m}_coverage']:>17.4f}" for m in _METHODS)
            )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps({"alphas": list(alphas), "cal_ratio": args.cal_ratio,
                    "seed": args.seed, "arms": report}, indent=2),
        encoding="utf-8",
    )
    print(f"\n[budget] wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
