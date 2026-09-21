#!/usr/bin/env python
"""Train and score one D4 v6.2 arm on one fold.

The contract is `docs/phases/PHASE_D4_predicted_causal_residual.md`. Three arms
share this file so that `base` is literally the same code path with the residual
removed -- a separate base script is how a second variable creeps in.

The evaluation manifest never reaches this file: scoring lives in
`evaluate_d4_predicted_causal.py`, so the S1 audit property "evaluation does not
appear in the trainer argv" still holds for the new family.

Why documents are the batching unit here while the frozen CLS anchor batches a
globally shuffled mention stream: a mention's residual needs its in-neighbours'
representations, so the neighbours have to be in the same step. Documents are
therefore packed until the step reaches `--batch-size` mentions, which keeps the
anchor's effective batch size while making each document whole. That is the only
recipe difference from the anchor, and `base` pays it too, so the three arms stay
a single-variable contrast.
"""

from __future__ import annotations

import argparse
import json
import random
from collections.abc import Iterator, Sequence
from pathlib import Path

from ekg.core.protocol import load_manifest_ids
from ekg.core.stage_bundle import sha256_file
from ekg.factuality.baselines import CLS_POOLING, marked_sentence, pool_mentions
from ekg.factuality.causal_residual import (
    ARMS,
    CausalEdge,
    build_causal_residual,
    decide_edges,
    residual_inputs,
    rewire_edges,
    validate_arm,
)
from ekg.factuality.metrics import factuality_report
from ekg.relations.data.maven_fact import (
    FACTUALITY_LABELS,
    FactualityDocument,
    load_maven_fact,
)

CONFIG_FILE = "d4_predicted_causal_config.json"
HEAD_FILE = "label_head.pt"
RESIDUAL_FILE = "causal_residual.pt"
DEV_CURVE_FILE = "dev_curve.json"


def _class_weights(docs: Sequence[FactualityDocument], alpha: float) -> list[float]:
    """``(N / n_c) ** alpha`` normalised to mean 1 — the anchor's own formula."""
    counts = {label: 0 for label in FACTUALITY_LABELS}
    for doc in docs:
        for mention in doc.mentions:
            counts[mention.factuality] += 1
    total = sum(counts.values())
    raw = [
        (total / counts[label]) ** alpha if counts[label] else 0.0
        for label in FACTUALITY_LABELS
    ]
    present = [weight for weight in raw if weight]
    mean = sum(present) / len(present)
    return [weight / mean for weight in raw]


def _sidecar_documents(path: Path) -> Iterator[tuple[str, list[dict]]]:
    """Stream the exhaustive sidecar one document at a time, in file order."""
    seen: set[str] = set()
    current: str | None = None
    rows: list[dict] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            row = json.loads(line)
            doc_id = row["doc_id"]
            if doc_id != current:
                if current is not None:
                    yield current, rows
                if doc_id in seen:
                    raise ValueError(f"{path}:{line_number}: {doc_id} is not contiguous")
                seen.add(doc_id)
                current, rows = doc_id, []
            rows.append(row)
    if current is not None:
        yield current, rows


def load_edges(
    sidecar: Path,
    class_weights: dict[str, float],
    *,
    arm: str,
    fold: int,
    document_ids: Sequence[str],
) -> dict[str, list[CausalEdge]]:
    """Decide (and for `rewired`, permute) this split's edges, once."""
    validate_arm(arm)
    wanted = set(document_ids)
    edges: dict[str, list[CausalEdge]] = {}
    for doc_id, rows in _sidecar_documents(sidecar):
        if doc_id not in wanted:
            raise ValueError(f"{sidecar}: {doc_id} is outside the split manifest")
        decided = decide_edges(rows, class_weights)
        if arm == "rewired":
            decided = rewire_edges(decided, fold=fold, doc_id=doc_id)
        edges[doc_id] = decided
    missing = wanted - set(edges)
    if missing:
        raise ValueError(f"{sidecar}: {len(missing)} split documents have no posterior")
    return edges


def _forward(
    docs: Sequence[FactualityDocument],
    edges: dict[str, list[CausalEdge]],
    *,
    arm: str,
    encoder,
    tokenizer,
    residual,
    head,
    max_length: int,
    device: str,
):
    """Per-document features -> optional residual -> shared 5-way head."""
    import torch

    logits = []
    for doc in docs:
        marked = [marked_sentence(doc, mention) for mention in doc.mentions]
        features = pool_mentions(
            encoder,
            tokenizer,
            [text for text, _, _ in marked],
            [(start, end) for _, start, end in marked],
            pooling=CLS_POOLING,
            max_length=max_length,
            device=device,
        )
        if arm != "base":
            features = residual(
                features,
                residual_inputs(
                    edges[doc.doc_id], [mention.mention_id for mention in doc.mentions]
                ),
            )
        logits.append(head(features))
    return torch.cat(logits, dim=0)


