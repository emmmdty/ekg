"""Bind externally predicted mention-local arguments to canonical event mentions."""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path

from ekg.core.schema import EvidenceSpan

_ROLES = {"participant", "place"}


def apply_predicted_arguments(docs: Sequence, path: str | Path) -> None:
    """Apply a complete JSONL prediction artifact, rejecting ID or offset drift."""
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    rows = [json.loads(line) for line in lines if line]
    by_id = {}
    for row in rows:
        mention_id = str(row.get("mention_id", ""))
        if not mention_id or mention_id in by_id:
            raise ValueError(f"duplicate or empty mention prediction: {mention_id!r}")
        by_id[mention_id] = row

    expected = {node.event_id for doc in docs for node in doc.nodes}
    missing, extra = expected - by_id.keys(), by_id.keys() - expected
    if missing or extra:
        raise ValueError(
            f"missing predictions={len(missing)} extra predictions={len(extra)}"
        )

    for doc in docs:
        for node in doc.nodes:
            row = by_id[node.event_id]
            if row.get("doc_id") != doc.doc_id or row.get("status") not in {"ok", "empty"}:
                raise ValueError(f"invalid prediction status or doc_id for {node.event_id}")
            roles = row.get("roles") or {}
            unknown = set(roles) - _ROLES
            if unknown:
                raise ValueError(f"unknown predicted roles for {node.event_id}: {sorted(unknown)}")
            arguments: dict[str, str] = {}
            evidence: dict[str, list[EvidenceSpan]] = {}
            for role, fillers in roles.items():
                spans = []
                for filler in fillers:
                    start, end = int(filler["char_start"]), int(filler["char_end"])
                    text = str(filler["text"])
                    if doc.doc_text[start:end] != text:
                        raise ValueError(
                            f"predicted argument offset mismatch for {node.event_id}: {text!r}"
                        )
                    spans.append(
                        EvidenceSpan(
                            doc_id=doc.doc_id,
                            char_start=start,
                            char_end=end,
                            text=text,
                        )
                    )
                if spans:
                    arguments[role] = " | ".join(span.text for span in spans)
                    evidence[role] = spans
            node.arguments = arguments
            node.argument_evidence = evidence
            node.metadata["argument_source"] = "predicted_mention_local"
