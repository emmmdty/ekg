#!/usr/bin/env python
"""Run the frozen G-19 EasyECR Global-Local Topic transparent adaptation.

The runner deliberately has no labelled evaluation argument.  Its only
evaluation input is the test-shaped file made by
``prepare_easyecr_glt_preflight.py``.  Exporting official predictions and
scoring are separate post-prediction steps, so selection and inference cannot
read the 291-document evaluation labels.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

EXPECTED_P1_PROTOCOL_SHA256 = "1e31a9acef39261f776f7ed4069fd73f4531e8d12b55779bfc0fbd74c67f9655"
SEED = 13
THRESHOLDS = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]


class G19RunError(ValueError):
    """A G-19 run input does not meet the frozen transparent-adaptation protocol."""


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise G19RunError(f"cannot read JSON object: {path}") from exc
    if not isinstance(payload, dict):
        raise G19RunError(f"{path} must contain a JSON object")
    return payload


def _validate_preflight(path: Path) -> dict[str, Path]:
    report = _read_json(path)
    if report.get("schema_version") != "ekg.easyecr_glt_preflight.v2":
        raise G19RunError("preflight schema is not the frozen G-19 version")
    if report.get("p1_protocol_sha256") != EXPECTED_P1_PROTOCOL_SHA256:
        raise G19RunError("preflight has the wrong P1 trust root")
    if report.get("evaluation_gold_access") is not False:
        raise G19RunError("G-19 evaluation input must not expose gold labels")
    if report.get("split_counts") != {
        "evaluation": 291,
        "selection_dev": 291,
        "training": 2331,
    }:
        raise G19RunError("preflight split counts differ from the frozen G-19 contract")

    root = path.parent
    names = {
        "train": "train.jsonl",
        "selection": "selection-valid.jsonl",
        "evaluation": "evaluation-test.jsonl",
    }
    artifact_hashes = report.get("artifact_sha256")
    if not isinstance(artifact_hashes, dict):
        raise G19RunError("preflight is missing artifact hashes")
    paths = {key: root / filename for key, filename in names.items()}
    for key, input_path in paths.items():
        if not input_path.is_file():
            raise G19RunError(f"missing frozen {key} input: {input_path}")
        report_key = "selection_dev" if key == "selection" else (
            "evaluation_test" if key == "evaluation" else key
        )
        if sha256_file(input_path) != artifact_hashes.get(report_key):
            raise G19RunError(f"{key} input digest differs from its preflight record")
    return paths


def _require_model_assets(doc_encoder: Path, mention_encoder: Path) -> None:
    for directory, label in ((doc_encoder, "Longformer"), (mention_encoder, "BERT")):
        missing = [
            name
            for name in ("config.json", "pytorch_model.bin")
            if not (directory / name).is_file()
        ]
        if missing:
            raise G19RunError(
                f"{label} asset is incomplete at {directory}: missing {', '.join(missing)}"
            )


def _configure_upstream_tempdir(output: Path) -> Path:
    """Override EasyECR's uncreated hard-coded global tempfile directory.

    ``easyecr.common.common_path`` assigns ``/home/nobody/code/tmp/`` without
    creating it.  PyTorch Lightning imports distributed utilities that create
    a TemporaryDirectory, so the assignment must be replaced before importing
    Global-Local Topic (and thus Lightning).  This is process-local runtime
    plumbing, not an EasyECR model or protocol change.
    """
    temporary_directory = output / "temporary"
    temporary_directory.mkdir(parents=True, exist_ok=False)
    tempfile.tempdir = str(temporary_directory)
    return temporary_directory


@contextmanager
def _run_in_output_directory(output: Path) -> Iterator[None]:
    """Contain EasyECR's unconfigured prediction-time Lightning logs.

    The upstream prediction method constructs another Trainer instead of using
    the frozen trainer parameters.  Its default relative ``lightning_logs``
    path must therefore be rooted at this immutable run output, rather than
    the repository root.  The current directory is restored even if prediction
    fails.
    """
    original_directory = Path.cwd()
    os.chdir(output)
    try:
        yield
    finally:
        os.chdir(original_directory)


def _take_documents(data: Any, count: int) -> Any:
    """Return a one-document EcrData view for a non-result CUDA smoke."""
    if count < 1:
        raise G19RunError("smoke document count must be positive")
    doc_ids = list(data.documents)[:count]
    if len(doc_ids) != count:
        raise G19RunError(
            f"cannot take {count} documents from a {len(data.documents)}-document input"
        )
    selected = set(doc_ids)
    mentions = {
        mention_id: item for mention_id, item in data.mentions.items() if item.doc_id in selected
    }
    if not mentions:
        raise G19RunError("smoke subset has no event mentions")
    events = None if data.events is None else [
        event for event in data.events if any(item.doc_id in selected for item in event.mentions)
    ]
    from easyecr.ecr_data.data_structure.data_structure import EcrData

    return EcrData(
        name=data.name,
        documents={doc_id: data.documents[doc_id] for doc_id in doc_ids},
        mentions=mentions,
        events=events,
        meta=data.meta,
    )


def _trainer_parameters(output: Path, *, smoke: bool) -> dict[str, Any]:
    parameters: dict[str, Any] = {
        "accelerator": "gpu",
        "devices": 1,
        "accumulate_grad_batches": 20,
        "gradient_clip_val": 10.0,
        "check_val_every_n_epoch": 1,
        "num_sanity_val_steps": 0,
        "max_epochs": 30,
        "default_root_dir": str(output / "lightning"),
        "logger": False,
        "enable_progress_bar": True,
    }
    if smoke:
        parameters.update(
            {
                "max_epochs": 1,
                "limit_train_batches": 1,
                "limit_val_batches": 1,
            }
        )
    return parameters


def _model_conf(
    *,
    doc_encoder: Path,
    mention_encoder: Path,
    trainer_parameters: dict[str, Any],
) -> dict[str, Any]:
    return {
        "seed": SEED,
        "module": {
            "doc_encoder": str(doc_encoder),
            "mention_encoder": str(mention_encoder),
            "num_classes": 169,
            "weight_decay": 0.05,
            "optimizer": "adam",
            "learning_rate": 0.000001,
            "num_warmup_steps": 0.0,
            "adam_beta1": 0.9,
            "adam_beta2": 0.98,
            "adam_epsilon": 0.00000001,
        },
        "dataloader": {
            "train_batch_size": 1,
            "evaluate_batch_size": 1,
            "predict_batch_size": 1,
            "num_workers": 0,
        },
        "trainer_parameters": trainer_parameters,
    }


def _raw_clusters(predicted: Any, expected: Any, output_tag: str) -> list[dict[str, Any]]:
    """Serialize every mention's predicted connected component without gold input."""
    expected_ids = set(expected.mentions)
    actual_ids = set(predicted.mentions)
    if actual_ids != expected_ids:
        raise G19RunError(
            "prediction coverage differs from frozen unlabeled evaluation mentions: "
            f"missing={len(expected_ids - actual_ids)} extra={len(actual_ids - expected_ids)}"
        )
    by_doc: dict[str, dict[str, list[str]]] = {}
    for mention_id, mention in predicted.mentions.items():
        if output_tag not in mention.meta:
            raise G19RunError(f"prediction has no cluster label for mention {mention_id}")
        clusters = by_doc.setdefault(mention.doc_id, {})
        clusters.setdefault(str(mention.meta[output_tag]), []).append(mention_id)

    rows: list[dict[str, Any]] = []
    for doc_id in expected.documents:
        clusters = by_doc.get(doc_id)
        if clusters is None:
            raise G19RunError(f"prediction omitted document {doc_id}")
        assigned = sorted(mention_id for group in clusters.values() for mention_id in group)
        expected_doc_mentions = sorted(
            mention_id for mention_id, item in expected.mentions.items() if item.doc_id == doc_id
        )
        if assigned != expected_doc_mentions:
            raise G19RunError(f"cluster labels do not cover exactly the mentions in {doc_id}")
        rows.append(
            {
                "id": doc_id,
                "clusters": [sorted(group) for _, group in sorted(clusters.items())],
                "mention_ids": expected_doc_mentions,
            }
        )
    return rows


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8"
    )


