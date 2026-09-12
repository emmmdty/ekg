#!/usr/bin/env python
"""Dump one A4 arm's predictions over the frozen candidate universe.

Inference is the base pass plus the revised pass the arm's residual defines,
applied to exactly the rows the base pass itself calls causal-positive -- never
to a row chosen by a gold label.  Every candidate pair still receives a label,
so the normaliser downstream sees the same population the official evaluator
scores; the edge file is byte-compatible with `evaluate_relations.py
--dump-predictions`, so `normalize_predictions` and `score_maven_ere_official.py`
are reused verbatim rather than re-implemented.

Alongside the edges it writes what the contract asks to be kept per instance:
the citation for every pair, the base/masked/retained causal logits for every
supervised row, and the registered mediator with its denominators.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ekg.relations.data.maven_ere import load_maven_ere
from ekg.relations.pair_evidence import (
    CONSISTENCY_FAMILY,
    CONSISTENCY_PAIR_CAP,
    arm_flags,
    context_dependence_report,
    counterfactual_sentence_ids,
    document_pair_evidence,
    load_pair_evidence_config,
    necessity_scoreable,
    pair_evidence_sidecar,
)
from ekg.relations.pair_heads import PAIR_EVIDENCE_HEAD, load_pair_head_config

NONE_INDEX = 0


def _write(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gold", required=True, type=Path, help="internal-dev documents")
    parser.add_argument("--checkpoint", required=True, type=Path)
    parser.add_argument("--max-length", type=int, required=True)
    parser.add_argument("--edges-output", required=True, type=Path)
    parser.add_argument("--evidence-output", required=True, type=Path)
    parser.add_argument("--logits-output", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path, help="report.json")
    parser.add_argument("--max-docs", type=int, help="smoke only: first N documents")
    args = parser.parse_args()

    head_config = load_pair_head_config(args.checkpoint)
    if head_config["name"] != PAIR_EVIDENCE_HEAD:
        raise SystemExit(f"{args.checkpoint} carries a {head_config['name']!r} head")
    config = load_pair_evidence_config(args.checkpoint)
    arm = str(config["arm"])
    flags = arm_flags(arm)

    import torch
    from transformers import AutoModel, AutoTokenizer

    from ekg.nodes.encoding import pair_features
    from ekg.relations.extractor.supervised import (
        FAMILY_SUBTYPES,
        distance_bucket,
        encode_trigger_reps,
    )
    from ekg.relations.pair_evidence import pair_counterfactual_embeddings
    from ekg.relations.pair_heads import build_pair_head
    from ekg.relations.pairs import pair_examples

    device = "cuda" if torch.cuda.is_available() else "cpu"
    tokenizer = AutoTokenizer.from_pretrained(str(args.checkpoint))
    encoder = AutoModel.from_pretrained(str(args.checkpoint)).to(device).eval()
    heads = build_pair_head(
        PAIR_EVIDENCE_HEAD,
        hidden_size=encoder.config.hidden_size,
        subtype_counts={family: len(subs) for family, subs in FAMILY_SUBTYPES.items()},
    ).to(device)
    heads.load_state_dict(torch.load(args.checkpoint / "heads.pt", map_location="cpu"))
    heads.eval()

    docs = list(load_maven_ere(args.gold, include_timex=True))
    if args.max_docs:
        docs = docs[: args.max_docs]
    edges_rows: list[dict] = []
    evidence: dict[str, dict] = {}
    traces: dict[str, dict] = {}
    mediator_records = []
    predicted_causal: dict[tuple[str, str], str] = {}
    gold_causal: dict[tuple[str, str], str] = {}
    logit_drop: dict[tuple[str, str], float] = {}
    candidates = 0
    revised_rows = 0

    with torch.no_grad():
        for doc in docs:
            rows = pair_examples(doc, expand_event_relations=True)
            candidates += len(rows)
            records = document_pair_evidence(
                doc.nodes, doc.doc_text, [(row.head_id, row.tail_id) for row in rows]
            )
            embeddings = encode_trigger_reps(
                encoder, tokenizer, doc.nodes, doc.doc_text, args.max_length, device
            )
            feats = pair_features(
                torch.stack([embeddings[row.head_id] for row in rows]),
                torch.stack([embeddings[row.tail_id] for row in rows]),
            )
            dist_ids = torch.tensor(
                [distance_bucket(row.distance) for row in rows], device=device
            )
            logits = heads(feats, dist_ids)
            probabilities = {
                family: torch.softmax(value, dim=-1) for family, value in logits.items()
            }
            causal_class = probabilities[CONSISTENCY_FAMILY].argmax(dim=-1)

            selected: list[int] = []
            if flags.evidence_stream:
                selected = [
                    index
                    for index, value in enumerate(causal_class.tolist())
                    if value != NONE_INDEX
                    and CONSISTENCY_FAMILY not in rows[index].ignored_families
                ][:CONSISTENCY_PAIR_CAP]
            if selected:
                sentences = len(doc.doc_text.split("\n"))
                requests = {"masked": [], "retained": []}
                for index in selected:
                    record = records[index]
                    sets = counterfactual_sentence_ids(record, sentences, arm=arm)
                    for kind in requests:
                        requests[kind].append(((record.head_id, record.tail_id), sets[kind]))
                counterfactual = {}
                for kind, batch in requests.items():
                    head_emb, tail_emb = pair_counterfactual_embeddings(
                        encoder, tokenizer, doc.nodes, doc.doc_text, batch,
                        args.max_length, device,
                    )
                    counterfactual[kind] = pair_features(head_emb, tail_emb)
                picked = torch.tensor(selected, device=device)
                revised = heads(feats[picked], dist_ids[picked], counterfactual["retained"])
                revised_causal = torch.softmax(revised[CONSISTENCY_FAMILY], dim=-1)
                base_logits = logits[CONSISTENCY_FAMILY][picked]
                masked_logits = heads.base(counterfactual["masked"], dist_ids[picked])[
                    CONSISTENCY_FAMILY
                ]
                retained_logits = heads.base(counterfactual["retained"], dist_ids[picked])[
                    CONSISTENCY_FAMILY
                ]
                for offset, index in enumerate(selected):
                    record = records[index]
                    # How much the *predicted* class loses when the interior is
                    # removed: the per-instance form of "did this prediction read
                    # its context at all".
                    predicted_class = int(causal_class[index])
                    drop = float(
                        base_logits[offset][predicted_class]
                        - masked_logits[offset][predicted_class]
                    )
                    logit_drop[(record.head_id, record.tail_id)] = drop
                    traces[f"{doc.doc_id}::{record.head_id}::{record.tail_id}"] = {
                        "base": base_logits[offset].tolist(),
                        "masked": masked_logits[offset].tolist(),
                        "retained": retained_logits[offset].tolist(),
                        "revised_probabilities": revised_causal[offset].tolist(),
                        "predicted_class": predicted_class,
                        "predicted_logit_drop": drop,
                        "cited": list(record.cited(arm)),
                        "necessity_scoreable": necessity_scoreable(record, arm=arm),
                    }
                # The revised pass is the arm's prediction rule, so it replaces
                # the base label rather than being reported beside it.
                probabilities[CONSISTENCY_FAMILY][picked] = revised_causal
                revised_rows += len(selected)

            doc_edges: list[dict] = []
            for position, row in enumerate(rows):
                key = (row.head_id, row.tail_id)
                for family, subtypes in FAMILY_SUBTYPES.items():
                    if family in row.ignored_families:
                        continue
                    values = probabilities[family][position]
                    confidence, class_index = float(values.max()), int(values.argmax())
                    if family == CONSISTENCY_FAMILY:
                        predicted_causal[key] = subtypes[class_index]
                        gold_causal[key] = row.labels.get(family, "NONE")
                    if class_index == NONE_INDEX:
                        continue
                    doc_edges.append(
                        {
                            "head_id": row.head_id,
                            "tail_id": row.tail_id,
                            "relation_type": family,
                            "subtype": subtypes[class_index],
                            "directed": True,
                            "confidence": confidence,
                        }
                    )
                if CONSISTENCY_FAMILY not in row.ignored_families:
                    mediator_records.append(records[position])
            edges_rows.append({"doc_id": doc.doc_id, "edges": doc_edges})
            evidence[doc.doc_id] = pair_evidence_sidecar(records, arm=arm)

    args.edges_output.parent.mkdir(parents=True, exist_ok=True)
    args.edges_output.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in edges_rows),
        encoding="utf-8",
    )
    _write(args.evidence_output, evidence)
    _write(args.logits_output, traces)
    mediator = context_dependence_report(
        mediator_records, predicted_causal, gold_causal, logit_drop=logit_drop
    )
    _write(
        args.output,
        {
            "schema_version": "ekg.a4_pair_evidence_evaluation.v1",
            "arm": arm,
            "documents": len(docs),
            "candidate_pairs": candidates,
            "revised_rows": revised_rows,
            "predicted_edges": sum(len(row["edges"]) for row in edges_rows),
            "mediator": mediator,
            "checkpoint_config": config,
        },
    )
    print(
        f"[a4-eval:{arm}] {len(docs)} docs, {candidates} candidates, "
        f"{revised_rows} revised, cross_fp={mediator['cross_sentence_false_positives']}, "
        f"context_independent="
        f"{mediator['context_independent_cross_sentence_false_positives']}"
        f"/{mediator['measured_cross_sentence_false_positives']}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
