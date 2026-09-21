#!/usr/bin/env python
"""Error attribution for a finished D4 v6.2 run: does the residual help where it reaches?

A mention with no incoming decided edge gets an exactly zero residual, so `full`
and `base` can only differ there through training noise. Splitting the pooled
OOF mentions by in-degree therefore separates two very different failures:

* `full` loses even on the mentions it reaches  -> the structural input is the
  problem (wrong edges, or the message carries nothing);
* `full` wins where it reaches but loses overall -> the reach is too small, or
  the extra parameters cost accuracy on the untouched majority.

Edge precision against the gold-expanded pairs is reported alongside, because a
message passed over mostly-wrong edges is the first thing to suspect. Gold is
read for scoring only and never enters a model.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from ekg.core.protocol import load_manifest_ids
from ekg.core.schema import RelationType
from ekg.core.stage_bundle import sha256_file
from ekg.factuality.causal_residual import ARMS, decide_edges
from ekg.factuality.metrics import factuality_report
from ekg.relations.data.maven_ere import load_maven_ere
from ekg.relations.data.maven_fact import load_maven_fact
from ekg.relations.pairs import gold_pair_labels

STRATA = ("in_degree_0", "in_degree_1", "in_degree_2plus")


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _stratum(in_degree: int) -> str:
    if in_degree == 0:
        return STRATA[0]
    return STRATA[1] if in_degree == 1 else STRATA[2]


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


def attribute(
    *,
    repo: Path,
    runs: Path,
    crossfit: Path,
    cv: Path,
    source: Path,
    relation_source: Path,
) -> dict:
    folds = {int(row["fold"]): row for row in _load(cv)["folds"]}
    in_degree: dict[str, int] = {}
    correct_in_degree: dict[str, int] = {}
    edges_total = 0
    edges_correct = 0

    gold_pairs: dict[str, dict[tuple[str, str], str]] = {}
    for doc in load_maven_ere(relation_source):
        gold_pairs[doc.doc_id] = gold_pair_labels(
            doc, family=RelationType.CAUSAL, expand_event_relations=True
        )

    for fold in range(1, 6):
        manifest = repo / folds[fold]["evaluation"]["path"]
        wanted = set(load_manifest_ids(manifest))
        calibration = _load(crossfit / f"fold-{fold}" / "dirichlet_calibration.metadata.json")
        sidecar = crossfit / f"fold-{fold}" / "dirichlet_causal_posteriors.jsonl"
        for doc_id, rows in _sidecar_documents(sidecar):
            if doc_id not in wanted:
                raise ValueError(f"fold {fold}: {doc_id} is outside the evaluation manifest")
            gold = gold_pairs.get(doc_id, {})
            for edge in decide_edges(rows, calibration["class_weights"]):
                edges_total += 1
                tail = edge.tail_mention_id
                in_degree[tail] = in_degree.get(tail, 0) + 1
                if gold.get((edge.head_mention_id, tail)) == edge.subtype:
                    edges_correct += 1
                    correct_in_degree[tail] = correct_in_degree.get(tail, 0) + 1

    docs = {doc.doc_id: doc for doc in load_maven_fact(source)}
    gold_labels = {
        mention.mention_id: mention.factuality
        for doc in docs.values()
        for mention in doc.mentions
    }
    predictions: dict[str, dict[str, str]] = {}
    for arm in ARMS:
        pooled: dict[str, str] = {}
        for fold in range(1, 6):
            pooled.update(_load(runs / arm / f"fold-{fold}" / "evaluation_labels.json"))
        predictions[arm] = pooled

    scored = set(predictions["base"])
    strata_members: dict[str, list[str]] = {name: [] for name in STRATA}
    for mention_id in scored:
        strata_members[_stratum(in_degree.get(mention_id, 0))].append(mention_id)

    report: dict = {
        "schema_version": "ekg.d4_predicted_causal_attribution.v1",
        "commit": subprocess.run(
            ("git", "rev-parse", "HEAD"),
            cwd=repo,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
        ).stdout.strip(),
        "runs": str(runs),
        "edges": {
            "decided": edges_total,
            "gold_exact_subtype": edges_correct,
            "precision": edges_correct / edges_total if edges_total else 0.0,
        },
        "mentions": {
            "scored": len(scored),
            "with_incoming_edge": sum(
                1 for mention_id in scored if in_degree.get(mention_id, 0)
            ),
            "with_a_correct_incoming_edge": sum(
                1 for mention_id in scored if correct_in_degree.get(mention_id, 0)
            ),
        },
        "strata": {},
    }
    for name, members in strata_members.items():
        gold_slice = {mention_id: gold_labels[mention_id] for mention_id in members}
        entry: dict = {"mentions": len(members)}
        if members:
            for arm in ARMS:
                arm_slice = {mention_id: predictions[arm][mention_id] for mention_id in members}
                scores = factuality_report(arm_slice, gold_slice)
                entry[arm] = {
                    "macro_f1": scores["macro_f1"],
                    "accuracy": scores["accuracy"],
                }
            entry["full_minus_base_accuracy"] = (
                entry["full"]["accuracy"] - entry["base"]["accuracy"]
            )
            entry["full_vs_base_disagreements"] = sum(
                1
                for mention_id in members
                if predictions["full"][mention_id] != predictions["base"][mention_id]
            )
            entry["full_right_base_wrong"] = sum(
                1
                for mention_id in members
                if predictions["full"][mention_id] == gold_labels[mention_id]
                and predictions["base"][mention_id] != gold_labels[mention_id]
            )
            entry["base_right_full_wrong"] = sum(
                1
                for mention_id in members
                if predictions["base"][mention_id] == gold_labels[mention_id]
                and predictions["full"][mention_id] != gold_labels[mention_id]
            )
        report["strata"][name] = entry
    report["command_argv"] = sys.argv
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--runs", required=True, type=Path)
    parser.add_argument("--crossfit", required=True, type=Path)
    parser.add_argument("--cv", required=True, type=Path)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--relation-source", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite: {args.output}")
    report = attribute(
        repo=args.repo.resolve(),
        runs=args.runs.resolve(),
        crossfit=args.crossfit.resolve(),
        cv=args.cv.resolve(),
        source=args.source.resolve(),
        relation_source=args.relation_source.resolve(),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({**report, "output_sha256": sha256_file(args.output)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
