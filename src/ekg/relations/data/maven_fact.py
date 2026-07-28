"""Loader for MAVEN-FACT (event factuality + supporting evidence).

MAVEN-FACT annotates the *same documents* as MAVEN-ERE and MAVEN-Arg (identical
doc ids; the valid split's 17,780 mentions match MAVEN-ERE exactly), so mention
ids are namespaced ``{doc_id}::{mention_id}`` here too and the factuality view
joins onto the predicted graph without a mapping table.

Three things this file settles, all verified against the released splits rather
than assumed — Phase A and Phase C both lost a run to an offset convention taken
on faith:

- **offsets are token-based** — a mention's ``offset`` indexes
  ``tokens[sent_id]``, and each ``evidence_offset`` entry is a
  ``[sent_id, token_index]`` pair, *not* a character range. Verified on both
  splits: 91,719/91,719 triggers slice back exactly.
- **``document`` is the whitespace join of ``tokens``** — exactly, on all 3,623
  released documents. That makes the token→character mapping computable rather
  than searched, so spans are stored as character offsets into ``document`` and
  the whole `nodes.encoding` stack (which takes character starts) applies
  unchanged. The join is re-checked per document and a disagreement raises.
- **argument offsets are characters** — on the same records. Three offset
  conventions coexist in one file, which is why each is checked rather than
  assumed; arguments slice back exactly on all 74,008 valid fillers, so a
  mismatch there raises.
- **evidence offsets carry annotation noise** — 24/5,997 evidence words in train
  and 6/1,296 in valid point at the wrong token (e.g. ``"voted"`` offset
  ``[0, 0]`` on a sentence starting ``"On"``). Those are dropped and counted in
  `FactualityDocument.evidence_mismatches`; storing them would put a span on a
  word that is not the evidence, and a silent ``(0, 0)`` fallback is the exact
  failure mode that cost Phase A a re-run. Triggers, which have no such noise,
  raise instead.

Class balance is extreme — CT+ is 94.4% of train — so `factuality_distribution`
exists to keep that visible, and evaluation must report macro-F1: the
all-CT+ baseline scores .9487 accuracy and .1947 macro-F1.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Iterator, Sequence
from dataclasses import dataclass, field
from itertools import combinations
from pathlib import Path

from ekg.core.io import read_jsonl
from ekg.core.schema import EventNode, EvidenceSpan, RelationEdge, RelationType

__all__ = [
    "FACTUALITY_LABELS",
    "FactualityMention",
    "FactualityDocument",
    "load_maven_fact",
    "factuality_distribution",
]

# Surface separator when a role has several fillers, as in the MAVEN-Arg loader:
# `EventNode.arguments` is a `dict[str, str]`, so the joined string is the
# readable summary while `argument_evidence` keeps one exact span per filler.
ARGUMENT_SEPARATOR = " | "

# The five official factuality classes, ordered by train frequency (CT+ 94.4%,
# PS+ 3.1%, CT- 2.0%, PS- 0.4%, Uu 0.2%). Index 0 is the majority class, which
# is what a trivial classifier collapses to.
FACTUALITY_LABELS: tuple[str, ...] = ("CT+", "PS+", "CT-", "PS-", "Uu")


@dataclass(frozen=True)
class FactualityMention:
    """One factuality decision: a trigger mention, its label and its evidence."""

    mention_id: str
    doc_id: str
    trigger: str
    span: EvidenceSpan
    factuality: str
    evidence: list[EvidenceSpan]
    event_id: str
    event_type: str


@dataclass
class FactualityDocument:
    """One MAVEN-FACT document: labelled mentions plus the gold relation graph.

    `gold_edges` carries coreference/temporal/causal/subevent so a
    structure-aware detector can condition on the *gold* graph; the predicted
    graph from Phase A/B substitutes for it in the robustness protocol.
    """

    doc_id: str
    doc_text: str
    title: str = ""
    nodes: list[EventNode] = field(default_factory=list)
    mentions: list[FactualityMention] = field(default_factory=list)
    gold_edges: list[RelationEdge] = field(default_factory=list)
    evidence_mismatches: int = 0
    # Sentence-grouped tokens and each token's character start in `doc_text`.
    # Carried because evidence extraction scores a trigger's *sentence*, and
    # re-deriving the grouping from `doc_text` is impossible (the join is
    # whitespace, and tokens contain no separator of their own).
    sentence_tokens: list[list[str]] = field(default_factory=list)
    token_starts: list[list[int]] = field(default_factory=list)


def _token_char_starts(tokens: Sequence[Sequence[str]]) -> list[list[int]]:
    """Character start of every token inside the whitespace-joined document."""
    starts: list[list[int]] = []
    cursor = 0
    for sentence in tokens:
        per_sentence: list[int] = []
        for token in sentence:
            per_sentence.append(cursor)
            cursor += len(token) + 1  # tokens are joined by a single space
        starts.append(per_sentence)
    return starts


def _char_span(doc_id: str, start: int, surface: str, sent_id: int) -> EvidenceSpan:
    return EvidenceSpan(
        doc_id=doc_id,
        char_start=start,
        char_end=start + len(surface),
        sent_id=sent_id,
        text=surface,
    )


def _arguments(
    event: dict, doc_id: str, doc_text: str
) -> tuple[dict[str, str], dict[str, list[EvidenceSpan]]]:
    """Event-level role fillers. **These offsets are characters**, unlike the
    token offsets on the same record's mentions — verified exactly on all 74,008
    valid argument mentions, so a disagreement is a bug and raises.
    """
    surfaces: dict[str, list[str]] = {}
    spans: dict[str, list[EvidenceSpan]] = {}
    for argument in event.get("arguments") or []:
        role = str(argument["type"])
        for filler in argument.get("mentions") or []:
            surface = str(filler["mention"])
            start, end = int(filler["offset"][0]), int(filler["offset"][1])
            if doc_text[start:end] != surface:
                raise ValueError(
                    f"{doc_id}: argument {role} offset [{start}, {end}] holds "
                    f"{doc_text[start:end]!r}, expected {surface!r}"
                )
            surfaces.setdefault(role, []).append(surface)
            spans.setdefault(role, []).append(
                EvidenceSpan(doc_id=doc_id, char_start=start, char_end=end, text=surface)
            )
    return {role: ARGUMENT_SEPARATOR.join(v) for role, v in surfaces.items()}, spans


def _parse_document(record: dict) -> FactualityDocument:
    doc_id = str(record["id"])
    tokens: list[list[str]] = record["tokens"]
    doc_text = str(record["document"])
    if doc_text != " ".join(" ".join(sentence) for sentence in tokens):
        raise ValueError(f"{doc_id}: document is not the whitespace join of tokens")
    starts = _token_char_starts(tokens)

    nodes: list[EventNode] = []
    mentions: list[FactualityMention] = []
    gold: list[RelationEdge] = []
    representative: dict[str, str] = {}
    mismatches = 0

    for event in record.get("events") or []:
        event_id = str(event["id"])
        event_type = str(event["type"])
        arguments, argument_evidence = _arguments(event, doc_id, doc_text)
        mention_ids: list[str] = []
        for mention in event.get("mention") or []:
            mention_id = f"{doc_id}::{mention['id']}"
            trigger = str(mention["trigger_word"])
            sent_id = int(mention["sent_id"])
            offset = mention["offset"]
            start = starts[sent_id][int(offset[0])]
            span = _char_span(doc_id, start, trigger, sent_id)
            if doc_text[span.char_start : span.char_end] != trigger:
                raise ValueError(
                    f"{doc_id}: trigger offset {offset} in sentence {sent_id} holds "
                    f"{doc_text[span.char_start : span.char_end]!r}, expected {trigger!r}"
                )

            factuality = str(mention["factuality"])
            if factuality not in FACTUALITY_LABELS:
                raise ValueError(f"{doc_id}: unknown factuality label {factuality!r}")

            evidence: list[EvidenceSpan] = []
            words = mention.get("evidence_word") or []
            offsets = mention.get("evidence_offset") or []
            for word, (ev_sent, ev_token) in zip(words, offsets, strict=True):
                word = str(word)
                sentence = tokens[ev_sent] if ev_sent < len(tokens) else []
                if ev_token >= len(sentence) or sentence[ev_token] != word:
                    mismatches += 1
                    continue
                evidence.append(_char_span(doc_id, starts[ev_sent][ev_token], word, ev_sent))

            mention_ids.append(mention_id)
            mentions.append(
                FactualityMention(
                    mention_id=mention_id,
                    doc_id=doc_id,
                    trigger=trigger,
                    span=span,
                    factuality=factuality,
                    evidence=evidence,
                    event_id=event_id,
                    event_type=event_type,
                )
            )
            nodes.append(
                EventNode(
                    event_id=mention_id,
                    event_type=event_type,
                    doc_id=doc_id,
                    trigger=trigger,
                    trigger_evidence=[span],
                    # Arguments are annotated per event, so every mention of that
                    # event carries them (same convention as the MAVEN-Arg loader).
                    arguments=dict(arguments),
                    argument_evidence={k: list(v) for k, v in argument_evidence.items()},
                    # `EventNode` takes no new fields (hard constraint), so the
                    # label rides in `metadata` where every other stage puts its
                    # annotations.
                    metadata={"event": event_id, "factuality": factuality, "source": "maven_fact"},
                )
            )
        if mention_ids:
            representative[event_id] = mention_ids[0]
        for head, tail in combinations(mention_ids, 2):
            gold.append(
                RelationEdge(
                    head_id=head,
                    tail_id=tail,
                    relation_type=RelationType.COREFERENCE,
                    directed=False,
                )
            )

    def rep(event_id: object) -> str | None:
        return representative.get(str(event_id))

    # Note the field name: MAVEN-FACT ships `causal_relation` (singular) where
    # MAVEN-ERE ships `causal_relations`. Reading the ERE name here would yield
    # zero causal edges without any error.
    for relation_type, source in (
        (RelationType.TEMPORAL, record.get("temporal_relations")),
        (RelationType.CAUSAL, record.get("causal_relation")),
    ):
        for subtype, pairs in (source or {}).items():
            for head, tail in pairs:
                rep_head, rep_tail = rep(head), rep(tail)
                if rep_head and rep_tail:
                    gold.append(
                        RelationEdge(
                            head_id=rep_head,
                            tail_id=rep_tail,
                            relation_type=relation_type,
                            subtype=str(subtype).upper(),
                        )
                    )
    for pair in record.get("subevent_relations") or []:
        rep_head, rep_tail = rep(pair[0]), rep(pair[1])
        if rep_head and rep_tail:
            gold.append(
                RelationEdge(
                    head_id=rep_head,
                    tail_id=rep_tail,
                    relation_type=RelationType.SUBEVENT,
                    subtype="SUBEVENT_OF",
                )
            )

    return FactualityDocument(
        doc_id=doc_id,
        doc_text=doc_text,
        title=str(record.get("title", "")),
        nodes=nodes,
        mentions=mentions,
        gold_edges=gold,
        evidence_mismatches=mismatches,
        sentence_tokens=[list(sentence) for sentence in tokens],
        token_starts=starts,
    )


def load_maven_fact(path: str | Path) -> Iterator[FactualityDocument]:
    """Yield one `FactualityDocument` per line of a MAVEN-FACT jsonl file."""
    for record in read_jsonl(path):
        yield _parse_document(record)


def factuality_distribution(docs: Iterable[FactualityDocument]) -> dict[str, int]:
    """Label counts over the given documents, every class present even at zero."""
    counts = Counter(m.factuality for doc in docs for m in doc.mentions)
    return {label: counts[label] for label in FACTUALITY_LABELS}
