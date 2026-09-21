#!/usr/bin/env python
"""Pool the official-EFD runs into one OOF row per structure and compare them.

The vendored trainer dumps predictions as a bare array, so the mention each
entry belongs to is recovered by walking the very split file it was given in the
loader's own order: documents in file order, events in list order, mentions in
list order. That reconstruction is *verified*, not assumed — the labels it
rebuilds must equal the labels the trainer recorded, element for element, or the
run is rejected.

Its label ids are not ours (`CT+ CT- PS+ PS- Uu` against our
`CT+ PS+ CT- PS- Uu`), so they are translated through the label names rather
than through position.

Both rows are FR-016 (b) transparent adaptations and the `gold` one is
non-deployable; neither may enter a promotion gate.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from aggregate_d4_predicted_causal import (
    _class_f1,
    _macro_f1,
    paired_bootstrap,
    per_document_matrices,
)

from ekg.core.protocol import load_manifest_ids
from ekg.core.stage_bundle import sha256_file
from ekg.relations.data.maven_fact import FACTUALITY_LABELS, load_maven_fact

STRUCTURES = ("gold", "predicted")
# trainEFD/data.py: label2id = {'CT+': 0, 'CT-': 1, "PS+": 2, "PS-": 3, "Uu": 4}
UPSTREAM_LABELS = ("CT+", "CT-", "PS+", "PS-", "Uu")
SIDE = len(FACTUALITY_LABELS)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def mention_order(split: Path) -> list[tuple[str, str]]:
    """`(doc_id, mention_id)` in exactly `EFDDataset.load_data`'s iteration order."""
    order: list[tuple[str, str]] = []
    for line in split.read_text(encoding="utf-8").splitlines():
        if not line:
            continue
        doc = json.loads(line)
        for event in doc["events"]:
            for mention in event["mention"]:
                order.append((doc["id"], mention["id"]))
    return order


def fold_predictions(run: Path) -> dict[tuple[str, str], str]:
    report = _load(run / "report.json")
    order = mention_order(run / "evaluation.jsonl")
    predictions = report["test_predictions"]
    labels = report["test_labels"]
    if not len(order) == len(predictions) == len(labels):
        raise ValueError(f"{run}: {len(order)} mentions but {len(predictions)} predictions")
    gold_by_mention = {}
    for line in (run / "evaluation.jsonl").read_text(encoding="utf-8").splitlines():
        if not line:
            continue
        doc = json.loads(line)
        for event in doc["events"]:
            for mention in event["mention"]:
                gold_by_mention[(doc["id"], mention["id"])] = mention["factuality"]
    for key, recorded in zip(order, labels, strict=True):
        if gold_by_mention[key] != UPSTREAM_LABELS[recorded]:
            raise ValueError(f"{run}: reconstructed order disagrees with the dumped labels")
    return {
        key: UPSTREAM_LABELS[value] for key, value in zip(order, predictions, strict=True)
    }


def aggregate(*, repo: Path, runs: Path, cv: Path, source: Path) -> dict:
    folds = {int(row["fold"]): row for row in _load(cv)["folds"]}
    document_ids: list[str] = []
    for fold in range(1, 6):
        document_ids.extend(load_manifest_ids(repo / folds[fold]["evaluation"]["path"]))
    docs = {doc.doc_id: doc for doc in load_maven_fact(source) if doc.doc_id in set(document_ids)}
    mentions_by_document = {
        doc_id: [mention.mention_id for mention in docs[doc_id].mentions]
        for doc_id in document_ids
    }
    gold = {
        mention.mention_id: mention.factuality
        for doc in docs.values()
        for mention in doc.mentions
    }

    rows = {}
    matrices = {}
    for structure in STRUCTURES:
        pooled: dict[str, str] = {}
        per_fold = []
        for fold in range(1, 6):
            run = runs / structure / f"fold-{fold}"
            metadata = _load(run / "run_metadata.json")
            if metadata["status"] != "complete" or metadata["structure"] != structure:
                raise ValueError(f"{run}: incomplete or mislabelled run")
            report = _load(run / "report.json")
            predictions = fold_predictions(run)
            for (doc_id, mention_id), label in predictions.items():
                key = f"{doc_id}::{mention_id}"
                if key in pooled:
                    raise ValueError(f"{structure}: {key} scored twice")
                pooled[key] = label
            per_fold.append(
                {
                    "fold": fold,
                    "selected_epoch": report["selected_epoch"],
                    "dev_macro_f1": report["dev"]["macro_f1"],
                    "test_macro_f1": report["test"]["macro_f1"],
                    "upstream_rule_epoch_max_test_macro_f1": report[
                        "epoch_max_test_macro_f1_upstream_rule"
                    ],
                    "cluster_relations": metadata["splits"]["evaluation"][
                        "cluster_relation_counts"
                    ],
                }
            )
        if set(pooled) != set(gold):
            raise ValueError(f"{structure}: pooled mention cover mismatch")
        matrix = per_document_matrices(document_ids, mentions_by_document, gold, pooled)
        matrices[structure] = matrix
        summary = matrix.sum(axis=0).reshape(SIDE, SIDE)
        rows[structure] = {
            "macro_f1": _macro_f1(summary),
            "per_class_f1": _class_f1(summary),
            "folds": per_fold,
        }

    return {
        "schema_version": "ekg.d4_official_efd_pooled.v1",
        "fidelity": "FR-016 (b) transparent adaptation; the gold row is non-deployable",
        "promotion_gate": "none — neither row may enter a gate",
        "coverage": {"documents": len(document_ids), "mentions": len(gold)},
        "rows": rows,
        "gold_minus_predicted": paired_bootstrap(
            matrices["gold"], matrices["predicted"], draws=10000, seed=13
        ),
        "command_argv": sys.argv,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--runs", required=True, type=Path)
    parser.add_argument("--cv", required=True, type=Path)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite: {args.output}")
    report = aggregate(
        repo=args.repo.resolve(),
        runs=args.runs.resolve(),
        cv=args.cv.resolve(),
        source=args.source.resolve(),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "macro_f1": {s: report["rows"][s]["macro_f1"] for s in STRUCTURES},
                "gold_minus_predicted": report["gold_minus_predicted"],
                "coverage": report["coverage"],
                "output_sha256": sha256_file(args.output),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
