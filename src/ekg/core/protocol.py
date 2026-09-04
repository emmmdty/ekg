"""Shared protocol-split helpers used by every chapter's trainer.

Each chapter used to carve its own dev set: Ch2 by explicit manifests, Ch3 by a
positional slice of a shuffled list, Ch1 not at all. Three implementations of the
same idea is how split drift starts, and split drift silently invalidates every
cross-chapter comparison. One implementation, bound to explicit document IDs.

A ratio-based split is not equivalent: it depends on the shuffle seed and on the
source file's contents, so it cannot be re-derived from the frozen protocol and
cannot be checked against a manifest hash.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path
from typing import Protocol, TypeVar


class HasDocId(Protocol):
    doc_id: str


DocT = TypeVar("DocT", bound=HasDocId)


def load_manifest_ids(path: Path) -> list[str]:
    """Read a frozen manifest's document IDs, rejecting duplicates and emptiness."""
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    ids = payload.get("doc_ids")
    if (
        not isinstance(ids, list)
        or not ids
        or not all(isinstance(item, str) for item in ids)
    ):
        raise ValueError(f"{path} has no non-empty doc_ids list")
    if len(set(ids)) != len(ids):
        raise ValueError(f"{path} contains duplicate document IDs")
    return ids


def split_docs_by_manifests(
    docs: Sequence[DocT], train_manifest: Path, dev_manifest: Path
) -> tuple[list[DocT], list[DocT]]:
    """Split documents by explicit manifests, rejecting overlap or omission.

    Returns documents in *manifest* order rather than source order, so the split is
    reproducible from the manifest alone.
    """
    docs = list(docs)
    docs_by_id: dict[str, DocT] = {doc.doc_id: doc for doc in docs}
    if len(docs_by_id) != len(docs):
        raise ValueError("training source contains duplicate document IDs")
    train_ids = load_manifest_ids(train_manifest)
    dev_ids = load_manifest_ids(dev_manifest)
    overlap = set(train_ids) & set(dev_ids)
    if overlap:
        raise ValueError(f"train/dev manifests overlap on {len(overlap)} document IDs")
    selected = set(train_ids) | set(dev_ids)
    missing = selected - docs_by_id.keys()
    omitted = docs_by_id.keys() - selected
    if missing or omitted:
        raise ValueError(
            "manifest/source ID mismatch: "
            f"missing_from_source={len(missing)} omitted_from_manifests={len(omitted)}"
        )
    return [docs_by_id[item] for item in train_ids], [docs_by_id[item] for item in dev_ids]
