#!/usr/bin/env python
"""Train an event factuality detector on MAVEN-FACT (server / CUDA).

Two detectors, one interface:

- ``lexicon`` — most-frequent-label-per-trigger table. Pure CPU, seconds, and
  the memorization floor the neural detector must clear.
- ``supervised`` — encoder span representation ⊕ graph structure features -> a
  5-way head, trained with inverse-frequency-weighted cross-entropy.

The class balance is the whole problem: CT+ is 94.4% of train, so unweighted
cross-entropy converges to the trivial all-CT+ classifier (.9487 accuracy,
.1947 macro-F1). The weighting exponent ``--alpha`` interpolates between none
(0.0) and full inverse frequency (1.0); Phase A measured that curve to be an
inverted U with its optimum at **0.25–0.5**, and full inverse frequency teaches
"fire on everything". Negative downsampling is deliberately *not* stacked on top
— Phase A showed both compensations together destroy precision.

Model selection happens on a document-level split of **train only** (the phase
contract reserves valid for the final report), reported every epoch as macro-F1
so an inverted-U alpha or an under-fit epoch count is visible rather than
inferred.

    .venv/bin/python -u scripts/train_factuality_detector.py \
        --train data/processed/maven_fact/train.jsonl \
        --detector supervised --model /data/TJK/models/roberta-base \
        --output runs/factuality/supervised_maven --epochs 6 --alpha 0.5
"""

from __future__ import annotations

import argparse
import json
import random
from collections.abc import Sequence
from pathlib import Path

from ekg.core.eval.relation import PRF
from ekg.factuality.detection import (
    EVIDENCE_HEAD_FILE,
    HEAD_FILE,
    LABELS_FILE,
    STRUCTURE_FEATURE_NAMES,
    LexiconFactualityDetector,
    structure_contexts,
)
from ekg.factuality.evidence import (
    SAME_SENTENCE_RECALL_CEILING,
    evidence_candidates,
    evidence_targets,
    gold_evidence_spans,
)
from ekg.factuality.metrics import (
    evidence_span_prf,
    factuality_report,
    majority_baseline_report,
)
from ekg.relations.data.maven_fact import (
    FACTUALITY_LABELS,
    FactualityDocument,
    factuality_distribution,
    load_maven_fact,
)

# Positive-token weight for the evidence BCE. Roughly 6% of a trigger
# sentence's tokens are evidence among annotated mentions (5,973 words over
# 3,706 mentions of ~25 tokens), so ~15 balances the two sides.
EVIDENCE_POS_WEIGHT = 15.0

# Per-epoch dev curve written next to the checkpoint, with the epoch selected.
DEV_CURVE_FILE = "dev_curve.json"


def class_weights(docs: Sequence[FactualityDocument], alpha: float) -> list[float]:
    """``(N / n_c) ** alpha`` per class, normalized to mean 1.

    A class absent from the training split gets weight 0: up-weighting a class
    with no examples would only add noise to the loss scale.
    """
    counts = factuality_distribution(docs)
    total = sum(counts.values())
    raw = [
        (total / counts[label]) ** alpha if counts[label] else 0.0 for label in FACTUALITY_LABELS
    ]
    present = [w for w in raw if w]
    mean = sum(present) / len(present)
    return [w / mean for w in raw]


def evaluate(detector, docs: Sequence[FactualityDocument]) -> tuple[dict, PRF]:
    """Label report and evidence span PRF over `docs` (the dev half of train)."""
    predicted: dict[str, str] = {}
    gold: dict[str, str] = {}
    predicted_evidence: dict[str, set[tuple[int, int]]] = {}
    for doc in docs:
        for mention_id, prediction in detector.predict(doc).items():
            predicted[mention_id] = prediction.factuality
            predicted_evidence[mention_id] = {
                (s.char_start, s.char_end) for s in prediction.evidence
            }
        gold.update({m.mention_id: m.factuality for m in doc.mentions})
    return (
        factuality_report(predicted, gold),
        evidence_span_prf(predicted_evidence, gold_evidence_spans(docs)),
    )


