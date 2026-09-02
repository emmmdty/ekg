"""Supporting-evidence extraction: which words license the factuality label.

MAVEN-FACT annotates supporting words for CT-/PS+/PS-, not CT+ or Uu: the modal,
the negation, or the reporting verb ("was powerless to", "may", "whether").
Predicting them turns those labels into something inspectable, which is what the
evidence-grounding requirement asks of every stage here.

Two measured facts shape the design:

- **evidence is a minority-class phenomenon** — 88–99% of PS+/CT−/PS− mentions
  carry evidence against **0.1% of CT+**. So this is not a task defined over all
  17,780 valid mentions: the denominator is the 843 that are annotated, and
  `metrics.evidence_span_prf` carries that count so it cannot be misstated.
- **97.4% of evidence words sit in the trigger's own sentence** (5,816/5,973 in
  train). Scoring every token of a document per mention would be ~40x the work
  for the remaining 2.6%, so candidates are the trigger sentence's tokens. That
  is a *recall ceiling*, not a free choice — `SAME_SENTENCE_RECALL_CEILING`
  names it so the reported recall is read against the right maximum.

Candidates are `EvidenceSpan`s carrying character offsets into the same
``doc_text`` the encoder pools from, so `nodes.encoding.encode_spans` scores a
mention's whole candidate set inside the document's single forward pass.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence

from ekg.core.schema import EvidenceSpan
from ekg.relations.data.maven_fact import FactualityDocument, FactualityMention

__all__ = [
    "SAME_SENTENCE_RECALL_CEILING",
    "evidence_candidates",
    "evidence_targets",
    "gold_evidence_spans",
]

# Share of gold evidence words inside the trigger's own sentence, measured on
# MAVEN-FACT train (5,816/5,973). Restricting candidates to that sentence caps
# recall here; reported recall must be read against this number.
SAME_SENTENCE_RECALL_CEILING = 0.974


def evidence_candidates(doc: FactualityDocument, mention: FactualityMention) -> list[EvidenceSpan]:
    """Every token of the mention's sentence, as a scorable character span."""
    sent_id = mention.span.sent_id
    if sent_id is None:
        raise ValueError(f"{mention.mention_id}: mention span carries no sent_id")
    return [
        EvidenceSpan(
            doc_id=doc.doc_id,
            char_start=start,
            char_end=start + len(token),
            sent_id=sent_id,
            text=token,
        )
        for token, start in zip(
            doc.sentence_tokens[sent_id], doc.token_starts[sent_id], strict=True
        )
    ]


def evidence_targets(candidates: Sequence[EvidenceSpan], mention: FactualityMention) -> list[int]:
    """1 per candidate that is a gold evidence word, 0 otherwise."""
    gold = {(s.char_start, s.char_end) for s in mention.evidence}
    return [int((c.char_start, c.char_end) in gold) for c in candidates]


def gold_evidence_spans(
    docs: Iterable[FactualityDocument],
) -> dict[str, set[tuple[int, int]]]:
    """Gold evidence per mention, in the form `evidence_span_prf` scores.

    Mentions with no annotated evidence are present with an empty set, so the
    scored population is every mention rather than only the annotated ones.
    """
    return {
        m.mention_id: {(s.char_start, s.char_end) for s in m.evidence}
        for doc in docs
        for m in doc.mentions
    }
