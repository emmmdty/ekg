"""Tests for the relation dataset loaders against the bundled fixtures."""

from __future__ import annotations

import pytest

from ekg.core.eval import relation_prf
from ekg.core.schema import RelationType
from ekg.relations.data import load_ccks_causal, load_maven_ere
from ekg.relations.data.maven_ere import TIMEX_EVENT_TYPE, _parse_document


def test_load_maven_ere_fixture(fixtures_dir) -> None:
    docs = list(load_maven_ere(fixtures_dir / "maven_ere" / "sample.jsonl"))
    assert len(docs) == 2
    doc1 = docs[0]
    types = {e.relation_type for e in doc1.gold_edges}
    # doc1 has coreference (EV1 has 2 mentions), temporal, causal and subevent.
    assert RelationType.COREFERENCE in types
    assert RelationType.TEMPORAL in types
    assert RelationType.CAUSAL in types
    # Gold-vs-gold is a perfect score (loader + metric integrate cleanly).
    assert relation_prf(doc1.gold_edges, doc1.gold_edges)["micro"]["f1"] == 1.0


def test_load_ccks_causal_fixture(fixtures_dir) -> None:
    docs = list(load_ccks_causal(fixtures_dir / "ccks_fin_causal" / "sample.jsonl"))
    assert len(docs) == 2
    assert all(
        any(e.relation_type is RelationType.CAUSAL for e in d.gold_edges) for d in docs
    )
    assert docs[0].nodes[0].doc_id == docs[0].doc_id


def _timex_record(sentence: str, tokens: list[str], offset: list[int]) -> dict:
    return {
        "id": "doc-1",
        "sentences": ["Filler sentence .", sentence],
        "tokens": [["Filler", "sentence", "."], tokens],
        "events": [
            {
                "id": "EV1",
                "type": "Attack",
                "mention": [
                    {"id": "m1", "trigger_word": "filler", "sent_id": 0, "offset": [0, 1]}
                ],
            }
        ],
        "TIMEX": [
            {
                "id": "TIME_1",
                "mention": " ".join(tokens[offset[0] : offset[1]]),
                "type": "DATE",
                "sent_id": 1,
                "offset": offset,
            }
        ],
        "temporal_relations": {},
        "causal_relations": {},
        "subevent_relations": [],
    }


@pytest.mark.parametrize(
    ("sentence", "tokens", "offset", "expected"),
    [
        # `tokens` splits punctuation, raw `sentences` does not: a literal search for
        # the tokenised mention "July 29 , 2012" can never match "July 29, 2012".
        (
            "Held on July 29, 2012 here.",
            ["Held", "on", "July", "29", ",", "2012", "here", "."],
            [2, 6],
            "July 29, 2012",
        ),
        # `tokens` are lower-cased while `sentences` keep their casing.
        (
            "Two days later it ended.",
            ["two", "days", "later", "it", "ended", "."],
            [0, 3],
            "Two days later",
        ),
        # The corpus UNKs a few characters; the span must still resolve.
        (
            "Ran July 1944 - November 1945 total.",
            ["Ran", "july", "1944", "UNK", "november", "1945", "total", "."],
            [1, 6],
            "July 1944 - November 1945",
        ),
    ],
)
def test_timex_surface_survives_the_tokenised_vs_raw_text_views(
    sentence: str, tokens: list[str], offset: list[int], expected: str
) -> None:
    """TIMEX spans must resolve against the raw doc text, not the token view.

    MAVEN-ERE ships two views of every sentence and they differ in punctuation
    spacing, casing, and UNK substitution. Single-token event triggers happen to be
    identical in both, which is why only TIMEX exposes the mismatch.
    """
    doc = _parse_document(_timex_record(sentence, tokens, offset), include_timex=True)
    timex = [n for n in doc.nodes if n.event_type == TIMEX_EVENT_TYPE]

    assert len(timex) == 1
    assert timex[0].trigger == expected
    span = timex[0].trigger_evidence[0]
    assert doc.doc_text[span.char_start : span.char_end] == expected


def test_unresolvable_timex_span_fails_instead_of_degrading_to_position_zero() -> None:
    record = _timex_record("Nothing matches here.", ["absent", "tokens"], [0, 2])
    with pytest.raises(ValueError, match="not locatable"):
        _parse_document(record, include_timex=True)
