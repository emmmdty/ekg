#!/usr/bin/env python
"""Train one frozen A4 pair-evidence arm on the v6 train manifest.

The candidate universe is never touched: rows are `pair_examples`' own output
with official mention expansion and every negative kept, which is the same
universe the official evaluator scores.  What the arm changes is the objective
and which sentences the counterfactual forwards intervene on.

Three contexts are encoded per supervised pair: the whole document (the
reproduction baseline's forward), the document with the pair's citation removed
(necessity) and the trigger sentences plus the citation alone (sufficiency).
Only rows the base pass already calls causal-positive, plus the gold causal
positives, are supervised that way -- one forward per pair over the whole
document would be thousands per document, and the claim is about what supports
a positive rather than about every candidate.

The evidence residual is applied by the *base pass's own prediction*, at
training and at inference alike, so the scored rule never reads a gold label.
"""

from __future__ import annotations

import argparse
import json
import math
import random
from collections.abc import Sequence
from pathlib import Path

from ekg.core.protocol import split_docs_by_manifests
from ekg.core.stage_bundle import sha256_file
from ekg.relations.data.maven_ere import load_maven_ere
from ekg.relations.pair_evidence import (
    CONFIG_FILE,
    CONSISTENCY_FAMILY,
    CONSISTENCY_PAIR_CAP,
    arm_flags,
    consistency_rows,
    counterfactual_sentence_ids,
    document_pair_evidence,
    necessity_scoreable,
    pair_evidence_config,
    validate_a4_arm,
)
from ekg.relations.pair_heads import PAIR_EVIDENCE_HEAD, PAIR_HEAD_CONFIG_FILE
from ekg.relations.pairs import PairExample, pair_examples

IGNORE_INDEX = -100
NONE_INDEX = 0
RUN_METADATA_FILE = "run_metadata.json"


def label_indices(subtypes: dict[str, tuple[str, ...]]) -> dict[str, dict[str, int]]:
    return {family: {name: i for i, name in enumerate(subs)} for family, subs in subtypes.items()}


def family_targets(
    rows: Sequence[PairExample], family: str, index: dict[str, dict[str, int]]
) -> list[int]:
    """Gold class per row, with the official ignore index where unscoreable.

    A pair touching a TIMEX is `-100` for causal and subevent exactly as the
    official baseline emits it; scoring it as a negative would inflate the
    denominator the reported F1 is read against.
    """
    return [
        IGNORE_INDEX
        if family in row.ignored_families
        else index[family][row.labels.get(family, "NONE")]
        for row in rows
    ]


def rows_by_document(
    docs, max_distance: int | None
) -> tuple[dict[str, list[PairExample]], int]:
    """Every document's labelled candidate universe, grouped, nothing dropped."""
    grouped: dict[str, list[PairExample]] = {}
    total = 0
    for doc in docs:
        # v6 manifest runs require official mention expansion; it is not a knob
        # here, because changing it changes the candidate universe itself.
        rows = pair_examples(doc, max_distance, expand_event_relations=True)
        grouped[doc.doc_id] = rows
        total += len(rows)
    return grouped, total


