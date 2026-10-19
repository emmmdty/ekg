"""Describe cached causal errors on train/internal-dev without changing predictions.

Subtype errors take priority when a wrong same-direction edge and a reverse edge
coexist. Overlap counts retain the reverse edge; they are not additional errors.
Annotation-NONE is not a world negative. No model, threshold or oracle correction.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

from ekg.core.stage_bundle import sha256_file
from ekg.relations.maven_ere_official import (
    OfficialProtocolError,
    gold_to_official_prediction,
    records_by_id,
    validate_official_predictions,
)

LABELS = ("NONE", "PRECONDITION", "CAUSE")
KINDS = (
    "same_direction_wrong_subtype", "reverse_only_same_subtype",
    "reverse_only_wrong_subtype", "neither_direction_positive",
)


def _labels(record: dict) -> dict[tuple[str, str], str]:
    result = {}
    for subtype, pairs in record["causal_relations"].items():
        for head, tail in pairs:
            pair = (head, tail)
            if pair in result and result[pair] != subtype:
                raise OfficialProtocolError(f"{record['id']}: overlapping causal subtypes {pair}")
            result[pair] = subtype
    return result


def _kind(pair: tuple[str, str], label: str, other: dict) -> str:
    if pair in other:
        return "same_direction_wrong_subtype"
    reverse_label = other.get((pair[1], pair[0]))
    if reverse_label == label:
        return "reverse_only_same_subtype"
    if reverse_label is not None:
        return "reverse_only_wrong_subtype"
    return "neither_direction_positive"


def profile(
    gold: dict, predictions: dict, *, expected_candidate_digest: str | None = None,
) -> dict:
    population = validate_official_predictions(
        gold, predictions, expected_candidate_digest=expected_candidate_digest,
    )
    confusion = [[0] * 3 for _ in range(3)]
    total: Counter = Counter()
    false_negative = Counter(dict.fromkeys(KINDS, 0))
    false_positive = Counter(dict.fromkeys(KINDS, 0))
    documents = []
    for doc_id in sorted(gold):
        g = _labels(gold_to_official_prediction(gold[doc_id]))
        p = _labels(predictions[doc_id])
        fn = Counter(dict.fromkeys(KINDS, 0))
        fp = Counter(dict.fromkeys(KINDS, 0))
        overlap_fn = overlap_fp = 0
        for pair in g.keys() | p.keys():
            a, b = g.get(pair, "NONE"), p.get(pair, "NONE")
            confusion[LABELS.index(a)][LABELS.index(b)] += 1
            if a == b:
                continue
            reverse = (pair[1], pair[0])
            if pair in g:
                fn[_kind(pair, a, p)] += 1
                overlap_fn += int(reverse in p)
            if pair in p:
                fp[_kind(pair, b, g)] += 1
                overlap_fp += int(reverse in g)
        counts = {
            "gold_positive": len(g), "predicted_positive": len(p),
            "true_positive": sum(p.get(pair) == label for pair, label in g.items()),
            "fn_with_any_reverse_prediction": overlap_fn,
            "fp_with_any_reverse_annotation": overlap_fp,
        }
        total.update(counts)
        false_negative.update(fn)
        false_positive.update(fp)
        documents.append({
            "doc_id": doc_id, **counts, "false_negative": dict(fn), "false_positive": dict(fp),
        })
    confusion[0][0] = population["relation_pairs"] - sum(map(sum, confusion))
    return {
        "schema_version": "ekg.a4_direction_error_profile.v1", "diagnostic_only": True,
        "population": population, "confusion_order": list(LABELS), "confusion": confusion,
        "total": {**total, "false_negative": dict(false_negative),
                  "false_positive": dict(false_positive)},
        "documents": documents,
        "limitations": [
            "Descriptive errors, not causal effects, correctability or a new primary metric.",
            "Gold identity is used only for diagnostic expansion, never inference input.",
            "Neither-direction-positive FP means annotation-NONE, not a world negative.",
            "Reverse overlap counts are subsets, not additional false positives/negatives.",
            "Training fit does not establish held-out generalization.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("gold", "pred", "manifest", "output"):
        parser.add_argument(f"--{name}", required=True, type=Path)
    parser.add_argument("--candidate-digest", required=True)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text())
    if manifest["split_role"] not in ("train", "internal-dev"):
        raise SystemExit("Only train or internal-dev manifests are allowed")
    paths = {name: getattr(args, name) for name in ("gold", "pred", "manifest")}
    records = {
        name: records_by_id(
            (json.loads(line) for line in paths[name].read_text().splitlines() if line.strip()),
            source=str(paths[name]),
        ) for name in ("gold", "pred")
    }
    ids = manifest["doc_ids"]
    if len(set(ids)) != len(ids) or len(ids) != manifest["doc_count"]:
        raise SystemExit("Manifest document count or duplicate IDs are invalid")
    if set(ids) != set(records["gold"]):
        raise SystemExit("Gold document IDs differ from manifest")
    report = profile(
        records["gold"], records["pred"], expected_candidate_digest=args.candidate_digest,
    )
    report.update({
        "split_role": manifest["split_role"], "command_argv": sys.argv,
        "inputs": {name: {"path": str(path), "sha256": sha256_file(path)}
                   for name, path in paths.items()},
        "script_sha256": sha256_file(Path(__file__)),
    })
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report["total"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
