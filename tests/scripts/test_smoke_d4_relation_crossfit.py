from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import pytest

from ekg.core.stage_bundle import model_content_digest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "smoke_d4_relation_crossfit", ROOT / "scripts/smoke_d4_relation_crossfit.py"
)
assert SPEC and SPEC.loader
smoke = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(smoke)


def test_smoke_contract_and_commands_are_bounded(tmp_path: Path) -> None:
    source = ROOT / "data/processed/maven_ere/train_smoke.jsonl"
    contract = smoke.smoke_contract(source)
    args = argparse.Namespace(
        repo=ROOT,
        source=source,
        model=tmp_path / "model",
        output=tmp_path / "output",
    )
    manifest = args.output / "evaluation_manifest.json"

    train, dump = smoke.commands(args, contract, manifest)

    assert contract["documents"] == 5
    assert contract["doc_ids"] == [
        "39c2db9e18cd4a02b9aa8c1a3c58aab7",
        "ab70a3e49966caa8c35f8b27fabea3ad",
        "6e8b453609327248f8613f78763dd02c",
        "79e2767b814f136745e35123957316b3",
        "9ee922c5c1afb72c9b49b057edc379a9",
    ]
    assert contract["ordered_mention_pairs"] == 5_198
    assert train[train.index("--epochs") + 1] == "1"
    assert train[train.index("--dev-docs") + 1] == "5"
    assert "--save-best-by-family" in train
    assert dump[dump.index("--checkpoint") + 1].endswith("by_family/causal")
    assert dump[dump.index("--expected-documents") + 1] == "5"


def test_smoke_validates_the_frozen_relation_backbone(tmp_path: Path) -> None:
    model = tmp_path / "model"
    model.mkdir()
    config = model / "config.json"
    config.write_text("frozen", encoding="utf-8")
    plan = tmp_path / "plan.json"
    plan.write_text(
        json.dumps(
            {
                "schema_version": "r1-v62-d4-crossfit-plan-v2",
                "inputs": {
                    "relation_model": {
                        "content_sha256": model_content_digest(model),
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    assert smoke.validate_model(plan, model) == model_content_digest(model)
    config.write_text("drifted", encoding="utf-8")
    with pytest.raises(smoke.D4SmokeError, match="model content hash mismatch"):
        smoke.validate_model(plan, model)