def train_supervised(
    train_docs: Sequence[FactualityDocument],
    dev_docs: Sequence[FactualityDocument],
    *,
    model_name: str,
    output: Path,
    epochs: int,
    lr: float,
    alpha: float,
    max_length: int,
    stride: int,
    use_structure: bool,
    evidence_weight: float,
    seed: int,
) -> None:
    import torch
    from torch import nn
    from transformers import AutoModel, AutoTokenizer

    from ekg.factuality.detection import SupervisedFactualityDetector
    from ekg.nodes.encoding import encode_spans, pair_features

    torch.manual_seed(seed)
    random.seed(seed)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    encoder = AutoModel.from_pretrained(model_name).to(device)
    encoder.gradient_checkpointing_enable()
    hidden = encoder.config.hidden_size
    width = hidden + (len(STRUCTURE_FEATURE_NAMES) if use_structure else 0)
    head = nn.Linear(width, len(FACTUALITY_LABELS)).to(device)
    evidence_head = nn.Linear(4 * hidden, 1).to(device) if evidence_weight else None

    label_index = {label: i for i, label in enumerate(FACTUALITY_LABELS)}
    weights = class_weights(train_docs, alpha)
    print(f"class weights (alpha={alpha}): {dict(zip(FACTUALITY_LABELS, weights, strict=True))}")
    # One lr for encoder and heads, as in `train_supervised_relations.py`: a
    # separate 1e-3 head lr diverged on the Phase C coreference head.
    parameters = [*encoder.parameters(), *head.parameters()]
    if evidence_head is not None:
        parameters += list(evidence_head.parameters())
    optimizer = torch.optim.AdamW(parameters, lr=lr)
    loss_fn = nn.CrossEntropyLoss(weight=torch.tensor(weights, dtype=torch.float, device=device))
    # Evidence is scored only on mentions that *have* annotated evidence, where
    # roughly 6% of the sentence's tokens are positive; over all mentions the
    # positive rate would be 0.3% and the head would collapse to "never".
    evidence_loss_fn = nn.BCEWithLogitsLoss(
        pos_weight=torch.tensor(EVIDENCE_POS_WEIGHT, device=device)
    )

    def forward(doc: FactualityDocument):
        """Joint forward: one encoding, label logits and evidence logits."""
        candidates = (
            [evidence_candidates(doc, m) for m in doc.mentions]
            if evidence_head is not None
            else [[] for _ in doc.mentions]
        )
        char_starts = [m.span.char_start for m in doc.mentions]
        char_starts += [c.char_start for per_mention in candidates for c in per_mention]
        pooled = encode_spans(
            encoder,
            tokenizer,
            doc.doc_text,
            char_starts,
            max_length=max_length,
            stride=stride,
            device=device,
        )
        triggers = pooled[: len(doc.mentions)]
        features = triggers
        if use_structure:
            contexts = structure_contexts(doc.mentions, doc.gold_edges, nodes=doc.nodes)
            structure = torch.tensor(
                [contexts[m.mention_id].as_vector() for m in doc.mentions],
                dtype=features.dtype,
                device=features.device,
            )
            features = torch.cat([features, structure], dim=-1)

        evidence_logits: list = []
        evidence_gold: list = []
        cursor = len(doc.mentions)
        for i, (mention, per_mention) in enumerate(zip(doc.mentions, candidates, strict=True)):
            span_features = pooled[cursor : cursor + len(per_mention)]
            cursor += len(per_mention)
            if not mention.evidence:
                continue
            trigger = triggers[i].expand(len(per_mention), -1)
            evidence_logits.append(evidence_head(pair_features(span_features, trigger)).squeeze(-1))
            evidence_gold.append(
                torch.tensor(
                    evidence_targets(per_mention, mention),
                    dtype=torch.float,
                    device=device,
                )
            )
        return head(features), evidence_logits, evidence_gold

    curve: list[dict] = []
    best: dict = {"macro_f1": -1.0, "epoch": 0}
    best_state: dict = {}

    order = list(range(len(train_docs)))
    for epoch in range(epochs):
        random.shuffle(order)
        encoder.train()
        head.train()
        if evidence_head is not None:
            evidence_head.train()
        total = 0.0
        total_evidence = 0.0
        seen = 0
        for step, i in enumerate(order, 1):
            doc = train_docs[i]
            if not doc.mentions:
                continue
            targets = torch.tensor([label_index[m.factuality] for m in doc.mentions], device=device)
            logits, evidence_logits, evidence_gold = forward(doc)
            label_loss = loss_fn(logits, targets)
            loss = label_loss
            if evidence_logits:
                evidence_loss = evidence_loss_fn(
                    torch.cat(evidence_logits), torch.cat(evidence_gold)
                )
                loss = loss + evidence_weight * evidence_loss
                total_evidence += float(evidence_loss.detach())
            loss.backward()
            optimizer.step()
            optimizer.zero_grad()
            total += float(label_loss.detach())
            seen += 1
            if step % 200 == 0:
                print(
                    f"epoch {epoch + 1} step {step}/{len(order)} "
                    f"label loss {total / seen:.4f} evidence loss {total_evidence / seen:.4f}",
                    flush=True,
                )
        print(
            f"epoch {epoch + 1} mean label loss {total / max(seen, 1):.4f} "
            f"mean evidence loss {total_evidence / max(seen, 1):.4f}",
            flush=True,
        )

        # Checkpoint every epoch, then score it: the epoch count was the
        # decisive variable in both Phase A and Phase C, so the curve has to be
        # observable rather than guessed at from the final number.
        output.mkdir(parents=True, exist_ok=True)
        encoder.save_pretrained(output)
        tokenizer.save_pretrained(output)
        torch.save(head.state_dict(), output / HEAD_FILE)
        if evidence_head is not None:
            torch.save(evidence_head.state_dict(), output / EVIDENCE_HEAD_FILE)
        (output / LABELS_FILE).write_text(json.dumps(list(FACTUALITY_LABELS)))
        if dev_docs:
            detector = SupervisedFactualityDetector(
                checkpoint_path=str(output),
                max_length=max_length,
                stride=stride,
                use_structure=use_structure,
            )
            report, evidence_prf = evaluate(detector, dev_docs)
            per_class = {c: round(p["f1"], 4) for c, p in report["per_class"].items()}
            print(
                f"epoch {epoch + 1} dev macro-F1 {report['macro_f1']:.4f} "
                f"accuracy {report['accuracy']:.4f} per-class-f1 {per_class}",
                flush=True,
            )
            print(
                f"epoch {epoch + 1} dev evidence span F1 {evidence_prf['f1']:.4f} "
                f"(P {evidence_prf['precision']:.4f} R {evidence_prf['recall']:.4f}, "
                f"{evidence_prf['n_mentions_with_evidence']} annotated mentions, "
                f"recall ceiling {SAME_SENTENCE_RECALL_CEILING})",
                flush=True,
            )
            curve.append(
                {
                    "epoch": epoch + 1,
                    "macro_f1": report["macro_f1"],
                    "accuracy": report["accuracy"],
                    "per_class_f1": {c: p["f1"] for c, p in report["per_class"].items()},
                    "evidence_span_f1": evidence_prf["f1"],
                }
            )
            # Keep the best epoch, not the last one. The macro average here is
            # driven by PS- and Uu, which have ~12 and ~5 dev instances: the
            # curve is not monotone and the final epoch is not reliably the
            # best, so "train N epochs and take what falls out" would report a
            # worse model than the run actually produced.
            if report["macro_f1"] > best["macro_f1"]:
                best = {"macro_f1": report["macro_f1"], "epoch": epoch + 1}
                best_state = {
                    "encoder": {
                        k: v.detach().cpu().clone() for k, v in encoder.state_dict().items()
                    },
                    "head": {k: v.detach().cpu().clone() for k, v in head.state_dict().items()},
                }
                if evidence_head is not None:
                    best_state["evidence"] = {
                        k: v.detach().cpu().clone() for k, v in evidence_head.state_dict().items()
                    }
            encoder.train()

    if best_state and best["epoch"] != epochs:
        print(
            f"restoring epoch {best['epoch']} (dev macro-F1 {best['macro_f1']:.4f}) "
            f"over the final epoch",
            flush=True,
        )
        encoder.load_state_dict(best_state["encoder"])
        head.load_state_dict(best_state["head"])
        if evidence_head is not None:
            evidence_head.load_state_dict(best_state["evidence"])
        encoder.save_pretrained(output)
        torch.save(head.state_dict(), output / HEAD_FILE)
        if evidence_head is not None:
            torch.save(evidence_head.state_dict(), output / EVIDENCE_HEAD_FILE)
    if curve:
        (output / DEV_CURVE_FILE).write_text(
            json.dumps({"selected_epoch": best["epoch"], "curve": curve}, indent=2)
        )
    print(f"saved factuality detector to {output}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train", required=True, type=Path, help="MAVEN-FACT train jsonl")
    parser.add_argument("--detector", default="supervised", choices=("lexicon", "supervised"))
    parser.add_argument("--model", default="roberta-base", help="base encoder (supervised)")
    parser.add_argument("--output", required=True, type=Path, help="checkpoint dir (or json file)")
    parser.add_argument("--epochs", type=int, default=6)
    parser.add_argument("--lr", type=float, default=2e-5)
    parser.add_argument(
        "--alpha",
        type=float,
        default=0.5,
        help="inverse-frequency exponent (Phase A optimum .25-.5)",
    )
    parser.add_argument("--max-length", type=int, default=512)
    parser.add_argument("--stride", type=int, default=128)
    parser.add_argument("--no-structure", action="store_true", help="ablate the graph features")
    parser.add_argument(
        "--evidence-weight",
        type=float,
        default=1.0,
        help="weight of the evidence-span loss; 0 trains the label head alone",
    )
    parser.add_argument(
        "--dev-ratio", type=float, default=0.1, help="held-out share of train for model selection"
    )
    parser.add_argument("--limit", type=int, default=None, help="first N documents (smoke)")
    parser.add_argument("--seed", type=int, default=13)
    args = parser.parse_args()

    docs = list(load_maven_fact(args.train))
    if args.limit:
        docs = docs[: args.limit]
    distribution = factuality_distribution(docs)
    print(f"loaded {len(docs)} documents, {sum(distribution.values())} mentions")
    print(f"label distribution: {distribution}")

    # Document-level split so no document's mentions straddle train and dev.
    random.Random(args.seed).shuffle(docs)
    n_dev = int(len(docs) * args.dev_ratio)
    dev_docs, train_docs = docs[:n_dev], docs[n_dev:]
    print(f"train {len(train_docs)} docs / dev {len(dev_docs)} docs (valid split stays untouched)")
    if dev_docs:
        dev_gold = {m.mention_id: m.factuality for d in dev_docs for m in d.mentions}
        baseline = majority_baseline_report(dev_gold)
        print(
            f"dev majority baseline: macro-F1 {baseline['macro_f1']:.4f} "
            f"accuracy {baseline['accuracy']:.4f}  <- the number to beat"
        )

    if args.detector == "lexicon":
        detector = LexiconFactualityDetector().fit(train_docs)
        detector.save(args.output)
        if dev_docs:
            report, _ = evaluate(detector, dev_docs)
            print(
                f"lexicon dev macro-F1 {report['macro_f1']:.4f} accuracy {report['accuracy']:.4f}"
            )
        print(f"saved lexicon detector to {args.output}")
        return 0

    train_supervised(
        train_docs,
        dev_docs,
        model_name=args.model,
        output=args.output,
        epochs=args.epochs,
        lr=args.lr,
        alpha=args.alpha,
        max_length=args.max_length,
        stride=args.stride,
        use_structure=not args.no_structure,
        evidence_weight=args.evidence_weight,
        seed=args.seed,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
