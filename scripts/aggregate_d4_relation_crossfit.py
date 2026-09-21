#!/usr/bin/env python
"""Aggregate the five frozen D4 relation cross-fit posterior folds.

This is an evaluator, not an inference component.  Gold causal labels are read
only after all fold outputs exist, then used to measure exhaustive OOF relation
quality and calibration.  Structural drift is fatal; a scientific quality-gate
failure is still written as a valid negative result.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from ekg.core.protocol import load_manifest_ids
from ekg.core.schema import RelationType
from ekg.core.stage_bundle import sha256_file
from ekg.relations.data.maven_ere import RelationDocument, load_maven_ere
from ekg.relations.pairs import candidate_pairs, gold_pair_labels

CLASSES = ("NONE", "CAUSE", "PRECONDITION")
PROBABILITY_FIELDS = ("p_none", "p_cause", "p_precondition")
ROW_FIELDS = {
    "doc_id",
    "head_mention_id",
    "tail_mention_id",
    *PROBABILITY_FIELDS,
}


class D4QualityError(ValueError):
    """A fold artifact differs from the frozen D4 input-quality protocol."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise D4QualityError(message)


def _load_object(path: Path) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise D4QualityError(f"missing artifact: {path}") from exc
    if not isinstance(payload, dict):
        raise D4QualityError(f"{path} must contain a JSON object")
    return payload


def _git_commit(repo: Path) -> str:
    return subprocess.run(
        ("git", "rev-parse", "HEAD"),
        cwd=repo,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    ).stdout.strip()


@dataclass
class ScoreAccumulator:
    rows: int = 0
    label_counts: list[int] = field(default_factory=lambda: [0, 0, 0])
    prediction_counts: list[int] = field(default_factory=lambda: [0, 0, 0])
    true_positive: int = 0
    false_positive: int = 0
    false_negative: int = 0
    brier_sum: float = 0.0

    def add(self, probabilities: tuple[float, float, float], gold_index: int) -> None:
        prediction = max(range(len(CLASSES)), key=probabilities.__getitem__)
        self.rows += 1
        self.label_counts[gold_index] += 1
        self.prediction_counts[prediction] += 1
        self.true_positive += int(gold_index > 0 and prediction == gold_index)
        self.false_positive += int(prediction > 0 and prediction != gold_index)
        self.false_negative += int(gold_index > 0 and prediction != gold_index)
        self.brier_sum += sum(
            (probability - float(index == gold_index)) ** 2
            for index, probability in enumerate(probabilities)
        )

    def merge(self, other: ScoreAccumulator) -> None:
        self.rows += other.rows
        for index in range(len(CLASSES)):
            self.label_counts[index] += other.label_counts[index]
            self.prediction_counts[index] += other.prediction_counts[index]
        self.true_positive += other.true_positive
        self.false_positive += other.false_positive
        self.false_negative += other.false_negative
        self.brier_sum += other.brier_sum

    def metrics(self) -> dict:
        _require(self.rows > 0, "cannot score an empty posterior population")
        tp, fp, fn = self.true_positive, self.false_positive, self.false_negative
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0.0
        prevalence = [count / self.rows for count in self.label_counts]
        no_skill = 1.0 - sum(value**2 for value in prevalence)
        return {
            "rows": self.rows,
            "label_counts": dict(zip(CLASSES, self.label_counts, strict=True)),
            "prediction_counts": dict(
                zip(CLASSES, self.prediction_counts, strict=True)
            ),
            "causal_positive": {
                "true_positive": tp,
                "false_positive": fp,
                "false_negative": fn,
                "precision": precision,
                "recall": recall,
                "f1": f1,
            },
            "multiclass_brier": {
                "model": self.brier_sum / self.rows,
                "evaluation_prevalence_no_skill": no_skill,
                "model_minus_no_skill": self.brier_sum / self.rows - no_skill,
                "prevalence": dict(zip(CLASSES, prevalence, strict=True)),
            },
        }


