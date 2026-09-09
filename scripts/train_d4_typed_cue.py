#!/usr/bin/env python
"""Train one frozen D4 typed-cue factuality arm without reading evaluation data."""

from __future__ import annotations

import argparse
import json
import random
from collections.abc import Sequence
from pathlib import Path

from ekg.core.protocol import load_manifest_ids
from ekg.factuality.detection import split_candidate_features
from ekg.factuality.evidence import evidence_candidates, gold_evidence_spans
from ekg.factuality.metrics import evidence_span_prf, factuality_report
from ekg.factuality.typed_cues import (
    CONFIG_FILE,
    CUE_HEAD_FILE,
    CUE_TYPES,
    DECISION_HEAD_FILE,
    TypedCueFactualityDetector,
    build_typed_cue_decision_head,
    cue_type_targets,
    typed_cue_features,
    typed_cue_logits_per_mention,
    validate_typed_cue_arm,
)
from ekg.nodes.encoding import encode_spans
from ekg.relations.data.maven_fact import (
    FACTUALITY_LABELS,
    FactualityDocument,
    factuality_distribution,
    load_maven_fact,
)

EVIDENCE_POS_WEIGHT = 15.0
DEV_CURVE_FILE = "dev_curve.json"


def _split_docs(
    source: Path, train_manifest: Path, selection_manifest: Path
) -> tuple[list[FactualityDocument], list[FactualityDocument]]:
    train_ids = load_manifest_ids(train_manifest)
    selection_ids = load_manifest_ids(selection_manifest)
    if set(train_ids) & set(selection_ids):
        raise ValueError("train and selection-dev manifests overlap")
    docs = {doc.doc_id: doc for doc in load_maven_fact(source)}
    missing = (set(train_ids) | set(selection_ids)) - docs.keys()
    if missing:
        raise ValueError(f"training source misses {len(missing)} manifest documents")
    # A D4 OOF worker receives a source materialized from exactly these two
    # manifests.  Rejecting extra rows proves an evaluation fold was never
    # slipped into the trainer's readable input.
    if set(docs) != set(train_ids) | set(selection_ids):
        raise ValueError("training source is not exactly train plus selection-dev")
    return [docs[doc_id] for doc_id in train_ids], [docs[doc_id] for doc_id in selection_ids]


def _class_weights(docs: Sequence[FactualityDocument], alpha: float) -> list[float]:
    counts = factuality_distribution(docs)
    total = sum(counts.values())
    raw = [
        (total / counts[label]) ** alpha if counts[label] else 0.0 for label in FACTUALITY_LABELS
    ]
    present = [weight for weight in raw if weight]
    if not present:
        raise ValueError("training set contains no factuality labels")
    mean = sum(present) / len(present)
    return [weight / mean for weight in raw]


def _evaluate(
    checkpoint: Path,
    docs: Sequence[FactualityDocument],
    *,
    arm: str,
    max_length: int,
    stride: int,
    use_structure: bool,
    permutation_seed: int,
) -> tuple[dict, dict]:
    detector = TypedCueFactualityDetector(
        checkpoint,
        arm=arm,
        max_length=max_length,
        stride=stride,
        use_structure=use_structure,
        permutation_seed=permutation_seed,
    )
    labels: dict[str, str] = {}
    evidence: dict[str, set[tuple[int, int]]] = {}
    gold: dict[str, str] = {}
    for doc in docs:
        predictions = detector.predict(doc)
        if set(predictions) != {mention.mention_id for mention in doc.mentions}:
            raise ValueError(f"{doc.doc_id}: detector did not cover every mention")
        for mention_id, prediction in predictions.items():
            labels[mention_id] = prediction.factuality
            evidence[mention_id] = {
                (span.char_start, span.char_end) for span in prediction.evidence
            }
        gold.update({mention.mention_id: mention.factuality for mention in doc.mentions})
    return factuality_report(labels, gold), evidence_span_prf(evidence, gold_evidence_spans(docs))


