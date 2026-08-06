#!/usr/bin/env python
"""Train the discriminative supervised relation extractor on MAVEN-ERE (server / CUDA).

Builds pair-classification rows from gold mentions (`relations.pairs.pair_examples`),
downsamples the dominant NONE class, and trains a RoBERTa encoder + per-family linear
heads with class-weighted cross-entropy. Saves encoder, tokenizer and heads to
`--output`, which `configs/relations/supervised.yaml` then loads.

This is the *discriminative* trainer — not `train_relation_extractor.py`, which is
the retained generative LoRA baseline.

Data preparation (`build_training_rows` / `downsample_negatives` / `class_weights`) is
pure Python and unit-tested on CPU; training needs the `llm` extra + a GPU:

    uv run --extra llm python scripts/train_supervised_relations.py \
        --train data/processed/maven_ere/train.jsonl \
        --model roberta-base \
        --output runs/relations/supervised_maven

`train_smoke.jsonl` / `valid_smoke.jsonl` are the small subsets for a quick check.
"""

from __future__ import annotations

import argparse
import math
import random
from pathlib import Path

from ekg.relations.data.maven_ere import load_maven_ere
from ekg.relations.extractor.supervised import FAMILY_SUBTYPES
from ekg.relations.pairs import PairExample, pair_examples


def build_training_rows(docs, max_distance: int | None = None) -> list[PairExample]:
    """Every document's labelled candidate universe, flattened.

    `pair_examples` already carries exactly what a pair classifier trains on
    (endpoint ids + one gold subtype per family, empty labels = negative), and it is
    the same universe evaluation scores against — so the rows *are* its output.
    """
    rows: list[PairExample] = []
    for doc in docs:
        rows.extend(pair_examples(doc, max_distance))
    return rows


def downsample_negatives(
    rows: list[PairExample], ratio: float, seed: int = 13
) -> list[PairExample]:
    """Keep every positive pair, subsample negatives to `ratio` per positive.

    Deterministic for a given seed. Raises when there is no positive at all:
    training on NONE only silently learns the majority class — exactly the failure
    behind the 0.4% causal recall — so this fails loudly instead of hiding it.

    ``ratio=inf`` keeps every negative, i.e. turns downsampling off. That is what
    the official MAVEN-ERE baseline does: its `Document.get_labels` enumerates all
    ``n^2 - n`` ordered mention pairs and labels the rest NONE, with no sampling
    anywhere (`THU-KEG/MAVEN-ERE/causal/src/data.py`). Ours defaulted to 30:1 and
    *also* applied inverse-frequency class weights — two corrections pushing the
    same way, which is the leading suspect for our collapsed precision.
    """
    if math.isinf(ratio):
        if not any(r.labels for r in rows):
            raise ValueError("no positive pair in the training rows")
        return list(rows)
    positives = [r for r in rows if r.labels]
    negatives = [r for r in rows if not r.labels]
    if not positives:
        raise ValueError("no positive pairs in training rows -- refusing to train on NONE only")
    keep = min(len(negatives), int(len(positives) * ratio))
    return positives + random.Random(seed).sample(negatives, keep)


def class_weights(
    rows: list[PairExample], alpha: float | dict[str, float] = 1.0
) -> dict[str, list[float]]:
    """Inverse-frequency weight per label per family, tempered by `alpha`.

    The weight is `(total / (k * count)) ** alpha`: alpha=1 is plain inverse
    frequency, alpha=0 is uniform (off), alpha=0.5 the usual middle ground. `alpha`
    may be a single value (all families) or a per-family dict.

    Tempering matters because the families differ in sparsity by ~39:3.4:1
    (temporal:causal:subevent gold), so a *per-family* alpha is the right control:
    the dense families (temporal) want a low alpha or they over-predict, the sparse
    ones (causal) want a higher alpha or their recall/F1 stays capped. A single
    global setting has to compromise across that whole range.
    """
    weights: dict[str, list[float]] = {}
    for family, subtypes in FAMILY_SUBTYPES.items():
        a = alpha[family] if isinstance(alpha, dict) else alpha
        index = {s: i for i, s in enumerate(subtypes)}
        counts = [0] * len(subtypes)
        for row in rows:
            # No gold label for this family = the negative class. An *unknown*
            # subtype must not be silently folded into NONE — that is how positives
            # go missing — so the lookup raises instead.
            counts[index[row.labels.get(family, "NONE")]] += 1
        total = sum(counts)
        weights[family] = [
            (total / (len(subtypes) * c)) ** a if c else 0.0 for c in counts
        ]
    return weights


