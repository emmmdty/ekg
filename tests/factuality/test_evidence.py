"""Tests for evidence-span candidate generation and its recall ceiling."""

from __future__ import annotations

import pytest

from ekg.factuality.evidence import (
    SAME_SENTENCE_RECALL_CEILING,
    evidence_candidates,
    evidence_targets,
    gold_evidence_spans,
)
from ekg.relations.data.maven_fact import load_maven_fact


@pytest.fixture
def docs(fixtures_dir):
    return list(load_maven_fact(fixtures_dir / "maven_fact" / "sample.jsonl"))


def test_candidates_are_the_tokens_of_the_trigger_sentence(docs) -> None:
    doc = docs[0]
    mention = doc.mentions[1]  # "restrain", sentence 1
    candidates = evidence_candidates(doc, mention)
    assert [c.text for c in candidates] == [
        "The", "commander", "was", "powerless", "to", "restrain", "them", ".",
    ]
    # Candidates are character spans into the same doc_text the encoder sees, so
    # they are poolable by `encode_spans` with no second convention.
    for candidate in candidates:
        assert doc.doc_text[candidate.char_start : candidate.char_end] == candidate.text


def test_targets_mark_exactly_the_gold_evidence_tokens(docs) -> None:
    doc = docs[0]
    mention = doc.mentions[1]
    candidates = evidence_candidates(doc, mention)
    targets = evidence_targets(candidates, mention)
    assert len(targets) == len(candidates)
    marked = [c.text for c, t in zip(candidates, targets, strict=True) if t]
    assert marked == ["was", "powerless", "to"]


def test_mention_without_evidence_yields_all_zero_targets(docs) -> None:
    doc = docs[0]
    mention = doc.mentions[0]  # "attacked", no evidence annotated
    targets = evidence_targets(evidence_candidates(doc, mention), mention)
    assert not any(targets)


def test_cross_sentence_evidence_is_out_of_reach_and_says_so(docs) -> None:
    # 2.6% of gold evidence words sit outside the trigger's sentence, so the
    # same-sentence candidate set caps recall. The ceiling is a named constant
    # rather than an unstated loss, and it is reported next to the score.
    assert 0.9 < SAME_SENTENCE_RECALL_CEILING < 1.0

    doc = docs[1]
    mention = next(m for m in doc.mentions if m.mention_id == "fdoc2::m2")
    candidates = evidence_candidates(doc, mention)
    targets = evidence_targets(candidates, mention)
    # "whether" is in the same sentence as "ban", so this one is reachable.
    assert [c.text for c, t in zip(candidates, targets, strict=True) if t] == ["whether"]


def test_gold_evidence_spans_key_by_mention(docs) -> None:
    gold = gold_evidence_spans(docs)
    assert gold["fdoc1::m1"] == set()
    assert len(gold["fdoc1::m2"]) == 3
    # Spans are (char_start, char_end) pairs, matching `evidence_span_prf`.
    assert all(isinstance(s, tuple) and len(s) == 2 for s in gold["fdoc1::m2"])
    assert set(gold) == {m.mention_id for d in docs for m in d.mentions}
