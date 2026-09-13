"""Prompt rendering and response parsing for the three chapters' LLM control.

Each method chapter reports one LLM row, and a row is only comparable if it was
produced under the same protocol as everything else in its table: the same
mention population, the same evaluator, no post-hoc repair.  This module fixes
the two ends of that -- how a document becomes a prompt, and how a response
becomes the exact file the chapter's evaluator reads.

The generation in between is deliberately not here.  A CPU box can therefore
exercise the whole path with recorded responses, which is what the C-7 fixture
does, and the GPU run only has to supply the text.

**Unparseable output is recorded, never repaired.**  An LLM will omit mentions,
invent ids and emit prose around its JSON; a baseline that silently patched
those would be scored on something its model never produced.  So every parse
returns the coverage alongside the prediction: what was answered, what was
missing, what was rejected and why.  The caller decides what an unanswered
mention counts as -- for factuality that has to be an explicit label, because
the evaluator demands full coverage, and `UNANSWERED_FACTUALITY` names it.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

__all__ = [
    "CHAPTERS",
    "UNANSWERED_FACTUALITY",
    "LLMBaselineConfig",
    "ParsedResponse",
    "extract_json_object",
    "load_llm_baseline_config",
    "official_shape",
    "parse_factuality",
    "parse_identity",
    "parse_relation",
    "render_prompt",
]

CHAPTERS = ("factuality", "relation", "identity")

# What a mention the model never answered for is scored as. The majority class:
# scoring it as anything rarer would flatter the baseline on the rare classes
# that are the hard part of MAVEN-FACT, and leaving it out is not an option
# because `factuality_report` requires every gold mention.
UNANSWERED_FACTUALITY = "CT+"

_JSON_OBJECT = re.compile(r"\{.*\}", re.DOTALL)


@dataclass(frozen=True)
class LLMBaselineConfig:
    """The frozen prompt and adapter budget, plus the hash they are pinned by."""

    path: Path
    sha256: str
    payload: dict[str, Any]

    def chapter(self, chapter: str) -> dict[str, Any]:
        if chapter not in CHAPTERS:
            raise ValueError(f"unknown chapter: {chapter!r}")
        section = self.payload["chapters"].get(chapter)
        if not isinstance(section, dict):
            raise ValueError(f"config has no {chapter} chapter")
        return section

    @property
    def lora(self) -> dict[str, Any]:
        return dict(self.payload["lora"])

    @property
    def decoding(self) -> dict[str, Any]:
        return dict(self.payload["decoding"])


@dataclass
class ParsedResponse:
    """A prediction plus an honest account of what the model did not deliver."""

    prediction: Any
    answered: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    rejected: dict[str, str] = field(default_factory=dict)

    @property
    def coverage(self) -> dict[str, int]:
        return {
            "answered": len(self.answered),
            "missing": len(self.missing),
            "rejected": len(self.rejected),
        }


def load_llm_baseline_config(path: str | Path) -> LLMBaselineConfig:
    from ekg.core.stage_bundle import sha256_file

    path = Path(path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != "ekg.llm_baseline_config.v1":
        raise ValueError(f"{path}: unexpected schema_version")
    for chapter in CHAPTERS:
        section = payload.get("chapters", {}).get(chapter)
        if not isinstance(section, dict) or "prompt_template" not in section:
            raise ValueError(f"{path}: chapter {chapter} has no prompt template")
    return LLMBaselineConfig(path=path, sha256=sha256_file(path), payload=payload)


def render_prompt(
    config: LLMBaselineConfig,
    chapter: str,
    *,
    document: str,
    mentions: list[dict[str, Any]],
) -> str:
    """One document's prompt, with every mention listed exactly once."""
    section = config.chapter(chapter)
    seen: set[str] = set()
    lines = []
    for mention in mentions:
        mention_id = str(mention["mention_id"])
        if mention_id in seen:
            raise ValueError(f"mention listed twice in one prompt: {mention_id}")
        seen.add(mention_id)
        lines.append(
            section["mention_line"].format(
                mention_id=mention_id,
                trigger=mention.get("trigger", ""),
                sent_id=mention.get("sent_id", 0),
            )
        )
    if not lines:
        raise ValueError("a prompt with no mentions asks the model nothing")
    return section["prompt_template"].format(document=document, mentions="\n".join(lines))


def extract_json_object(text: str) -> dict[str, Any]:
    """The first balanced JSON object in the response.

    Models wrap JSON in prose and fences whatever the prompt says, so the
    envelope is stripped rather than treated as a failure -- but a response with
    no object in it, or one that does not parse, raises instead of returning an
    empty prediction that would score as a confident abstention.
    """
    match = _JSON_OBJECT.search(text)
    if match is None:
        raise ValueError("response contains no JSON object")
    payload = json.loads(match.group(0))
    if not isinstance(payload, dict):
        raise ValueError("response JSON is not an object")
    return payload


