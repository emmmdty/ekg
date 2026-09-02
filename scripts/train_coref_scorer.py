#!/usr/bin/env python
"""Train the similar-event discriminator on MAVEN-Arg mention pairs (server / CUDA).

The candidate universe is same-type mention pairs (a MAVEN event carries one
type, so cross-type pairs are trivially negative). Within it the decision that
matters is the **hard** one — a near-identical trigger belonging to a *different*
event — so `sample_training_pairs` keeps every positive and draws
``--hard-fraction`` of the negative budget from that subset. Raising it trades
merge recall for a lower mis-merge rate at training time, which is the knob the
canonicalizer's abstention band cannot buy back afterwards.

Shares the encoder pooling and pair feature with the detector and the relation
extractor (`nodes.encoding`), so a coreference decision is read off the same
representation as a relation decision.

    uv run --extra llm python scripts/train_coref_scorer.py \
        --train data/processed/maven_arg/train.jsonl \
        --model roberta-base --output runs/nodes/coref_supervised

``--save-every-epoch`` keeps `<output>/epochs/epoch-N` for every epoch. The in-loop dev
score here is pair-level F1, which is **not** what the chapter reports: the
first C4 run selected on it and the official MUC ranked the arms differently,
with each arm stopping at a different epoch. Keeping the epochs lets the
official evaluator do the selecting and lets the arms be read at matched
epochs, which is the only way the epoch stops being a confound.
"""

from __future__ import annotations

import argparse
import json
import random
from collections.abc import Sequence
from pathlib import Path

from ekg.core.protocol import split_docs_by_manifests
from ekg.nodes.coref import (
    HEAD_FILE,
    CorefPair,
    cluster_of_nodes,
    labelled_coref_pairs,
    sample_training_pairs,
)
from ekg.nodes.discriminative import (
    ALL_COMPONENTS,
    ARGUMENT_POOLING_ORACLE,
    CONFIG_FILE,
    CONTEXT_POOLING,
    FEATURE_NAMES,
    argument_spans_and_counts,
    context_ranges_for,
    head_input_dim,
    pair_head_inputs,
    pool_argument_features,
    validate_components,
)
from ekg.relations.data.maven_arg import ArgumentDocument, load_maven_arg


def build_eval_pairs(docs: Sequence[ArgumentDocument]) -> dict[str, list[CorefPair]]:
    """The *complete* labelled pair universe, for model selection only.

    Selection must not run on the same downsampled distribution training saw:
    a sampled negative set makes precision look better than it is on the real
    candidate population, so the chosen epoch would be chosen on the wrong axis.
    """
    per_doc: dict[str, list[CorefPair]] = {}
    for doc in docs:
        pairs = labelled_coref_pairs(doc.nodes, cluster_of_nodes(doc.nodes))
        if pairs:
            per_doc[doc.doc_id] = pairs
    return per_doc


def build_training_pairs(
    docs: Sequence[ArgumentDocument],
    *,
    neg_ratio: float,
    hard_fraction: float,
    seed: int,
    include_negative_only_docs: bool = False,
) -> dict[str, list[CorefPair]]:
    """Per-document sampled pairs, optionally retaining all-negative documents.

    Sampling per document (not corpus-wide) keeps every document's negatives
    proportional to its own positives, so a long document cannot dominate the
    negative budget.  ``include_negative_only_docs`` retains every candidate
    from documents whose gold clustering is all singleton; there are only 11,465
    such pairs in MAVEN-Arg train, and dropping them causes a measured train/test
    prior mismatch in exactly the false-merge direction.
    """
    per_doc: dict[str, list[CorefPair]] = {}
    has_positive = False
    for doc in docs:
        pairs = labelled_coref_pairs(doc.nodes, cluster_of_nodes(doc.nodes))
        if not any(p.label for p in pairs):
            if include_negative_only_docs and pairs:
                per_doc[doc.doc_id] = pairs
            continue
        has_positive = True
        per_doc[doc.doc_id] = sample_training_pairs(
            pairs, neg_ratio=neg_ratio, hard_fraction=hard_fraction, seed=seed
        )
    if not has_positive:
        raise ValueError("no coreferent pair in the training split -- refusing to train")
    return per_doc


