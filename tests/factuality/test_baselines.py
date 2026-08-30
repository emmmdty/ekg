"""Tests for the same-protocol public MAVEN-FACT baselines (CPU paths)."""

from __future__ import annotations

import pytest

from ekg.factuality.baselines import (
    BASELINE_POOLINGS,
    CLS_POOLING,
    DYNAMIC_MULTI_POOLING,
    TRIGGER_MARKER,
    baseline_head_input_dim,
    marked_sentence,
    pool_mentions,
    validate_pooling,
)
from ekg.nodes.encoding import TORCH_AVAILABLE
from ekg.relations.data.maven_fact import load_maven_fact


@pytest.fixture
def docs(fixtures_dir):
    return list(load_maven_fact(fixtures_dir / "maven_fact" / "sample.jsonl"))


def test_pooling_names_are_validated() -> None:
    for pooling in BASELINE_POOLINGS:
        assert validate_pooling(pooling) == pooling
    with pytest.raises(ValueError, match="unknown baseline pooling"):
        validate_pooling("mean")


def test_head_width_matches_the_architecture() -> None:
    assert baseline_head_input_dim(8, CLS_POOLING) == 8
    # Dynamic multi-pooling concatenates left / trigger / right.
    assert baseline_head_input_dim(8, DYNAMIC_MULTI_POOLING) == 24


def test_each_mention_marks_its_own_trigger(docs) -> None:
    for doc in docs:
        for mention in doc.mentions:
            text, start, end = marked_sentence(doc, mention)
            assert text[start:end] == mention.trigger
            assert text.count(TRIGGER_MARKER) == 2


def test_two_triggers_in_one_sentence_get_different_inputs(docs) -> None:
    # The reason marking is not optional: an unmarked [CLS] would hand both
    # mentions of a sentence the identical vector.
    by_sentence: dict[tuple[str, int], list[str]] = {}
    for doc in docs:
        for mention in doc.mentions:
            by_sentence.setdefault((doc.doc_id, mention.span.sent_id), []).append(
                marked_sentence(doc, mention)[0]
            )
    shared = [texts for texts in by_sentence.values() if len(texts) > 1]
    assert shared, "fixture no longer covers two triggers in one sentence"
    for texts in shared:
        assert len(set(texts)) == len(texts)


def test_a_trigger_span_covering_no_token_is_rejected(docs) -> None:
    doc = docs[0]
    mention = doc.mentions[0]
    broken = type(mention)(
        mention_id=mention.mention_id,
        doc_id=mention.doc_id,
        trigger=mention.trigger,
        span=mention.span.model_copy(update={"char_start": 10**6, "char_end": 10**6 + 1}),
        factuality=mention.factuality,
        evidence=mention.evidence,
        event_id=mention.event_id,
        event_type=mention.event_type,
    )
    with pytest.raises(ValueError, match="covers no token"):
        marked_sentence(doc, broken)


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="needs torch")
def test_dynamic_multi_pooling_separates_the_two_contexts() -> None:
    """Hermetic: a word-level stub stands in for encoder and tokenizer.

    Deliberately no `from_pretrained` -- the GPU box has no outbound network,
    and a test that reaches for one hangs there instead of failing.
    """
    import torch

    class FakeEncoder:
        def __call__(self, input_ids=None, attention_mask=None, **kwargs):
            n, length = input_ids.shape
            values = torch.arange(length, dtype=torch.float).view(1, length, 1)
            return type("Out", (), {"last_hidden_state": values.expand(n, length, 4).clone()})()

    class FakeTokenizer:
        """One token per whitespace word, plus a leading special token."""

        def __call__(self, texts, **kwargs):
            rows = []
            for text in texts:
                offsets, cursor = [(0, 0)], 0
                for word in text.split(" "):
                    offsets.append((cursor, cursor + len(word)))
                    cursor += len(word) + 1
                rows.append(offsets)
            width = max(len(r) for r in rows)
            padded = [r + [(0, 0)] * (width - len(r)) for r in rows]
            mask = [[1] * len(r) + [0] * (width - len(r)) for r in rows]
            return {
                "input_ids": torch.zeros(len(rows), width, dtype=torch.long),
                "attention_mask": torch.tensor(mask),
                "offset_mapping": torch.tensor(padded),
            }

    text = "aa bb cc dd"
    start, end = 6, 8  # "cc"
    features = pool_mentions(
        FakeEncoder(), FakeTokenizer(), [text], [(start, end)],
        pooling=DYNAMIC_MULTI_POOLING, max_length=32,
    )
    assert features.shape == (1, 12)
    left, at, right = features[0, :4], features[0, 4:8], features[0, 8:]
    # Token rows increase left to right, so the three segment maxima must be
    # strictly ordered -- were the trigger split ignored they would be equal.
    assert left.max() < at.max() < right.max()

    cls = pool_mentions(
        FakeEncoder(), FakeTokenizer(), [text], [(start, end)],
        pooling=CLS_POOLING, max_length=32,
    )
    assert cls.shape == (1, 4)
    assert torch.allclose(cls[0], torch.zeros(4))  # position 0 is the special token
