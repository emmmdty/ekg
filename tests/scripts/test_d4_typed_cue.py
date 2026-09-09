"""Leakage and CLI contracts for the D4 typed-cue worker scripts."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "train_d4_typed_cue", ROOT / "scripts/train_d4_typed_cue.py"
)
assert SPEC and SPEC.loader
train_d4 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(train_d4)


def _manifest(path: Path, ids: list[str]) -> Path:
    path.write_text(json.dumps({"doc_ids": ids}), encoding="utf-8")
    return path


def test_training_source_is_exactly_train_plus_selection_dev(fixtures_dir, tmp_path: Path) -> None:
    source = fixtures_dir / "maven_fact" / "sample.jsonl"
    train, selection = train_d4._split_docs(
        source,
        _manifest(tmp_path / "train.json", ["fdoc1"]),
        _manifest(tmp_path / "selection.json", ["fdoc2"]),
    )
    assert [doc.doc_id for doc in train] == ["fdoc1"]
    assert [doc.doc_id for doc in selection] == ["fdoc2"]


def test_training_source_rejects_overlapping_train_and_selection(
    fixtures_dir, tmp_path: Path
) -> None:
    source = fixtures_dir / "maven_fact" / "sample.jsonl"
    with pytest.raises(ValueError, match="overlap"):
        train_d4._split_docs(
            source,
            _manifest(tmp_path / "train.json", ["fdoc1"]),
            _manifest(tmp_path / "selection.json", ["fdoc1"]),
        )
