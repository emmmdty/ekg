"""What the frozen Ch6 evaluation unit has to guarantee before competitors run.

The unit exists so that arms scored weeks apart answer the identical questions.
Its whole value is that a drifted query set is *detected*, so that is what these
tests exercise: a clean round trip, a mutated unit, and a rebuild that no longer
yields the frozen number of instances.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "freeze_e3_evaluation_unit", ROOT / "scripts/freeze_e3_evaluation_unit.py"
)
assert SPEC and SPEC.loader
freezer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(freezer)


def _document(doc_id: str) -> dict:
    """5 events, one query edge: m4 is the only node with outdeg 0 and indeg 1.

    m1 -CAUSE-> m2 -PRECONDITION-> m3 -SUBEVENT_OF-> m5,  m2 -CAUSE-> m4,
    m1 -CAUSE-> m5 (so m5 has in-degree 2 and can never be gold).
    """
    triggers = ["alpha", "bravo", "charlie", "delta", "echo"]
    return {
        "id": doc_id,
        "sentences": [f"the {t} happened" for t in triggers],
        "events": [
            {
                "id": f"EVENT_{doc_id}_{i}",
                "type": f"Type_{i}",
                "mention": [
                    {"id": f"m{i}", "trigger_word": trigger, "sent_id": i - 1, "offset": [1, 2]}
                ],
            }
            for i, trigger in enumerate(triggers, start=1)
        ],
        "temporal_relations": {"BEFORE": [[f"EVENT_{doc_id}_1", f"EVENT_{doc_id}_3"]]},
        "causal_relations": {
            "CAUSE": [
                [f"EVENT_{doc_id}_1", f"EVENT_{doc_id}_2"],
                [f"EVENT_{doc_id}_2", f"EVENT_{doc_id}_4"],
                [f"EVENT_{doc_id}_1", f"EVENT_{doc_id}_5"],
            ],
            "PRECONDITION": [[f"EVENT_{doc_id}_2", f"EVENT_{doc_id}_3"]],
        },
        "subevent_relations": [[f"EVENT_{doc_id}_3", f"EVENT_{doc_id}_5"]],
    }


@pytest.fixture
def unit(tmp_path: Path) -> argparse.Namespace:
    source = tmp_path / "valid.jsonl"
    source.write_text(
        "\n".join(json.dumps(_document(f"doc{i}")) for i in range(3)) + "\n", encoding="utf-8"
    )
    args = argparse.Namespace(
        repo=ROOT,
        source=source,
        seed=209,
        min_nodes=4,
        no_subevent=False,
        candidates=4,
        expect_instances=3,
        output=tmp_path / "unit",
        verify=None,
    )
    freezer.freeze(args)
    args.verify, args.output = args.output, None
    return args


def test_a_clean_round_trip_reports_no_drift(unit: argparse.Namespace) -> None:
    manifest, drift = freezer.verify(unit)
    assert drift == []
    assert manifest["population"]["instances"] == 3
    assert manifest["population"]["documents_with_instances"] == 3
    assert manifest["status"] == "frozen"


def test_every_query_pins_the_six_fields_the_contract_names(
    unit: argparse.Namespace,
) -> None:
    lines = (unit.verify / "queries.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 3
    for line in lines:
        query = json.loads(line)
        assert set(query) == {
            "instance_id", "doc_id", "anchor", "relation", "gold", "label", "candidates"
        }
        # The gold successor is reachable only through the frozen label index,
        # so a shuffled candidate list cannot silently re-point the answer.
        assert query["candidates"][query["label"]] == query["gold"]
        assert query["anchor"] != query["gold"]


def test_a_mutated_unit_is_caught(unit: argparse.Namespace) -> None:
    queries = unit.verify / "queries.jsonl"
    first, *rest = queries.read_text(encoding="utf-8").splitlines()
    query = json.loads(first)
    query["candidates"] = list(reversed(query["candidates"]))
    queries.write_text(
        "\n".join([json.dumps(query, sort_keys=True, separators=(",", ":")), *rest]) + "\n",
        encoding="utf-8",
    )
    _, drift = freezer.verify(unit)
    assert any("on disk" in line for line in drift)


def test_a_source_that_no_longer_yields_the_frozen_count_fails_fast(
    unit: argparse.Namespace, tmp_path: Path
) -> None:
    unit.source.write_text(json.dumps(_document("doc0")) + "\n", encoding="utf-8")
    unit.output, unit.verify = tmp_path / "again", None
    with pytest.raises(SystemExit, match="instance count drifted"):
        freezer.freeze(unit)