def _probabilities(row: dict, *, location: str) -> tuple[float, float, float]:
    _require(set(row) == ROW_FIELDS, f"{location}: posterior row fields drifted")
    values: list[float] = []
    for field_name in PROBABILITY_FIELDS:
        raw = row[field_name]
        _require(
            isinstance(raw, (int, float)) and not isinstance(raw, bool),
            f"{location}: {field_name} is not numeric",
        )
        value = float(raw)
        _require(math.isfinite(value), f"{location}: non-finite probability")
        _require(0.0 <= value <= 1.0, f"{location}: probability outside [0, 1]")
        values.append(value)
    _require(
        abs(math.fsum(values) - 1.0) <= 1e-6,
        f"{location}: probabilities do not sum to one",
    )
    return values[0], values[1], values[2]


def _posterior_rows(path: Path):
    try:
        handle = path.open(encoding="utf-8")
    except FileNotFoundError as exc:
        raise D4QualityError(f"missing posterior: {path}") from exc
    with handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                raise D4QualityError(f"{path}:{line_number}: blank posterior row")
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise D4QualityError(f"{path}:{line_number}: invalid JSON") from exc
            if not isinstance(row, dict):
                raise D4QualityError(f"{path}:{line_number}: row is not an object")
            yield line_number, row


def _validate_fold_metadata(
    *,
    fold: int,
    row: dict,
    plan_hash: str,
    source_hash: str,
    manifest_path: Path,
    posterior_path: Path,
) -> tuple[dict, dict]:
    run_dir = posterior_path.parent
    run = _load_object(run_dir / "run_metadata.json")
    posterior = _load_object(run_dir / "causal_posteriors.metadata.json")
    posterior_hash = sha256_file(posterior_path)
    posterior_metadata_hash = sha256_file(
        run_dir / "causal_posteriors.metadata.json"
    )

    _require(run.get("status") == "complete", f"fold {fold}: run is not complete")
    _require(run.get("fold") == fold, f"fold {fold}: run fold mismatch")
    _require(run.get("seed") == row.get("seed") == 13, f"fold {fold}: seed drift")
    _require(run.get("plan_sha256") == plan_hash, f"fold {fold}: plan hash drift")
    _require(run.get("source_sha256") == source_hash, f"fold {fold}: source hash drift")
    _require(
        run.get("manifest_sha256", {}).get("evaluation")
        == sha256_file(manifest_path),
        f"fold {fold}: evaluation manifest hash drift",
    )
    _require(
        run.get("selection_uses_evaluation") is False,
        f"fold {fold}: evaluation participated in selection",
    )
    _require(
        run.get("final_valid_accessed") is False,
        f"fold {fold}: final-valid was accessed",
    )
    train_argv = [str(item) for item in run.get("train_argv", [])]
    dump_argv = [str(item) for item in run.get("dump_argv", [])]
    _require(
        str(manifest_path) not in train_argv,
        f"fold {fold}: evaluation manifest appears in trainer argv",
    )
    _require(
        str(manifest_path) in dump_argv,
        f"fold {fold}: evaluation manifest absent from dumper argv",
    )
    expected = row["expected_output"]
    _require(
        run.get("posterior", {}).get("documents") == expected["documents"],
        f"fold {fold}: run document count drift",
    )
    _require(
        run.get("posterior", {}).get("ordered_mention_pairs")
        == expected["ordered_mention_pairs"],
        f"fold {fold}: run pair count drift",
    )
    _require(
        run.get("posterior", {}).get("sha256") == posterior_hash,
        f"fold {fold}: run posterior hash drift",
    )
    artifacts = run.get("artifacts_sha256", {})
    _require(
        artifacts.get("causal_posteriors.jsonl") == posterior_hash,
        f"fold {fold}: posterior artifact hash drift",
    )
    _require(
        artifacts.get("causal_posteriors.metadata.json") == posterior_metadata_hash,
        f"fold {fold}: posterior metadata hash drift",
    )

    _require(
        posterior.get("schema_version") == "ekg.relation_causal_posteriors.v1",
        f"fold {fold}: posterior schema drift",
    )
    _require(
        posterior.get("gold_fields_present") is False,
        f"fold {fold}: posterior metadata reports gold fields",
    )
    _require(
        posterior.get("class_order") == list(CLASSES),
        f"fold {fold}: posterior class order drift",
    )
    _require(
        posterior.get("documents") == expected["documents"],
        f"fold {fold}: posterior document count drift",
    )
    _require(
        posterior.get("ordered_mention_pairs") == expected["ordered_mention_pairs"],
        f"fold {fold}: posterior pair count drift",
    )
    _require(
        posterior.get("output_sha256") == posterior_hash,
        f"fold {fold}: posterior metadata output hash drift",
    )
    return run, posterior


