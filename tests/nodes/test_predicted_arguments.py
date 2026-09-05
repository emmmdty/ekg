from __future__ import annotations

import json

import pytest

from ekg.core.schema import EventNode, EvidenceSpan
from ekg.nodes.predicted_arguments import apply_predicted_arguments


def _node() -> EventNode:
    return EventNode(
        event_id="d::m1",
        event_type="Attack",
        doc_id="d",
        trigger="attacked",
        trigger_evidence=[
            EvidenceSpan(doc_id="d", char_start=6, char_end=14, sent_id=0, text="attacked")
        ],
        metadata={"event": "e1"},
    )


def test_predicted_arguments_bind_exact_mention_local_spans(tmp_path) -> None:
    path = tmp_path / "predictions.jsonl"
    path.write_text(
        json.dumps(
            {
                "doc_id": "d",
                "mention_id": "d::m1",
                "status": "ok",
                "roles": {
                    "participant": [{"text": "Alice", "char_start": 0, "char_end": 5}],
                    "place": [{"text": "Rome", "char_start": 15, "char_end": 19}],
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )
    node = _node()

    doc = type(
        "Doc",
        (),
        {"doc_id": "d", "doc_text": "Alice attacked Rome.", "nodes": [node]},
    )()
    apply_predicted_arguments([doc], path)

    assert node.arguments == {"participant": "Alice", "place": "Rome"}
    assert node.argument_evidence["place"][0].text == "Rome"
    assert node.metadata["argument_source"] == "predicted_mention_local"


def test_predicted_arguments_require_one_valid_row_per_mention(tmp_path) -> None:
    path = tmp_path / "predictions.jsonl"
    path.write_text("", encoding="utf-8")
    doc = type("Doc", (), {"doc_id": "d", "doc_text": "Alice attacked Rome.", "nodes": [_node()]})()

    with pytest.raises(ValueError, match="missing predictions"):
        apply_predicted_arguments([doc], path)
