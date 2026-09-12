"""CLI-shape contracts for the A4 worker scripts (no torch, no encoder)."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from ekg.core.protocol import load_manifest_ids
from ekg.relations.data.maven_ere import load_maven_ere
from ekg.relations.pairs import PairExample, candidate_pairs

ROOT = Path(__file__).resolve().parents[2]


def _module(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / f"scripts/{name}.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


train_a4 = _module("train_a4_pair_evidence")
smoke_a4 = _module("smoke_a4_pair_evidence")


def test_an_unscoreable_family_gets_the_official_ignore_index() -> None:
    rows = [
        PairExample("d", "a", "b", 1, "cross_sentence", {"causal": "CAUSE"}),
        PairExample("d", "a", "c", 2, "cross_sentence", {}, frozenset({"causal"})),
    ]
    index = train_a4.label_indices({"causal": ("NONE", "CAUSE", "PRECONDITION")})

    # A pair touching a TIMEX is -100 for causal, exactly as the official
    # baseline emits it; scoring it as a negative would inflate the denominator.
    assert train_a4.family_targets(rows, "causal", index) == [1, train_a4.IGNORE_INDEX]


def test_rows_are_the_whole_candidate_universe_of_every_document(fixtures_dir) -> None:
    docs = list(load_maven_ere(fixtures_dir / "maven_ere" / "sample_with_text.jsonl"))
    grouped, total = train_a4.rows_by_document(docs, None)

    assert sorted(grouped) == sorted(doc.doc_id for doc in docs)
    assert total == sum(len(rows) for rows in grouped.values())
    for doc in docs:
        keys = [(row.head_id, row.tail_id) for row in grouped[doc.doc_id]]
        # Same pairs, same order as the frozen candidate enumeration.
        assert keys == candidate_pairs(doc)


def test_the_smoke_subset_refuses_to_silently_cover_fewer_documents(tmp_path: Path) -> None:
    source = tmp_path / "source.jsonl"
    source.write_text(
        "\n".join(json.dumps({"id": f"doc{i}"}) for i in range(3)) + "\n", encoding="utf-8"
    )
    output = tmp_path / "subset.jsonl"

    smoke_a4._subset(source, ["doc0", "doc2"], output)
    assert [json.loads(line)["id"] for line in output.read_text().splitlines()] == ["doc0", "doc2"]

    with pytest.raises(smoke_a4.SmokeError, match="smoke source covers"):
        smoke_a4._subset(source, ["doc0", "missing"], output)


def test_the_smoke_writes_manifests_the_frozen_loader_accepts(tmp_path: Path) -> None:
    path = smoke_a4._manifest(tmp_path / "m.json", ["doc0", "doc1"])
    assert load_manifest_ids(path) == ["doc0", "doc1"]


def test_non_finite_counterfactual_logits_fail_the_smoke() -> None:
    assert smoke_a4._finite([[0.1, -2.0], [3.0]])
    assert not smoke_a4._finite([float("inf")])
    assert not smoke_a4._finite([[0.0, float("nan")]])