def _score_fold(
    *,
    fold: int,
    docs: dict[str, RelationDocument],
    document_ids: list[str],
    posterior_path: Path,
) -> ScoreAccumulator:
    accumulator = ScoreAccumulator()
    rows = iter(_posterior_rows(posterior_path))
    for doc_id in document_ids:
        _require(doc_id in docs, f"fold {fold}: {doc_id} is absent from source")
        doc = docs[doc_id]
        gold = gold_pair_labels(
            doc,
            family=RelationType.CAUSAL,
            expand_event_relations=True,
        )
        for head, tail in candidate_pairs(doc):
            try:
                line_number, row = next(rows)
            except StopIteration as exc:
                raise D4QualityError(f"fold {fold}: posterior ended early") from exc
            location = f"{posterior_path}:{line_number}"
            _require(
                (row.get("doc_id"), row.get("head_mention_id"), row.get("tail_mention_id"))
                == (doc_id, head, tail),
                f"{location}: posterior candidate/order mismatch",
            )
            label = gold.get((head, tail), "NONE")
            _require(label in CLASSES, f"{location}: unknown gold causal label {label}")
            accumulator.add(_probabilities(row, location=location), CLASSES.index(label))
    try:
        line_number, _ = next(rows)
    except StopIteration:
        return accumulator
    raise D4QualityError(f"{posterior_path}:{line_number}: unexpected extra row")


