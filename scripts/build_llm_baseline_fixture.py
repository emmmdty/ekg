#!/usr/bin/env python
"""Run the three chapters' LLM control end to end on CPU, with recorded answers.

C-7's completion test is narrow and worth stating plainly: for each of the
three method chapters, ten fixed inputs must come out the other side as a
prediction file that **that chapter's frozen evaluator will score**, whatever
the score is.  Generation is the one step not exercised here, because it is the
one step that needs a GPU -- everything on either side of it is.

The recorded answers are deliberately imperfect.  They carry the failure modes
a real Qwen3 run produces: a mention it never answered for, a label it invented,
an id from no document, a self-relation, a mention claimed by two clusters.  A
fixture built on clean answers would prove only that the happy path parses; this
one proves the scaffolding writes those failures down instead of repairing them
into a score the model did not earn.

The prompt templates and the LoRA budget live in `data/protocols/v6/llm_baseline.json`
and are hashed into the report, so a chapter's preflight can bind them the same
way it binds an encoder.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from ekg.core.stage_bundle import sha256_file
from ekg.llm_baseline import (
    CHAPTERS,
    load_llm_baseline_config,
    parse_factuality,
    parse_identity,
    parse_relation,
    render_prompt,
)
from ekg.relations.maven_ere_official import candidate_population_digest


class FixtureError(ValueError):
    """The LLM-control fixture did not produce something its evaluator can read."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise FixtureError(message)


def _write(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _load_document(path: Path) -> dict:
    lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line]
    _require(len(lines) == 1, f"{path}: the fixture is one document")
    return json.loads(lines[0])


def _mentions(document: dict) -> list[dict]:
    listed = [
        {
            "mention_id": str(mention["id"]),
            "trigger": mention.get("trigger_word", ""),
            "sent_id": mention.get("sent_id", 0),
            "factuality": mention.get("factuality"),
        }
        for event in document["events"]
        for mention in event["mention"]
    ]
    ids = [m["mention_id"] for m in listed]
    _require(len(set(ids)) == len(ids), "the fixture repeats a mention id")
    return listed


def _score_factuality(prediction: dict[str, str], gold: dict[str, str]) -> dict:
    """The chapter's own frozen scorer, not a second implementation of it."""
    from ekg.factuality.metrics import factuality_report

    report = factuality_report(prediction, gold)
    return {"macro_f1": report["macro_f1"], "accuracy": report["accuracy"]}


def _score_official(
    repo: Path, evaluator: Path, gold: Path, predictions: Path, output: Path, digest: str
) -> dict:
    """MAVEN-ERE's own `evaluate.py`, through the frozen wrapper.

    The wrapper demands the candidate digest rather than defaulting it, which is
    the guard that keeps a run from being scored against a population it never
    saw. The fixture recomputes it from its own document instead of hardcoding
    one, so the check stays real here too.
    """
    completed = subprocess.run(
        [
            sys.executable, "-u", "scripts/score_maven_ere_official.py",
            "--evaluator", str(evaluator),
            "--gold", str(gold),
            "--pred", str(predictions),
            "--candidate-digest", digest,
            "--output", str(output),
        ],
        cwd=repo,
        text=True,
        capture_output=True,
    )
    if completed.returncode != 0:
        raise FixtureError(
            f"official scoring failed\n{completed.stdout}\n{completed.stderr}"
        )
    return json.loads(output.read_text(encoding="utf-8"))["scores"]


