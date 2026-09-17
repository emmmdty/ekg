"""The invariants a KGC export has to hold, because the opponent cannot check them.

If a query edge survives into the training graph the opponent trains on its own
answers and its row is worthless; if the candidate file drifts out of step with
the test file the masking silently scores the wrong 512 entities. Neither would
raise anything in their code, so both are asserted here.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest
from tests.scripts.test_freeze_e3_evaluation_unit import _document

ROOT = Path(__file__).resolve().parents[2]


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / f"scripts/{name}.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


exporter = _load("export_cgep_as_kgc")
freezer = _load("freeze_e3_evaluation_unit")


def _numbered(path: Path) -> list[str]:
    lines = path.read_text(encoding="utf-8").strip("\n").split("\n")
    assert int(lines[0]) == len(lines) - 1, f"{path.name}: count line disagrees with the body"
    return lines[1:]


@pytest.fixture
def export(tmp_path: Path) -> Path:
    import argparse

    train = tmp_path / "train.jsonl"
    valid = tmp_path / "valid.jsonl"
    train.write_text(
        "\n".join(json.dumps(_document(f"tr{i}")) for i in range(4)) + "\n", encoding="utf-8"
    )
    valid.write_text(
        "\n".join(json.dumps(_document(f"va{i}")) for i in range(3)) + "\n", encoding="utf-8"
    )
    freezer.freeze(
        argparse.Namespace(
            repo=ROOT, source=valid, seed=209, min_nodes=4, no_subevent=False,
            candidates=4, expect_instances=3, output=tmp_path / "unit", verify=None,
        )
    )
    out = tmp_path / "CGEP-MAVEN"
    argv = [
        "export_cgep_as_kgc", "--unit", str(tmp_path / "unit"),
        "--train", str(train), "--valid", str(valid), "--output", str(out),
        "--simkgc", str(tmp_path / "CGEP-MAVEN-simkgc"),
    ]
    old, sys.argv = sys.argv, argv
    try:
        assert exporter.main() == 0
    finally:
        sys.argv = old
    return out


def test_no_query_edge_survives_into_the_training_graph(export: Path) -> None:
    train = {tuple(line.split()) for line in _numbered(export / "train2id.txt")}
    dev = {tuple(line.split()) for line in _numbered(export / "valid2id.txt")}
    test = {tuple(line.split()) for line in _numbered(export / "test2id.txt")}
    assert test, "fixture produced no queries"
    assert not (test & train), "a CGEP answer is in the opponent's training graph"
    assert not (test & dev), "a CGEP answer is in the opponent's dev set"
    assert not (train & dev), "the dev slice was not removed from train"


def test_the_candidate_file_stays_in_step_with_the_test_file(export: Path) -> None:
    test = [line.split() for line in _numbered(export / "test2id.txt")]
    candidates = [set(line.split()) for line in _numbered(export / "test_candidates.txt")]
    assert len(candidates) == len(test)
    for (head, tail, _), pool in zip(test, candidates, strict=True):
        assert tail in pool, "the gold successor is not among its own candidates"
        assert head not in {tail}, "anchor and gold collided"


def test_every_id_file_is_readable_by_their_loader(export: Path) -> None:
    """`helper.read`/`read_file` assert the count line and split on tab or space."""
    n_ent = len(_numbered(export / "entity2id.txt"))
    for name in ("entityid2name.txt", "entityid2description.txt"):
        rows = _numbered(export / name)
        assert len(rows) == n_ent
        assert all(len(row.split("\t")) == 2 for row in rows), f"{name}: not id<TAB>text"
    for stem in ("train", "valid", "test"):
        for row in _numbered(export / f"{stem}2id.txt"):
            head, tail, rel = (int(x) for x in row.split(" "))
            assert 0 <= head < n_ent and 0 <= tail < n_ent and 0 <= rel < 3


def test_a_drifted_unit_is_refused(export: Path) -> None:
    unit = export.parent / "unit"
    queries = unit / "queries.jsonl"
    queries.write_text(queries.read_text(encoding="utf-8").replace("va0", "va0 "), "utf-8")
    argv = [
        "export_cgep_as_kgc", "--unit", str(unit),
        "--train", str(export.parent / "train.jsonl"),
        "--valid", str(export.parent / "valid.jsonl"),
        "--output", str(export.parent / "again"),
    ]
    old, sys.argv = sys.argv, argv
    try:
        with pytest.raises(SystemExit, match="unit drifted"):
            exporter.main()
    finally:
        sys.argv = old


def test_both_formats_describe_the_same_queries_in_the_same_order(export: Path) -> None:
    """Two opponents, one question set -- or their two rows are not comparable."""
    simkgc = export.parent / "CGEP-MAVEN-simkgc"
    entity_id = dict(line.split("\t") for line in _numbered(export / "entity2id.txt"))
    csprom = [line.split() for line in _numbered(export / "test2id.txt")]
    other = json.loads((simkgc / "test.txt.json").read_text(encoding="utf-8"))
    assert len(other) == len(csprom)
    for (head, tail, _), row in zip(csprom, other, strict=True):
        assert entity_id[row["head_id"]] == head
        assert entity_id[row["tail_id"]] == tail

    pools = json.loads((simkgc / "test_candidates.json").read_text(encoding="utf-8"))
    mirrored = [set(line.split()) for line in _numbered(export / "test_candidates.txt")]
    assert len(pools) == len(mirrored)
    for pool, expected in zip(pools, mirrored, strict=True):
        assert {entity_id[c] for c in pool} == expected
