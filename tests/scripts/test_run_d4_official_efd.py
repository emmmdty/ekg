import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def _load_script(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


official = _load_script("run_d4_official_efd")


def _document() -> dict:
    return {
        "id": "d1",
        "events": [
            {"id": "E1", "mention": [{"id": "m1"}, {"id": "m2"}]},
            {"id": "E2", "mention": [{"id": "m3"}]},
        ],
        "causal_relation": {"CAUSE": [["E2", "E1"]], "PRECONDITION": []},
    }


def _source(tmp_path: Path) -> Path:
    path = tmp_path / "src.jsonl"
    path.write_text(json.dumps(_document(), sort_keys=True) + "\n", encoding="utf-8")
    return path


def test_gold_structure_passes_the_annotation_through_untouched(tmp_path: Path) -> None:
    written = official.write_split(
        source=_source(tmp_path),
        document_ids=["d1"],
        structure="gold",
        mention_edges=None,
        output=tmp_path / "out.jsonl",
    )

    assert written["cluster_relation_counts"] == {"CAUSE": 1, "PRECONDITION": 0}
    doc = json.loads((tmp_path / "out.jsonl").read_text(encoding="utf-8"))
    assert doc["causal_relation"] == {"CAUSE": [["E2", "E1"]], "PRECONDITION": []}


def test_predicted_structure_lifts_mentions_to_clusters_and_drops_self_edges(
    tmp_path: Path,
) -> None:
    edges = {
        "d1": {
            # m1 and m2 are the same cluster: that pair must not become a self-edge.
            "CAUSE": {("m3", "m1"), ("m1", "m2")},
            "PRECONDITION": {("m1", "m3")},
        }
    }

    written = official.write_split(
        source=_source(tmp_path),
        document_ids=["d1"],
        structure="predicted",
        mention_edges=edges,
        output=tmp_path / "out.jsonl",
    )

    doc = json.loads((tmp_path / "out.jsonl").read_text(encoding="utf-8"))
    assert doc["causal_relation"] == {
        "CAUSE": [["E2", "E1"]],
        "PRECONDITION": [["E1", "E2"]],
    }
    assert written["cluster_relation_counts"] == {"CAUSE": 1, "PRECONDITION": 1}


def test_predicted_structure_without_edges_fails_fast(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="requires decided mention edges"):
        official.write_split(
            source=_source(tmp_path),
            document_ids=["d1"],
            structure="predicted",
            mention_edges=None,
            output=tmp_path / "out.jsonl",
        )


def test_a_missing_document_is_not_silently_dropped(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="expected 2 documents"):
        official.write_split(
            source=_source(tmp_path),
            document_ids=["d1", "d2"],
            structure="gold",
            mention_edges=None,
            output=tmp_path / "out.jsonl",
        )
