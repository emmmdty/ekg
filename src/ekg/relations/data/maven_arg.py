"""Loader for MAVEN-Arg (event detection candidates, coreference, arguments).

MAVEN-Arg annotates the *same documents* as MAVEN-ERE (verified: 99.8% of its
mention ids and 99.0% of its event ids are shared), so this loader uses the
identical ``{doc_id}::{mention_id}`` namespacing as `maven_ere.py` and the two
views join without a mapping table.

Three things this file normalizes that MAVEN-ERE does not carry:

- **detection candidates** — gold trigger mentions *plus* the official
  ``negative_triggers``, the labelled universe event detection decides over;
- **arguments** — a role filler is either an inline ``{content, offset}`` span or
  an ``{entity_id}`` reference into the document's entity list; both resolve to
  surface text plus `EvidenceSpan`s here, so callers never see the split;
- **character offsets** — unlike MAVEN-ERE's token offsets these index
  ``document`` directly, so every span is verified to slice back to its surface
  and a mismatch raises. On the released valid split the mismatch count is 0
  (16,996 triggers / 46,458 arguments), so tolerance would only ever hide a bug.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path

from ekg.core.io import read_jsonl
from ekg.core.schema import EventNode, EvidenceSpan

__all__ = ["NONE_TYPE", "TriggerCandidate", "ArgumentDocument", "load_maven_arg"]

# Label of a candidate span that is not an event trigger.
NONE_TYPE = "NONE"

# Surface separator when a role has several fillers. `EventNode.arguments` is a
# frozen `dict[str, str]`, so the joined string is the readable summary while
# `argument_evidence` keeps one exact span per filler.
ARGUMENT_SEPARATOR = " | "


@dataclass(frozen=True)
class TriggerCandidate:
    """One span the detector must label: a gold mention, or a negative trigger."""

    candidate_id: str
    doc_id: str
    trigger: str
    span: EvidenceSpan
    event_type: str  # NONE_TYPE for negative triggers
    event_id: str = ""  # gold coreference cluster; "" for negative triggers


@dataclass
class ArgumentDocument:
    """One MAVEN-Arg document: mention nodes, gold clusters, detection candidates."""

    doc_id: str
    doc_text: str
    title: str = ""
    nodes: list[EventNode] = field(default_factory=list)
    clusters: dict[str, list[str]] = field(default_factory=dict)  # event id -> node ids
    candidates: list[TriggerCandidate] = field(default_factory=list)

    def gold_clusters(self) -> list[set[str]]:
        """Gold coreference clustering in the form `core.eval.coreference` takes."""
        return [set(ids) for ids in self.clusters.values()]


def _span(doc_id: str, doc_text: str, offset: list[int], surface: str, where: str) -> EvidenceSpan:
    """Verified character span; a disagreeing offset raises rather than degrades."""
    start, end = int(offset[0]), int(offset[1])
    if doc_text[start:end] != surface:
        raise ValueError(
            f"{doc_id}: {where} offset [{start}, {end}] holds "
            f"{doc_text[start:end]!r}, expected {surface!r}"
        )
    return EvidenceSpan(doc_id=doc_id, char_start=start, char_end=end, text=surface)


def _resolve_argument(
    values: list[dict], entities: dict[str, dict], doc_id: str, doc_text: str, role: str
) -> tuple[str, list[EvidenceSpan]]:
    """Role fillers -> (surface summary, spans). Entity refs expand to all mentions."""
    surfaces: list[str] = []
    spans: list[EvidenceSpan] = []
    for value in values:
        if "offset" in value:
            content = str(value["content"])
            surfaces.append(content)
            spans.append(_span(doc_id, doc_text, value["offset"], content, f"argument {role}"))
            continue
        entity_id = str(value["entity_id"])
        entity = entities.get(entity_id)
        if entity is None:
            raise ValueError(f"{doc_id}: argument {role} references unknown entity {entity_id}")
        mentions = entity.get("mention") or []
        if not mentions:
            raise ValueError(f"{doc_id}: entity {entity_id} has no mentions")
        # The entity is itself a coreference cluster: its first mention is the
        # filler surface, every mention is evidence for it.
        surfaces.append(str(mentions[0]["mention"]))
        spans.extend(
            _span(doc_id, doc_text, m["offset"], str(m["mention"]), f"entity {entity_id}")
            for m in mentions
        )
    return ARGUMENT_SEPARATOR.join(surfaces), spans


def _parse_document(record: dict) -> ArgumentDocument:
    doc_id = str(record["id"])
    doc_text = str(record["document"])
    entities = {str(e["id"]): e for e in record.get("entities") or []}

    nodes: list[EventNode] = []
    clusters: dict[str, list[str]] = {}
    candidates: list[TriggerCandidate] = []

    for event in record.get("events") or []:
        event_id = str(event["id"])
        event_type = str(event["type"])
        arguments: dict[str, str] = {}
        argument_evidence: dict[str, list[EvidenceSpan]] = {}
        for role, values in (event.get("argument") or {}).items():
            surface, spans = _resolve_argument(values, entities, doc_id, doc_text, str(role))
            arguments[str(role)] = surface
            argument_evidence[str(role)] = spans

        mention_ids: list[str] = []
        for mention in event.get("mention") or []:
            node_id = f"{doc_id}::{mention['id']}"
            trigger = str(mention["trigger_word"])
            span = _span(doc_id, doc_text, mention["offset"], trigger, f"trigger {node_id}")
            mention_ids.append(node_id)
            nodes.append(
                EventNode(
                    event_id=node_id,
                    event_type=event_type,
                    doc_id=doc_id,
                    trigger=trigger,
                    trigger_evidence=[span],
                    # Arguments are annotated per event, so every mention of that
                    # event carries them; cluster-level aggregation happens later.
                    arguments=dict(arguments),
                    argument_evidence={k: list(v) for k, v in argument_evidence.items()},
                    metadata={"event": event_id, "source": "maven_arg"},
                )
            )
            candidates.append(
                TriggerCandidate(
                    candidate_id=node_id,
                    doc_id=doc_id,
                    trigger=trigger,
                    span=span,
                    event_type=event_type,
                    event_id=event_id,
                )
            )
        clusters[event_id] = mention_ids

    for negative in record.get("negative_triggers") or []:
        candidate_id = f"{doc_id}::{negative['id']}"
        trigger = str(negative["trigger_word"])
        candidates.append(
            TriggerCandidate(
                candidate_id=candidate_id,
                doc_id=doc_id,
                trigger=trigger,
                span=_span(
                    doc_id, doc_text, negative["offset"], trigger, f"negative {candidate_id}"
                ),
                event_type=NONE_TYPE,
            )
        )

    return ArgumentDocument(
        doc_id=doc_id,
        doc_text=doc_text,
        title=str(record.get("title", "")),
        nodes=nodes,
        clusters=clusters,
        candidates=candidates,
    )


def load_maven_arg(path: str | Path) -> Iterator[ArgumentDocument]:
    """Yield one `ArgumentDocument` per line of a MAVEN-Arg jsonl file."""
    for record in read_jsonl(path):
        yield _parse_document(record)