def run(args: argparse.Namespace) -> dict:
    _require(not args.output.exists(), f"refusing to overwrite: {args.output}")
    config = load_llm_baseline_config(args.config)
    document = _load_document(args.document)
    mentions = _mentions(document)
    _require(
        len(mentions) == args.inputs,
        f"the fixture holds {len(mentions)} mentions, expected {args.inputs}",
    )
    recorded = json.loads(args.responses.read_text(encoding="utf-8"))["responses"]
    for chapter in CHAPTERS:
        _require(chapter in recorded, f"no recorded response for {chapter}")

    doc_id = str(document["id"])
    mention_ids = [m["mention_id"] for m in mentions]
    args.output.mkdir(parents=True)

    # Gold, in each evaluator's own shape. The official one reads event-level
    # relations and expands them itself, so the gold record goes through intact.
    gold_official = args.output / "gold.jsonl"
    gold_official.write_text(
        json.dumps(document, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    digest, counts = candidate_population_digest({doc_id: document})
    gold_factuality = {
        m["mention_id"]: m["factuality"] for m in mentions if m["factuality"]
    }
    _require(
        len(gold_factuality) == len(mentions),
        "every fixture mention needs a gold factuality label",
    )

    chapters: dict[str, dict] = {}
    for chapter in CHAPTERS:
        prompt = render_prompt(
            config, chapter, document=document["document"], mentions=mentions
        )
        _require(
            all(mention_id in prompt for mention_id in mention_ids),
            f"{chapter}: the prompt does not ask about every mention",
        )
        text = recorded[chapter]
        predictions = args.output / f"{chapter}.predictions.jsonl"

        if chapter == "factuality":
            parsed = parse_factuality(text, mention_ids)
            predictions.write_text(
                json.dumps(parsed.prediction, ensure_ascii=False, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            scores = _score_factuality(parsed.prediction, gold_factuality)
        else:
            parser = parse_relation if chapter == "relation" else parse_identity
            parsed = parser(text, doc_id, mention_ids, config)
            predictions.write_text(
                json.dumps(parsed.prediction, ensure_ascii=False) + "\n", encoding="utf-8"
            )
            scores = _score_official(
                args.repo,
                args.evaluator,
                gold_official,
                predictions,
                args.output / f"{chapter}.metrics.json",
                digest,
            )

        chapters[chapter] = {
            "prompt_sha256": sha256_file(_write_prompt(args.output, chapter, prompt)),
            "predictions_sha256": sha256_file(predictions),
            "coverage": parsed.coverage,
            "rejected": parsed.rejected,
            "scores": scores,
        }
        print(
            f"[llm-fixture] {chapter}: scored, "
            f"answered={parsed.coverage['answered']} "
            f"missing={parsed.coverage['missing']} "
            f"rejected={parsed.coverage['rejected']}"
        )

    payload = {
        "schema_version": "ekg.llm_baseline_fixture.v1",
        "status": "pass",
        "inputs": len(mentions),
        "document": doc_id,
        "population": {"candidate_id_digest": digest, **counts},
        "config": {"path": str(args.config), "sha256": config.sha256},
        "lora": config.lora,
        "decoding": config.decoding,
        "responses_sha256": sha256_file(args.responses),
        "chapters": chapters,
    }
    _write(args.output / "fixture.json", payload)
    return payload


def _write_prompt(output: Path, chapter: str, prompt: str) -> Path:
    path = output / f"{chapter}.prompt.txt"
    path.write_text(prompt, encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument(
        "--config", type=Path, default=Path("data/protocols/v6/llm_baseline.json")
    )
    parser.add_argument(
        "--document", type=Path, default=Path("data/fixtures/llm_baseline/document.jsonl")
    )
    parser.add_argument(
        "--responses", type=Path, default=Path("data/fixtures/llm_baseline/responses.json")
    )
    parser.add_argument(
        "--evaluator", type=Path, default=Path("data/protocols/v6/tools/maven_ere_evaluate.py")
    )
    parser.add_argument("--inputs", type=int, default=10)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    args.repo = args.repo.resolve()
    for name in ("config", "document", "responses", "evaluator", "output"):
        setattr(args, name, getattr(args, name).resolve())

    payload = run(args)
    print(
        f"[llm-fixture] {payload['status'].upper()} {args.output} "
        f"chapters={len(payload['chapters'])} config={payload['config']['sha256'][:12]}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