def parse_weight_alpha(spec: str) -> float | dict[str, float]:
    """Parse `--weight-alpha`: a bare float, or `causal=0.7,temporal=0.25,...`.

    A per-family spec must name every family so no default is silently applied to
    an unlisted one (an unnamed family would otherwise train with a surprise alpha).
    """
    if "=" not in spec:
        return float(spec)
    per = dict(item.split("=", 1) for item in spec.split(","))
    parsed = {fam: float(per[fam]) for fam in FAMILY_SUBTYPES if fam in per}
    missing = set(FAMILY_SUBTYPES) - parsed.keys()
    extra = set(per) - set(FAMILY_SUBTYPES)
    if missing or extra:
        raise ValueError(
            f"per-family --weight-alpha must name exactly {sorted(FAMILY_SUBTYPES)}; "
            f"missing={sorted(missing)} unknown={sorted(extra)}"
        )
    return parsed


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--train", required=True, type=Path, help="MAVEN-ERE train jsonl")
    parser.add_argument("--model", required=True, type=str, help="base RoBERTa (name or path)")
    parser.add_argument("--output", required=True, type=Path, help="checkpoint directory")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--lr", type=float, default=2e-5)
    parser.add_argument(
        "--neg-ratio", type=float, default=3.0,
        help="negatives per positive; `inf` keeps every negative, which is what the "
             "official MAVEN-ERE baseline does (no sampling at all)",
    )
    parser.add_argument(
        "--weight-alpha",
        type=str,
        default="1.0",
        help="class-imbalance dial (PHASE_A ablation): CE weight = inverse_freq ** alpha. "
        "A bare float applies to all families (1.0 = plain inverse, 0.0 = off, 0.5 = middle), "
        "or per-family e.g. 'causal=0.7,temporal=0.25,subevent=0.5'.",
    )
    parser.add_argument("--max-distance", type=int, default=None, help="None = document-level")
    parser.add_argument(
        "--max-length", type=int, default=512, help="512 covers the longest sentence (322 tokens)"
    )
    parser.add_argument(
        "--head-lr", type=float, default=None,
        help="separate learning rate for the pair heads; the official baseline runs the "
             "encoder at 1e-5 and the scorer at 1e-4. Default None keeps one rate for "
             "everything. ⚠️ Phase C diverged at head lr 1e-3 -- that is 10x the official "
             "value, not evidence against 1e-4",
    )
    parser.add_argument(
        "--warmup-steps", type=int, default=0,
        help="linear warmup on the encoder rate (the official baseline uses 200); 0 = off",
    )
    parser.add_argument(
        "--dev-metric", choices=("micro", "macro"), default="micro",
        help="how --dev-docs scores an epoch. micro pools all families and is "
             "dominated by temporal (~39x subevent's pair count); macro weights the "
             "three families equally. Default stays micro so existing runs reproduce",
    )
    parser.add_argument(
        "--accum-steps", type=int, default=1,
        help="accumulate gradients over N documents before stepping. The official "
             "baseline batches 8 documents; ours updates per document (= batch 1), "
             "which both adds gradient noise and makes --warmup-steps mean 8x fewer "
             "documents than the official 200",
    )
    parser.add_argument("--seed", type=int, default=13)
    parser.add_argument(
        "--dev-docs", type=int, default=0,
        help="hold out this many TRAIN docs as dev and keep the best-scoring epoch "
             "(the official baseline selects on dev; 0 = off, keep the last epoch). "
             "Never carved from valid -- selecting and reporting on the same split "
             "would bias the reported number",
    )
    args = parser.parse_args()

    # torch-only imports stay inside main so the data helpers above import on CPU.
    import torch
    import torch.nn.functional as F
    from transformers import AutoModel, AutoTokenizer

    from ekg.relations.extractor.supervised import (
        PairClassifier,
        _pair_features,
        distance_bucket,
        encode_trigger_reps,
    )

    docs = list(load_maven_ere(args.train))
    rows = downsample_negatives(
        build_training_rows(docs, args.max_distance), args.neg_ratio, args.seed
    )
    alpha = parse_weight_alpha(args.weight_alpha)
    weights = None if alpha == 0.0 else class_weights(rows, alpha)
    docs_by_id = {d.doc_id: d for d in docs}
    rows_by_doc: dict[str, list[PairExample]] = {}
    for row in rows:
        rows_by_doc.setdefault(row.doc_id, []).append(row)
    kept = "all (no downsampling)" if math.isinf(args.neg_ratio) else f"{args.neg_ratio}:1"
    print(
        f"[train] {len(docs)} docs, {len(rows)} rows (negatives {kept}), "
        f"weight_alpha={args.weight_alpha}, lr={args.lr}, head_lr={args.head_lr}, "
        f"warmup={args.warmup_steps}, accum={args.accum_steps}, "
        f"max_length={args.max_length}",
        flush=True,
    )

    device = "cuda" if torch.cuda.is_available() else "cpu"
    torch.manual_seed(args.seed)
    tokenizer = AutoTokenizer.from_pretrained(args.model)
    encoder = AutoModel.from_pretrained(args.model).to(device)
    counts = {fam: len(subs) for fam, subs in FAMILY_SUBTYPES.items()}
    heads = PairClassifier(encoder.config.hidden_size, counts).to(device)
    weight_tensors = (
        {f: torch.tensor(w, device=device) for f, w in weights.items()} if weights else {}
    )
    label_index = {f: {s: i for i, s in enumerate(subs)} for f, subs in FAMILY_SUBTYPES.items()}
    # Two param groups rather than one rate: the official baseline trains the encoder
    # at 1e-5 and the scorer head at 1e-4, and gives the head plain Adam (no decoupled
    # weight decay), which `weight_decay=0.0` reproduces inside AdamW.
    optimiser = torch.optim.AdamW(
        [
            {"params": list(encoder.parameters()), "lr": args.lr},
            {
                "params": list(heads.parameters()),
                "lr": args.head_lr if args.head_lr is not None else args.lr,
                "weight_decay": 0.0,
            },
        ],
        lr=args.lr,
    )
    # Held-out dev carved out of TRAIN, never from valid: selecting the checkpoint on
    # valid and then reporting valid would bias the reported number. The official
    # baseline selects on dev and reports test; we have no test, so the split has to
    # come out of train instead.
    all_ids = list(rows_by_doc)
    random.Random(args.seed).shuffle(all_ids)
    dev_ids = all_ids[: args.dev_docs] if args.dev_docs else []
    train_ids = all_ids[args.dev_docs :] if args.dev_docs else all_ids

    scheduler = None
    if args.warmup_steps > 0:
        from transformers import get_linear_schedule_with_warmup

        # Count optimiser steps, not documents: with --accum-steps N the schedule
        # advances once per N docs, and dev docs never enter the training loop.
        # Getting this wrong stretches the decay past the end of training, so the
        # rate never actually anneals.
        steps_per_epoch = math.ceil(len(train_ids) / args.accum_steps)
        scheduler = get_linear_schedule_with_warmup(
            optimiser, args.warmup_steps, args.epochs * steps_per_epoch
        )
    if args.dev_docs:
        print(
            f"[train] holdout dev: {len(dev_ids)} docs (from train), "
            f"training on {len(train_ids)}",
            flush=True,
        )

    def save_checkpoint() -> None:
        args.output.mkdir(parents=True, exist_ok=True)
        encoder.save_pretrained(args.output)
        tokenizer.save_pretrained(args.output)
        torch.save(heads.state_dict(), args.output / "heads.pt")

    def dev_f1() -> tuple[float, dict[str, float]]:
        """Pair-level F1 over non-NONE classes; `--dev-metric` picks micro or macro.

        Micro pools every family, so it is dominated by whichever family has the most
        candidate pairs -- temporal outnumbers subevent ~39:1 on valid. A run selected
        on micro happily trades subevent away for temporal (measured: temporal +3.84
        while subevent fell 22.26 -> 19.65). Macro weights the three families equally.
        """
        encoder.eval()
        heads.eval()
        per_family = {fam: [0, 0, 0] for fam in FAMILY_SUBTYPES}  # tp, fp, fn
        with torch.no_grad():
            for doc_id in dev_ids:
                doc = docs_by_id[doc_id]
                doc_rows = rows_by_doc[doc_id]
                embs = encode_trigger_reps(
                    encoder, tokenizer, doc.nodes, doc.doc_text, args.max_length, device
                )
                logits = heads(
                    _pair_features(
                        torch.stack([embs[r.head_id] for r in doc_rows]),
                        torch.stack([embs[r.tail_id] for r in doc_rows]),
                    ),
                    torch.tensor([distance_bucket(r.distance) for r in doc_rows], device=device),
                )
                for family in FAMILY_SUBTYPES:
                    gold = torch.tensor(
                        [label_index[family][r.labels.get(family, "NONE")] for r in doc_rows],
                        device=device,
                    )
                    pred = logits[family].argmax(dim=-1)
                    hit = pred == gold
                    per_family[family][0] += int(((gold > 0) & hit).sum())
                    per_family[family][1] += int(((pred > 0) & ~hit).sum())
                    per_family[family][2] += int(((gold > 0) & ~hit).sum())
        encoder.train()
        heads.train()

        def f1_of(tp: int, fp: int, fn: int) -> float:
            if tp == 0:
                return 0.0
            p, r = tp / (tp + fp), tp / (tp + fn)
            return 2 * p * r / (p + r)

        by_family = {fam: f1_of(*counts) for fam, counts in per_family.items()}
        if args.dev_metric == "macro":
            return sum(by_family.values()) / len(by_family), by_family
        pooled = [sum(c[i] for c in per_family.values()) for i in range(3)]
        return f1_of(*pooled), by_family

    best_f1 = -1.0
    encoder.train()
    heads.train()
    for epoch in range(args.epochs):
        doc_ids = list(train_ids)
        random.Random(args.seed + epoch).shuffle(doc_ids)
        running = 0.0
        for seen, doc_id in enumerate(doc_ids, start=1):
            doc = docs_by_id[doc_id]
            embs = encode_trigger_reps(
                encoder, tokenizer, doc.nodes, doc.doc_text, args.max_length, device
            )
            doc_rows = rows_by_doc[doc_id]
            # One batched pair feature per document: per-pair construction launches
            # a kernel per candidate (thousands in a single document).
            head_emb = torch.stack([embs[r.head_id] for r in doc_rows])
            tail_emb = torch.stack([embs[r.tail_id] for r in doc_rows])
            dist_ids = torch.tensor(
                [distance_bucket(r.distance) for r in doc_rows], device=device
            )
            logits = heads(_pair_features(head_emb, tail_emb), dist_ids)
            loss = torch.zeros((), device=device)
            for family in FAMILY_SUBTYPES:
                target = torch.tensor(
                    [label_index[family][r.labels.get(family, "NONE")] for r in doc_rows],
                    device=device,
                )
                loss = loss + F.cross_entropy(
                    logits[family], target, weight=weight_tensors.get(family)
                )
            running += float(loss)
            # Scale so the accumulated gradient matches a true batch of that size,
            # and step the scheduler with the optimiser -- stepping it per document
            # would race through the warmup N times too fast.
            (loss / args.accum_steps).backward()
            if seen % args.accum_steps == 0 or seen == len(doc_ids):
                optimiser.step()
                if scheduler is not None:
                    scheduler.step()
                optimiser.zero_grad()
            if seen % 500 == 0:  # long run: report progress inside the epoch too
                print(
                    f"[train] epoch {epoch} {seen}/{len(doc_ids)} docs "
                    f"running_loss={running / seen:.4f}",
                    flush=True,
                )
        print(f"[train] epoch {epoch} mean_loss={running / max(1, len(doc_ids)):.4f}", flush=True)
        if dev_ids:
            f1, by_family = dev_f1()
            better = f1 > best_f1
            detail = " ".join(f"{fam[:4]}={v:.3f}" for fam, v in by_family.items())
            print(
                f"[dev] epoch {epoch} {args.dev_metric}_f1={f1:.4f} ({detail})"
                + (f"  <- best (was {best_f1:.4f}), saving" if better else "  (keeping best)"),
                flush=True,
            )
            if better:
                best_f1 = f1
                save_checkpoint()

    if not dev_ids:  # no selection signal: last epoch is all we have
        save_checkpoint()
        print(f"[train] saved last-epoch encoder + heads to {args.output}")
    else:
        print(f"[train] best dev {args.dev_metric}_f1={best_f1:.4f}; checkpoint at {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
