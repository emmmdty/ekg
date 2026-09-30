from __future__ import annotations

from pathlib import Path

import pytest


def test_self_attentive_span_extractor_masks_padding_and_uses_inclusive_endpoints() -> None:
    torch = pytest.importorskip("torch")
    from baselines.easyecr.easyecr.external_code.allennlp_span_extractor import (
        SelfAttentiveSpanExtractor,
    )

    extractor = SelfAttentiveSpanExtractor(input_dim=2)
    with torch.no_grad():
        extractor._global_attention.weight.copy_(torch.tensor([[1.0, 0.0]]))
        extractor._global_attention.bias.zero_()

    sequence = torch.tensor([[[1.0, 10.0], [2.0, 20.0], [3.0, 30.0]]])
    spans = torch.tensor([[[0, 1], [1, 2], [0, 0]]])
    output = extractor(sequence, spans, span_indices_mask=torch.tensor([[1, 1, 0]]))

    first_weights = torch.softmax(torch.tensor([1.0, 2.0]), dim=0)
    second_weights = torch.softmax(torch.tensor([2.0, 3.0]), dim=0)
    expected = torch.stack(
        [
            first_weights @ sequence[0, :2],
            second_weights @ sequence[0, 1:],
            torch.zeros(2),
        ]
    ).unsqueeze(0)
    torch.testing.assert_close(output, expected)


def test_global_local_topic_test_prediction_never_requires_gold_cluster_ids() -> None:
    source = (
        Path(__file__).parents[2]
        / "baselines/easyecr/easyecr/ecr_model/model/pl_ecr_models/global_local_topic.py"
    ).read_text(encoding="utf-8")
    assert '"cluster_id": m.meta.get("event_id", m.mention_id)' in source
    assert "EcrData(data.name, documents, doc_mentions, None, data.meta)" in source
