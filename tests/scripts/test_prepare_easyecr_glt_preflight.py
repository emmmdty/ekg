from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
_SCRIPT = _ROOT / "scripts" / "prepare_easyecr_glt_preflight.py"
_SPEC = importlib.util.spec_from_file_location("prepare_easyecr_glt_preflight", _SCRIPT)
assert _SPEC is not None and _SPEC.loader is not None
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
PreflightError = _MODULE.PreflightError
prepare = _MODULE.prepare


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def _write_source(path: Path) -> None:
    records = []
    for index in range(6):
        records.append(
            {
                "id": f"doc-{index}",
                "title": f"title {index}",
                "tokens": [["event", str(index)]],
                "sentences": [f"event {index}"],
                "events": [
                    {
                        "id": f"event-{index}",
                        "type": "Test.Type",
                        "type_id": 1,
                        "mention": [
                            {
                                "id": f"mention-{index}",
                                "sent_id": 0,
                                "offset": [0, 1],
                                "trigger_word": "event",
                            }
                        ],
                    }
                ],
            }
        )
    path.write_text("".join(json.dumps(record) + "\n" for record in records), encoding="utf-8")


def _manifest(path: Path, *, role: str, doc_ids: list[str], source_sha256: str) -> None:
    _write_json(
        path,
        {
            "dataset": "maven_ere",
            "doc_count": len(doc_ids),
            "doc_ids": doc_ids,
            "source_sha256": source_sha256,
            "split_role": role,
        },
    )


def test_prepare_freezes_disjoint_selection_and_unlabeled_evaluation(tmp_path: Path) -> None:
    source = tmp_path / "source.jsonl"
    _write_source(source)
    source_sha256 = _sha256(source)
    train_manifest = tmp_path / "train.json"
    evaluation_manifest = tmp_path / "evaluation.json"
    _manifest(
        train_manifest,
        role="train",
        doc_ids=[f"doc-{index}" for index in range(4)],
        source_sha256=source_sha256,
    )
    _manifest(
        evaluation_manifest,
        role="internal-dev",
        doc_ids=["doc-4", "doc-5"],
        source_sha256=source_sha256,
    )
    p1_protocol = tmp_path / "protocol.json"
    _write_json(p1_protocol, {"identity": "test"})
    p1_sha256 = _sha256(p1_protocol)

    report = prepare(
        source=source,
        train_manifest=train_manifest,
        evaluation_manifest=evaluation_manifest,
        p1_protocol=p1_protocol,
        expected_p1_protocol_sha256=p1_sha256,
        output=tmp_path / "one",
        selection_size=2,
    )
    assert report["split_counts"] == {"evaluation": 2, "selection_dev": 2, "training": 2}
    selection_path = tmp_path / "one" / "selection_manifest.json"
    selection = json.loads(selection_path.read_text(encoding="utf-8"))
    assert set(selection["doc_ids"]).isdisjoint({"doc-4", "doc-5"})
    test_path = tmp_path / "one" / "evaluation-test.jsonl"
    test_record = json.loads(test_path.read_text(encoding="utf-8").splitlines()[0])
    assert "events" not in test_record
    assert test_record["event_mentions"][0]["type"] == "Test.Type"

    prepare(
        source=source,
        train_manifest=train_manifest,
        evaluation_manifest=evaluation_manifest,
        p1_protocol=p1_protocol,
        expected_p1_protocol_sha256=p1_sha256,
        output=tmp_path / "two",
        selection_size=2,
    )
    assert (tmp_path / "one" / "selection_manifest.json").read_bytes() == (
        tmp_path / "two" / "selection_manifest.json"
    ).read_bytes()


def test_prepare_rejects_evaluation_overlap(tmp_path: Path) -> None:
    source = tmp_path / "source.jsonl"
    _write_source(source)
    source_sha256 = _sha256(source)
    train_manifest = tmp_path / "train.json"
    evaluation_manifest = tmp_path / "evaluation.json"
    _manifest(
        train_manifest,
        role="train",
        doc_ids=["doc-0", "doc-1", "doc-2", "doc-3"],
        source_sha256=source_sha256,
    )
    _manifest(
        evaluation_manifest,
        role="internal-dev",
        doc_ids=["doc-3", "doc-4", "doc-5"],
        source_sha256=source_sha256,
    )
    p1_protocol = tmp_path / "protocol.json"
    _write_json(p1_protocol, {"identity": "test"})

    with pytest.raises(PreflightError, match="overlap"):
        prepare(
            source=source,
            train_manifest=train_manifest,
            evaluation_manifest=evaluation_manifest,
            p1_protocol=p1_protocol,
            expected_p1_protocol_sha256=_sha256(p1_protocol),
            output=tmp_path / "out",
            selection_size=2,
        )
