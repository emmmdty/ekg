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
    parser.add_argument("--seed", type=int, default=13)
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
        f"warmup={args.warmup_steps}, max_length={args.max_length}",
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
    scheduler = None
    if args.warmup_steps > 0:
        from transformers import get_linear_schedule_with_warmup

        total = args.epochs * len(rows_by_doc)
        scheduler = get_linear_schedule_with_warmup(optimiser, args.warmup_steps, total)

    encoder.train()
    heads.train()
    for epoch in range(args.epochs):
        doc_ids = list(rows_by_doc)
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
            optimiser.zero_grad()
            loss.backward()
            optimiser.step()
            if scheduler is not None:
                scheduler.step()
            running += float(loss)
            if seen % 500 == 0:  # long run: report progress inside the epoch too
                print(
                    f"[train] epoch {epoch} {seen}/{len(doc_ids)} docs "
                    f"running_loss={running / seen:.4f}",
                    flush=True,
                )
        print(f"[train] epoch {epoch} mean_loss={running / max(1, len(doc_ids)):.4f}", flush=True)

    args.output.mkdir(parents=True, exist_ok=True)
    encoder.save_pretrained(args.output)
    tokenizer.save_pretrained(args.output)
    torch.save(heads.state_dict(), args.output / "heads.pt")
    print(f"[train] saved encoder + heads to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
