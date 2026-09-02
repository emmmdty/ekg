#!/usr/bin/env python
"""Measure event-level versus mention-local argument signal for coreference.

MAVEN-Arg stores arguments on an event and copies them to every mention.  An
event-level signature is therefore identical inside every gold cluster by
construction.  This report aligns MAVEN-ERE's sentence-token view to the flat
MAVEN-Arg text and keeps only argument spans in the mention's own sentence, so
the two signals cannot be confused.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from ekg.core.io import read_jsonl
from ekg.nodes.coref import labelled_coref_pairs
from ekg.relations.data.maven_arg import ArgumentDocument, load_maven_arg


def sentence_ranges(record: dict, doc_text: str) -> list[tuple[int, int]]:
    """Return exact sentence character ranges in MAVEN-Arg's flat token text."""
    sentences = [" ".join(map(str, tokens)) for tokens in record.get("tokens", [])]
    flattened = " ".join(sentences)
    if flattened != doc_text:
        raise ValueError(
            f"{record.get('id')}: MAVEN-ERE tokens do not reconstruct MAVEN-Arg text"
        )
    ranges: list[tuple[int, int]] = []
    cursor = 0
    for sentence in sentences:
        ranges.append((cursor, cursor + len(sentence)))
        cursor += len(sentence) + 1
    return ranges


def mention_sentences(record: dict, doc_id: str) -> dict[str, int]:
    """Namespaced mention id -> official MAVEN-ERE sentence id."""
    return {
        f"{doc_id}::{mention['id']}": int(mention["sent_id"])
        for event in record.get("events", [])
        for mention in event.get("mention", [])
    }


def argument_signatures(node, sentence_range: tuple[int, int]) -> tuple[tuple, tuple]:
    """Return event-level and same-sentence ``(role, normalized surface)`` tuples."""
    start, end = sentence_range

    def item(role, span):
        return str(role), " ".join(span.text.lower().split())

    global_signature = tuple(
        sorted(
            item(role, span)
            for role, spans in node.argument_evidence.items()
            for span in spans
        )
    )
    local_signature = tuple(
        sorted(
            item(role, span)
            for role, spans in node.argument_evidence.items()
            for span in spans
            if start <= span.char_start and span.char_end <= end
        )
    )
    return global_signature, local_signature


def analyze_document(doc: ArgumentDocument, ere_record: dict) -> Counter[str]:
    ranges = sentence_ranges(ere_record, doc.doc_text)
    sent_ids = mention_sentences(ere_record, doc.doc_id)
    aligned = [node for node in doc.nodes if node.event_id in sent_ids]
    signatures = {
        node.event_id: argument_signatures(node, ranges[sent_ids[node.event_id]])
        for node in aligned
    }
    cluster = {
        mention_id: event_id
        for event_id, mention_ids in doc.clusters.items()
        for mention_id in mention_ids
    }
    nodes = {node.event_id: node for node in doc.nodes}
    counts: Counter[str] = Counter(
        arg_mentions=len(doc.nodes),
        aligned_mentions=len(aligned),
        unaligned_mentions=len(doc.nodes) - len(aligned),
    )
    for pair in labelled_coref_pairs(doc.nodes, cluster):
        head, tail = nodes[pair.head_id], nodes[pair.tail_id]
        if head.trigger.strip().lower() != tail.trigger.strip().lower():
            continue
        if pair.head_id not in signatures or pair.tail_id not in signatures:
            counts["unaligned_exact_trigger_pairs"] += 1
            continue
        label = "positive" if pair.label else "negative"
        counts[f"{label}_pairs"] += 1
        for source, index in (("event_level", 0), ("mention_local", 1)):
            left, right = signatures[pair.head_id][index], signatures[pair.tail_id][index]
            counts[f"{label}_{source}_equal"] += left == right
            counts[f"{label}_{source}_different"] += left != right
            counts[f"{label}_{source}_both_nonempty"] += bool(left) and bool(right)
            counts[f"{label}_{source}_either_nonempty"] += bool(left) or bool(right)
    return counts


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _summary(counts: Counter[str]) -> dict:
    result: dict[str, dict] = {}
    for label in ("positive", "negative"):
        total = counts[f"{label}_pairs"]
        result[label] = {"pairs": total}
        for source in ("event_level", "mention_local"):
            values = {
                name: counts[f"{label}_{source}_{name}"]
                for name in ("equal", "different", "both_nonempty", "either_nonempty")
            }
            result[label][source] = {
                **values,
                **{
                    f"{name}_rate": value / total if total else 0.0
                    for name, value in values.items()
                },
            }
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arg", required=True, type=Path)
    parser.add_argument("--ere", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    selected_ids = [str(doc_id) for doc_id in manifest.get("doc_ids", [])]
    if (
        manifest.get("doc_count") != len(selected_ids)
        or len(set(selected_ids)) != len(selected_ids)
    ):
        raise SystemExit(f"{args.manifest}: invalid doc_count or duplicate doc_ids")

    arg_by_id = {doc.doc_id: doc for doc in load_maven_arg(args.arg)}
    ere_by_id = {str(row["id"]): row for row in read_jsonl(args.ere)}
    missing = [
        doc_id
        for doc_id in selected_ids
        if doc_id not in arg_by_id or doc_id not in ere_by_id
    ]
    if missing:
        raise SystemExit(f"manifest documents missing from an annotation view; first={missing[0]}")

    counts: Counter[str] = Counter()
    for doc_id in selected_ids:
        counts.update(analyze_document(arg_by_id[doc_id], ere_by_id[doc_id]))
    report = {
        "schema_version": "ekg.coref_argument_locality.v1",
        "n_docs": len(selected_ids),
        "alignment": {
            name: counts[name]
            for name in (
                "arg_mentions",
                "aligned_mentions",
                "unaligned_mentions",
                "unaligned_exact_trigger_pairs",
            )
        },
        "exact_trigger_same_type": _summary(counts),
        "hashes": {
            "arg": _sha256(args.arg),
            "ere": _sha256(args.ere),
            "manifest": _sha256(args.manifest),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report["exact_trigger_same_type"], indent=2, sort_keys=True))
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
