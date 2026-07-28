#!/usr/bin/env python
"""Train an event detector on MAVEN-Arg's candidate universe (server / CUDA).

Two detectors, one interface:

- ``lexicon`` — fits the most-frequent-type-per-trigger table. Pure CPU, seconds,
  and the memorization floor the neural detector must clear.
- ``supervised`` — RoBERTa encoder + a linear head over ``NONE + event types``,
  trained on every candidate (gold triggers *and* ``negative_triggers``) with
  plain cross-entropy. No negative downsampling and no class reweighting on
  purpose: Phase A showed that stacking both compensations teaches the model to
  fire on everything, and detection here is already the balanced-enough
  candidate-classification task, not the 63:1 pair universe.

The document is encoded once per step and every candidate is pooled out of it
(`nodes.encoding.encode_spans`), so cost scales with document length, not with
the ~136 candidates a document carries.

    uv run --extra llm python scripts/train_event_detector.py \
        --train data/processed/maven_arg/train.jsonl \
        --detector supervised --model roberta-base \
        --output runs/nodes/detector_supervised
"""

from __future__ import annotations

import argparse
import json
import random
from collections.abc import Sequence
from pathlib import Path

from ekg.nodes.detection import HEAD_FILE, LABELS_FILE, LexiconEventDetector
from ekg.relations.data.maven_arg import NONE_TYPE, ArgumentDocument, load_maven_arg


def detection_labels(docs: Sequence[ArgumentDocument]) -> list[str]:
    """Label vocabulary with NONE pinned at index 0 (the head's negative class)."""
    types = {c.event_type for doc in docs for c in doc.candidates if c.event_type != NONE_TYPE}
    if not types:
        raise ValueError("no event types in the training split -- refusing to train on NONE only")
    return [NONE_TYPE, *sorted(types)]


def train_supervised(
    docs: Sequence[ArgumentDocument],
    labels: Sequence[str],
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

    from ekg.nodes.encoding import encode_spans

    torch.manual_seed(seed)
    random.seed(seed)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    encoder = AutoModel.from_pretrained(model_name).to(device)
    encoder.gradient_checkpointing_enable()
    head = nn.Linear(encoder.config.hidden_size, len(labels)).to(device)

    label_index = {label: i for i, label in enumerate(labels)}
    # One lr for encoder and head, as in `train_supervised_relations.py`
    # (a separate 1e-3 head lr diverged on the coreference head).
    optimizer = torch.optim.AdamW([*encoder.parameters(), *head.parameters()], lr=lr)
    loss_fn = nn.CrossEntropyLoss()

    order = list(range(len(docs)))
    for epoch in range(epochs):
        random.shuffle(order)
        encoder.train()
        head.train()
        total = 0.0
        seen = 0
        for step, i in enumerate(order, 1):
            doc = docs[i]
            if not doc.candidates:
                continue
            targets = torch.tensor(
                [label_index[c.event_type] for c in doc.candidates], device=device
            )
            embeddings = encode_spans(
                encoder,
                tokenizer,
                doc.doc_text,
                [c.span.char_start for c in doc.candidates],
                max_length=max_length,
                stride=stride,
                device=device,
            )
            loss = loss_fn(head(embeddings), targets)
            loss.backward()
            optimizer.step()
            optimizer.zero_grad()
            total += float(loss.detach())
            seen += 1
            if step % 200 == 0:
                print(f"epoch {epoch + 1} step {step}/{len(order)} loss {total / seen:.4f}")
        print(f"epoch {epoch + 1} mean loss {total / max(seen, 1):.4f}", flush=True)

    output.mkdir(parents=True, exist_ok=True)
    encoder.save_pretrained(output)
    tokenizer.save_pretrained(output)
    torch.save(head.state_dict(), output / HEAD_FILE)
    (output / LABELS_FILE).write_text(json.dumps(list(labels)))
    print(f"saved detector to {output}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train", required=True, type=Path, help="MAVEN-Arg train jsonl")
    parser.add_argument("--detector", default="supervised", choices=("lexicon", "supervised"))
    parser.add_argument("--model", default="roberta-base", help="base encoder (supervised)")
    parser.add_argument("--output", required=True, type=Path, help="checkpoint dir (or json file)")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--lr", type=float, default=2e-5)
    parser.add_argument("--max-length", type=int, default=512)
    parser.add_argument("--stride", type=int, default=128)
    parser.add_argument("--limit", type=int, default=None, help="first N documents (smoke)")
    parser.add_argument("--seed", type=int, default=13)
    args = parser.parse_args()

    docs = list(load_maven_arg(args.train))
    if args.limit:
        docs = docs[: args.limit]
    print(f"loaded {len(docs)} documents, {sum(len(d.candidates) for d in docs)} candidates")

    if args.detector == "lexicon":
        LexiconEventDetector().fit(docs).save(args.output)
        print(f"saved lexicon detector to {args.output}")
        return 0

    labels = detection_labels(docs)
    print(f"{len(labels)} labels (index 0 = {labels[0]})")
    train_supervised(
        docs,
        labels,
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
