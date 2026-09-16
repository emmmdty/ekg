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
    assert node.metadata["argument_prediction_status"] == "ok"


def test_predicted_arguments_accept_explicit_partial_rejection(tmp_path) -> None:
    path = tmp_path / "predictions.jsonl"
    path.write_text(
        json.dumps(
            {
                "doc_id": "d",
                "mention_id": "d::m1",
                "status": "partial",
                "roles": {
                    "participant": [{"text": "Alice", "char_start": 0, "char_end": 5}]
                },
                "rejected": [
                    {"role": "place", "value": "Italy", "reason": "cannot align"}
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    node = _node()
    doc = type(
        "Doc", (), {"doc_id": "d", "doc_text": "Alice attacked Rome.", "nodes": [node]}
    )()

    apply_predicted_arguments([doc], path)

    assert node.arguments == {"participant": "Alice"}
    assert node.metadata["argument_prediction_status"] == "partial"


def test_predicted_arguments_reject_inconsistent_rejection_status(tmp_path) -> None:
    path = tmp_path / "predictions.jsonl"
    path.write_text(
        json.dumps(
            {
                "doc_id": "d",
                "mention_id": "d::m1",
                "status": "rejected",
                "roles": {},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    doc = type(
        "Doc", (), {"doc_id": "d", "doc_text": "Alice attacked Rome.", "nodes": [_node()]}
    )()

    with pytest.raises(ValueError, match="rejection metadata mismatch"):
        apply_predicted_arguments([doc], path)


def test_predicted_arguments_require_one_valid_row_per_mention(tmp_path) -> None:
    path = tmp_path / "predictions.jsonl"
    path.write_text("", encoding="utf-8")
    doc = type("Doc", (), {"doc_id": "d", "doc_text": "Alice attacked Rome.", "nodes": [_node()]})()

    with pytest.raises(ValueError, match="missing predictions"):
        apply_predicted_arguments([doc], path)


def _row(mention_id: str, doc_id: str = "d") -> str:
    return json.dumps(
        {
            "doc_id": doc_id,
            "mention_id": mention_id,
            "status": "ok",
            "roles": {"participant": [{"text": "Alice", "char_start": 0, "char_end": 5}]},
        }
    )


def test_a_wider_artifact_is_refused_unless_the_subset_is_declared(tmp_path) -> None:
    """Inference annotates a split of the corpus the trainer bound.

    C5 trains on all 2,913 documents and predicts 291 of them from the same
    artifact, so the other 2,622 are not drift. Subsetting the file instead
    would hand the two sides different artifacts, which is the mismatch this
    binding exists to catch -- so the subset is declared at the call site.
    """
    path = tmp_path / "predictions.jsonl"
    path.write_text(_row("d::m1") + "\n" + _row("other::m9", "other") + "\n", encoding="utf-8")
    node = _node()
    doc = type(
        "Doc", (), {"doc_id": "d", "doc_text": "Alice attacked Rome.", "nodes": [node]}
    )()

    with pytest.raises(ValueError, match="extra predictions=1"):
        apply_predicted_arguments([doc], path)

    apply_predicted_arguments([doc], path, allow_extra=True)
    assert node.metadata["argument_prediction_status"] == "ok"


def test_the_declared_subset_still_refuses_a_mention_it_cannot_annotate(tmp_path) -> None:
    """`allow_extra` drops one half of the guard, never the missing half."""
    path = tmp_path / "predictions.jsonl"
    path.write_text(_row("other::m9", "other") + "\n", encoding="utf-8")
    doc = type(
        "Doc", (), {"doc_id": "d", "doc_text": "Alice attacked Rome.", "nodes": [_node()]}
    )()

    with pytest.raises(ValueError, match="missing predictions=1"):
        apply_predicted_arguments([doc], path, allow_extra=True)
