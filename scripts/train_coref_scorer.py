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
"""

from __future__ import annotations

import argparse
import random
from collections.abc import Sequence
from pathlib import Path

from ekg.nodes.coref import (
    HEAD_FILE,
    CorefPair,
    cluster_of_nodes,
    labelled_coref_pairs,
    sample_training_pairs,
)
from ekg.relations.data.maven_arg import ArgumentDocument, load_maven_arg


def build_training_pairs(
    docs: Sequence[ArgumentDocument], *, neg_ratio: float, hard_fraction: float, seed: int
) -> dict[str, list[CorefPair]]:
    """Per-document sampled pairs; documents without a positive are dropped.

    Sampling per document (not corpus-wide) keeps every document's negatives
    proportional to its own positives, so a long document cannot dominate the
    negative budget.
    """
    per_doc: dict[str, list[CorefPair]] = {}
    for doc in docs:
        pairs = labelled_coref_pairs(doc.nodes, cluster_of_nodes(doc.nodes))
        if not any(p.label for p in pairs):
            continue
        per_doc[doc.doc_id] = sample_training_pairs(
            pairs, neg_ratio=neg_ratio, hard_fraction=hard_fraction, seed=seed
        )
    if not per_doc:
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
) -> None:
    import torch
    from torch import nn
    from transformers import AutoModel, AutoTokenizer

    from ekg.nodes.encoding import encode_spans, pair_features

    torch.manual_seed(seed)
    random.seed(seed)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    encoder = AutoModel.from_pretrained(model_name).to(device)
    encoder.gradient_checkpointing_enable()
    head = nn.Linear(encoder.config.hidden_size * 4, 2).to(device)

    # One lr for encoder and head, as in `train_supervised_relations.py`. A
    # separate high head lr (1e-3) was tried first and diverged: loss rose
    # 0.428 -> 0.646 within epoch 1 and plateaued above the constant-prior
    # optimum (~0.305 at 1:10), i.e. the 3072-dim head outran the encoder.
    optimizer = torch.optim.AdamW([*encoder.parameters(), *head.parameters()], lr=lr)
    loss_fn = nn.CrossEntropyLoss()
    by_id = {doc.doc_id: doc for doc in docs}
    doc_ids = list(per_doc)

    for epoch in range(epochs):
        random.shuffle(doc_ids)
        encoder.train()
        head.train()
        total = 0.0
        seen = 0
        for step, doc_id in enumerate(doc_ids, 1):
            doc = by_id[doc_id]
            pairs = per_doc[doc_id]
            order = {node.event_id: i for i, node in enumerate(doc.nodes)}
            embeddings = encode_spans(
                encoder,
                tokenizer,
                doc.doc_text,
                [n.trigger_evidence[0].char_start for n in doc.nodes],
                max_length=max_length,
                stride=stride,
                device=device,
            )
            head_idx = torch.tensor([order[p.head_id] for p in pairs], device=device)
            tail_idx = torch.tensor([order[p.tail_id] for p in pairs], device=device)
            targets = torch.tensor([int(p.label) for p in pairs], device=device)
            logits = head(pair_features(embeddings[head_idx], embeddings[tail_idx]))
            loss = loss_fn(logits, targets)
            loss.backward()
            optimizer.step()
            optimizer.zero_grad()
            total += float(loss.detach())
            seen += 1
            if step % 200 == 0:
                print(f"epoch {epoch + 1} step {step}/{len(doc_ids)} loss {total / seen:.4f}")
        print(f"epoch {epoch + 1} mean loss {total / max(seen, 1):.4f}", flush=True)

    output.mkdir(parents=True, exist_ok=True)
    encoder.save_pretrained(output)
    tokenizer.save_pretrained(output)
    torch.save(head.state_dict(), output / HEAD_FILE)
    print(f"saved coreference scorer to {output}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train", required=True, type=Path, help="MAVEN-Arg train jsonl")
    parser.add_argument("--model", default="roberta-base")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--lr", type=float, default=2e-5)
    parser.add_argument("--neg-ratio", type=float, default=10.0)
    parser.add_argument("--hard-fraction", type=float, default=0.5)
    parser.add_argument("--max-length", type=int, default=512)
    parser.add_argument("--stride", type=int, default=128)
    parser.add_argument("--limit", type=int, default=None, help="first N documents (smoke)")
    parser.add_argument("--seed", type=int, default=13)
    args = parser.parse_args()

    docs = list(load_maven_arg(args.train))
    if args.limit:
        docs = docs[: args.limit]
    per_doc = build_training_pairs(
        docs, neg_ratio=args.neg_ratio, hard_fraction=args.hard_fraction, seed=args.seed
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
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