def _f1(tp: int, fp: int, fn: int) -> float:
    if tp == 0:
        return 0.0
    precision, recall = tp / (tp + fp), tp / (tp + fn)
    return 2 * precision * recall / (precision + recall)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train", required=True, type=Path, help="MAVEN-ERE train source")
    parser.add_argument("--train-manifest", required=True, type=Path)
    parser.add_argument("--dev-manifest", required=True, type=Path)
    parser.add_argument("--model", required=True, type=str, help="frozen encoder directory")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--arm", required=True)
    parser.add_argument("--epochs", type=int, required=True)
    parser.add_argument("--lr", type=float, required=True, help="encoder learning rate")
    parser.add_argument("--head-lr", type=float, required=True)
    parser.add_argument("--warmup-steps", type=int, required=True)
    parser.add_argument("--accum-steps", type=int, required=True)
    parser.add_argument("--max-length", type=int, required=True)
    parser.add_argument("--consistency-weight", type=float, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--max-distance", type=int)
    parser.add_argument("--max-docs", type=int, help="smoke only: first N train documents")
    args = parser.parse_args()
    arm = validate_a4_arm(args.arm)
    flags = arm_flags(arm)

    import torch
    from transformers import AutoModel, AutoTokenizer

    from ekg.nodes.encoding import pair_features
    from ekg.relations.extractor.supervised import (
        FAMILY_SUBTYPES,
        distance_bucket,
        encode_trigger_reps,
    )
    from ekg.relations.pair_evidence import (
        pair_counterfactual_embeddings,
        sufficiency_necessity_loss,
    )
    from ekg.relations.pair_heads import build_pair_head

    docs = list(load_maven_ere(args.train, include_timex=True))
    train_docs, dev_docs = split_docs_by_manifests(docs, args.train_manifest, args.dev_manifest)
    if args.max_docs:
        train_docs, dev_docs = train_docs[: args.max_docs], dev_docs[: args.max_docs]
    docs_by_id = {doc.doc_id: doc for doc in docs}
    grouped, candidates = rows_by_document(train_docs + dev_docs, args.max_distance)
    index = label_indices(FAMILY_SUBTYPES)
    families = tuple(FAMILY_SUBTYPES)
    evidence_by_doc = {
        doc_id: document_pair_evidence(
            docs_by_id[doc_id].nodes,
            docs_by_id[doc_id].doc_text,
            [(row.head_id, row.tail_id) for row in rows],
        )
        for doc_id, rows in grouped.items()
    }

    device = "cuda" if torch.cuda.is_available() else "cpu"
    torch.manual_seed(args.seed)
    tokenizer = AutoTokenizer.from_pretrained(args.model)
    encoder = AutoModel.from_pretrained(args.model).to(device)
    heads = build_pair_head(
        PAIR_EVIDENCE_HEAD,
        hidden_size=encoder.config.hidden_size,
        subtype_counts={family: len(subs) for family, subs in FAMILY_SUBTYPES.items()},
    ).to(device)
    optimiser = torch.optim.AdamW(
        [
            {"params": list(encoder.parameters()), "lr": args.lr},
            {"params": list(heads.parameters()), "lr": args.head_lr, "weight_decay": 0.0},
        ],
        lr=args.lr,
    )
    scheduler = None
    if args.warmup_steps > 0:
        from transformers import get_linear_schedule_with_warmup

        steps = math.ceil(len(train_docs) / args.accum_steps) * args.epochs
        scheduler = get_linear_schedule_with_warmup(optimiser, args.warmup_steps, steps)

    run_metadata = {
        "schema_version": "ekg.a4_pair_evidence_run.v1",
        "status": "running",
        "configuration": {
            "arm": arm,
            "epochs": args.epochs,
            "lr": args.lr,
            "head_lr": args.head_lr,
            "warmup_steps": args.warmup_steps,
            "accum_steps": args.accum_steps,
            "max_length": args.max_length,
            "max_distance": args.max_distance,
            "consistency_weight": args.consistency_weight,
            "seed": args.seed,
            "official_mention_expansion": True,
            "negatives": "all",
            "families": list(families),
        },
        "population": {
            "train_documents": len(train_docs),
            "dev_documents": len(dev_docs),
            "candidate_pairs": candidates,
        },
        "device": device,
        "manifest_sha256": {
            "train": sha256_file(args.train_manifest),
            "internal_dev": sha256_file(args.dev_manifest),
        },
    }
    args.output.mkdir(parents=True, exist_ok=True)
    _write(args.output / RUN_METADATA_FILE, run_metadata)

    def forward_document(doc_id: str, rows: Sequence[PairExample]):
        """Base pass: pair features, distance ids and per-family logits."""
        doc = docs_by_id[doc_id]
        embeddings = encode_trigger_reps(
            encoder, tokenizer, doc.nodes, doc.doc_text, args.max_length, device
        )
        head_emb = torch.stack([embeddings[row.head_id] for row in rows])
        tail_emb = torch.stack([embeddings[row.tail_id] for row in rows])
        feats = pair_features(head_emb, tail_emb)
        dist_ids = torch.tensor([distance_bucket(row.distance) for row in rows], device=device)
        return feats, dist_ids, heads(feats, dist_ids)

    def counterfactual_features(doc_id: str, records, selected: Sequence[int]):
        """Masked and retained pair features for the supervised rows."""
        doc = docs_by_id[doc_id]
        sentences = len(doc.doc_text.split("\n"))
        requests = {"masked": [], "retained": []}
        for row_index in selected:
            record = records[row_index]
            sets = counterfactual_sentence_ids(record, sentences, arm=arm)
            key = (record.head_id, record.tail_id)
            for kind in requests:
                requests[kind].append((key, sets[kind]))
        out = {}
        for kind, batch in requests.items():
            head_emb, tail_emb = pair_counterfactual_embeddings(
                encoder, tokenizer, doc.nodes, doc.doc_text, batch, args.max_length, device
            )
            out[kind] = pair_features(head_emb, tail_emb)
        return out

    def supervised_rows(records, logits, targets):
        """The rows the revised pass trains on, balanced by `consistency_rows`.

        Gold positives and the base pass's current false positives in equal
        measure: trained on base-predicted positives alone the revision sees a
        row set that is ~80% gold-NONE and collapses to always-NONE (measured).
        The scored rule is unchanged — inference revises every base-predicted
        positive.

        A pair that is unscoreable for causal (a TIMEX endpoint) is excluded on
        both counts.  It has to be: the official protocol does not score it, so
        supervising the causal head on it would train outside the reported
        population -- and a step whose every selected row was unscoreable made
        `cross_entropy` average over zero rows and return `nan`, which is how
        this was found (the 2026-09-12 smoke, all three evidence arms).
        """
        causal = logits[CONSISTENCY_FAMILY].detach().argmax(dim=-1)
        target = targets[CONSISTENCY_FAMILY]
        gold_positive: list[bool] = []
        predicted_positive: list[bool] = []
        for predicted, gold in zip(causal.tolist(), target.tolist(), strict=True):
            scoreable = gold != IGNORE_INDEX
            gold_positive.append(bool(scoreable and gold != NONE_INDEX))
            predicted_positive.append(bool(scoreable and predicted != NONE_INDEX))
        return consistency_rows(records, gold_positive, predicted_positive, arm=arm)

    def dev_scores() -> tuple[float, dict[str, float]]:
        """Macro pair F1 over non-NONE classes, with the residual applied."""
        encoder.eval()
        heads.eval()
        counts = {family: [0, 0, 0] for family in families}
        with torch.no_grad():
            for doc in dev_docs:
                rows = grouped[doc.doc_id]
                feats, dist_ids, logits = forward_document(doc.doc_id, rows)
                targets = {
                    family: torch.tensor(family_targets(rows, family, index), device=device)
                    for family in families
                }
                predictions = {family: logits[family].argmax(dim=-1) for family in families}
                if flags.evidence_stream:
                    causal = predictions[CONSISTENCY_FAMILY]
                    selected = [i for i, value in enumerate(causal.tolist()) if value != NONE_INDEX]
                    selected = selected[:CONSISTENCY_PAIR_CAP]
                    if selected:
                        cf = counterfactual_features(doc.doc_id, evidence_by_doc[doc.doc_id],
                                                     selected)
                        picked = torch.tensor(selected, device=device)
                        revised = heads(feats[picked], dist_ids[picked], cf["retained"])
                        causal[picked] = revised[CONSISTENCY_FAMILY].argmax(dim=-1)
                for family in families:
                    gold, predicted = targets[family], predictions[family]
                    scored = gold != IGNORE_INDEX
                    hit = (predicted == gold) & scored
                    gold = torch.where(scored, gold, torch.zeros_like(gold))
                    predicted = torch.where(scored, predicted, torch.zeros_like(predicted))
                    counts[family][0] += int(((gold > 0) & hit).sum())
                    counts[family][1] += int(((predicted > 0) & ~hit).sum())
                    counts[family][2] += int(((gold > 0) & ~hit).sum())
        encoder.train()
        heads.train()
        by_family = {family: _f1(*values) for family, values in counts.items()}
        return sum(by_family.values()) / len(by_family), by_family

    def save_checkpoint(destination: Path) -> None:
        destination.mkdir(parents=True, exist_ok=True)
        encoder.save_pretrained(destination)
        tokenizer.save_pretrained(destination)
        torch.save(heads.state_dict(), destination / "heads.pt")
        _write(
            destination / PAIR_HEAD_CONFIG_FILE,
            {"schema_version": "ekg.relation_pair_head.v1", "name": PAIR_EVIDENCE_HEAD},
        )
        _write(destination / CONFIG_FILE, pair_evidence_config(arm))

    epoch_losses: list[float] = []
    best_f1, best_epoch, best_by_family = -1.0, None, {}
    family_selection = {family: {"best_f1": -1.0, "best_epoch": None} for family in families}
    skipped_total = 0
    encoder.train()
    heads.train()
    for epoch in range(args.epochs):
        order = [doc.doc_id for doc in train_docs]
        random.Random(args.seed + epoch).shuffle(order)
        running = 0.0
        for seen, doc_id in enumerate(order, start=1):
            rows = grouped[doc_id]
            records = evidence_by_doc[doc_id]
            feats, dist_ids, logits = forward_document(doc_id, rows)
            targets = {
                family: torch.tensor(family_targets(rows, family, index), device=device)
                for family in families
            }
            loss = torch.zeros((), device=device)
            for family in families:
                loss = loss + torch.nn.functional.cross_entropy(
                    logits[family], targets[family], ignore_index=IGNORE_INDEX
                )
            selected, skipped = supervised_rows(records, logits, targets)
            skipped_total += skipped
            if selected:
                cf = counterfactual_features(doc_id, records, selected)
                picked = torch.tensor(selected, device=device)
                target = targets[CONSISTENCY_FAMILY][picked]
                revised = heads(feats[picked], dist_ids[picked], cf["retained"])
                loss = loss + torch.nn.functional.cross_entropy(
                    revised[CONSISTENCY_FAMILY], target, ignore_index=IGNORE_INDEX
                )
                if flags.consistency_loss:
                    base = heads.base(feats[picked], dist_ids[picked])[CONSISTENCY_FAMILY]
                    masked = heads.base(cf["masked"], dist_ids[picked])[CONSISTENCY_FAMILY]
                    retained = heads.base(cf["retained"], dist_ids[picked])[CONSISTENCY_FAMILY]
                    scoreable = torch.tensor(
                        [necessity_scoreable(records[i], arm=arm) for i in selected],
                        device=device,
                    )
                    loss = loss + args.consistency_weight * sufficiency_necessity_loss(
                        base, masked, retained, target, scoreable=scoreable,
                        ignore_index=IGNORE_INDEX,
                    )
            if not bool(torch.isfinite(loss)):
                # Averaging a nan into the epoch mean hides which step produced
                # it, and the checkpoint that follows would look trained.
                raise ValueError(f"[a4:{arm}] non-finite loss on {doc_id}")
            running += float(loss.detach())
            (loss / args.accum_steps).backward()
            if seen % args.accum_steps == 0 or seen == len(order):
                optimiser.step()
                if scheduler is not None:
                    scheduler.step()
                optimiser.zero_grad()
            if seen % 200 == 0:
                print(
                    f"[a4:{arm}] epoch {epoch} {seen}/{len(order)} "
                    f"running_loss={running / seen:.4f}",
                    flush=True,
                )
        epoch_losses.append(running / max(1, len(order)))
        print(f"[a4:{arm}] epoch {epoch} mean_loss={epoch_losses[-1]:.4f}", flush=True)
        f1, by_family = dev_scores()
        detail = " ".join(f"{family[:4]}={value:.3f}" for family, value in by_family.items())
        better = f1 > best_f1
        print(
            f"[dev:{arm}] epoch {epoch} macro_f1={f1:.4f} ({detail})"
            + ("  <- best, saving" if better else "  (keeping best)"),
            flush=True,
        )
        if better:
            best_f1, best_epoch, best_by_family = f1, epoch, by_family
            save_checkpoint(args.output)
        for family, family_f1 in by_family.items():
            if family_f1 <= family_selection[family]["best_f1"]:
                continue
            family_selection[family].update(best_f1=family_f1, best_epoch=epoch)
            destination = args.output / "by_family" / family
            save_checkpoint(destination)
            _write(
                destination / "selection.json",
                {"family": family, "epoch": epoch, "dev_macro_f1": family_f1},
            )

    run_metadata.update(
        {
            "status": "complete",
            "selection": {
                "metric": "macro",
                "best_epoch": best_epoch,
                "best_f1": best_f1,
                "best_by_family": best_by_family,
                "family_checkpoints": family_selection,
            },
            "epoch_mean_loss": epoch_losses,
            "consistency": {
                "family": CONSISTENCY_FAMILY,
                "pair_cap": CONSISTENCY_PAIR_CAP,
                "rows_dropped_by_cap": skipped_total,
            },
        }
    )
    _write(args.output / RUN_METADATA_FILE, run_metadata)
    print(f"[a4:{arm}] best dev macro_f1={best_f1:.4f}; checkpoint at {args.output}")
    return 0


def _write(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
