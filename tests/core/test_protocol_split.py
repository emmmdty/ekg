"""The one split implementation every chapter's trainer must use."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pytest

from ekg.core.protocol import load_manifest_ids, split_docs_by_manifests


@dataclass
class _Doc:
    doc_id: str


def _manifest(path: Path, ids: list[str]) -> Path:
    path.write_text(json.dumps({"doc_ids": ids}), encoding="utf-8")
    return path


def test_split_follows_manifest_order_not_source_order(tmp_path: Path) -> None:
    """Manifest order makes the split reproducible from the manifest alone."""
    docs = [_Doc("d1"), _Doc("d2"), _Doc("d3")]
    train = _manifest(tmp_path / "t.json", ["d3", "d1"])
    dev = _manifest(tmp_path / "d.json", ["d2"])

    train_docs, dev_docs = split_docs_by_manifests(docs, train, dev)

    assert [d.doc_id for d in train_docs] == ["d3", "d1"]
    assert [d.doc_id for d in dev_docs] == ["d2"]


def test_overlap_omission_and_missing_ids_are_all_rejected(tmp_path: Path) -> None:
    docs = [_Doc("d1"), _Doc("d2"), _Doc("d3")]

    with pytest.raises(ValueError, match="overlap"):
        split_docs_by_manifests(
            docs, _manifest(tmp_path / "a.json", ["d1", "d2"]),
            _manifest(tmp_path / "b.json", ["d2", "d3"]),
        )
    # a document present in the source but named by neither manifest is a silent
    # sample loss, so it must fail rather than shrink the corpus
    with pytest.raises(ValueError, match="omitted_from_manifests=1"):
        split_docs_by_manifests(
            docs, _manifest(tmp_path / "c.json", ["d1"]),
            _manifest(tmp_path / "e.json", ["d2"]),
        )
    with pytest.raises(ValueError, match="missing_from_source=1"):
        split_docs_by_manifests(
            docs, _manifest(tmp_path / "f.json", ["d1", "d2", "d3"]),
            _manifest(tmp_path / "g.json", ["ghost"]),
        )


def test_duplicate_and_empty_manifests_are_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="duplicate"):
        load_manifest_ids(_manifest(tmp_path / "d.json", ["d1", "d1"]))
    with pytest.raises(ValueError, match="non-empty"):
        load_manifest_ids(_manifest(tmp_path / "e.json", []))
    with pytest.raises(ValueError, match="non-empty"):
        load_manifest_ids(_manifest(tmp_path / "n.json", [1]))


def test_frozen_fact_manifests_split_the_registered_corpus(tmp_path: Path) -> None:
    """The real P1 MAVEN-FACT manifests must partition without overlap."""
    root = Path(__file__).resolve().parents[2] / "data/protocols/v6/manifests"
    train = load_manifest_ids(root / "maven_fact_train.json")
    dev = load_manifest_ids(root / "maven_fact_internal-dev.json")

    assert not set(train) & set(dev)
    assert len(train) > len(dev) > 0
