#!/usr/bin/env python
"""Bounded, torch-free check of the D4 v6.2 non-model pipeline on real inputs.

Everything between the frozen sidecar and the model — the cost-aware edge
decision, the degree-preserving rewiring, the mention indexing and the two
mediators — runs on CPU. This exercises it over the first `--documents`
documents of one fold's evaluation sidecar, so a contract break shows up in
seconds instead of after a GPU run.

It never loads an encoder and never writes into the run directory.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from train_d4_predicted_causal import _sidecar_documents

from ekg.core.schema import RelationType
from ekg.factuality.causal_residual import (
    consistency_violations,
    decide_edges,
    residual_inputs,
    rewire_edges,
    rewiring_diagnostics,
)
from ekg.relations.data.maven_ere import load_maven_ere
from ekg.relations.data.maven_fact import load_maven_fact
from ekg.relations.pairs import gold_pair_labels


def smoke_contract(
    *,
    sidecar: Path,
    calibration_metadata: Path,
    fact_source: Path,
    relation_source: Path,
    fold: int,
    documents: int,
) -> dict:
    if documents <= 0:
        raise ValueError("--documents must be positive")
    calibration = json.loads(calibration_metadata.read_text(encoding="utf-8"))
    if calibration.get("fold") != fold:
        raise ValueError("calibration metadata belongs to another fold")
    weights = calibration["class_weights"]

    decided: dict[str, list] = {}
    for doc_id, rows in _sidecar_documents(sidecar):
        decided[doc_id] = decide_edges(rows, weights)
        if len(decided) == documents:
            break
    if len(decided) != documents:
        raise ValueError(f"{sidecar} holds fewer than {documents} documents")

    fact = {doc.doc_id: doc for doc in load_maven_fact(fact_source) if doc.doc_id in decided}
    ere = {doc.doc_id: doc for doc in load_maven_ere(relation_source) if doc.doc_id in decided}
    missing = set(decided) - (set(fact) & set(ere))
    if missing:
        raise ValueError(f"{len(missing)} smoke documents are absent from a source")

    edges = 0
    rewired_identical = 0
    gated_targets = 0
    for doc_id, doc_edges in decided.items():
        mention_ids = [mention.mention_id for mention in fact[doc_id].mentions]
        grouped = residual_inputs(doc_edges, mention_ids)
        gated_targets += sum(len(targets) for _, targets, _ in grouped.values())
        rewired = rewire_edges(doc_edges, fold=fold, doc_id=doc_id)
        report = rewiring_diagnostics(doc_edges, rewired)
        if not report.structure_preserved:
            raise ValueError(f"{doc_id}: rewiring lost the frozen structure")
        edges += report.edges
        rewired_identical += report.identical_edges

    predicted = {
        mention.mention_id: mention.factuality
        for doc in fact.values()
        for mention in doc.mentions
    }
    pooled_pairs: dict[tuple[str, str], str] = {}
    for doc in ere.values():
        pooled_pairs.update(
            gold_pair_labels(doc, family=RelationType.CAUSAL, expand_event_relations=True)
        )
    mediators = consistency_violations(pooled_pairs, predicted)

    return {
        "fold": fold,
        "documents": len(decided),
        "mentions": len(predicted),
        "edges": edges,
        "gated_residual_targets": gated_targets,
        "rewired_identical_edges": rewired_identical,
        "gold_expanded_causal_pairs": len(pooled_pairs),
        # Mediators on *gold* factuality here: the smoke has no model, so this
        # only proves the counter runs and its denominators are non-empty.
        "mediators_on_gold_labels": mediators,
        "torch_loaded": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sidecar", required=True, type=Path)
    parser.add_argument("--calibration-metadata", required=True, type=Path)
    parser.add_argument("--fact-source", required=True, type=Path)
    parser.add_argument("--relation-source", required=True, type=Path)
    parser.add_argument("--fold", required=True, type=int)
    parser.add_argument("--documents", type=int, default=20)
    args = parser.parse_args()
    print(
        json.dumps(
            smoke_contract(
                sidecar=args.sidecar,
                calibration_metadata=args.calibration_metadata,
                fact_source=args.fact_source,
                relation_source=args.relation_source,
                fold=args.fold,
                documents=args.documents,
            ),
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
