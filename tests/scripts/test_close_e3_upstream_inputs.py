"""What E3.1 has to catch before any Ch6 arm is scored.

The registry is only worth writing if it fails on the two ways an upstream layer
can be quietly wrong: a document the layer never covers (that arm is then weaker
than it looks, with no error anywhere), and an edge whose endpoint is not in the
unit's node frame (a different namespace wearing the same shape).
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / f"scripts/{name}.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


closer = _load("close_e3_upstream_inputs")
freezer = _load("freeze_e3_evaluation_unit")
from tests.scripts.test_freeze_e3_evaluation_unit import _document  # noqa: E402


def _factuality_document(doc: dict) -> dict:
    """The same document in MAVEN-FACT shape: tokenised, with a label per mention."""
    sentences = [s.split() for s in doc["sentences"]]
    return {
        "id": doc["id"],
        "tokens": sentences,
        "document": " ".join(" ".join(s) for s in sentences),
        "events": [
            {
                "id": event["id"],
                "type": event["type"],
                "mention": [
                    {**mention, "factuality": "CT+", "evidence_word": [], "evidence_offset": []}
                    for mention in event["mention"]
                ],
            }
            for event in doc["events"]
        ],
    }


@pytest.fixture
def world(tmp_path: Path) -> argparse.Namespace:
    """A three-document unit plus a relation dump that covers it exactly."""
    source = tmp_path / "valid.jsonl"
    docs = [_document(f"doc{i}") for i in range(3)]
    source.write_text("\n".join(json.dumps(d) for d in docs) + "\n", encoding="utf-8")
    freezer.freeze(
        argparse.Namespace(
            repo=ROOT, source=source, seed=209, min_nodes=4, no_subevent=False,
            candidates=4, expect_instances=3, output=tmp_path / "unit", verify=None,
        )
    )
    dump = tmp_path / "dump.jsonl"
    dump.write_text(
        "\n".join(
            json.dumps(
                {
                    "doc_id": d["id"],
                    "edges": [
                        {
                            "head_id": f"{d['id']}::m1",
                            "tail_id": f"{d['id']}::m2",
                            "relation_type": "causal",
                            "subtype": "CAUSE",
                        }
                    ],
                }
            )
            for d in docs
        )
        + "\n",
        encoding="utf-8",
    )
    fact = tmp_path / "fact.jsonl"
    fact.write_text(
        "\n".join(json.dumps(_factuality_document(d)) for d in docs) + "\n", encoding="utf-8"
    )
    return argparse.Namespace(
        unit=tmp_path / "unit", ere=source, dump=dump, fact=fact, tmp=tmp_path
    )


def _run(world: argparse.Namespace, **overrides) -> int:
    import sys

    argv = [
        "close_e3_upstream_inputs",
        "--unit", str(world.unit),
        "--ere", str(world.ere),
        "--fact", str(overrides.get("fact", world.fact)),
        "--relation-dump", str(overrides.get("dump", world.dump)),
        "--no-write",
    ]
    old, sys.argv = sys.argv, argv
    try:
        return closer.main()
    finally:
        sys.argv = old


def test_a_dump_missing_a_document_fails_fast(world: argparse.Namespace) -> None:
    short = world.tmp / "short.jsonl"
    short.write_text(world.dump.read_text(encoding="utf-8").splitlines()[0] + "\n", "utf-8")
    with pytest.raises(SystemExit, match="unit documents"):
        _run(world, dump=short)


def test_an_endpoint_outside_the_node_frame_fails_fast(world: argparse.Namespace) -> None:
    stray = world.tmp / "stray.jsonl"
    rows = [json.loads(line) for line in world.dump.read_text(encoding="utf-8").splitlines()]
    rows[0]["edges"][0]["tail_id"] = "someotherdoc::mX"
    stray.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    with pytest.raises(SystemExit, match="outside the node frame"):
        _run(world, dump=stray)


def test_a_drifted_unit_fails_before_any_layer_is_read(world: argparse.Namespace) -> None:
    queries = world.unit / "queries.jsonl"
    queries.write_text(queries.read_text(encoding="utf-8").replace("doc0", "doc0 "), "utf-8")
    with pytest.raises(SystemExit, match="unit drifted"):
        _run(world)


def test_the_registry_names_the_upstream_identity_of_each_condition(
    world: argparse.Namespace, capsys: pytest.CaptureFixture[str]
) -> None:
    assert _run(world) == 0
    out = capsys.readouterr().out
    assert "status=closed_except_factuality" in out
    assert "predicted=pending" in out
