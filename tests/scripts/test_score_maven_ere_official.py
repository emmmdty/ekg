"""The frozen official scorer must bind code, population, and output provenance."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

from ekg.relations.maven_ere_official import (
    candidate_population_digest,
    gold_to_official_prediction,
    records_by_id,
)

_REPO = Path(__file__).resolve().parents[2]
_PROTOCOL = _REPO / "data" / "protocols" / "v6"
_SCRIPT = _REPO / "scripts" / "score_maven_ere_official.py"
_SPEC = importlib.util.spec_from_file_location("score_maven_ere_official", _SCRIPT)
assert _SPEC and _SPEC.loader
scorer = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(scorer)


def _run_main(argv: list[str]) -> int:
    previous = sys.argv
    sys.argv = argv
    try:
        return scorer.main()
    finally:
        sys.argv = previous


def _candidate_digest(gold: Path) -> str:
    records = [
        json.loads(line)
        for line in gold.read_text(encoding="utf-8").splitlines()
        if line
    ]
    return candidate_population_digest(records_by_id(records, source=str(gold)))[0]


def _write_gold_self(gold: Path, pred: Path) -> None:
    records = [
        json.loads(line)
        for line in gold.read_text(encoding="utf-8").splitlines()
        if line
    ]
    pred.write_text(
        "".join(json.dumps(gold_to_official_prediction(record)) + "\n" for record in records),
        encoding="utf-8",
    )


def test_gold_self_report_binds_all_provenance(tmp_path: Path) -> None:
    gold = _PROTOCOL / "baselines" / "fixture" / "gold.jsonl"
    pred = tmp_path / "gold_prediction.jsonl"
    _write_gold_self(gold, pred)
    evaluator = _PROTOCOL / "tools" / "maven_ere_evaluate.py"
    source_lock = _PROTOCOL / "source_lock.json"
    output = tmp_path / "metrics.json"
    argv = [
        "score_maven_ere_official.py",
        "--evaluator", str(evaluator),
        "--source-lock", str(source_lock),
        "--gold", str(gold),
        "--pred", str(pred),
        "--candidate-digest", _candidate_digest(gold),
        "--output", str(output),
    ]

    assert _run_main(argv) == 0
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["schema_version"] == "ekg.maven_ere_official_metrics.v2"
    assert set(report["hashes"]) == {
        "evaluator",
        "gold",
        "predictions",
        "source_lock",
    }
    assert report["command_argv"] == argv
    assert report["population"]["candidate_id_digest"] == _candidate_digest(gold)
    assert all(value == pytest.approx(100.0) for value in report["scores"].values())


def test_modified_evaluator_is_rejected_before_scoring(tmp_path: Path) -> None:
    gold = _PROTOCOL / "baselines" / "fixture" / "gold.jsonl"
    pred = _PROTOCOL / "evaluator" / "gold_prediction.jsonl"
    evaluator = tmp_path / "evaluate.py"
    evaluator.write_bytes(
        (_PROTOCOL / "tools" / "maven_ere_evaluate.py").read_bytes() + b"\n# tampered\n"
    )

    with pytest.raises(SystemExit, match="evaluator hash mismatch"):
        _run_main(
            [
                "score_maven_ere_official.py",
                "--evaluator", str(evaluator),
                "--source-lock", str(_PROTOCOL / "source_lock.json"),
                "--gold", str(gold),
                "--pred", str(pred),
                "--candidate-digest", _candidate_digest(gold),
            ]
        )