def train(
    docs: Sequence[ArgumentDocument],
    per_doc: dict[str, list[CorefPair]],
    *,
    model_name: str,
    output: Path,
    epochs: int,
    lr: float,
    max_length: int,
    stride: int,
    seed: int,
    head_lr: float | None = None,
    warmup_steps: int = 0,
    accum_steps: int = 1,
    components: tuple[str, ...] = (),
    dev_docs: Sequence[ArgumentDocument] = (),
    dev_pairs: dict[str, list[CorefPair]] | None = None,
    save_every_epoch: bool = False,
) -> None:
    import torch
    from torch import nn
    from transformers import AutoModel, AutoTokenizer

    from ekg.nodes.encoding import encode_spans, encode_spans_with_context

    torch.manual_seed(seed)
    random.seed(seed)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    encoder = AutoModel.from_pretrained(model_name).to(device)
    encoder.gradient_checkpointing_enable()
    context_discriminative = CONTEXT_POOLING in components
    argument_oracle = ARGUMENT_POOLING_ORACLE in components
    head = nn.Linear(
        head_input_dim(encoder.config.hidden_size, components), 2
    ).to(device)

    # One lr for encoder and head, as in `train_supervised_relations.py`. A
    # separate high head lr (1e-3) was tried first and diverged: loss rose
    # 0.428 -> 0.646 within epoch 1 and plateaued above the constant-prior
    # optimum (~0.305 at 1:10), i.e. the 3072-dim head outran the encoder.
    # Mirrors `train_supervised_relations.py`, and for the same measured reason.
    # This trainer had a single constant rate and no schedule at all, and its
    # cost is visible in the C4-r2 curve: every arm peaks at epoch 2 and then
    # loses 4-8 MUC points over the next eight. PHASE_A recorded warmup + linear
    # decay as "the official ingredient we kept missing"; Ch2 recovered causal
    # +5.11 from the recipe alone. Ch1 never had a reproduction base at all.
    optimizer = torch.optim.AdamW(
        [
            {"params": list(encoder.parameters()), "lr": lr},
            {
                "params": list(head.parameters()),
                "lr": lr if head_lr is None else head_lr,
                "weight_decay": 0.0,
            },
        ],
        lr=lr,
    )
    scheduler = None
    if warmup_steps > 0:
        import math

        from transformers import get_linear_schedule_with_warmup

        # Optimiser steps, not documents: with accumulation the schedule advances
        # once per N docs. Counting documents stretches the decay past the end of
        # training, so the rate never actually anneals -- the exact bug that would
        # make this change look like a no-op.
        steps_per_epoch = math.ceil(len(per_doc) / accum_steps)
        scheduler = get_linear_schedule_with_warmup(
            optimizer, warmup_steps, epochs * steps_per_epoch
        )
    loss_fn = nn.CrossEntropyLoss()
    by_id = {doc.doc_id: doc for doc in docs}
    doc_ids = list(per_doc)
    best_f1 = -1.0
    best_epoch: int | None = None

    def _save(enc, tok, hd, out: Path) -> None:
        out.mkdir(parents=True, exist_ok=True)
        enc.save_pretrained(out)
        tok.save_pretrained(out)
        torch.save(hd.state_dict(), out / HEAD_FILE)
        # The scorer rebuilds the head from this, so the feature layout can never
        # silently diverge between training and inference.
        (out / CONFIG_FILE).write_text(
            json.dumps(
                {
                    "components": list(components),
                    "context_discriminative": context_discriminative,
                    "argument_source": (
                        "gold_event_level_oracle" if argument_oracle else "none"
                    ),
                    "lr": lr,
                    "head_lr": lr if head_lr is None else head_lr,
                    "warmup_steps": warmup_steps,
                    "accum_steps": accum_steps,
                    "feature_names": list(FEATURE_NAMES),
                    "hidden_size": enc.config.hidden_size,
                    "head_input_dim": head_input_dim(enc.config.hidden_size, components),
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )

    def _forward(doc, pairs):
        starts = [n.trigger_evidence[0].char_start for n in doc.nodes]
        argument_spans, argument_counts = argument_spans_and_counts(doc.nodes)
        arguments = None
        if context_discriminative:
            oracle_starts = [start for start, _ in argument_spans] if argument_oracle else []
            combined_starts = starts + oracle_starts
            combined_ranges = context_ranges_for(doc.nodes, doc.doc_text)
            if argument_oracle:
                combined_ranges += argument_spans
            encoded_spans, encoded_contexts = encode_spans_with_context(
                encoder, tokenizer, doc.doc_text, combined_starts,
                combined_ranges,
                max_length=max_length, stride=stride, device=device,
            )
            triggers = encoded_spans[: len(starts)]
            contexts = encoded_contexts[: len(starts)]
            if argument_oracle:
                arguments = pool_argument_features(
                    encoded_spans[len(starts) :], argument_counts
                )
        elif argument_oracle:
            combined = encode_spans(
                encoder,
                tokenizer,
                doc.doc_text,
                starts + [start for start, _ in argument_spans],
                max_length=max_length,
                stride=stride,
                device=device,
            )
            triggers = combined[: len(starts)]
            contexts = triggers
            arguments = pool_argument_features(combined[len(starts) :], argument_counts)
        else:
            triggers = encode_spans(
                encoder, tokenizer, doc.doc_text, starts,
                max_length=max_length, stride=stride, device=device,
            )
            contexts = triggers
        order = {node.event_id: i for i, node in enumerate(doc.nodes)}
        nodes_by_id = {node.event_id: node for node in doc.nodes}
        inputs = pair_head_inputs(
            triggers, contexts, [(p.head_id, p.tail_id) for p in pairs],
            nodes_by_id, order, components=components,
            arguments=arguments,
        )
        return head(inputs)

    for epoch in range(epochs):
        random.shuffle(doc_ids)
        encoder.train()
        head.train()
        total = 0.0
        seen = 0
        for step, doc_id in enumerate(doc_ids, 1):
            doc = by_id[doc_id]
            pairs = per_doc[doc_id]
            targets = torch.tensor([int(p.label) for p in pairs], device=device)
            logits = _forward(doc, pairs)
            loss = loss_fn(logits, targets)
            # Scale so the accumulated gradient matches a true batch of that size,
            # and step the scheduler with the optimiser -- stepping it per document
            # would race through the warmup N times too fast.
            (loss / accum_steps).backward()
            if step % accum_steps == 0 or step == len(doc_ids):
                optimizer.step()
                if scheduler is not None:
                    scheduler.step()
                optimizer.zero_grad()
            total += float(loss.detach())
            seen += 1
            if step % 200 == 0:
                print(f"epoch {epoch + 1} step {step}/{len(doc_ids)} loss {total / seen:.4f}")
        print(f"epoch {epoch + 1} mean loss {total / max(seen, 1):.4f}", flush=True)

        if not dev_pairs:
            continue
        encoder.eval()
        head.eval()
        tp = fp = fn = 0
        by_dev = {doc.doc_id: doc for doc in dev_docs}
        with torch.no_grad():
            for dev_id, pairs in dev_pairs.items():
                doc = by_dev[dev_id]
                gold = torch.tensor([int(p.label) for p in pairs], device=device)
                pred = _forward(doc, pairs).argmax(dim=-1)
                tp += int(((pred == 1) & (gold == 1)).sum())
                fp += int(((pred == 1) & (gold == 0)).sum())
                fn += int(((pred == 0) & (gold == 1)).sum())
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        print(
            f"[dev] epoch {epoch + 1} pair P {precision:.4f} R {recall:.4f} F1 {f1:.4f}"
            f" (tp={tp} fp={fp} fn={fn})",
            flush=True,
        )
        if save_every_epoch:
            # Pair-level F1 is *not* the axis this chapter reports, and on the
            # first C4 run the two disagreed in direction: pair-F1 ranked the
            # mechanism below the control while official MUC ranked it 2.09
            # above, and the four arms stopped at four different epochs
            # (10/5/7/3), so the epoch itself was an uncontrolled confound.
            # Keeping every epoch lets the official evaluator -- the scorer that
            # produces the reported number -- pick the epoch afterwards, and
            # lets the arms be compared at matched epochs.
            _save(encoder, tokenizer, head, output / "epochs" / f"epoch-{epoch + 1}")
            print(f"[dev] epoch {epoch + 1} checkpoint kept for official scoring", flush=True)
        if f1 > best_f1:
            best_f1, best_epoch = f1, epoch + 1
            _save(encoder, tokenizer, head, output)
            print(f"[dev] epoch {epoch + 1} is best so far, saved", flush=True)

    if dev_pairs:
        if best_epoch is None:
            raise SystemExit("no epoch produced a dev score; refusing to save a blind checkpoint")
        print(f"best dev pair-F1 {best_f1:.4f} at epoch {best_epoch}; checkpoint at {output}")
        return
    _save(encoder, tokenizer, head, output)
    print(f"saved coreference scorer to {output}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train", required=True, type=Path, help="MAVEN-Arg train jsonl")
    parser.add_argument("--model", default="roberta-base")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--lr", type=float, default=2e-5)
    parser.add_argument(
        "--head-lr", type=float, default=None,
        help="separate rate for the pair head (the official baseline uses 1e-4); "
             "default = same as --lr, which is what every run before 2026-08-30 used",
    )
    parser.add_argument(
        "--warmup-steps", type=int, default=0,
        help="linear warmup then linear decay (the official baseline uses 200); 0 = off, "
             "i.e. the constant rate whose decay the C4-r2 curve exposed",
    )
    parser.add_argument(
        "--accum-steps", type=int, default=1,
        help="documents per optimiser step; >1 makes --warmup-steps count that many "
             "fewer steps, as in the relation trainer",
    )
    parser.add_argument("--neg-ratio", type=float, default=10.0)
    parser.add_argument("--hard-fraction", type=float, default=0.5)
    parser.add_argument(
        "--include-negative-only-docs",
        action="store_true",
        help=(
            "retain every same-type negative pair from documents with no positive coreference "
            "pair; this restores all-singleton documents omitted by the historical sampler"
        ),
    )
    parser.add_argument("--max-length", type=int, default=512)
    parser.add_argument("--stride", type=int, default=128)
    parser.add_argument(
        "--train-manifest", type=Path, default=None,
        help="frozen P1 MAVEN-ERE train manifest; MAVEN-Arg shares MAVEN-ERE's document IDs",
    )
    parser.add_argument(
        "--dev-manifest", type=Path, default=None,
        help="frozen P1 internal-dev manifest, used for best-epoch selection",
    )
    parser.add_argument(
        "--components", nargs="*", default=[], choices=list(ALL_COMPONENTS),
        help="mechanism components to enable; empty = trigger-only control",
    )
    parser.add_argument(
        "--save-every-epoch", action="store_true",
        help=(
            "also keep every epoch under <output>/epochs/epoch-N, so the official evaluator can "
            "select the epoch and the arms can be compared at matched epochs"
        ),
    )
    parser.add_argument("--limit", type=int, default=None, help="first N documents (smoke)")
    parser.add_argument("--seed", type=int, default=13)
    args = parser.parse_args()

    docs = list(load_maven_arg(args.train))
    if args.limit:
        docs = docs[: args.limit]
    # MAVEN-Arg and MAVEN-ERE are the same documents with different annotation
    # layers (train 2,913 / valid 710, identical IDs). Training on the full Arg
    # train therefore includes every P1 internal-dev document, so selecting on
    # internal-dev without this split would select on trained-on data.
    if bool(args.train_manifest) != bool(args.dev_manifest):
        raise SystemExit("--train-manifest and --dev-manifest must be given together")
    dev_docs: list[ArgumentDocument] = []
    if args.train_manifest:
        docs, dev_docs = split_docs_by_manifests(docs, args.train_manifest, args.dev_manifest)
        print(f"protocol split: train {len(docs)} docs / internal-dev {len(dev_docs)} docs")
    else:
        print(
            "[train] WARNING: no manifests given; training on every document and "
            "saving the last epoch blind (historical/exploratory only)",
            flush=True,
        )
    per_doc = build_training_pairs(
        docs,
        neg_ratio=args.neg_ratio,
        hard_fraction=args.hard_fraction,
        seed=args.seed,
        include_negative_only_docs=args.include_negative_only_docs,
    )
    n_pairs = sum(len(p) for p in per_doc.values())
    n_pos = sum(1 for pairs in per_doc.values() for p in pairs if p.label)
    n_hard = sum(1 for pairs in per_doc.values() for p in pairs if p.hard)
    print(
        f"{len(per_doc)}/{len(docs)} documents carry a positive; "
        f"{n_pairs} training pairs ({n_pos} positive, {n_hard} hard negative)"
    )

    train(
        docs,
        per_doc,
        model_name=args.model,
        output=args.output,
        epochs=args.epochs,
        lr=args.lr,
        max_length=args.max_length,
        stride=args.stride,
        seed=args.seed,
        head_lr=args.head_lr,
        warmup_steps=args.warmup_steps,
        accum_steps=args.accum_steps,
        components=validate_components(args.components),
        dev_docs=dev_docs,
        dev_pairs=build_eval_pairs(dev_docs) if dev_docs else None,
        save_every_epoch=args.save_every_epoch,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
