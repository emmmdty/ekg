#!/usr/bin/env python
"""CPU text-observation diagnostic within C5 train, without coreference training."""

from __future__ import annotations

import argparse
import hashlib
import json
import warnings
from pathlib import Path

import joblib
import numpy as np
import sklearn
from sklearn.exceptions import ConvergenceWarning
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

from ekg.core.stage_bundle import sha256_file
from ekg.factuality.metrics import factuality_report
from ekg.relations.data.maven_fact import FACTUALITY_LABELS as LABELS


def marked_text(record, mention):
    sent, (start, end) = mention["sent_id"], mention["offset"]
    if not (0 <= sent < len(record["tokens"])
            and 0 <= start < end <= len(record["tokens"][sent])):
        raise ValueError("invalid mention offset")
    tokens = record["tokens"][sent]
    return " ".join([*tokens[:start], "*", *tokens[start:end], "*", *tokens[end:]])


def validate_config(config):
    if (config["schema_version"] != "ekg.c5_factuality_observation_probe.v1"
            or config["diagnostic_only"] is not True or config["final_valid_accessed"] is not False
            or config["seed"] != 13 or config["folds"] != 5
            or config["classifier"]["random_state"] != 13):
        raise ValueError("observation probe role/seed/fold drift")
    if sklearn.__version__ != config["sklearn_version"]:
        raise ValueError("sklearn version differs from frozen config")


def document_folds(examples, seed, folds):
    ids = {example["doc_id"] for example in examples}
    if len(ids) < folds:
        raise ValueError("too few documents for crossfit")
    ordered = sorted(ids, key=lambda doc_id: (
        hashlib.sha256(f"c5-fact-observation-{seed}:{doc_id}".encode()).hexdigest(), doc_id))
    return {doc_id: index % folds for index, doc_id in enumerate(ordered)}


def crossfit(examples, config, output):
    validate_config(config)
    ids = [example["mention_id"] for example in examples]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate mention examples")
    groups = document_folds(examples, config["seed"], config["folds"])
    partitions = []
    for fold in range(config["folds"]):
        train = [row for row in examples if groups[row["doc_id"]] != fold]
        evaluation = [row for row in examples if groups[row["doc_id"]] == fold]
        if set(row["label"] for row in train) != set(LABELS):
            raise ValueError("training fold does not contain all factuality classes")
        partitions.append((train, evaluation))
    output.mkdir(parents=True, exist_ok=False)
    folds, predicted = [], {}
    gold = {example["mention_id"]: example["label"] for example in examples}
    with (output / "probabilities.jsonl").open("x") as handle:
        for fold, (train, evaluation) in enumerate(partitions, 1):
            params = {**config["vectorizer"],
                      "ngram_range": tuple(config["vectorizer"]["ngram_range"])}
            vectorizer = TfidfVectorizer(**params)
            train_features = vectorizer.fit_transform([row["text"] for row in train])
            classifier = LogisticRegression(**config["classifier"])
            with warnings.catch_warnings():
                warnings.simplefilter("error", ConvergenceWarning)
                classifier.fit(train_features, [row["label"] for row in train])
            order = [list(classifier.classes_).index(label) for label in LABELS]
            probabilities = classifier.predict_proba(
                vectorizer.transform([row["text"] for row in evaluation]))[:, order]
            if (not np.isfinite(probabilities).all()
                    or not np.allclose(probabilities.sum(axis=1), 1.0)):
                raise ValueError("invalid factuality probabilities")
            fold_output = output / f"fold-{fold}"
            fold_output.mkdir()
            joblib.dump({"vectorizer": vectorizer, "classifier": classifier,
                         "class_order": list(LABELS)}, fold_output / "model.joblib")
            for example, values in zip(evaluation, probabilities, strict=True):
                label = LABELS[int(values.argmax())]
                predicted[example["mention_id"]] = label
                handle.write(json.dumps({"doc_id": example["doc_id"],
                                         "mention_id": example["mention_id"], "fold": fold,
                                         "label": label, "probabilities": values.tolist()}) + "\n")
            folds.append({"fold": fold,
                          "train_doc_ids": sorted({row["doc_id"] for row in train}),
                          "evaluation_doc_ids": sorted({row["doc_id"] for row in evaluation}),
                          "train_mentions": len(train), "evaluation_mentions": len(evaluation),
                          "vocabulary": len(vectorizer.vocabulary_),
                          "iterations": classifier.n_iter_.tolist(),
                          "model_sha256": sha256_file(fold_output / "model.joblib")})
            print(f"fold {fold}: train={len(train)} evaluation={len(evaluation)}", flush=True)
    if set(predicted) != set(gold):
        raise ValueError("OOF mention coverage mismatch")
    summary = {"schema_version": "ekg.c5_factuality_observation_result.v1",
               "diagnostic_only": True, "final_valid_accessed": False, "seed": 13,
               "documents": len(groups), "mentions": len(examples), "folds": folds,
               "class_order": list(LABELS), "factuality_diagnostic": factuality_report(
                   predicted, gold), "consumer_evaluation_labels_accessed": False,
               "probabilities_sha256": sha256_file(output / "probabilities.jsonl"),
               "limitations": ["Classic lexical auxiliary observer; not a new factuality method",
                                "No coreference prediction, main score or method admission",
                                "Only C5 train document folds; no consumer dev/final input",
                                "Local CPU models remain local; no checkpoint transfer"]}
    with (output / "summary.json").open("x") as handle:
        json.dump(summary, handle, indent=2, sort_keys=True)
    return summary


def main():
    from report_factuality_identity_signal import load_train, validate_manifest

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    validate_config(config)
    for path, expected in config["input_sha256"].items():
        if sha256_file(Path(path)) != expected:
            raise ValueError(f"input hash drift: {path}")
    records = load_train(Path(config["source"]), Path(config["manifest"]), "maven_fact")
    consumer_manifest = json.loads(Path(config["consumer_train_manifest"]).read_text())
    consumer_ids = validate_manifest(consumer_manifest, "maven_ere")
    if set(records) != consumer_ids:
        raise ValueError("consumer train document coverage mismatch")
    examples = []
    for doc_id, record in sorted(records.items()):
        for event in record["events"]:
            for mention in event["mention"]:
                examples.append({"doc_id": doc_id, "mention_id": f"{doc_id}::{mention['id']}",
                                 "text": marked_text(record, mention),
                                 "label": mention["factuality"]})
    output = Path(config["output"])
    result = crossfit(examples, config, output)
    provenance = {"config_sha256": sha256_file(args.config),
                  "script_sha256": sha256_file(Path(__file__)),
                  "loader_sha256": sha256_file(Path(__file__).with_name(
                      "report_factuality_identity_signal.py")),
                  "sklearn_version": sklearn.__version__, "input_sha256": config["input_sha256"],
                  "summary_sha256": sha256_file(output / "summary.json")}
    with (output / "provenance.json").open("x") as handle:
        json.dump(provenance, handle, indent=2, sort_keys=True)
    print(json.dumps({key: result[key] for key in
                      ("documents", "mentions", "factuality_diagnostic")}, indent=2))


if __name__ == "__main__":
    main()