def train(args: argparse.Namespace) -> None:
    import torch
    from torch import nn
    from transformers import AutoModel, AutoTokenizer

    train_docs, selection_docs = _split_docs(
        args.train, args.train_manifest, args.selection_manifest
    )
    if args.output.exists():
        raise ValueError(f"refusing to overwrite checkpoint directory {args.output}")
    torch.manual_seed(args.seed)
    random.seed(args.seed)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    tokenizer = AutoTokenizer.from_pretrained(str(args.model))
    encoder = AutoModel.from_pretrained(str(args.model)).to(device)
    encoder.gradient_checkpointing_enable()
    hidden = encoder.config.hidden_size
    cue_head = nn.Linear(4 * hidden, len(CUE_TYPES)).to(device)
    decision_head = build_typed_cue_decision_head(
        hidden, 0, arm=args.arm
    ).to(device)
    optimizer = torch.optim.AdamW(
        [*encoder.parameters(), *cue_head.parameters(), *decision_head.parameters()],
        lr=args.lr,
    )
    weights = torch.tensor(_class_weights(train_docs, args.alpha), device=device)
    label_loss_fn = nn.NLLLoss(weight=weights)
    cue_loss_fn = nn.BCEWithLogitsLoss(
        pos_weight=torch.full((len(CUE_TYPES),), EVIDENCE_POS_WEIGHT, device=device)
    )
    label_index = {label: index for index, label in enumerate(FACTUALITY_LABELS)}

    def forward(doc: FactualityDocument):
        candidates = [evidence_candidates(doc, mention) for mention in doc.mentions]
        starts = [mention.span.char_start for mention in doc.mentions]
        starts += [cue.char_start for cues in candidates for cue in cues]
        pooled = encode_spans(
            encoder,
            tokenizer,
            doc.doc_text,
            starts,
            max_length=args.max_length,
            stride=args.stride,
            device=device,
        )
        triggers = pooled[: len(doc.mentions)]
        features = split_candidate_features(
            pooled, len(doc.mentions), [len(cues) for cues in candidates]
        )
        cue_logits = typed_cue_logits_per_mention(triggers, features, cue_head)
        cue_features = typed_cue_features(features, cue_logits)
        if args.arm == "permutation":
            from ekg.factuality.typed_cues import permute_cue_features

            cue_features = permute_cue_features(
                cue_features, [doc.doc_id] * len(doc.mentions), args.permutation_seed
            )
        probabilities = decision_head(triggers, None, cue_features)
        supervised_logits: list = []
        supervised_targets: list = []
        for mention, per_mention, logits in zip(
            doc.mentions, candidates, cue_logits, strict=True
        ):
            if not mention.evidence:
                continue
            targets = cue_type_targets(per_mention, mention)
            if not any(modality or polarity for modality, polarity in targets):
                # Gold evidence outside the same-sentence candidate universe is
                # a documented recall ceiling, not a false all-negative target.
                continue
            supervised_logits.append(logits)
            supervised_targets.append(
                torch.tensor(targets, dtype=logits.dtype, device=device)
            )
        return probabilities, supervised_logits, supervised_targets

    def save_checkpoint() -> None:
        args.output.mkdir(parents=True, exist_ok=True)
        encoder.save_pretrained(args.output)
        tokenizer.save_pretrained(args.output)
        torch.save(cue_head.state_dict(), args.output / CUE_HEAD_FILE)
        torch.save(decision_head.state_dict(), args.output / DECISION_HEAD_FILE)
        config = {
            "schema_version": "ekg.typed_cue_factuality.v1",
            "labels": list(FACTUALITY_LABELS),
            "arm": args.arm,
            "use_structure": False,
            "permutation_seed": args.permutation_seed,
            "max_length": args.max_length,
            "stride": args.stride,
        }
        (args.output / CONFIG_FILE).write_text(json.dumps(config, indent=2) + "\n")

    curve: list[dict] = []
    best = {"macro_f1": -1.0, "epoch": 0}
    best_state: dict[str, dict] | None = None
    order = list(range(len(train_docs)))
    for epoch in range(1, args.epochs + 1):
        random.shuffle(order)
        encoder.train()
        cue_head.train()
        decision_head.train()
        total_label = total_cue = 0.0
        seen = 0
        for step, index in enumerate(order, 1):
            doc = train_docs[index]
            probabilities, cue_logits, cue_targets = forward(doc)
            target = torch.tensor(
                [label_index[mention.factuality] for mention in doc.mentions], device=device
            )
            label_loss = label_loss_fn(probabilities.clamp_min(1e-12).log(), target)
            loss = label_loss
            if cue_logits:
                cue_loss = cue_loss_fn(torch.cat(cue_logits), torch.cat(cue_targets))
                loss = loss + args.cue_weight * cue_loss
                total_cue += float(cue_loss.detach())
            loss.backward()
            optimizer.step()
            optimizer.zero_grad()
            total_label += float(label_loss.detach())
            seen += 1
            if step % 200 == 0:
                print(
                    f"epoch {epoch} step {step}/{len(order)} label={total_label / seen:.4f} "
                    f"typed-cue={total_cue / seen:.4f}",
                    flush=True,
                )
        save_checkpoint()
        report, evidence = _evaluate(
            args.output,
            selection_docs,
            arm=args.arm,
            max_length=args.max_length,
            stride=args.stride,
            use_structure=False,
            permutation_seed=args.permutation_seed,
        )
        entry = {
            "epoch": epoch,
            "macro_f1": report["macro_f1"],
            "per_class_f1": {label: row["f1"] for label, row in report["per_class"].items()},
            "evidence_span_f1": evidence["f1"],
        }
        curve.append(entry)
        print(
            f"epoch {epoch} selection macro-F1={entry['macro_f1']:.4f} "
            f"evidence-F1={entry['evidence_span_f1']:.4f}",
            flush=True,
        )
        if entry["macro_f1"] > best["macro_f1"]:
            best = {"macro_f1": entry["macro_f1"], "epoch": epoch}
            best_state = {
                "encoder": {
                    key: value.detach().cpu().clone()
                    for key, value in encoder.state_dict().items()
                },
                "cue_head": {
                    key: value.detach().cpu().clone()
                    for key, value in cue_head.state_dict().items()
                },
                "decision_head": {
                    key: value.detach().cpu().clone()
                    for key, value in decision_head.state_dict().items()
                },
            }
    if best_state is None:
        raise ValueError("no selected checkpoint was produced")
    if best["epoch"] != args.epochs:
        encoder.load_state_dict(best_state["encoder"])
        cue_head.load_state_dict(best_state["cue_head"])
        decision_head.load_state_dict(best_state["decision_head"])
        save_checkpoint()
    (args.output / DEV_CURVE_FILE).write_text(
        json.dumps({"selected_epoch": best["epoch"], "curve": curve}, indent=2) + "\n"
    )
    print(f"saved selected epoch {best['epoch']} to {args.output}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train", required=True, type=Path)
    parser.add_argument("--train-manifest", required=True, type=Path)
    parser.add_argument("--selection-manifest", required=True, type=Path)
    parser.add_argument("--model", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--arm", required=True, choices=("full", "remove_core", "permutation"))
    parser.add_argument("--epochs", type=int, default=12)
    parser.add_argument("--lr", type=float, default=2e-5)
    parser.add_argument("--alpha", type=float, default=0.5)
    parser.add_argument("--cue-weight", type=float, default=1.0)
    parser.add_argument("--max-length", type=int, default=128)
    parser.add_argument("--stride", type=int, default=64)
    parser.add_argument("--seed", type=int, default=13)
    parser.add_argument("--permutation-seed", type=int, default=13)
    args = parser.parse_args()
    args.arm = validate_typed_cue_arm(args.arm)
    for path in (args.train, args.train_manifest, args.selection_manifest, args.model):
        if not path.exists():
            raise SystemExit(f"missing input: {path}")
    train(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
