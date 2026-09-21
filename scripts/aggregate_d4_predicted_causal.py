#!/usr/bin/env python
"""Pool the D4 v6.2 five-fold, three-arm OOF runs and apply the frozen gate.

The contract is `docs/phases/PHASE_D4_predicted_causal_residual.md`. Nothing in
here may be tuned after seeing a number: the target, the floors, the resample
count and the mediator definition all come from that file.

The paired comparison is a document-cluster bootstrap. Recomputing macro-F1 from
scratch 10,000 times over 73,939 mentions would be minutes of Python, so each
document is reduced once to its 5x5 gold-by-prediction confusion matrix and a
resample is a single ``counts @ matrices`` product. That is arithmetically the
same pooled macro-F1, not an approximation of it.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

from ekg.core.protocol import load_manifest_ids
from ekg.core.schema import RelationType
from ekg.core.stage_bundle import sha256_file
from ekg.factuality.causal_residual import ARMS, EDGE_SUBTYPES, consistency_violations
from ekg.relations.data.maven_ere import load_maven_ere
from ekg.relations.data.maven_fact import FACTUALITY_LABELS, load_maven_fact
from ekg.relations.pairs import gold_pair_labels

# Frozen in the contract; changing any of these is changing the gate.
MACRO_TARGET = 0.583995
FLOORS = {"PS-": 0.352456, "Uu": 0.166850}
BOOTSTRAP_DRAWS = 10000
EXPECTED_DOCUMENTS = 2913
EXPECTED_MENTIONS = 73939


class D4AggregationError(ValueError):
    """The pooled run does not satisfy the frozen contract."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise D4AggregationError(message)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _confusion(gold: str, predicted: str) -> tuple[int, int]:
    return FACTUALITY_LABELS.index(gold), FACTUALITY_LABELS.index(predicted)


def _macro_f1(matrix: np.ndarray) -> float:
    """Macro-F1 from a pooled 5x5 gold-by-prediction confusion matrix."""
    true_positive = np.diag(matrix).astype(np.float64)
    predicted = matrix.sum(axis=0).astype(np.float64)
    actual = matrix.sum(axis=1).astype(np.float64)
    denominator = predicted + actual
    with np.errstate(divide="ignore", invalid="ignore"):
        f1 = np.where(denominator > 0, 2.0 * true_positive / denominator, 0.0)
    return float(f1.mean())


