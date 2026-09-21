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


build = _load_script("build_d4_gold_sidecars")
residual = _load_script("train_d4_predicted_causal")

WEIGHTS = {
    "NONE": 0.5834365142779171,
    "CAUSE": 7.695400460634976,
    "PRECONDITION": 4.694399765188356,
}


def _source(path: Path) -> Path:
    rows = [
        {"doc_id": "d1", "head_mention_id": "m1", "tail_mention_id": "m2",
         "p_none": 0.9, "p_cause": 0.05, "p_precondition": 0.05},
        {"doc_id": "d1", "head_mention_id": "m2", "tail_mention_id": "m1",
         "p_none": 0.2, "p_cause": 0.7, "p_precondition": 0.1},
    ]
    path.write_text("\n".join(json.dumps(r, sort_keys=True) for r in rows) + "\n", encoding="utf-8")
    return path


def test_gold_rewrite_flips_the_decided_edges_and_keeps_every_row(tmp_path, monkeypatch):
    source = _source(tmp_path / "src.jsonl")
    manifest = tmp_path / "m.json"
    manifest.write_text(json.dumps({"doc_ids": ["d1"]}), encoding="utf-8")
    relations = tmp_path / "rel.jsonl"
    relations.write_text("{}\n", encoding="utf-8")
    monkeypatch.setattr(build, "load_maven_ere", lambda path: [])
    # Gold says m1->m2 is a PRECONDITION and m2->m1 is nothing -- the exact
    # opposite of what the predicted sidecar decided.
    monkeypatch.setattr(
        build, "gold_pair_labels", lambda doc, **kw: {("m1", "m2"): "PRECONDITION"}
    )

    class _Doc:
        doc_id = "d1"

    monkeypatch.setattr(build, "load_maven_ere", lambda path: [_Doc()])
    output = tmp_path / "gold.jsonl"
    report = build.build(
        source=source, manifest=manifest, relation_source=relations, output=output
    )

    assert report["deployable"] is False
    assert report["rows"] == 2
    assert report["gold_label_counts"] == {"NONE": 1, "CAUSE": 0, "PRECONDITION": 1}
    edges = residual.load_edges(output, WEIGHTS, arm="full", fold=1, document_ids=["d1"])
    assert [(e.head_mention_id, e.tail_mention_id, e.subtype) for e in edges["d1"]] == [
        ("m1", "m2", "PRECONDITION")
    ]
    assert edges["d1"][0].confidence == pytest.approx(build.CERTAIN)


def test_gold_rewrite_refuses_to_overwrite(tmp_path):
    output = tmp_path / "gold.jsonl"
    output.write_text("occupied\n", encoding="utf-8")

    with pytest.raises(FileExistsError):
        build.build(
            source=_source(tmp_path / "src.jsonl"),
            manifest=tmp_path / "m.json",
            relation_source=tmp_path / "rel.jsonl",
            output=output,
        )
