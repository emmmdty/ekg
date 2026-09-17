#!/usr/bin/env python
"""Score an external opponent's candidate scores with *our* evaluator (G-11a).

Table 6-2's rows have to come off one scorer. `docs/PROTOCOL_TABLE.md` pins Ch6's
evaluator to `succession/metrics.py`, and an opponent row computed by that
opponent's own metric code would break the three-axis consistency that makes the
table a table -- their KGC `get_performance` averages head and tail prediction
and has its own tie convention, neither of which is CGEP's.

So the opponent is patched to dump the 512 candidate scores per query and
nothing else; ranking, ties and Hit@k happen here, the same way they happened
for `gold`, `predicted`, `random` and `frequency`.

Input is one JSON object per line::

    {"row": 0, "gold": 1234, "candidates": [ids...], "scores": [floats...]}

`row` indexes the frozen unit's queries in file order, which is the order the
export wrote `test2id.txt` and `test_candidates.txt` in.

    uv run python scripts/score_kgc_opponent.py --scores runs/.../csprom_scores.jsonl \\
        --export runs/stages/E3/kgc/CGEP-MAVEN --name CSProm-KG
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ekg.core.io import read_jsonl
from ekg.succession.metrics import cgep_metrics, sedgpl_rank, strict_rank


def _numbered(path: Path) -> list[str]:
    lines = path.read_text(encoding="utf-8").strip("\n").split("\n")
    if int(lines[0]) != len(lines) - 1:
        raise SystemExit(f"{path}: count line {lines[0]} disagrees with {len(lines) - 1} rows")
    return lines[1:]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scores", type=Path, required=True, help="the opponent's dump")
    parser.add_argument("--export", type=Path, default=Path("runs/stages/E3/kgc/CGEP-MAVEN"))
    parser.add_argument("--name", required=True, help="row label for table 6-2")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    manifest = json.loads((args.export / "export_manifest.json").read_text(encoding="utf-8"))
    expected = [
        (int(line.split()[1]), set(cand.split()))
        for line, cand in zip(
            _numbered(args.export / "test2id.txt"),
            _numbered(args.export / "test_candidates.txt"),
            strict=True,
        )
    ]

    ranks: list[int] = []
    strict: list[int] = []
    seen: set[int] = set()
    for record in read_jsonl(args.scores):
        row = int(record["row"])
        if row in seen:
            raise SystemExit(f"row {row} scored twice")
        seen.add(row)
        gold, pool = expected[row]
        if int(record["gold"]) != gold:
            raise SystemExit(f"row {row}: dumped gold {record['gold']} != exported {gold}")
        candidates = [int(c) for c in record["candidates"]]
        if {str(c) for c in candidates} != pool:
            raise SystemExit(f"row {row}: candidate set differs from the export")
        scores = [float(s) for s in record["scores"]]
        if len(scores) != len(candidates):
            raise SystemExit(f"row {row}: {len(scores)} scores for {len(candidates)} candidates")
        label = candidates.index(gold)
        ranks.append(sedgpl_rank(scores, label))
        strict.append(strict_rank(scores, label))

    missing = set(range(len(expected))) - seen
    if missing:
        # Dropping unscorable rows would quietly shrink the denominator, which is
        # the one thing PROTOCOL_TABLE says never to do.
        raise SystemExit(
            f"{len(missing)} of {len(expected)} queries were not scored; "
            "rank them worst rather than dropping them"
        )

    report = {
        "method": args.name,
        "fidelity": manifest["fidelity"],
        "unit": manifest["unit"],
        "evaluator": "src/ekg/succession/metrics.py (the same one every other row uses)",
        "metrics": cgep_metrics(ranks),
        "metrics_strict": {f"{k}_strict": v for k, v in cgep_metrics(strict).items()},
        "differences_from_the_published_setting":
            manifest["differences_from_the_published_setting"],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    m = report["metrics"]
    print(
        f"[kgc-score] {args.name}: MRR {m['mrr']:.4f}  "
        + "  ".join(f"H@{k} {m[f'hits@{k}']:.4f}" for k in (1, 3, 10, 20, 50))
        + f"  n={int(m['n'])}\n[kgc-score] wrote {args.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