def _class_f1(matrix: np.ndarray) -> dict[str, float]:
    true_positive = np.diag(matrix).astype(np.float64)
    denominator = matrix.sum(axis=0) + matrix.sum(axis=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        f1 = np.where(denominator > 0, 2.0 * true_positive / denominator, 0.0)
    return dict(zip(FACTUALITY_LABELS, (float(value) for value in f1), strict=True))


def per_document_matrices(
    document_ids: list[str],
    mentions_by_document: dict[str, list[str]],
    gold: dict[str, str],
    predicted: dict[str, str],
) -> np.ndarray:
    """``(documents, 25)`` flattened confusion matrices, in manifest order."""
    matrices = np.zeros((len(document_ids), len(FACTUALITY_LABELS) ** 2), dtype=np.int64)
    for position, doc_id in enumerate(document_ids):
        for mention_id in mentions_by_document[doc_id]:
            row, column = _confusion(gold[mention_id], predicted[mention_id])
            matrices[position, row * len(FACTUALITY_LABELS) + column] += 1
    return matrices


def paired_bootstrap(
    left: np.ndarray, right: np.ndarray, *, draws: int, seed: int
) -> dict[str, float]:
    """95% CI of ``macro(left) - macro(right)`` under document resampling."""
    _require(left.shape == right.shape, "paired arms must cover the same documents")
    documents = left.shape[0]
    side = len(FACTUALITY_LABELS)
    point = _macro_f1(left.sum(axis=0).reshape(side, side)) - _macro_f1(
        right.sum(axis=0).reshape(side, side)
    )
    generator = np.random.default_rng(seed)
    probabilities = np.full(documents, 1.0 / documents)
    deltas = np.empty(draws, dtype=np.float64)
    for index in range(draws):
        counts = generator.multinomial(documents, probabilities)
        deltas[index] = _macro_f1((counts @ left).reshape(side, side)) - _macro_f1(
            (counts @ right).reshape(side, side)
        )
    deltas.sort()
    return {
        "delta": point,
        "ci_low": float(deltas[int(0.025 * draws)]),
        "ci_high": float(deltas[int(0.975 * draws)]),
        "draws": draws,
        "positive": bool(deltas[int(0.025 * draws)] > 0.0),
    }


def _git_commit(repo: Path) -> str:
    return subprocess.run(
        ("git", "rev-parse", "HEAD"),
        cwd=repo,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    ).stdout.strip()


def aggregate(
    *,
    repo: Path,
    runs: Path,
    cv: Path,
    source: Path,
    relation_source: Path,
    draws: int = BOOTSTRAP_DRAWS,
    seed: int = 13,
) -> dict:
    cv_payload = _load(cv)
    folds = {int(row["fold"]): row for row in cv_payload["folds"]}
    _require(sorted(folds) == [1, 2, 3, 4, 5], "CV must hold folds 1 through 5")

    document_ids: list[str] = []
    fold_of: dict[str, int] = {}
    for fold in range(1, 6):
        manifest = repo / folds[fold]["evaluation"]["path"]
        _require(
            sha256_file(manifest) == folds[fold]["evaluation"]["sha256"],
            f"fold {fold}: evaluation manifest hash drift",
        )
        for doc_id in load_manifest_ids(manifest):
            _require(doc_id not in fold_of, f"{doc_id} appears in two evaluation folds")
            fold_of[doc_id] = fold
            document_ids.append(doc_id)
    _require(len(document_ids) == EXPECTED_DOCUMENTS, "pooled OOF document count")

    docs = {doc.doc_id: doc for doc in load_maven_fact(source) if doc.doc_id in fold_of}
    _require(len(docs) == EXPECTED_DOCUMENTS, "source is missing evaluation documents")
    mentions_by_document = {
        doc_id: [mention.mention_id for mention in docs[doc_id].mentions]
        for doc_id in document_ids
    }
    gold = {
        mention.mention_id: mention.factuality
        for doc in docs.values()
        for mention in doc.mentions
    }
    _require(len(gold) == EXPECTED_MENTIONS, "pooled OOF mention count")

    gold_pairs: dict[tuple[str, str], str] = {}
    for doc in load_maven_ere(relation_source):
        if doc.doc_id in fold_of:
            gold_pairs.update(
                gold_pair_labels(doc, family=RelationType.CAUSAL, expand_event_relations=True)
            )

    arms: dict[str, dict] = {}
    matrices: dict[str, np.ndarray] = {}
    input_hashes: dict[str, str] = {str(cv): sha256_file(cv)}
    for arm in ARMS:
        predicted: dict[str, str] = {}
        fold_reports = []
        for fold in range(1, 6):
            run = runs / arm / f"fold-{fold}"
            metadata = _load(run / "run_metadata.json")
            _require(metadata["status"] == "complete", f"{arm} fold {fold} is not complete")
            _require(metadata["arm"] == arm and metadata["fold"] == fold, "run identity drift")
            _require(metadata["final_valid_accessed"] is False, "final-valid was touched")
            report = _load(run / "evaluation_report.json")
            labels = _load(run / "evaluation_labels.json")
            _require(
                report["gold_edges_used_by_model"] is False, "a gold edge reached the model"
            )
            overlap = set(labels) & set(predicted)
            _require(not overlap, f"{arm}: {len(overlap)} mentions scored twice")
            predicted.update(labels)
            fold_reports.append(
                {
                    "fold": fold,
                    "macro_f1": report["macro_f1"],
                    "documents": report["documents"],
                    "mentions": report["mentions"],
                    "edges": report["edges"],
                    "selected_epoch": metadata["selected_epoch"],
                    "mediators": report["mediators"],
                    **({"rewiring": report["rewiring"]} if "rewiring" in report else {}),
                }
            )
            for name in ("run_metadata.json", "evaluation_report.json", "evaluation_labels.json"):
                input_hashes[str(run / name)] = sha256_file(run / name)
        _require(set(predicted) == set(gold), f"{arm}: pooled mention cover mismatch")

        matrix = per_document_matrices(document_ids, mentions_by_document, gold, predicted)
        matrices[arm] = matrix
        side = len(FACTUALITY_LABELS)
        pooled = matrix.sum(axis=0).reshape(side, side)
        arms[arm] = {
            "macro_f1": _macro_f1(pooled),
            "per_class_f1": _class_f1(pooled),
            "accuracy": float(np.trace(pooled) / pooled.sum()),
            "mediators": consistency_violations(gold_pairs, predicted),
            "folds": fold_reports,
        }

    contrasts = {
        "full_minus_base": paired_bootstrap(
            matrices["full"], matrices["base"], draws=draws, seed=seed
        ),
        "full_minus_rewired": paired_bootstrap(
            matrices["full"], matrices["rewired"], draws=draws, seed=seed
        ),
    }

    full = arms["full"]
    mediator_pass = all(
        full["mediators"][subtype]["rate"] < arms["base"]["mediators"][subtype]["rate"]
        for subtype in EDGE_SUBTYPES
    )
    rewired_keeps_mediator = all(
        arms["rewired"]["mediators"][subtype]["rate"]
        < arms["base"]["mediators"][subtype]["rate"]
        for subtype in EDGE_SUBTYPES
    )
    gate = {
        "coverage_pass": True,
        "macro_target_pass": full["macro_f1"] >= MACRO_TARGET,
        "beats_base_pass": contrasts["full_minus_base"]["positive"],
        "beats_rewired_pass": contrasts["full_minus_rewired"]["positive"],
        "rare_class_floor_pass": all(
            full["per_class_f1"][label] >= floor for label, floor in FLOORS.items()
        ),
        "no_class_collapse_pass": all(value > 0.0 for value in full["per_class_f1"].values()),
        "mediator_pass": mediator_pass,
        "rewiring_does_not_reproduce_mediator_pass": not rewired_keeps_mediator,
    }
    gate["necessary_pass"] = all(
        gate[name]
        for name in (
            "macro_target_pass",
            "beats_base_pass",
            "beats_rewired_pass",
            "rare_class_floor_pass",
            "no_class_collapse_pass",
        )
    )
    gate["mechanism_pass"] = gate["necessary_pass"] and mediator_pass and not rewired_keeps_mediator

    return {
        "schema_version": "ekg.d4_predicted_causal_pooled.v1",
        "status": "gate_passed" if gate["necessary_pass"] else "gate_failed",
        "commit": _git_commit(repo),
        "contract": {
            "document": "docs/phases/PHASE_D4_predicted_causal_residual.md",
            "macro_target": MACRO_TARGET,
            "rare_class_floors": FLOORS,
            "bootstrap": "document-cluster paired, 95% CI",
            "bootstrap_draws": draws,
            "anchor_macro_f1": 0.553995,
        },
        "coverage": {"documents": len(document_ids), "mentions": len(gold)},
        "arms": arms,
        "contrasts": contrasts,
        "gate": gate,
        "input_sha256": dict(sorted(input_hashes.items())),
        "command_argv": sys.argv,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--runs", required=True, type=Path, help="seed-13 directory")
    parser.add_argument("--cv", required=True, type=Path)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--relation-source", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--draws", type=int, default=BOOTSTRAP_DRAWS)
    parser.add_argument("--seed", type=int, default=13)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite: {args.output}")
    report = aggregate(
        repo=args.repo.resolve(),
        runs=args.runs.resolve(),
        cv=args.cv.resolve(),
        source=args.source.resolve(),
        relation_source=args.relation_source.resolve(),
        draws=args.draws,
        seed=args.seed,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "status": report["status"],
                "macro_f1": {arm: report["arms"][arm]["macro_f1"] for arm in ARMS},
                "contrasts": report["contrasts"],
                "gate": report["gate"],
                "output_sha256": sha256_file(args.output),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
