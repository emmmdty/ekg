#!/usr/bin/env python
"""Freeze leakage-free, rare-label-balanced MAVEN-FACT cross-validation folds.

The public training split is divided into five document groups.  In run ``i``,
group ``i`` is evaluation-only, group ``i + 1`` selects the checkpoint, and the
other three groups train the model.  Rotating those roles yields exactly one
out-of-fold prediction per document without touching public valid/final-valid.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from ekg.core.stage_bundle import sha256_file
from ekg.relations.data.maven_fact import FACTUALITY_LABELS, load_maven_fact

SCHEMA_VERSION = "ekg.r1_factuality_cv.v1"
MANIFEST_SCHEMA_VERSION = "ekg.r1_factuality_cv_manifest.v1"


def _stable_hash(seed: int, *parts: object) -> str:
    text = ":".join((str(seed), *(str(part) for part in parts)))
    return hashlib.sha256(text.encode()).hexdigest()


def _label_counts(document) -> tuple[int, ...]:
    counts = Counter(mention.factuality for mention in document.mentions)
    return tuple(counts[label] for label in FACTUALITY_LABELS)


def _cost(
    mention_counts: list[int],
    document_counts: list[int],
    size: int,
    *,
    target_mentions: list[float],
    target_documents: list[float],
    target_size: int,
) -> float:
    mention_error = sum(
        ((actual - target) / max(target, 1.0)) ** 2
        for actual, target in zip(mention_counts, target_mentions, strict=True)
    )
    document_error = sum(
        ((actual - target) / max(target, 1.0)) ** 2
        for actual, target in zip(document_counts, target_documents, strict=True)
    )
    size_error = ((size - target_size) / target_size) ** 2
    return mention_error + document_error + size_error


def assign_groups(documents: list, *, folds: int, seed: int) -> list[list]:
    """Greedily balance mention and document support for every factuality label."""
    if folds < 3:
        raise ValueError("at least three folds are required for train/select/evaluate rotation")
    if len(documents) < folds:
        raise ValueError("fewer documents than folds")
    ids = [document.doc_id for document in documents]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate document IDs")

    vectors = {document.doc_id: _label_counts(document) for document in documents}
    total_mentions = [sum(v[i] for v in vectors.values()) for i in range(len(FACTUALITY_LABELS))]
    total_documents = [
        sum(vector[i] > 0 for vector in vectors.values())
        for i in range(len(FACTUALITY_LABELS))
    ]
    target_mentions = [value / folds for value in total_mentions]
    target_documents = [value / folds for value in total_documents]
    capacities = [len(documents) // folds + (i < len(documents) % folds) for i in range(folds)]

    # Documents carrying the rarest labels are placed first.  The stable hash is
    # the only tie-breaker, so input line order cannot change the assignment.
    ordered = sorted(
        documents,
        key=lambda document: (
            -max(
                vectors[document.doc_id][i] / max(total_mentions[i], 1)
                for i in range(len(FACTUALITY_LABELS))
            ),
            _stable_hash(seed, document.doc_id),
        ),
    )
    groups: list[list] = [[] for _ in range(folds)]
    mention_counts = [[0] * len(FACTUALITY_LABELS) for _ in range(folds)]
    document_counts = [[0] * len(FACTUALITY_LABELS) for _ in range(folds)]
    for document in ordered:
        vector = vectors[document.doc_id]
        choices: list[tuple[float, str, int]] = []
        for fold in range(folds):
            if len(groups[fold]) >= capacities[fold]:
                continue
            before = _cost(
                mention_counts[fold],
                document_counts[fold],
                len(groups[fold]),
                target_mentions=target_mentions,
                target_documents=target_documents,
                target_size=capacities[fold],
            )
            after = _cost(
                [a + b for a, b in zip(mention_counts[fold], vector, strict=True)],
                [
                    a + int(b > 0)
                    for a, b in zip(document_counts[fold], vector, strict=True)
                ],
                len(groups[fold]) + 1,
                target_mentions=target_mentions,
                target_documents=target_documents,
                target_size=capacities[fold],
            )
            choices.append((after - before, _stable_hash(seed, document.doc_id, fold), fold))
        fold = min(choices)[2]
        groups[fold].append(document)
        mention_counts[fold] = [
            a + b for a, b in zip(mention_counts[fold], vector, strict=True)
        ]
        document_counts[fold] = [
            a + int(b > 0)
            for a, b in zip(document_counts[fold], vector, strict=True)
        ]
    return groups


def _support(documents: list) -> dict[str, dict[str, int]]:
    result: dict[str, dict[str, int]] = {}
    for label in FACTUALITY_LABELS:
        result[label] = {
            "mention_count": sum(
                mention.factuality == label
                for document in documents
                for mention in document.mentions
            ),
            "document_support": sum(
                any(mention.factuality == label for mention in document.mentions)
                for document in documents
            ),
        }
    return result


def _write_manifest(
    path: Path,
    documents: list,
    *,
    fold: int,
    role: str,
    source: Path,
    source_sha256: str,
    source_records: int,
    seed: int,
) -> dict:
    payload = {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "dataset": "maven_fact",
        "fold": fold,
        "split_role": role,
        "doc_count": len(documents),
        "doc_ids": sorted(document.doc_id for document in documents),
        "support": _support(documents),
        "source_path": str(source),
        "source_sha256": source_sha256,
        "source_records": source_records,
        "selection": {
            "algorithm": "deterministic greedy balance of per-label mention/document support",
            "seed": seed,
            "manual_selection": False,
        },
        "final_valid_accessed": False,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "path": str(path),
        "sha256": sha256_file(path),
        "doc_count": len(documents),
        "support": payload["support"],
    }


def freeze(source: Path, output: Path, *, folds: int, seed: int) -> dict:
    documents = list(load_maven_fact(source))
    groups = assign_groups(documents, folds=folds, seed=seed)
    source_sha256 = sha256_file(source)
    all_ids = {document.doc_id for document in documents}
    fold_reports = []
    evaluation_ids: set[str] = set()
    for index in range(folds):
        evaluation = groups[index]
        selection = groups[(index + 1) % folds]
        training = [
            document
            for group_index, group in enumerate(groups)
            if group_index not in {index, (index + 1) % folds}
            for document in group
        ]
        role_ids = [
            {document.doc_id for document in role}
            for role in (training, selection, evaluation)
        ]
        if any(role_ids[i] & role_ids[j] for i in range(3) for j in range(i + 1, 3)):
            raise ValueError(f"fold {index + 1} roles overlap")
        if set().union(*role_ids) != all_ids:
            raise ValueError(f"fold {index + 1} does not partition the source")
        evaluation_ids.update(role_ids[2])
        fold_dir = output / f"fold-{index + 1}"
        fold_reports.append(
            {
                "fold": index + 1,
                "train": _write_manifest(
                    fold_dir / "train.json",
                    training,
                    fold=index + 1,
                    role="train",
                    source=source,
                    source_sha256=source_sha256,
                    source_records=len(documents),
                    seed=seed,
                ),
                "selection_dev": _write_manifest(
                    fold_dir / "selection-dev.json",
                    selection,
                    fold=index + 1,
                    role="selection-dev",
                    source=source,
                    source_sha256=source_sha256,
                    source_records=len(documents),
                    seed=seed,
                ),
                "evaluation": _write_manifest(
                    fold_dir / "evaluation.json",
                    evaluation,
                    fold=index + 1,
                    role="evaluation",
                    source=source,
                    source_sha256=source_sha256,
                    source_records=len(documents),
                    seed=seed,
                ),
            }
        )
    evaluation_count = sum(row["evaluation"]["doc_count"] for row in fold_reports)
    if evaluation_ids != all_ids or evaluation_count != len(all_ids):
        raise ValueError("evaluation folds are not an exact one-time cover of the source")

    balance = {}
    for label in FACTUALITY_LABELS:
        mentions = [row["evaluation"]["support"][label]["mention_count"] for row in fold_reports]
        documents_with_label = [
            row["evaluation"]["support"][label]["document_support"] for row in fold_reports
        ]
        balance[label] = {
            "evaluation_mention_min": min(mentions),
            "evaluation_mention_max": max(mentions),
            "evaluation_document_min": min(documents_with_label),
            "evaluation_document_max": max(documents_with_label),
        }
    report = {
        "schema_version": SCHEMA_VERSION,
        "status": "pass",
        "source": {
            "path": str(source),
            "sha256": source_sha256,
            "documents": len(documents),
            "support": _support(documents),
        },
        "config": {
            "folds": folds,
            "seed": seed,
            "rotation": "evaluation=i; selection_dev=(i+1) mod folds; train=remaining groups",
            "evaluation_unit": "document",
            "primary_metric": "five-class macro-F1 over pooled out-of-fold predictions",
            "paired_inference": "document-cluster bootstrap on the same pooled OOF documents",
            "checkpoint_selection": (
                "selection-dev only; evaluation is inaccessible until checkpoint freeze"
            ),
            "single_seed": 13,
            "additional_seeds_authorized": False,
            "final_valid_accessed": False,
        },
        "balance": balance,
        "folds": fold_reports,
    }
    summary = output / "factuality_cv.json"
    summary.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"[r1-factuality-cv] pass: wrote {summary}")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--folds", type=int, default=5)
    parser.add_argument("--seed", type=int, default=260904)
    args = parser.parse_args()
    if args.output.exists() and any(args.output.iterdir()):
        raise SystemExit(f"refusing to overwrite non-empty output: {args.output}")
    args.output.mkdir(parents=True, exist_ok=True)
    freeze(args.source, args.output, folds=args.folds, seed=args.seed)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
