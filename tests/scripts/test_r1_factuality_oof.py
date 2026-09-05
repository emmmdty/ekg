from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "run_r1_factuality_oof", ROOT / "scripts/run_r1_factuality_oof.py"
)
assert SPEC and SPEC.loader
oof = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(oof)


def test_commands_never_pass_evaluation_manifest_to_training(tmp_path: Path) -> None:
    args = argparse.Namespace(
        output=tmp_path / "out",
        source=tmp_path / "source.jsonl",
        pooling="cls",
        model=tmp_path / "model",
        epochs=12,
        lr=2e-5,
        alpha=0.5,
        batch_size=32,
        max_length=128,
        seed=13,
    )
    manifests = {
        "train": tmp_path / "train.json",
        "selection_dev": tmp_path / "selection.json",
        "evaluation": tmp_path / "evaluation.json",
    }

    train, evaluate = oof.commands(args, manifests)

    assert str(manifests["evaluation"]) not in train
    assert str(manifests["train"]) not in evaluate
    assert str(manifests["selection_dev"]) not in evaluate
    assert train[train.index("--seed") + 1] == "13"
    assert evaluate[evaluate.index("--manifest") + 1] == str(manifests["evaluation"])
