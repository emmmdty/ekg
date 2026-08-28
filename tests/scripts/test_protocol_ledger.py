"""Final-valid access ledgers are append-only and their count never decreases."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def _load_script(name: str):
    path = Path(__file__).resolve().parents[2] / "scripts" / name
    spec = importlib.util.spec_from_file_location(name.removesuffix(".py"), path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


freeze = _load_script("freeze_v6_protocol.py")
verify = _load_script("verify_p1_scorer.py")


def _ledger(path: Path, count: int) -> None:
    path.write_text(
        json.dumps(
            {
                "schema_version": "ekg.final_valid_access.v1",
                "historical_final_access_disclosed": True,
                "v6_confirmatory_eval_count": count,
                "entries": [],
            }
        ),
        encoding="utf-8",
    )


def test_freezer_preserves_existing_confirmatory_count(tmp_path: Path) -> None:
    root = tmp_path / "protocol"
    root.mkdir()
    _ledger(root / "access_ledger.json", 3)
    valid = tmp_path / "valid.jsonl"
    valid.write_text('{"id":"d1"}\n', encoding="utf-8")

    freeze._update_access_ledger(root, [valid])

    result = json.loads((root / "access_ledger.json").read_text(encoding="utf-8"))
    assert result["v6_confirmatory_eval_count"] == 3
    assert len(result["entries"]) == 1


def test_scorer_fixture_preserves_existing_confirmatory_count(tmp_path: Path) -> None:
    output = tmp_path / "protocol" / "evaluator"
    output.mkdir(parents=True)
    _ledger(output.parent / "access_ledger.json", 4)
    gold = tmp_path / "valid.jsonl"
    gold.write_text('{"id":"d1"}\n', encoding="utf-8")
    fixtures = tmp_path / "fixtures"
    fixtures.mkdir()

    verify._record_access(output, gold=gold, fixtures=fixtures)

    result = json.loads((output.parent / "access_ledger.json").read_text(encoding="utf-8"))
    assert result["v6_confirmatory_eval_count"] == 4
    assert len(result["entries"]) == 2
