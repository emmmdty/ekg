from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import pytest

from ekg.core.stage_bundle import model_content_digest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "run_d4_relation_crossfit", ROOT / "scripts/run_d4_relation_crossfit.py"
)
assert SPEC and SPEC.loader
crossfit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(crossfit)


def test_frozen_commands_keep_evaluation_out_of_training(tmp_path: Path) -> None:
    plan = ROOT / "runs/stages/R1/r1-v62-20260920/d4_crossfit_plan.json"
    fold_data = crossfit.validate_fold(ROOT, plan, 1)
    args = argparse.Namespace(
        repo=ROOT,
        plan=plan.resolve(),
        fold=1,
        model=tmp_path / "model",
        output=tmp_path / "fold-1",
    )
    training_source = args.output / "training_source.jsonl"

    train, dump = crossfit.commands(args, fold_data, training_source)

    evaluation = str(fold_data["manifests"]["evaluation"])
    assert evaluation not in train
    assert evaluation in dump
    assert str(fold_data["source"]) not in train
    assert str(training_source) in train
    assert train[train.index("--epochs") + 1] == "50"
    assert train[train.index("--family-loss-rates") + 1] == (
        "temporal=2,causal=4,subevent=4"
    )
    assert "--save-best-by-family" in train
    assert dump[dump.index("--checkpoint") + 1].endswith("by_family/causal")


def test_materialized_source_contains_only_train_and_selection(tmp_path: Path) -> None:
    source = tmp_path / "source.jsonl"
    source.write_text(
        "\n".join(json.dumps({"id": doc_id}) for doc_id in ("a", "b", "c")) + "\n",
        encoding="utf-8",
    )
    train = tmp_path / "train.json"
    dev = tmp_path / "dev.json"
    train.write_text(json.dumps({"doc_ids": ["a"]}), encoding="utf-8")
    dev.write_text(json.dumps({"doc_ids": ["b"]}), encoding="utf-8")
    output = tmp_path / "materialized.jsonl"

    crossfit._materialize_training_source(source, train, dev, output)

    ids = [json.loads(line)["id"] for line in output.read_text().splitlines()]
    assert ids == ["a", "b"]


def test_relation_backbone_pin_rejects_content_drift(tmp_path: Path) -> None:
    model = tmp_path / "model"
    model.mkdir()
    config = model / "config.json"
    config.write_text("frozen", encoding="utf-8")
    plan = {
        "inputs": {
            "relation_model": {
                "content_sha256": model_content_digest(model),
            }
        }
    }

    assert crossfit.validate_model(plan, model) == model_content_digest(model)
    config.write_text("drifted", encoding="utf-8")
    with pytest.raises(crossfit.D4CrossfitError, match="model content hash mismatch"):
        crossfit.validate_model(plan, model)