def _packed_batches(
    docs: Sequence[FactualityDocument], budget: int
) -> list[list[FactualityDocument]]:
    """Whole documents packed to the batch whose size is closest to `budget`.

    The first rule here cut as soon as the batch reached `budget`. A MAVEN-FACT
    document carries 25.4 mentions on average, so "at least 32" almost always
    swallowed a second document: fold 1 ran at 48.8 mentions over 910 steps per
    epoch against the frozen anchor's 32 over 1,387 — a third of the optimiser
    steps gone at the same learning rate, which is the measured candidate cause
    of the base arm's -.042 gap to that anchor (`results/PHASE_R1.md` §25.19).
    Closing on whichever boundary is nearer the budget gives 1,248 steps at 35.6.
    """
    batches: list[list[FactualityDocument]] = []
    current: list[FactualityDocument] = []
    mentions = 0
    for doc in docs:
        size = len(doc.mentions)
        if current and abs(mentions - budget) <= abs(mentions + size - budget):
            batches.append(current)
            current, mentions = [], 0
        current.append(doc)
        mentions += size
    if current:
        batches.append(current)
    return batches


def _score(
    docs: Sequence[FactualityDocument],
    edges: dict[str, list[CausalEdge]],
    *,
    arm: str,
    encoder,
    tokenizer,
    residual,
    head,
    max_length: int,
    device: str,
) -> tuple[dict, dict[str, str]]:
    import torch

    encoder.eval()
    head.eval()
    if residual is not None:
        residual.eval()
    predicted: dict[str, str] = {}
    gold: dict[str, str] = {}
    with torch.no_grad():
        for doc in docs:
            logits = _forward(
                [doc],
                edges,
                arm=arm,
                encoder=encoder,
                tokenizer=tokenizer,
                residual=residual,
                head=head,
                max_length=max_length,
                device=device,
            )
            for mention, index in zip(doc.mentions, logits.argmax(dim=-1).tolist(), strict=True):
                predicted[mention.mention_id] = FACTUALITY_LABELS[index]
                gold[mention.mention_id] = mention.factuality
    return factuality_report(predicted, gold), predicted