def parse_factuality(text: str, mention_ids: list[str]) -> ParsedResponse:
    """`{mention_id: label}` over exactly the mentions that were asked about."""
    from ekg.relations.data.maven_fact import FACTUALITY_LABELS

    wanted = list(dict.fromkeys(mention_ids))
    result = ParsedResponse(prediction={})
    try:
        payload = extract_json_object(text)
    except ValueError as exc:
        result.rejected = dict.fromkeys(wanted, str(exc))
        result.missing = wanted
        result.prediction = dict.fromkeys(wanted, UNANSWERED_FACTUALITY)
        return result

    known = set(wanted)
    for mention_id in wanted:
        raw = payload.get(mention_id)
        if raw is None:
            result.missing.append(mention_id)
            result.prediction[mention_id] = UNANSWERED_FACTUALITY
        elif raw not in FACTUALITY_LABELS:
            result.rejected[mention_id] = f"not a factuality label: {raw!r}"
            result.prediction[mention_id] = UNANSWERED_FACTUALITY
        else:
            result.answered.append(mention_id)
            result.prediction[mention_id] = raw
    for mention_id in payload:
        if mention_id not in known:
            result.rejected[str(mention_id)] = "label for a mention that was not asked about"
    return result


def _pairs(raw: Any, known: set[str], rejected: dict[str, str], where: str) -> list[list[str]]:
    """Ordered id pairs, dropping -- and recording -- anything malformed."""
    if not isinstance(raw, list):
        rejected[where] = f"expected a list of pairs, got {type(raw).__name__}"
        return []
    pairs: list[list[str]] = []
    for index, pair in enumerate(raw):
        if not isinstance(pair, (list, tuple)) or len(pair) != 2:
            rejected[f"{where}[{index}]"] = "not a pair"
            continue
        head, tail = str(pair[0]), str(pair[1])
        unknown = [m for m in (head, tail) if m not in known]
        if unknown:
            rejected[f"{where}[{index}]"] = f"mention not in this document: {unknown}"
            continue
        if head == tail:
            rejected[f"{where}[{index}]"] = "a mention cannot relate to itself"
            continue
        pairs.append([head, tail])
    return pairs


def official_shape(doc_id: str, config: LLMBaselineConfig) -> dict[str, Any]:
    """An empty MAVEN-ERE prediction record with every key the scorer reads."""
    families = config.chapter("relation")["families"]
    return {
        "id": doc_id,
        "coreference": [],
        "temporal_relations": {name: [] for name in families["temporal"]},
        "causal_relations": {name: [] for name in families["causal"]},
        "subevent_relations": [],
    }


def parse_relation(
    text: str, doc_id: str, mention_ids: list[str], config: LLMBaselineConfig
) -> ParsedResponse:
    """One official-shape record; unasked or malformed pairs are dropped loudly."""
    known = set(mention_ids)
    record = official_shape(doc_id, config)
    result = ParsedResponse(prediction=record)
    try:
        payload = extract_json_object(text)
    except ValueError as exc:
        result.rejected["response"] = str(exc)
        return result

    for family in ("causal", "temporal"):
        key = f"{family}_relations"
        raw = payload.get(key, {})
        if not isinstance(raw, dict):
            result.rejected[key] = f"expected an object, got {type(raw).__name__}"
            continue
        for name, value in raw.items():
            if name not in record[key]:
                result.rejected[f"{key}.{name}"] = "not a relation type of this family"
                continue
            record[key][name] = _pairs(value, known, result.rejected, f"{key}.{name}")
    record["subevent_relations"] = _pairs(
        payload.get("subevent_relations", []), known, result.rejected, "subevent_relations"
    )
    result.answered = sorted(
        {m for pair in _all_pairs(record) for m in pair} & known
    )
    result.missing = sorted(known - set(result.answered))
    return result


def _all_pairs(record: dict[str, Any]) -> list[list[str]]:
    pairs = list(record["subevent_relations"])
    for key in ("causal_relations", "temporal_relations"):
        for value in record[key].values():
            pairs.extend(value)
    return pairs


def parse_identity(
    text: str, doc_id: str, mention_ids: list[str], config: LLMBaselineConfig
) -> ParsedResponse:
    """One official-shape record carrying only the coreference clusters.

    A mention in two clusters is a contradiction, not a merge: the second
    membership is rejected rather than silently unioned, because the official
    scorer would accept either and the two answers score differently.
    """
    known = set(mention_ids)
    record = official_shape(doc_id, config)
    result = ParsedResponse(prediction=record)
    try:
        payload = extract_json_object(text)
    except ValueError as exc:
        result.rejected["response"] = str(exc)
        return result

    raw = payload.get("coreference", [])
    if not isinstance(raw, list):
        result.rejected["coreference"] = f"expected a list, got {type(raw).__name__}"
        return result

    placed: set[str] = set()
    clusters: list[list[str]] = []
    for index, cluster in enumerate(raw):
        where = f"coreference[{index}]"
        if not isinstance(cluster, (list, tuple)):
            result.rejected[where] = "not a list of mention ids"
            continue
        members: list[str] = []
        for mention in cluster:
            mention_id = str(mention)
            if mention_id not in known:
                result.rejected[f"{where}:{mention_id}"] = "mention not in this document"
            elif mention_id in placed:
                result.rejected[f"{where}:{mention_id}"] = "mention already in another cluster"
            elif mention_id in members:
                result.rejected[f"{where}:{mention_id}"] = "mention repeated inside one cluster"
            else:
                members.append(mention_id)
        if len(members) < 2:
            # Singletons are free to the scorer, so a one-member group carries no
            # information; it is dropped without being called an error.
            continue
        placed.update(members)
        clusters.append(members)
    record["coreference"] = clusters
    result.answered = sorted(placed)
    result.missing = sorted(known - placed)
    return result
