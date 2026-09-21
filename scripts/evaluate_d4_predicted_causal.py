#!/usr/bin/env python
"""Score one trained D4 v6.2 arm on its fold's evaluation manifest.

Separate from the trainer on purpose: the S1 audit property is that the
evaluation manifest never appears in a training command, so evaluation lives in
its own process that only ever *loads* a finished checkpoint.

It also emits the two frozen mediators and, for the ``rewired`` arm, the proof
that the control really was degree- and payload-matched. Gold relations are read
here and only here — they never touch a model arm.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from train_d4_predicted_causal import (
    CONFIG_FILE,
    HEAD_FILE,
    RESIDUAL_FILE,
    _score,
    load_edges,
)

from ekg.core.protocol import load_manifest_ids
from ekg.core.schema import RelationType
from ekg.core.stage_bundle import sha256_file
from ekg.factuality.causal_residual import (
    ARMS,
    CausalEdge,
    build_causal_residual,
    consistency_violations,
    rewiring_diagnostics,
    validate_arm,
)
from ekg.factuality.metrics import majority_baseline_report
from ekg.relations.data.maven_ere import load_maven_ere
from ekg.relations.data.maven_fact import FACTUALITY_LABELS, load_maven_fact
from ekg.relations.pairs import gold_pair_labels


def _pooled_rewiring(
    original: dict[str, list[CausalEdge]], rewired: dict[str, list[CausalEdge]]
) -> dict:
    """Pooled proof that the negative control is structure-matched."""
    edges = 0
    identical = 0
    drifted = 0
    for doc_id, source_edges in original.items():
        report = rewiring_diagnostics(source_edges, rewired[doc_id])
        edges += report.edges
        identical += report.identical_edges
        if not report.structure_preserved:
            drifted += 1
    if drifted:
        raise ValueError(f"{drifted} documents lost the frozen structure under rewiring")
    return {
        "edges": edges,
        "identical_edges": identical,
        "identical_edge_fraction": identical / edges if edges else 0.0,
    }


def _mediators(source: Path, document_ids: list[str], predicted: dict[str, str]) -> dict:
    """Pair-micro CAUSE/PRECONDITION violation rates over gold-expanded pairs."""
    wanted = set(document_ids)
    pooled: dict[tuple[str, str], str] = {}
    for doc in load_maven_ere(source):
        if doc.doc_id not in wanted:
            continue
        pooled.update(
            gold_pair_labels(doc, family=RelationType.CAUSAL, expand_event_relations=True)
        )
    return consistency_violations(pooled, predicted)


def evaluate(args: argparse.Namespace) -> dict:
    import torch
    from torch import nn
    from transformers import AutoModel, AutoTokenizer

    arm = validate_arm(args.arm)
    config = json.loads((args.checkpoint / CONFIG_FILE).read_text(encoding="utf-8"))
    if config["arm"] != arm or config["fold"] != args.fold:
        raise ValueError("checkpoint was trained for another arm or fold")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    tokenizer = AutoTokenizer.from_pretrained(str(args.checkpoint))
    encoder = AutoModel.from_pretrained(str(args.checkpoint)).to(device)
    hidden = encoder.config.hidden_size
    head = nn.Linear(hidden, len(FACTUALITY_LABELS)).to(device)
    head.load_state_dict(torch.load(args.checkpoint / HEAD_FILE, map_location=device))
    residual = None
    if arm != "base":
        residual = build_causal_residual(hidden).to(device)
        residual.load_state_dict(
            torch.load(args.checkpoint / RESIDUAL_FILE, map_location=device)
        )
    elif (args.checkpoint / RESIDUAL_FILE).exists():
        raise ValueError("a base checkpoint must not carry a residual")

    document_ids = load_manifest_ids(args.manifest)
    docs = {doc.doc_id: doc for doc in load_maven_fact(args.source)}
    missing = [doc_id for doc_id in document_ids if doc_id not in docs]
    if missing:
        raise ValueError(f"{len(missing)} evaluation documents are absent from the source")
    evaluation_docs = [docs[doc_id] for doc_id in document_ids]

    edges = load_edges(
        args.sidecar,
        config["class_weights"],
        arm=arm,
        fold=args.fold,
        document_ids=document_ids,
    )
    report, predicted = _score(
        evaluation_docs,
        edges,
        arm=arm,
        encoder=encoder,
        tokenizer=tokenizer,
        residual=residual,
        head=head,
        max_length=config["recipe"]["max_length"],
        device=device,
    )
    gold = {m.mention_id: m.factuality for doc in evaluation_docs for m in doc.mentions}

    payload = {
        "schema_version": "ekg.d4_predicted_causal_evaluation.v1",
        "arm": arm,
        "fold": args.fold,
        "seed": config["seed"],
        "documents": len(document_ids),
        "mentions": len(predicted),
        "macro_f1": report["macro_f1"],
        "accuracy": report["accuracy"],
        "per_class": report["per_class"],
        "majority_floor": majority_baseline_report(gold)["macro_f1"],
        "mediators": _mediators(args.relation_source, document_ids, predicted),
        "edges": sum(len(value) for value in edges.values()),
        "inputs": {
            "checkpoint_config": {
                "path": str(args.checkpoint / CONFIG_FILE),
                "sha256": sha256_file(args.checkpoint / CONFIG_FILE),
            },
            "manifest": {"path": str(args.manifest), "sha256": sha256_file(args.manifest)},
            "sidecar": {"path": str(args.sidecar), "sha256": sha256_file(args.sidecar)},
            "relation_source": {
                "path": str(args.relation_source),
                "sha256": sha256_file(args.relation_source),
            },
        },
        "gold_edges_used_by_model": False,
        "gold_relations_used_for_mediators_only": True,
    }
    if arm == "rewired":
        payload["rewiring"] = _pooled_rewiring(
            load_edges(
                args.sidecar,
                config["class_weights"],
                arm="full",
                fold=args.fold,
                document_ids=document_ids,
            ),
            edges,
        )

    if args.output.exists() or args.labels_output.exists():
        raise FileExistsError("refusing to overwrite an existing evaluation")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.labels_output.write_text(
        json.dumps(predicted, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    args.output.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arm", required=True, choices=ARMS)
    parser.add_argument("--fold", required=True, type=int)
    parser.add_argument("--checkpoint", required=True, type=Path)
    parser.add_argument("--source", required=True, type=Path, help="MAVEN-FACT jsonl")
    parser.add_argument(
        "--relation-source", required=True, type=Path, help="MAVEN-ERE jsonl, mediators only"
    )
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--sidecar", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--labels-output", required=True, type=Path)
    args = parser.parse_args()
    payload = evaluate(args)
    print(
        json.dumps(
            {
                "arm": payload["arm"],
                "fold": payload["fold"],
                "macro_f1": payload["macro_f1"],
                "mediators": payload["mediators"],
                "output_sha256": sha256_file(args.output),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
