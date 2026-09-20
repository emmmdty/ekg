import importlib.util
import json
from pathlib import Path

import pytest

from ekg.core.schema import EventNode, EvidenceSpan
from ekg.relations.data.maven_ere import RelationDocument
from ekg.relations.pairs import candidate_pairs

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "dump_relation_causal_posteriors",
    ROOT / "scripts/dump_relation_causal_posteriors.py",
)
assert SPEC is not None and SPEC.loader is not None
dump = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(dump)


def _document(doc_id: str) -> RelationDocument:
    nodes = [
        EventNode(
            event_id=f"{doc_id}::m{index}",
            event_type="Event",
            doc_id=doc_id,
            trigger=f"t{index}",
            trigger_evidence=[
                EvidenceSpan(
                    doc_id=doc_id,
                    char_start=index,
                    char_end=index + 1,
                    sent_id=0,
                    text=f"t{index}",
                )
            ],
        )
        for index in range(2)
    ]
    return RelationDocument(doc_id=doc_id, nodes=nodes, gold_edges=[], doc_text="t0 t1")


def _scorer(doc: RelationDocument):
    return {pair: (0.6, 0.3, 0.1) for pair in candidate_pairs(doc)}


def test_dump_causal_posteriors_writes_every_pair_without_gold(tmp_path: Path) -> None:
    output = tmp_path / "causal_posteriors.jsonl"

    report = dump.dump_causal_posteriors(
        [_document("d1"), _document("d2")],
        _scorer,
        output,
        expected_documents=2,
        expected_pairs=4,
    )

    rows = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
    assert report["documents"] == 2
    assert report["ordered_mention_pairs"] == 4
    assert len(rows) == 4
    assert all(set(row) == {
        "doc_id",
        "head_mention_id",
        "tail_mention_id",
        "p_none",
        "p_cause",
        "p_precondition",
    } for row in rows)


def test_dump_causal_posteriors_does_not_publish_partial_output(tmp_path: Path) -> None:
    output = tmp_path / "causal_posteriors.jsonl"

    with pytest.raises(ValueError, match="pair count mismatch"):
        dump.dump_causal_posteriors(
            [_document("d")],
            _scorer,
            output,
            expected_documents=1,
            expected_pairs=3,
        )

    assert not output.exists()


def test_dump_causal_posteriors_refuses_overwrite(tmp_path: Path) -> None:
    output = tmp_path / "causal_posteriors.jsonl"
    output.write_text("owned\n", encoding="utf-8")

    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        dump.dump_causal_posteriors(
            [_document("d")],
            _scorer,
            output,
            expected_documents=1,
            expected_pairs=2,
        )

    assert output.read_text(encoding="utf-8") == "owned\n"