def aggregate_quality(
    *,
    repo: Path,
    plan_path: Path,
    expected_documents: int = 2913,
    expected_mentions: int = 73939,
    expected_pairs: int = 2532394,
    minimum_causal_f1: float = 0.300,
) -> dict:
    repo = repo.resolve()
    plan_path = plan_path.resolve()
    plan = _load_object(plan_path)
    _require(
        plan.get("schema_version") == "r1-v62-d4-crossfit-plan-v2",
        "D4 cross-fit plan schema mismatch",
    )
    plan_hash = sha256_file(plan_path)
    source_entry = plan.get("inputs", {}).get("ere_train", {})
    source_path = (repo / source_entry.get("path", "")).resolve()
    _require(source_path.is_file(), "registered MAVEN-ERE source is missing")
    source_hash = sha256_file(source_path)
    _require(source_hash == source_entry.get("sha256"), "source hash mismatch")

    documents = list(load_maven_ere(source_path))
    docs = {doc.doc_id: doc for doc in documents}
    _require(len(docs) == len(documents), "source contains duplicate document IDs")
    fold_rows = plan.get("folds", [])
    _require(
        [item.get("fold") for item in fold_rows] == [1, 2, 3, 4, 5],
        "cross-fit plan must contain folds 1 through 5 in order",
    )

    pooled = ScoreAccumulator()
    observed_documents: set[str] = set()
    fold_reports: list[dict] = []
    input_hashes: dict[str, str] = {
        str(source_path): source_hash,
        str(plan_path): plan_hash,
    }
    for row in fold_rows:
        fold = int(row["fold"])
        manifest_entry = row["manifests"]["evaluation"]
        manifest_path = (repo / manifest_entry["path"]).resolve()
        _require(manifest_path.is_file(), f"fold {fold}: evaluation manifest missing")
        manifest_hash = sha256_file(manifest_path)
        _require(
            manifest_hash == manifest_entry["sha256"],
            f"fold {fold}: evaluation manifest hash mismatch",
        )
        document_ids = load_manifest_ids(manifest_path)
        _require(
            len(document_ids) == row["expected_output"]["documents"],
            f"fold {fold}: evaluation document count mismatch",
        )
        overlap = observed_documents.intersection(document_ids)
        _require(not overlap, f"fold {fold}: repeated evaluation documents")
        observed_documents.update(document_ids)

        posterior_path = (plan_path.parent / row["expected_output"]["path"]).resolve()
        run, posterior = _validate_fold_metadata(
            fold=fold,
            row=row,
            plan_hash=plan_hash,
            source_hash=source_hash,
            manifest_path=manifest_path,
            posterior_path=posterior_path,
        )
        score = _score_fold(
            fold=fold,
            docs=docs,
            document_ids=document_ids,
            posterior_path=posterior_path,
        )
        _require(
            score.rows == row["expected_output"]["ordered_mention_pairs"],
            f"fold {fold}: scored pair count mismatch",
        )
        pooled.merge(score)
        run_dir = posterior_path.parent
        input_hashes[str(manifest_path)] = manifest_hash
        input_hashes[str(posterior_path)] = sha256_file(posterior_path)
        input_hashes[str(run_dir / "run_metadata.json")] = sha256_file(
            run_dir / "run_metadata.json"
        )
        input_hashes[str(run_dir / "causal_posteriors.metadata.json")] = sha256_file(
            run_dir / "causal_posteriors.metadata.json"
        )
        fold_reports.append(
            {
                "fold": fold,
                "documents": len(document_ids),
                "mentions": sum(len(docs[doc_id].nodes) for doc_id in document_ids),
                "metrics": score.metrics(),
                "run_commit": run.get("commit"),
                "posterior_sha256": posterior["output_sha256"],
            }
        )

    _require(observed_documents == set(docs), "five folds do not cover the source exactly")
    mention_count = sum(len(docs[doc_id].nodes) for doc_id in observed_documents)
    coverage = {
        "documents": len(observed_documents),
        "mentions": mention_count,
        "ordered_mention_pairs": pooled.rows,
    }
    expected = {
        "documents": expected_documents,
        "mentions": expected_mentions,
        "ordered_mention_pairs": expected_pairs,
    }
    coverage_pass = coverage == expected
    pooled_metrics = pooled.metrics()
    causal_f1 = pooled_metrics["causal_positive"]["f1"]
    brier = pooled_metrics["multiclass_brier"]
    causal_pass = causal_f1 >= minimum_causal_f1
    brier_pass = brier["model"] < brier["evaluation_prevalence_no_skill"]
    gate = {
        "coverage_pass": coverage_pass,
        "no_gold_fields_pass": True,
        "causal_f1_pass": causal_pass,
        "multiclass_brier_pass": brier_pass,
        "passed": coverage_pass and causal_pass and brier_pass,
    }
    return {
        "schema_version": "ekg.d4_relation_crossfit_quality.v1",
        "status": "quality_gate_passed" if gate["passed"] else "quality_gate_failed",
        "scientific_result": True,
        "gold_used_for_evaluation_only": True,
        "commit": _git_commit(repo),
        "contract": {
            "class_order": list(CLASSES),
            "hard_prediction": "argmax with class-order tie break",
            "causal_positive_f1": "micro exact-subtype F1 over CAUSE/PRECONDITION",
            "minimum_causal_f1": minimum_causal_f1,
            "multiclass_brier": "mean per-pair sum_k (p_k - y_k)^2",
            "brier_baseline": "constant pooled evaluation-label prevalence",
            "expected_coverage": expected,
        },
        "coverage": coverage,
        "folds": fold_reports,
        "pooled_metrics": pooled_metrics,
        "gate": gate,
        "input_sha256": dict(sorted(input_hashes.items())),
        "command_argv": sys.argv,
    }


def _write_report(report: dict, output: Path) -> None:
    if output.exists():
        raise FileExistsError(f"refusing to overwrite quality report: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=output.parent,
        prefix=f".{output.name}.",
        suffix=".tmp",
        delete=False,
    ) as handle:
        temporary = Path(handle.name)
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")
    try:
        os.replace(temporary, output)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    report = aggregate_quality(repo=args.repo, plan_path=args.plan)
    _write_report(report, args.output)
    print(
        json.dumps(
            {
                "status": report["status"],
                "coverage": report["coverage"],
                "causal_f1": report["pooled_metrics"]["causal_positive"]["f1"],
                "multiclass_brier": report["pooled_metrics"]["multiclass_brier"],
                "output": str(args.output),
                "output_sha256": sha256_file(args.output),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
