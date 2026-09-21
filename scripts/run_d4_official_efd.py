#!/usr/bin/env python
"""Run the vendored official MAVEN-FACT EFD trainer on one fold, gold vs predicted.

Our own oracle already showed that a *perfect* causal graph adds nothing when
the structure is fused as a confidence-gated residual over the predecessor's
pooled representation (`docs/results/PHASE_R1.md` §25.25). The published `+2.0`
uses a different fusion: the predecessor *sentences* are re-encoded with markers
and concatenated. This script runs that published fusion, unchanged, under two
structure sources that differ in nothing else:

``gold``       the document's annotated ``causal_relation`` (the paper's setting;
               non-deployable)
``predicted``  the same field rebuilt from our frozen five-fold posteriors,
               lifted from mention pairs to the event-cluster pairs the official
               loader expects (deployable)

Two disclosures the write-up must carry, both in `baselines/maven_fact/README.md`:
the upstream trainer selects its epoch on the test split (this fork selects on
dev and reports both), and the split holding the published numbers is not
obtainable, so this is an FR-016 (b) transparent adaptation, never an (a).
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from ekg.core.protocol import load_manifest_ids
from ekg.core.stage_bundle import sha256_file
from ekg.factuality.causal_residual import decide_edges

STRUCTURES = ("gold", "predicted")
VENDORED = Path("baselines/maven_fact/trainEFD")


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sidecar_documents(path: Path):
    current: str | None = None
    rows: list[dict] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row["doc_id"] != current:
                if current is not None:
                    yield current, rows
                current, rows = row["doc_id"], []
            rows.append(row)
    if current is not None:
        yield current, rows


def _bare(mention_id: str, doc_id: str) -> str:
    """Our loaders namespace mention ids as ``<doc>::<mention>``; upstream does not."""
    prefix = f"{doc_id}::"
    if not mention_id.startswith(prefix):
        raise ValueError(f"{mention_id} does not belong to {doc_id}")
    return mention_id[len(prefix) :]


def write_split(
    *,
    source: Path,
    document_ids: list[str],
    structure: str,
    mention_edges: dict[str, dict[str, set[tuple[str, str]]]] | None,
    output: Path,
) -> dict:
    if output.exists():
        raise FileExistsError(f"refusing to overwrite: {output}")
    wanted = set(document_ids)
    kept = 0
    counts = {"CAUSE": 0, "PRECONDITION": 0}
    lines: list[str] = []
    for line in source.read_text(encoding="utf-8").splitlines():
        if not line:
            continue
        doc = json.loads(line)
        if doc["id"] not in wanted:
            continue
        if structure == "predicted":
            if mention_edges is None:
                raise ValueError("predicted structure requires decided mention edges")
            cluster_of = {
                mention["id"]: event["id"]
                for event in doc["events"]
                for mention in event["mention"]
            }
            rebuilt: dict[str, list[list[str]]] = {"CAUSE": [], "PRECONDITION": []}
            for subtype, pairs in mention_edges[doc["id"]].items():
                lifted = set()
                for head, tail in pairs:
                    source_cluster = cluster_of[_bare(head, doc["id"])]
                    target_cluster = cluster_of[_bare(tail, doc["id"])]
                    if source_cluster != target_cluster:
                        lifted.add((source_cluster, target_cluster))
                rebuilt[subtype] = [[head, tail] for head, tail in sorted(lifted)]
            doc["causal_relation"] = rebuilt
        for subtype in counts:
            counts[subtype] += len(doc["causal_relation"].get(subtype, []))
        lines.append(json.dumps(doc, sort_keys=True))
        kept += 1
    if kept != len(wanted):
        raise ValueError(f"{output}: expected {len(wanted)} documents, wrote {kept}")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {
        "path": str(output),
        "sha256": sha256_file(output),
        "documents": kept,
        "cluster_relation_counts": counts,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--structure", required=True, choices=STRUCTURES)
    parser.add_argument("--fold", required=True, type=int)
    parser.add_argument("--cv", required=True, type=Path)
    parser.add_argument("--source", required=True, type=Path, help="MAVEN-FACT jsonl")
    parser.add_argument("--crossfit", required=True, type=Path)
    parser.add_argument("--model", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--lr", type=float, default=1e-5)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--max-length", type=int, default=160)
    parser.add_argument("--seed", type=int, default=13)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    repo = args.repo.resolve()
    output = args.output.resolve()
    if output.exists():
        raise FileExistsError(f"refusing to overwrite run: {output}")

    row = {int(item["fold"]): item for item in _load(args.cv.resolve())["folds"]}[args.fold]
    splits = {
        role: load_manifest_ids(repo / row[role]["path"])
        for role in ("train", "selection_dev", "evaluation")
    }
    mention_edges = None
    if args.structure == "predicted":
        # Only this fold's own three sidecars. They already cover all 2,913
        # documents (1,747 + 583 + 583), and reaching for another fold's OOF
        # posterior is exactly the leakage path rejected in PHASE_R1 §25.14:
        # the relation model that produced it was trained on this fold's
        # evaluation documents.
        crossfit = args.crossfit.resolve() / f"fold-{args.fold}"
        weights = _load(crossfit / "dirichlet_calibration.metadata.json")["class_weights"]
        mention_edges = {}
        for stem, role in (
            ("train_dirichlet", "train"),
            ("selection_dirichlet", "selection_dev"),
            ("dirichlet", "evaluation"),
        ):
            wanted = set(splits[role])
            for doc_id, rows in _sidecar_documents(
                crossfit / f"{stem}_causal_posteriors.jsonl"
            ):
                if doc_id not in wanted:
                    raise ValueError(f"{doc_id} is outside the {role} manifest")
                decided = decide_edges(rows, weights)
                mention_edges[doc_id] = {
                    subtype: {
                        (e.head_mention_id, e.tail_mention_id)
                        for e in decided
                        if e.subtype == subtype
                    }
                    for subtype in ("CAUSE", "PRECONDITION")
                }
        missing = {
            doc_id
            for role in splits
            for doc_id in splits[role]
            if doc_id not in mention_edges
        }
        if missing:
            raise ValueError(f"{len(missing)} documents have no predicted structure")

    output.mkdir(parents=True)
    written = {
        role: write_split(
            source=args.source.resolve(),
            document_ids=splits[role],
            structure=args.structure,
            mention_edges=mention_edges,
            output=output / f"{role}.jsonl",
        )
        for role in ("train", "selection_dev", "evaluation")
    }
    command = [
        sys.executable,
        "-u",
        "train.py",
        "--train_data",
        str(output / "train.jsonl"),
        "--dev_data",
        str(output / "selection_dev.jsonl"),
        "--test_data",
        str(output / "evaluation.jsonl"),
        "--report_out",
        str(output / "report.json"),
        "--model_dir",
        str(output / "models"),
        "--log_dir",
        str(output / "logs"),
        "--model",
        "DMBert",
        "--pooling_type",
        "cls",
        "--model_name",
        "roberta-base",
        "--ckpt",
        str(args.model.resolve()),
        "--batch_size",
        str(args.batch_size),
        "--max_length",
        str(args.max_length),
        "--lr",
        str(args.lr),
        "--epochs",
        str(args.epochs),
        "--seed",
        str(args.seed),
        "--add_relation",
    ]
    metadata = {
        "schema_version": "ekg.d4_official_efd_run.v1",
        "status": "incomplete",
        "structure": args.structure,
        "fold": args.fold,
        "seed": args.seed,
        "fidelity": "FR-016 (b) transparent adaptation",
        "upstream": _load(repo / "baselines/maven_fact/UPSTREAM.json")["upstream"],
        "splits": written,
        "command": command,
        "working_directory": str(repo / VENDORED),
    }
    (output / "run_metadata.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    if not args.execute:
        print(json.dumps(metadata, indent=2, sort_keys=True))
        return 0
    try:
        subprocess.run(command, cwd=repo / VENDORED, check=True)
        metadata["report"] = _load(output / "report.json")
        metadata["status"] = "complete"
    except Exception:
        metadata["status"] = "failed"
        (output / "run_metadata.json").write_text(
            json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        raise
    (output / "run_metadata.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "structure": args.structure,
                "fold": args.fold,
                "dev_selected_test_macro_f1": metadata["report"]["test"]["macro_f1"],
                "upstream_rule_epoch_max": metadata["report"][
                    "epoch_max_test_macro_f1_upstream_rule"
                ],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