def run(args: argparse.Namespace) -> None:
    if args.output.exists():
        raise G19RunError(f"output already exists; G-19 runs are immutable: {args.output}")
    inputs = _validate_preflight(args.preflight)
    _require_model_assets(args.doc_encoder, args.mention_encoder)

    args.output.mkdir(parents=True)
    trainer_parameters = _trainer_parameters(args.output, smoke=args.stage == "smoke")
    conf = _model_conf(
        doc_encoder=args.doc_encoder,
        mention_encoder=args.mention_encoder,
        trainer_parameters=trainer_parameters,
    )

    # Delayed imports make local protocol tests independent of EasyECR's GPU stack.
    from easyecr.ecr_data.data_converter.data_converter import SplitDataConverter
    from easyecr.ecr_evaluate.ecr_evaluate import Evaluator
    from easyecr.ecr_model.cluster.cluster_model import EcrConnectedComponent
    from easyecr.ecr_model.framework.ecr_framework import EcrFramework

    temporary_directory = _configure_upstream_tempdir(args.output)
    from easyecr.ecr_model.model.pl_ecr_models.global_local_topic import GlobalLocalTopicModel

    _write_json(
        args.output / "run_manifest.json",
        {
            "schema_version": "ekg.easyecr_glt_run.v1",
            "stage": args.stage,
            "seed": SEED,
            "evaluation_gold_access": False,
            "preflight": str(args.preflight),
            "preflight_sha256": sha256_file(args.preflight),
            "input_sha256": {name: sha256_file(path) for name, path in inputs.items()},
            "doc_encoder": str(args.doc_encoder),
            "mention_encoder": str(args.mention_encoder),
            "temporary_directory": str(temporary_directory),
            "trainer_parameters": trainer_parameters,
            "threshold_grid": THRESHOLDS,
            "command_argv": sys.argv,
        },
    )

    train, selection, evaluation = SplitDataConverter().split(
        dataset_name="mavenere",
        train_path=str(inputs["train"]),
        dev_path=str(inputs["selection"]),
        test_path=str(inputs["evaluation"]),
    )
    model_dir = args.output / "checkpoints"
    model = GlobalLocalTopicModel(
        mode="train",
        model_dir=str(model_dir),
        model_filename="global-local-topic",
        trainer_parameters=trainer_parameters,
        conf=conf,
    )
    if args.stage == "smoke":
        smoke_train = _take_documents(train, args.smoke_documents)
        smoke_selection = _take_documents(selection, args.smoke_documents)
        smoke_evaluation = _take_documents(evaluation, args.smoke_documents)
        model.train(smoke_train, smoke_selection)
        with _run_in_output_directory(args.output):
            predicted = model.predict(smoke_evaluation, "distance")
        if not predicted.mentions:
            raise G19RunError("one-batch smoke produced no unlabeled prediction mentions")
        _write_json(
            args.output / "smoke.json",
            {
                "status": "pass",
                "training_documents": args.smoke_documents,
                "selection_documents": args.smoke_documents,
                "unlabeled_prediction_documents": args.smoke_documents,
                "unlabeled_prediction_mentions": len(predicted.mentions),
            },
        )
        return

    cluster = EcrConnectedComponent(distance_threshold=THRESHOLDS)
    framework = EcrFramework(
        predict_topic="doc_id",
        evaluate_topic="doc_id",
        main_metric="CoNLL",
        ecr_model=model,
        ecr_model_output_tag="distance",
        cluster_model=cluster,
        evaluator=Evaluator(
            average_over_topic=False,
            metric_names=["mentions", "muc", "bcub", "ceafe", "lea"],
            keep_singletons=True,
        ),
    )
    framework.train(train, selection)
    if cluster.best_distance is None or not (model_dir / "best.ckpt").is_file():
        raise G19RunError(
            "selection did not produce a best checkpoint and connected-component threshold"
        )
    with _run_in_output_directory(args.output):
        predicted = framework.predict(evaluation, output_tag="event_id_pred")
    raw_path = args.output / "raw_clusters.jsonl"
    _write_jsonl(raw_path, _raw_clusters(predicted, evaluation, "event_id_pred"))
    _write_json(
        args.output / "selection.json",
        {
            "checkpoint": str(model_dir / "best.ckpt"),
            "checkpoint_sha256": sha256_file(model_dir / "best.ckpt"),
            "selection_metric": "EasyECR CoNLL on hash-frozen selection-dev only",
            "selected_distance_threshold": cluster.best_distance,
            "threshold_grid": THRESHOLDS,
        },
    )
    print(f"[g19] wrote unlabeled raw clusters: {raw_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preflight", required=True, type=Path)
    parser.add_argument("--doc-encoder", required=True, type=Path)
    parser.add_argument("--mention-encoder", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--stage", choices=("smoke", "train-predict"), required=True)
    parser.add_argument("--smoke-documents", type=int, default=1)
    return parser.parse_args()


def main() -> int:
    try:
        run(parse_args())
    except G19RunError as exc:
        raise SystemExit(f"G-19 protocol error: {exc}") from exc
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
