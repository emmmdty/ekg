#!/usr/bin/env python
"""Dump exhaustive causal posteriors for one frozen cross-fit evaluation fold.

The normal relation extractor emits only non-NONE edges. D4 instead needs the
full uncertainty vector for every ordered event-mention pair, including NONE.
This adapter binds inference to an explicit manifest and rejects any missing or
extra document, pair, class, or invalid probability before publishing output.
"""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path

from ekg.core.protocol import load_manifest_ids
from ekg.core.stage_bundle import sha256_file
from ekg.relations.data.maven_ere import RelationDocument, load_maven_ere
from ekg.relations.pairs import candidate_pairs
from ekg.relations.posteriors import causal_posterior_rows

Pair = tuple[str, str]
Scorer = Callable[[RelationDocument], Mapping[Pair, Sequence[float]]]


def select_manifest_documents(
    data_path: Path, manifest_path: Path
) -> list[RelationDocument]:
    """Load documents in manifest order and reject source/manifest identity drift."""
    docs = list(load_maven_ere(data_path))
    by_id = {doc.doc_id: doc for doc in docs}
    if len(by_id) != len(docs):
        raise ValueError("relation source contains duplicate document IDs")
    ids = load_manifest_ids(manifest_path)
    missing = set(ids) - by_id.keys()
    if missing:
        raise ValueError(f"manifest has {len(missing)} document IDs absent from source")
    return [by_id[doc_id] for doc_id in ids]


def dump_causal_posteriors(
    docs: Sequence[RelationDocument],
    scorer: Scorer,
    output: Path,
    *,
    expected_documents: int,
    expected_pairs: int,
) -> dict[str, object]:
    """Write an exhaustive JSONL atomically after corpus-level count checks."""
    if output.exists():
        raise FileExistsError(f"refusing to overwrite posterior output: {output}")
    if len(docs) != expected_documents:
        raise ValueError(
            f"document count mismatch: expected {expected_documents}, got {len(docs)}"
        )
    doc_ids = [doc.doc_id for doc in docs]
    if len(set(doc_ids)) != len(doc_ids):
        raise ValueError("selected documents contain duplicate document IDs")

    output.parent.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=output.parent,
        prefix=f".{output.name}.",
        suffix=".tmp",
        delete=False,
    )
    temporary = Path(handle.name)
    pair_count = 0
    try:
        with handle:
            for doc in docs:
                pairs = candidate_pairs(doc)
                rows = causal_posterior_rows(doc.doc_id, pairs, scorer(doc))
                for row in rows:
                    handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")))
                    handle.write("\n")
                pair_count += len(rows)
        if pair_count != expected_pairs:
            raise ValueError(
                f"pair count mismatch: expected {expected_pairs}, got {pair_count}"
            )
        os.replace(temporary, output)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise

    return {
        "documents": len(docs),
        "ordered_mention_pairs": pair_count,
        "output": str(output),
        "output_sha256": sha256_file(output),
    }


def checkpoint_hashes(checkpoint: Path) -> dict[str, str]:
    """Hash every checkpoint file so a posterior dump identifies its exact model."""
    if not checkpoint.is_dir():
        raise FileNotFoundError(f"checkpoint directory not found: {checkpoint}")
    files = [path for path in sorted(checkpoint.rglob("*")) if path.is_file()]
    if not files:
        raise ValueError(f"checkpoint directory is empty: {checkpoint}")
    return {
        path.relative_to(checkpoint).as_posix(): sha256_file(path)
        for path in files
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--checkpoint", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--metadata-output", required=True, type=Path)
    parser.add_argument("--expected-documents", required=True, type=int)
    parser.add_argument("--expected-pairs", required=True, type=int)
    parser.add_argument("--max-length", default=512, type=int)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.metadata_output.exists():
        raise FileExistsError(
            f"refusing to overwrite posterior metadata: {args.metadata_output}"
        )

    from ekg.relations.extractor.base import ExtractionContext
    from ekg.relations.extractor.supervised import SupervisedRelationExtractor

    docs = select_manifest_documents(args.data, args.manifest)
    extractor = SupervisedRelationExtractor(
        checkpoint_path=str(args.checkpoint),
        max_distance=None,
        max_length=args.max_length,
    )

    def score(doc: RelationDocument) -> Mapping[Pair, Sequence[float]]:
        context = ExtractionContext(doc_text={doc.doc_id: doc.doc_text})
        return extractor.predict_family_posteriors(
            doc.nodes,
            context,
            family="causal",
        )

    report = dump_causal_posteriors(
        docs,
        score,
        args.output,
        expected_documents=args.expected_documents,
        expected_pairs=args.expected_pairs,
    )
    metadata = {
        "schema_version": "ekg.relation_causal_posteriors.v1",
        **report,
        "candidate_universe": "all ordered non-self event-mention pairs",
        "class_order": ["NONE", "CAUSE", "PRECONDITION"],
        "gold_fields_present": False,
        "inputs": {
            "data": {"path": str(args.data), "sha256": sha256_file(args.data)},
            "manifest": {
                "path": str(args.manifest),
                "sha256": sha256_file(args.manifest),
            },
            "checkpoint": {
                "path": str(args.checkpoint),
                "files": checkpoint_hashes(args.checkpoint),
            },
        },
    }
    args.metadata_output.parent.mkdir(parents=True, exist_ok=True)
    args.metadata_output.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(metadata, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
