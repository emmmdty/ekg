#!/usr/bin/env python
"""Train and evaluate a causal-pair bi-encoder retrieval diagnostic.

This is Stage 1 only: it measures whether top-k retrieval can keep causal gold
pairs while pruning unrelated candidates. It does not produce relation labels or
official F1, and therefore cannot be promoted as a relation-extraction result.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from train_supervised_relations import validate_v6_protocol_inputs  # noqa: E402

from ekg.core.protocol import split_docs_by_manifests  # noqa: E402
from ekg.core.schema import RelationType  # noqa: E402
from ekg.relations.data.maven_ere import load_maven_ere  # noqa: E402
from ekg.relations.pairs import gold_pair_labels, mention_order  # noqa: E402
from ekg.relations.retrieval import (  # noqa: E402
    retrieval_counts,
    sample_binary_pairs,
    top_k_pairs,
)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def mention_ids(doc) -> list[str]:
    order = mention_order(doc)
    return sorted(order, key=order.__getitem__)


def causal_pairs(doc) -> set[tuple[str, str]]:
    return set(
        gold_pair_labels(
            doc,
            family=RelationType.CAUSAL,
            expand_event_relations=True,
        )
    )


def sentence_ids(doc) -> dict[str, int]:
    result = {}
    for node in doc.nodes:
        span = node.trigger_evidence[0] if node.trigger_evidence else None
        if span is None or span.sent_id is None:
            raise ValueError(f"{doc.doc_id}/{node.event_id}: retriever needs sentence ID")
        result[node.event_id] = span.sent_id
    return result


def aggregate_counts(items: list[dict[str, int | float]]) -> dict[str, float | int]:
    fields = (
        "gold",
        "retrieved_gold",
        "same_gold",
        "retrieved_same_gold",
        "cross_gold",
        "retrieved_cross_gold",
        "selected",
        "universe",
    )
    total = {field: sum(int(item[field]) for item in items) for field in fields}
    total["recall_at_k"] = total["retrieved_gold"] / total["gold"]
    total["same_sentence_recall_at_k"] = (
        total["retrieved_same_gold"] / total["same_gold"]
    )
    total["cross_sentence_recall_at_k"] = (
        total["retrieved_cross_gold"] / total["cross_gold"]
    )
    total["candidate_compression"] = 1.0 - total["selected"] / total["universe"]
    return total


def checkpoint_hashes(output: Path) -> dict[str, str]:
    return {
        path.relative_to(output).as_posix(): sha256_file(path)
        for path in sorted(output.rglob("*"))
        if path.is_file() and path.name != "run_metadata.json"
    }


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train", required=True, type=Path)
    parser.add_argument("--train-manifest", required=True, type=Path)
    parser.add_argument("--dev-manifest", required=True, type=Path)
    parser.add_argument("--protocol-root", required=True, type=Path)
    parser.add_argument("--repo-root", required=True, type=Path)
    parser.add_argument("--p1-protocol-sha256", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--top-k", type=int, default=15)
    parser.add_argument("--negative-ratio", type=int, default=5)
    parser.add_argument("--lr", type=float, default=2e-5)
    parser.add_argument("--head-lr", type=float, default=1e-4)
    parser.add_argument("--warmup-steps", type=int, default=100)
    parser.add_argument("--accum-steps", type=int, default=8)
    parser.add_argument("--max-length", type=int, default=512)
    parser.add_argument("--temperature", type=float, default=0.1)
    parser.add_argument("--seed", type=int, default=13)
    args = parser.parse_args()

    if args.epochs <= 0 or args.top_k <= 0 or args.accum_steps <= 0:
        parser.error("epochs, top-k and accum-steps must be positive")
    if args.negative_ratio <= 0 or args.temperature <= 0:
        parser.error("negative-ratio and temperature must be positive")
    if args.output.exists() and any(args.output.iterdir()):
        parser.error(f"refusing non-empty immutable output directory: {args.output}")

    try:
        protocol = validate_v6_protocol_inputs(
            repo_root=args.repo_root,
            train_path=args.train,
            train_manifest=args.train_manifest,
            dev_manifest=args.dev_manifest,
            protocol_root=args.protocol_root,
            expected_p1_protocol_sha256=args.p1_protocol_sha256,
        )
    except ValueError as exc:
        parser.error(str(exc))
    protocol["hashes"]["retriever_trainer"] = sha256_file(Path(__file__).resolve())

    args.output.mkdir(parents=True, exist_ok=True)
    metadata = {
        "schema_version": "ekg.relation_retriever_diagnostic.v1",
        "status": "incomplete",
        "confirmation_eligible": False,
        "claim_boundary": "Stage-1 causal candidate recall only; no relation F1",
        "command_argv": list(sys.argv),
        "working_directory": str(Path.cwd().resolve()),
        "protocol_binding": protocol,
        "final_valid_accessed": False,
        "configuration": {
            "model": args.model,
            "epochs": args.epochs,
            "top_k": args.top_k,
            "negative_ratio": args.negative_ratio,
            "lr": args.lr,
            "head_lr": args.head_lr,
            "warmup_steps": args.warmup_steps,
            "accum_steps": args.accum_steps,
            "max_length": args.max_length,
            "temperature": args.temperature,
            "seed": args.seed,
        },
    }
    write_json(args.output / "run_metadata.json", metadata)

    import torch
    import torch.nn.functional as functional
    from transformers import AutoModel, AutoTokenizer, get_linear_schedule_with_warmup

    from ekg.relations.extractor.supervised import encode_trigger_reps

    device = "cuda" if torch.cuda.is_available() else "cpu"
    if device != "cuda":
        raise SystemExit("relation retriever training requires CUDA")
    torch.manual_seed(args.seed)
    docs = list(load_maven_ere(args.train, include_timex=False))
    train_docs, dev_docs = split_docs_by_manifests(
        docs,
        args.train_manifest,
        args.dev_manifest,
    )
    tokenizer = AutoTokenizer.from_pretrained(args.model)
    encoder = AutoModel.from_pretrained(args.model).to(device)
    hidden_size = encoder.config.hidden_size
    query = torch.nn.Linear(hidden_size, hidden_size, bias=False).to(device)
    key = torch.nn.Linear(hidden_size, hidden_size, bias=False).to(device)
    torch.nn.init.eye_(query.weight)
    torch.nn.init.eye_(key.weight)
    optimiser = torch.optim.AdamW(
        [
            {"params": encoder.parameters(), "lr": args.lr},
            {"params": list(query.parameters()) + list(key.parameters()), "lr": args.head_lr},
        ]
    )
    steps_per_epoch = math.ceil(len(train_docs) / args.accum_steps)
    scheduler = get_linear_schedule_with_warmup(
        optimiser,
        args.warmup_steps,
        args.epochs * steps_per_epoch,
    )
    positive_weight = torch.tensor(float(args.negative_ratio), device=device)

    def encode(doc):
        ids = mention_ids(doc)
        representations = encode_trigger_reps(
            encoder,
            tokenizer,
            doc.nodes,
            doc.doc_text,
            args.max_length,
            device,
        )
        return ids, torch.stack([representations[item] for item in ids])

    def evaluate() -> dict[str, float | int]:
        encoder.eval()
        query.eval()
        key.eval()
        counts = []
        with torch.no_grad():
            for doc in dev_docs:
                ids, representations = encode(doc)
                if len(ids) < 2:
                    continue
                query_vectors = functional.normalize(query(representations), dim=-1)
                key_vectors = functional.normalize(key(representations), dim=-1)
                matrix = (query_vectors @ key_vectors.T).cpu()
                score_map = {
                    (head, tail): float(matrix[i, j])
                    for i, head in enumerate(ids)
                    for j, tail in enumerate(ids)
                    if i != j
                }
                selected = top_k_pairs(ids, score_map, args.top_k)
                counts.append(
                    retrieval_counts(
                        selected,
                        causal_pairs(doc),
                        mention_ids=ids,
                        sentence_by_id=sentence_ids(doc),
                    )
                )
        return aggregate_counts(counts)

    best_recall = -1.0
    best_epoch = None
    best_metrics = None
    optimiser.zero_grad()
    for epoch in range(args.epochs):
        encoder.train()
        query.train()
        key.train()
        ordered_docs = list(train_docs)
        random.Random(args.seed + epoch).shuffle(ordered_docs)
        running_loss = 0.0
        used_docs = 0
        for index, doc in enumerate(ordered_docs, start=1):
            ids, representations = encode(doc)
            if len(ids) < 2:
                continue
            pairs, labels = sample_binary_pairs(
                ids,
                causal_pairs(doc),
                negative_ratio=args.negative_ratio,
                rng=random.Random(args.seed * 1_000_003 + epoch * 10_007 + index),
            )
            positions = {item: i for i, item in enumerate(ids)}
            head_index = torch.tensor([positions[head] for head, _ in pairs], device=device)
            tail_index = torch.tensor([positions[tail] for _, tail in pairs], device=device)
            query_vectors = functional.normalize(query(representations[head_index]), dim=-1)
            key_vectors = functional.normalize(key(representations[tail_index]), dim=-1)
            logits = (query_vectors * key_vectors).sum(dim=-1) / args.temperature
            targets = torch.tensor(labels, dtype=torch.float32, device=device)
            loss = functional.binary_cross_entropy_with_logits(
                logits,
                targets,
                pos_weight=positive_weight,
            )
            (loss / args.accum_steps).backward()
            running_loss += float(loss.detach())
            used_docs += 1
            if index % args.accum_steps == 0 or index == len(ordered_docs):
                optimiser.step()
                scheduler.step()
                optimiser.zero_grad()
            if index % 500 == 0:
                print(
                    f"[retriever] epoch {epoch} {index}/{len(ordered_docs)} "
                    f"loss={running_loss / used_docs:.4f}",
                    flush=True,
                )

        metrics = evaluate()
        print(
            f"[retriever] epoch {epoch} recall@{args.top_k}="
            f"{metrics['recall_at_k']:.4f} cross={metrics['cross_sentence_recall_at_k']:.4f} "
            f"compression={metrics['candidate_compression']:.4f}",
            flush=True,
        )
        if metrics["recall_at_k"] > best_recall:
            best_recall = float(metrics["recall_at_k"])
            best_epoch = epoch
            best_metrics = metrics
            encoder.save_pretrained(args.output)
            tokenizer.save_pretrained(args.output)
            torch.save(
                {"query": query.state_dict(), "key": key.state_dict()},
                args.output / "retriever_heads.pt",
            )
            write_json(args.output / "retrieval_metrics.json", metrics)

    metadata.update(
        {
            "status": "complete",
            "device": device,
            "selection": {
                "best_epoch": best_epoch,
                "best_recall_at_k": best_recall,
                "best_metrics": best_metrics,
            },
            "checkpoint_sha256": checkpoint_hashes(args.output),
        }
    )
    write_json(args.output / "run_metadata.json", metadata)
    print(
        f"[retriever] best epoch={best_epoch} recall@{args.top_k}={best_recall:.4f}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
