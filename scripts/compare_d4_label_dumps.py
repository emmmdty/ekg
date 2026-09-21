#!/usr/bin/env python
"""Pool two D4 label dumps over the same OOF documents and compare them.

Written for the oracle diagnostic: that row has only one arm, so the three-arm
aggregator does not apply, but the comparison still has to be the contract's
paired document-cluster bootstrap rather than two point estimates eyeballed
side by side. The scoring and resampling come from
`aggregate_d4_predicted_causal` so there is one implementation of each.

Any row produced here is a **diagnostic**: the promotion gate lives in the
aggregator, and nothing printed here may be substituted for it.
"""

from __future__ import annotations

import argparse
import json
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

SIDE = len(FACTUALITY_LABELS)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _pooled_labels(root: Path, arm: str) -> dict[str, str]:
    labels: dict[str, str] = {}
    for fold in range(1, 6):
        fold_labels = _load(root / arm / f"fold-{fold}" / "evaluation_labels.json")
        overlap = set(fold_labels) & set(labels)
        if overlap:
            raise ValueError(f"{root}/{arm}: {len(overlap)} mentions scored twice")
        labels.update(fold_labels)
    return labels


def compare(
    *, repo: Path, cv: Path, source: Path, left: tuple[Path, str], right: tuple[Path, str]
) -> dict:
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

    sides = {}
    matrices = {}
    for name, (root, arm) in (("left", left), ("right", right)):
        labels = _pooled_labels(root, arm)
        if set(labels) != set(gold):
            raise ValueError(f"{name}: pooled mention cover mismatch")
        matrix = per_document_matrices(document_ids, mentions_by_document, gold, labels)
        matrices[name] = matrix
        pooled = matrix.sum(axis=0).reshape(SIDE, SIDE)
        sides[name] = {
            "runs": str(root),
            "arm": arm,
            "macro_f1": _macro_f1(pooled),
            "per_class_f1": _class_f1(pooled),
        }

    return {
        "schema_version": "ekg.d4_label_dump_comparison.v1",
        "diagnostic_only": True,
        "coverage": {"documents": len(document_ids), "mentions": len(gold)},
        "left": sides["left"],
        "right": sides["right"],
        "left_minus_right": paired_bootstrap(
            matrices["left"], matrices["right"], draws=10000, seed=13
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--cv", required=True, type=Path)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--left-runs", required=True, type=Path)
    parser.add_argument("--left-arm", required=True)
    parser.add_argument("--right-runs", required=True, type=Path)
    parser.add_argument("--right-arm", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite: {args.output}")
    report = compare(
        repo=args.repo.resolve(),
        cv=args.cv.resolve(),
        source=args.source.resolve(),
        left=(args.left_runs.resolve(), args.left_arm),
        right=(args.right_runs.resolve(), args.right_arm),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({**report, "output_sha256": sha256_file(args.output)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
