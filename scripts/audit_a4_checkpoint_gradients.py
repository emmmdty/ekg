#!/usr/bin/env python
"""Differentiate a frozen A4 checkpoint on deterministic train-only documents.

No optimizer, selection-dev or evaluation scores. This samples train-mode
gradients at a selected checkpoint; it cannot reconstruct its training history.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from ekg.core.protocol import load_manifest_ids
from ekg.core.stage_bundle import sha256_file
from ekg.relations.data.maven_ere import TIMEX_EVENT_TYPE, load_maven_ere


def select_documents(docs, train_ids, count):
    if count < 1:
        raise ValueError("sample count must be positive")
    eligible = [d for d in docs if d.doc_id in train_ids and len(d.nodes) <= 32
                and sum(n.event_type != TIMEX_EVENT_TYPE for n in d.nodes) >= 2
                and len(d.doc_text.split("\n")) <= 8]
    eligible.sort(key=lambda d: hashlib.sha256(d.doc_id.encode()).hexdigest())
    if len(eligible) < count:
        raise ValueError(f"only {len(eligible)} eligible train documents for {count} requested")
    return eligible[:count]


def audit_document(doc, encoder, tokenizer, heads, *, max_length, weight, device):
    import torch
    from audit_auxiliary_gradients import gradient_report
    from train_a4_pair_evidence import family_targets, label_indices, rows_by_document

    from ekg.nodes.encoding import pair_features
    from ekg.relations.evidence_objective import loss_terms, supervised_rows
    from ekg.relations.extractor.supervised import (
        FAMILY_SUBTYPES,
        distance_bucket,
        encode_trigger_reps,
    )
    from ekg.relations.pair_evidence import (
        counterfactual_sentence_ids,
        document_pair_evidence,
        pair_counterfactual_embeddings,
    )

    grouped, _ = rows_by_document([doc], None)
    rows = grouped[doc.doc_id]
    records = document_pair_evidence(doc, [(r.head_id, r.tail_id) for r in rows])
    embeddings = encode_trigger_reps(encoder, tokenizer, doc.nodes, doc.doc_text,
                                     max_length, device)
    features = pair_features(torch.stack([embeddings[r.head_id] for r in rows]),
                             torch.stack([embeddings[r.tail_id] for r in rows]))
    distances = torch.tensor([distance_bucket(r.distance) for r in rows], device=device)
    logits = heads(features, distances)
    index = label_indices(FAMILY_SUBTYPES)
    targets = {f: torch.tensor(family_targets(rows, f, index), device=device) for f in index}
    selected, skipped = supervised_rows(records, logits, targets, arm="full")
    cf = {}
    for kind in ("masked", "retained"):
        if selected:
            requests = [((records[i].head_id, records[i].tail_id),
                         counterfactual_sentence_ids(records[i],
                             len(doc.doc_text.split("\n")), arm="full")[kind]) for i in selected]
            left, right = pair_counterfactual_embeddings(encoder, tokenizer, doc.nodes,
                doc.doc_text, requests, max_length, device)
            cf[kind] = pair_features(left, right)
    primary, revision, hinge = loss_terms(heads, features, distances, logits, targets,
                                          cf, selected, records, arm="full")
    main = sum(primary.values())
    combined = revision + weight * hinge
    comparisons = {"main_vs_revision": (main, revision), "main_vs_hinge": (main, hinge),
                   **{f"{f}_vs_combined_aux": (value, combined)
                      for f, value in primary.items()}}
    return {
        "id": doc.doc_id, "candidate_pairs": len(rows), "selected_rows": list(selected),
        "rows_dropped_by_cap": skipped,
        "loss": {**{f: float(v.detach()) for f, v in primary.items()},
                 "revision": float(revision.detach()), "hinge": float(hinge.detach())},
        "encoder_alignment": {name: gradient_report(left, right, encoder.parameters(),
            weight=weight if name == "main_vs_hinge" else 1.0)
            for name, (left, right) in comparisons.items()},
        "heads_alignment": gradient_report(main, combined, heads.parameters()),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--train-manifest", required=True, type=Path)
    parser.add_argument("--checkpoint", required=True, type=Path)
    parser.add_argument("--documents", type=int, default=8)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    metadata = json.loads((args.checkpoint / "run_metadata.json").read_text())
    config = metadata["configuration"]
    if metadata["status"] != "complete" or config["arm"] != "full" or config["seed"] != 13:
        raise ValueError("requires frozen completed full-arm seed-13 checkpoint")
    if metadata["manifest_sha256"]["train"] != sha256_file(args.train_manifest):
        raise ValueError("checkpoint/train manifest mismatch")
    docs = select_documents(list(load_maven_ere(args.source, include_timex=True)),
                            set(load_manifest_ids(args.train_manifest)), args.documents)
    import torch

    from ekg.relations.extractor.supervised import SupervisedRelationExtractor

    model = SupervisedRelationExtractor(checkpoint_path=str(args.checkpoint))
    model._ensure_model()
    model._encoder.train()
    model._model.train()
    report = {"schema_version": "ekg.a4_checkpoint_gradient_audit.v1",
              "diagnostic_only": True, "optimizer_steps": 0, "seed": 13,
              "checkpoint_location": str(args.checkpoint.resolve()),
              "parameter_scope": "all encoder parameters; all pair heads separately",
              "sample_rule": "sha256(doc_id), train-only, 2..32 mentions, <=8 sentences",
              "final_valid_accessed": False, "checkpoint_sha256": {
                  p.name: sha256_file(p) for p in args.checkpoint.iterdir() if p.is_file()},
              "input_sha256": {str(p): sha256_file(p) for p in
                  (args.source, args.train_manifest, Path(__file__))}, "documents": []}
    for doc in docs:
        torch.manual_seed(13)
        row = audit_document(doc, model._encoder, model._tokenizer, model._model,
                             max_length=config["max_length"],
                             weight=config["consistency_weight"], device=model._device)
        report["documents"].append(row)
        print(json.dumps(row), flush=True)
    if any(p.grad is not None for p in (*model._encoder.parameters(), *model._model.parameters())):
        raise RuntimeError("audit unexpectedly mutated .grad")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as handle:
        json.dump(report, handle, indent=2, allow_nan=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
