"""evaluate_relation_pairs re-scores an edge-list predictions dump in the
pair-classification setting (corpus-aggregated), so existing generative runs
become comparable with supervised pair baselines without re-running the LLM.
Feeding gold back as predictions must score micro F1 = 1.0 (contract check).
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

from ekg.relations.data.maven_ere import load_maven_ere

_REPO = Path(__file__).resolve().parents[2]
_FIXTURE = _REPO / "data" / "fixtures" / "maven_ere" / "sample.jsonl"


def _load_script():
    path = _REPO / "scripts" / "evaluate_relation_pairs.py"
    spec = importlib.util.spec_from_file_location("evaluate_relation_pairs", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


erp = _load_script()


def _candidate_digest() -> str:
    records = [
        json.loads(line)
        for line in _FIXTURE.read_text(encoding="utf-8").splitlines()
        if line
    ]
    by_id = erp.records_by_id(records, source=str(_FIXTURE))
    return erp.candidate_population_digest(by_id)[0]


def _run_main(argv: list[str]) -> int:
    old_argv = sys.argv
    sys.argv = argv
    try:
        return erp.main()
    finally:
        sys.argv = old_argv


def test_gold_as_predictions_scores_perfect(tmp_path: Path) -> None:
    docs = list(load_maven_ere(_FIXTURE))
    pred = tmp_path / "pred.jsonl"
    pred.write_text(
        "".join(
            json.dumps(
                {"doc_id": d.doc_id, "edges": [e.model_dump(mode="json") for e in d.gold_edges]},
                ensure_ascii=False,
            )
            + "\n"
            for d in docs
        ),
        encoding="utf-8",
    )
    out = tmp_path / "pair_eval.json"
    assert (
        _run_main(
            [
                "x",
                "--predictions", str(pred),
                "--gold-path", str(_FIXTURE),
                "--candidate-digest", _candidate_digest(),
                "--window-ceilings", "2", "24",
                "--output", str(out),
            ]
        )
        == 0
    )
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["pair"]["micro"]["f1"] == 1.0
    assert report["pair"]["diagnostics"]["hallucinated_pred_pairs"] == 0
    # the ceiling table is monotone in the window size
    ceilings = report["window_recall_ceiling"]
    assert ceilings["2"]["ceiling"] <= ceilings["24"]["ceiling"] <= 1.0


def test_windowed_setting_shrinks_universe(tmp_path: Path) -> None:
    docs = list(load_maven_ere(_FIXTURE))
    pred = tmp_path / "pred.jsonl"
    pred.write_text(
        "".join(
            json.dumps({"doc_id": d.doc_id, "edges": []}, ensure_ascii=False) + "\n"
            for d in docs
        ),
        encoding="utf-8",
    )
    out = tmp_path / "pair_eval.json"
    assert (
        _run_main(
            [
                "x",
                "--predictions", str(pred),
                "--gold-path", str(_FIXTURE),
                "--candidate-digest", _candidate_digest(),
                "--max-distance", "2",
                "--output", str(out),
            ]
        )
        == 0
    )
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["max_distance"] == 2
    assert report["pair"]["micro"]["recall"] == 0.0


def test_duplicate_prediction_document_is_rejected(tmp_path: Path) -> None:
    doc_id = next(iter(load_maven_ere(_FIXTURE))).doc_id
    pred = tmp_path / "pred.jsonl"
    row = json.dumps({"doc_id": doc_id, "edges": []})
    pred.write_text(f"{row}\n{row}\n", encoding="utf-8")

    with pytest.raises(ValueError, match="duplicate prediction document ID"):
        erp._load_predictions(pred)


@pytest.mark.parametrize("mode", ["missing", "extra"])
def test_prediction_document_set_must_match_gold(tmp_path: Path, mode: str) -> None:
    docs = list(load_maven_ere(_FIXTURE))
    rows = [{"doc_id": doc.doc_id, "edges": []} for doc in docs]
    if mode == "missing":
        rows.pop()
    else:
        rows.append({"doc_id": "unexpected", "edges": []})
    pred = tmp_path / "pred.jsonl"
    pred.write_text(
        "".join(json.dumps(row) + "\n" for row in rows),
        encoding="utf-8",
    )

    with pytest.raises(SystemExit, match="prediction document IDs differ from gold"):
        _run_main(
            [
                "x",
                "--predictions", str(pred),
                "--gold-path", str(_FIXTURE),
                "--candidate-digest", _candidate_digest(),
            ]
        )
