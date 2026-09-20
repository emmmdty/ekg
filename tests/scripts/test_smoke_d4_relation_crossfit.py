from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path

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
    assert contract["ordered_mention_pairs"] > 0
    assert train[train.index("--epochs") + 1] == "1"
    assert train[train.index("--dev-docs") + 1] == "5"
    assert "--save-best-by-family" in train
    assert dump[dump.index("--checkpoint") + 1].endswith("by_family/causal")
    assert dump[dump.index("--expected-documents") + 1] == "5"
