"""The opponent scorer's job is to refuse a dump that does not match the export.

Every check here guards a way an opponent row could look fine and be wrong: a
shifted row index, a shrunken denominator, a candidate set that drifted from the
frozen one. The metric itself is `succession/metrics.py`, already tested.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location(
    "score_kgc_opponent", ROOT / "scripts/score_kgc_opponent.py"
)
assert _spec and _spec.loader
scorer = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(scorer)


@pytest.fixture
def export(tmp_path: Path) -> Path:
    out = tmp_path / "CGEP-MAVEN"
    out.mkdir()
    # Two queries: gold 1 among {0,1,2}, gold 4 among {3,4,5}.
    (out / "test2id.txt").write_text("2\n0 1 0\n3 4 1\n", encoding="utf-8")
    (out / "test_candidates.txt").write_text("2\n0 1 2\n3 4 5\n", encoding="utf-8")
    (out / "export_manifest.json").write_text(
        json.dumps({"fidelity": "(b)", "unit": {"sha256": "x"},
                    "differences_from_the_published_setting": []}),
        encoding="utf-8",
    )
    return out


def _dump(path: Path, rows: list[dict]) -> Path:
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    return path


def _run(export: Path, dump: Path, out: Path) -> int:
    argv = ["score_kgc_opponent", "--scores", str(dump), "--export", str(export),
            "--name", "T", "--output", str(out)]
    old, sys.argv = sys.argv, argv
    try:
        return scorer.main()
    finally:
        sys.argv = old


def test_a_clean_dump_scores_with_our_metric(export: Path, tmp_path: Path) -> None:
    dump = _dump(tmp_path / "s.jsonl", [
        {"row": 0, "gold": 1, "candidates": [0, 1, 2], "scores": [0.1, 0.9, 0.5]},
        {"row": 1, "gold": 4, "candidates": [3, 4, 5], "scores": [0.9, 0.2, 0.5]},
    ])
    out = tmp_path / "r.json"
    assert _run(export, dump, out) == 0
    report = json.loads(out.read_text(encoding="utf-8"))
    # gold ranks 0-based: query 0 is rank 0, query 1 is rank 2 -> MRR = (1 + 1/3)/2
    assert report["metrics"]["mrr"] == pytest.approx((1.0 + 1.0 / 3.0) / 2)
    assert report["metrics"]["n"] == 2.0


def test_an_unscored_query_is_refused_rather_than_dropped(export: Path, tmp_path: Path) -> None:
    dump = _dump(tmp_path / "s.jsonl",
                 [{"row": 0, "gold": 1, "candidates": [0, 1, 2], "scores": [0.1, 0.9, 0.5]}])
    with pytest.raises(SystemExit, match="were not scored"):
        _run(export, dump, tmp_path / "r.json")


def test_a_shifted_row_index_is_caught_by_the_gold(export: Path, tmp_path: Path) -> None:
    dump = _dump(tmp_path / "s.jsonl", [
        {"row": 0, "gold": 4, "candidates": [3, 4, 5], "scores": [0.9, 0.2, 0.5]},
        {"row": 1, "gold": 1, "candidates": [0, 1, 2], "scores": [0.1, 0.9, 0.5]},
    ])
    with pytest.raises(SystemExit, match="dumped gold"):
        _run(export, dump, tmp_path / "r.json")


def test_a_drifted_candidate_set_is_caught(export: Path, tmp_path: Path) -> None:
    dump = _dump(tmp_path / "s.jsonl", [
        {"row": 0, "gold": 1, "candidates": [0, 1, 9], "scores": [0.1, 0.9, 0.5]},
        {"row": 1, "gold": 4, "candidates": [3, 4, 5], "scores": [0.9, 0.2, 0.5]},
    ])
    with pytest.raises(SystemExit, match="candidate set differs"):
        _run(export, dump, tmp_path / "r.json")