def train_arm(args: argparse.Namespace) -> dict:
    import torch
    from torch import nn
    from transformers import AutoModel, AutoTokenizer

    arm = validate_arm(args.arm)
    torch.manual_seed(args.seed)
    random.seed(args.seed)
    device = "cuda" if torch.cuda.is_available() else "cpu"

    docs = {doc.doc_id: doc for doc in load_maven_fact(args.train)}
    train_ids = load_manifest_ids(args.train_manifest)
    dev_ids = load_manifest_ids(args.dev_manifest)
    missing = [doc_id for doc_id in (*train_ids, *dev_ids) if doc_id not in docs]
    if missing:
        raise ValueError(f"{len(missing)} manifest documents are absent from {args.train}")
    train_docs = [docs[doc_id] for doc_id in train_ids]
    dev_docs = [docs[doc_id] for doc_id in dev_ids]

    calibration = json.loads(args.calibration_metadata.read_text(encoding="utf-8"))
    if calibration.get("fold") != args.fold:
        raise ValueError("calibration metadata belongs to another fold")
    class_weights = calibration["class_weights"]
    train_edges = load_edges(
        args.train_sidecar, class_weights, arm=arm, fold=args.fold, document_ids=train_ids
    )
    dev_edges = load_edges(
        args.dev_sidecar, class_weights, arm=arm, fold=args.fold, document_ids=dev_ids
    )

    tokenizer = AutoTokenizer.from_pretrained(str(args.model))
    encoder = AutoModel.from_pretrained(str(args.model)).to(device)
    encoder.gradient_checkpointing_enable()
    hidden = encoder.config.hidden_size
    head = nn.Linear(hidden, len(FACTUALITY_LABELS)).to(device)
    residual = None if arm == "base" else build_causal_residual(hidden).to(device)
    parameters = [*encoder.parameters(), *head.parameters()]
    if residual is not None:
        parameters += list(residual.parameters())
    optimizer = torch.optim.AdamW(parameters, lr=args.lr)
    weights = _class_weights(train_docs, args.alpha)
    loss_fn = nn.CrossEntropyLoss(
        weight=torch.tensor(weights, dtype=torch.float, device=device)
    )
    label_index = {label: index for index, label in enumerate(FACTUALITY_LABELS)}
    print(f"arm={arm} fold={args.fold} device={device} class weights {weights}", flush=True)

    stream = random.Random(args.seed)
    order = list(train_docs)
    curve: list[dict] = []
    best = {"macro_f1": -1.0, "epoch": 0}
    best_state: dict = {}
    for epoch in range(1, args.epochs + 1):
        stream.shuffle(order)
        encoder.train()
        head.train()
        if residual is not None:
            residual.train()
        total, steps = 0.0, 0
        for batch in _packed_batches(order, args.batch_size):
            logits = _forward(
                batch,
                train_edges,
                arm=arm,
                encoder=encoder,
                tokenizer=tokenizer,
                residual=residual,
                head=head,
                max_length=args.max_length,
                device=device,
            )
            targets = torch.tensor(
                [label_index[m.factuality] for doc in batch for m in doc.mentions],
                device=device,
            )
            loss = loss_fn(logits, targets)
            loss.backward()
            optimizer.step()
            optimizer.zero_grad()
            total += float(loss.detach())
            steps += 1
        print(f"epoch {epoch} mean loss {total / max(steps, 1):.4f}", flush=True)

        report, _ = _score(
            dev_docs,
            dev_edges,
            arm=arm,
            encoder=encoder,
            tokenizer=tokenizer,
            residual=residual,
            head=head,
            max_length=args.max_length,
            device=device,
        )
        per_class = {name: round(row["f1"], 4) for name, row in report["per_class"].items()}
        print(
            f"epoch {epoch} dev macro-F1 {report['macro_f1']:.4f} per-class {per_class}",
            flush=True,
        )
        curve.append(
            {
                "epoch": epoch,
                "macro_f1": report["macro_f1"],
                "accuracy": report["accuracy"],
                "per_class_f1": {n: r["f1"] for n, r in report["per_class"].items()},
            }
        )
        if report["macro_f1"] > best["macro_f1"]:
            best = {"macro_f1": report["macro_f1"], "epoch": epoch}
            best_state = {
                "encoder": {k: v.detach().cpu().clone() for k, v in encoder.state_dict().items()},
                "head": {k: v.detach().cpu().clone() for k, v in head.state_dict().items()},
                "residual": (
                    None
                    if residual is None
                    else {k: v.detach().cpu().clone() for k, v in residual.state_dict().items()}
                ),
            }

    if not best_state:
        raise ValueError("no epoch produced a dev score; refusing to publish a checkpoint")
    encoder.load_state_dict(best_state["encoder"])
    head.load_state_dict(best_state["head"])
    if residual is not None:
        residual.load_state_dict(best_state["residual"])
    print(f"selected epoch {best['epoch']} (dev macro-F1 {best['macro_f1']:.4f})", flush=True)

    args.output.mkdir(parents=True, exist_ok=True)
    encoder.save_pretrained(args.output)
    tokenizer.save_pretrained(args.output)
    torch.save(head.state_dict(), args.output / HEAD_FILE)
    if residual is not None:
        torch.save(residual.state_dict(), args.output / RESIDUAL_FILE)
    (args.output / DEV_CURVE_FILE).write_text(
        json.dumps({"selected_epoch": best["epoch"], "curve": curve}, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )

    summary = {
        "schema_version": "ekg.d4_predicted_causal_run.v1",
        "arm": arm,
        "fold": args.fold,
        "seed": args.seed,
        "pooling": CLS_POOLING,
        "labels": list(FACTUALITY_LABELS),
        "selected_epoch": best["epoch"],
        "dev_macro_f1": best["macro_f1"],
        "recipe": {
            "epochs": args.epochs,
            "lr": args.lr,
            "alpha": args.alpha,
            "mention_batch_budget": args.batch_size,
            "max_length": args.max_length,
            "batching": "documents packed to the mention budget",
        },
        "class_weights": class_weights,
        "inputs": {
            "train_sidecar": {
                "path": str(args.train_sidecar),
                "sha256": sha256_file(args.train_sidecar),
            },
            "dev_sidecar": {
                "path": str(args.dev_sidecar),
                "sha256": sha256_file(args.dev_sidecar),
            },
            "calibration_metadata": {
                "path": str(args.calibration_metadata),
                "sha256": sha256_file(args.calibration_metadata),
            },
        },
        "edges": {
            "train": sum(len(value) for value in train_edges.values()),
            "dev": sum(len(value) for value in dev_edges.values()),
        },
        "gold_edges_used": False,
        "gold_factuality_used_for_structure": False,
    }

    (args.output / CONFIG_FILE).write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arm", required=True, choices=ARMS)
    parser.add_argument("--fold", required=True, type=int)
    parser.add_argument("--train", required=True, type=Path, help="MAVEN-FACT jsonl")
    parser.add_argument("--train-manifest", required=True, type=Path)
    parser.add_argument("--dev-manifest", required=True, type=Path)
    parser.add_argument("--train-sidecar", required=True, type=Path)
    parser.add_argument("--dev-sidecar", required=True, type=Path)
    parser.add_argument("--calibration-metadata", required=True, type=Path)
    parser.add_argument("--model", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--epochs", type=int, default=12)
    parser.add_argument("--lr", type=float, default=2e-5)
    parser.add_argument("--alpha", type=float, default=0.5)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--max-length", type=int, default=128)
    parser.add_argument("--seed", type=int, default=13)
    args = parser.parse_args()
    summary = train_arm(args)
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
