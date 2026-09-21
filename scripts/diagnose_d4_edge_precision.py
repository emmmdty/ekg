#!/usr/bin/env python
"""Diagnostic only: what precision is reachable from the frozen edge posteriors?

The failed cycle passed messages over edges that were 22.4% correct
(`results/PHASE_R1.md` §25.21), so the obvious question for any second design is
whether precision can be bought at all, and at what cost in reach. This answers
it from the *already frozen* natural posteriors, without training anything and
without re-scoring any arm.

**This is not a threshold sweep for the mechanism.** The frozen decision rule
stays `argmax_k w_k p_k`; the contract forbids tuning it, and nothing here may
enter a main table or be subtracted from a reported score. It exists so the
author can see whether path (a) — raise edge precision — is viable before
deciding to spend a second cycle on it.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from ekg.core.protocol import load_manifest_ids
from ekg.core.schema import RelationType
from ekg.core.stage_bundle import sha256_file
from ekg.factuality.causal_residual import decide_edges
from ekg.relations.data.maven_ere import load_maven_ere
from ekg.relations.pairs import gold_pair_labels

CUTOFFS = (0.0, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sidecar_documents(path: Path):
    current: str | None = None
    rows: list[dict] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row["doc_id"] != current:
                if current is not None:
                    yield current, rows
                current, rows = row["doc_id"], []
            rows.append(row)
    if current is not None:
        yield current, rows


def diagnose(
    *, repo: Path, crossfit: Path, cv: Path, relation_source: Path
) -> dict:
    folds = {int(row["fold"]): row for row in _load(cv)["folds"]}
    gold_pairs = {
        doc.doc_id: gold_pair_labels(
            doc, family=RelationType.CAUSAL, expand_event_relations=True
        )
        for doc in load_maven_ere(relation_source)
    }
    gold_total = 0
    kept: list[tuple[float, bool, str]] = []
    reachable: dict[float, set[str]] = {cutoff: set() for cutoff in CUTOFFS}
    mentions: set[str] = set()

    for fold in range(1, 6):
        wanted = set(load_manifest_ids(repo / folds[fold]["evaluation"]["path"]))
        weights = _load(
            crossfit / f"fold-{fold}" / "dirichlet_calibration.metadata.json"
        )["class_weights"]
        for doc_id, rows in _sidecar_documents(
            crossfit / f"fold-{fold}" / "dirichlet_causal_posteriors.jsonl"
        ):
            if doc_id not in wanted:
                raise ValueError(f"fold {fold}: {doc_id} is outside the evaluation manifest")
            gold = gold_pairs.get(doc_id, {})
            gold_total += len(gold)
            for row in rows:
                mentions.add(row["head_mention_id"])
                mentions.add(row["tail_mention_id"])
            for edge in decide_edges(rows, weights):
                correct = gold.get((edge.head_mention_id, edge.tail_mention_id)) == edge.subtype
                kept.append((edge.confidence, correct, edge.tail_mention_id))
                for cutoff in CUTOFFS:
                    if edge.confidence >= cutoff:
                        reachable[cutoff].add(edge.tail_mention_id)

    curve = []
    for cutoff in CUTOFFS:
        selected = [(c, ok) for c, ok, _ in kept if c >= cutoff]
        correct = sum(1 for _, ok in selected if ok)
        curve.append(
            {
                "confidence_at_least": cutoff,
                "edges": len(selected),
                "correct": correct,
                "precision": correct / len(selected) if selected else 0.0,
                "recall_of_gold_pairs": correct / gold_total if gold_total else 0.0,
                "mentions_with_an_incoming_edge": len(reachable[cutoff]),
            }
        )
    return {
        "schema_version": "ekg.d4_edge_precision_diagnostic.v1",
        "diagnostic_only": True,
        "frozen_decision_rule": "argmax_k w_k p_k (unchanged; this is not a sweep)",
        "mentions": len(mentions),
        "gold_expanded_causal_pairs": gold_total,
        "curve": curve,
        "command_argv": sys.argv,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--crossfit", required=True, type=Path)
    parser.add_argument("--cv", required=True, type=Path)
    parser.add_argument("--relation-source", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite: {args.output}")
    report = diagnose(
        repo=args.repo.resolve(),
        crossfit=args.crossfit.resolve(),
        cv=args.cv.resolve(),
        relation_source=args.relation_source.resolve(),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({**report, "output_sha256": sha256_file(args.output)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
