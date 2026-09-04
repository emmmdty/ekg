#!/usr/bin/env python
"""Take one trained A3 arm from checkpoint to official MAVEN-ERE scores.

Three steps that must not drift apart, so they live in one command: dump the
arm's per-pair edges, normalise them into the official prediction shape against
the frozen candidate population, and score with MAVEN-ERE's own `evaluate.py`.
`normalize_predictions` is imported from the A3 launcher rather than
re-implemented -- two converters would be two candidate populations, which is
how the same protocol produces two different numbers.

    .venv/bin/python scripts/score_a3_arm.py \
        --run-dir runs/stages/A3/a3-v6-balanced-r11/control/seed-13 \
        --gold runs/stages/A3/a3-v6-balanced-r11/preflight/data/MAVEN_ERE/valid.jsonl \
        --candidate-digest <frozen digest>
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from run_a3_baseline import normalize_predictions  # noqa: E402

from ekg.core.schema import RelationEdge  # noqa: E402
from ekg.relations.extractor.supervised import checkpoint_active_families  # noqa: E402

FAMILIES = ("causal", "subevent", "temporal")


def run(argv: list[str], log: Path) -> None:
    with log.open("a", encoding="utf-8") as fh:
        completed = subprocess.run(argv, stdout=fh, stderr=subprocess.STDOUT, text=True)
    if completed.returncode != 0:
        raise SystemExit(f"{argv[1]} returned {completed.returncode}; see {log}")


def _read_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line
    ]


def merge_family_predictions(family_paths: dict[str, Path], output: Path) -> None:
    """Combine only the selected family from each family-specific checkpoint.

    Each checkpoint contains all three heads and a shared encoder snapshot from
    the epoch selected for one family.  Taking every edge from any one snapshot
    would therefore not implement per-family checkpoint selection.
    """
    if set(family_paths) != set(FAMILIES):
        raise ValueError(f"family prediction set must be exactly {sorted(FAMILIES)}")
    records = {family: _read_jsonl(path) for family, path in family_paths.items()}
    reference_ids: list[str] | None = None
    by_family: dict[str, dict[str, dict]] = {}
    for family in FAMILIES:
        indexed: dict[str, dict] = {}
        ordered_ids: list[str] = []
        for row in records[family]:
            doc_id = row.get("doc_id")
            if not isinstance(doc_id, str) or doc_id in indexed:
                raise ValueError(f"invalid/duplicate {family} prediction document: {doc_id}")
            indexed[doc_id] = row
            ordered_ids.append(doc_id)
        if reference_ids is None:
            reference_ids = ordered_ids
        elif ordered_ids != reference_ids:
            raise ValueError(f"{family} prediction document order/set differs")
        by_family[family] = indexed

    merged: list[dict] = []
    for doc_id in reference_ids or []:
        selected_edges: list[dict] = []
        for family in FAMILIES:
            for item in by_family[family][doc_id].get("edges", []):
                edge = RelationEdge.model_validate(item)
                if edge.relation_type.value == family:
                    selected_edges.append(item)
        merged.append({"doc_id": doc_id, "edges": selected_edges})
    output.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in merged),
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True, type=Path, help="holds checkpoint/")
    parser.add_argument("--gold", required=True, type=Path)
    parser.add_argument("--candidate-digest", required=True)
    parser.add_argument(
        "--config", type=Path, default=Path("configs/relations/supervised_dump.yaml")
    )
    parser.add_argument(
        "--evaluator", type=Path, default=Path("data/protocols/v6/tools/maven_ere_evaluate.py")
    )
    parser.add_argument(
        "--source-lock", type=Path, default=Path("data/protocols/v6/source_lock.json")
    )
    parser.add_argument(
        "--per-family-checkpoints",
        action="store_true",
        help="score checkpoint/by_family/<family> and combine only that family's edges",
    )
    args = parser.parse_args()

    checkpoint = args.run_dir / "checkpoint"
    if not (checkpoint / "heads.pt").exists():
        raise SystemExit(f"no trained heads under {checkpoint}")
    log = args.run_dir / "score.log"
    edges = args.run_dir / "edge_predictions.jsonl"
    official = args.run_dir / "official_predictions.jsonl"
    metrics = args.run_dir / "official_metrics.json"

    def inference_argv(selected_checkpoint: Path, raw: Path, metrics: Path) -> list[str]:
        return [
            sys.executable, "-u", "scripts/evaluate_relations.py",
            "--config", str(args.config),
            "--path", str(args.gold),
            "--checkpoint-path", str(selected_checkpoint),
            "--dump-predictions", str(raw),
            "--output", str(metrics),
        ]

    if args.per_family_checkpoints:
        family_paths: dict[str, Path] = {}
        for family in FAMILIES:
            selected = checkpoint / "by_family" / family
            selection = selected / "selection.json"
            if not (selected / "heads.pt").is_file() or not selection.is_file():
                raise SystemExit(f"missing selected {family} checkpoint under {selected}")
            selection_payload = json.loads(selection.read_text(encoding="utf-8"))
            if selection_payload.get("family") != family:
                raise SystemExit(f"selection metadata mismatch under {selected}")
            raw = args.run_dir / f"edge_predictions.{family}.jsonl"
            run(
                inference_argv(
                    selected,
                    raw,
                    args.run_dir / f"native_metrics.{family}.json",
                ),
                log,
            )
            family_paths[family] = raw
        merge_family_predictions(family_paths, edges)
    else:
        run(
            inference_argv(checkpoint, edges, args.run_dir / "native_metrics.json"),
            log,
        )
    normalize_predictions(
        baseline="local_pair",
        raw_path=edges,
        gold_path=args.gold,
        output=official,
        candidate_digest=args.candidate_digest,
        active_families=(
            FAMILIES
            if args.per_family_checkpoints
            else checkpoint_active_families(checkpoint)
        ),
    )
    run(
        [
            sys.executable, "-u", "scripts/score_maven_ere_official.py",
            "--evaluator", str(args.evaluator),
            "--source-lock", str(args.source_lock),
            "--gold", str(args.gold),
            "--pred", str(official),
            "--candidate-digest", args.candidate_digest,
            "--output", str(metrics),
        ],
        log,
    )
    scores = json.loads(metrics.read_text(encoding="utf-8"))["scores"]
    print(
        f"{args.run_dir.parent.name:<20}"
        + "  ".join(
            f"{fam[:4]} P{scores[f'{fam}_precision']:6.2f} R{scores[f'{fam}_recall']:6.2f} "
            f"F{scores[f'{fam}_f1']:6.2f}"
            for fam in FAMILIES
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
