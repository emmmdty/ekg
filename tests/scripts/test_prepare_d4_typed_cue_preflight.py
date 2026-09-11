"""Contracts that D4 preflight must verify before any CUDA job runs."""

from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path

from ekg.core.stage_bundle import content_digest, model_content_digest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "prepare_d4_typed_cue_preflight", ROOT / "scripts/prepare_d4_typed_cue_preflight.py"
)
assert SPEC and SPEC.loader
preflight = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(preflight)


def test_cv_and_t024_contract_are_currently_eligible() -> None:
    cv = ROOT / "runs/stages/R1/r1-v61-20260904/factuality_cv/factuality_cv.json"
    source = ROOT / "data/processed/maven_fact/train.jsonl"
    r1_protocol = ROOT / "runs/stages/R1/r1-v61-20260904/protocol.json"
    t024 = ROOT / "runs/stages/R1/r1-v61-20260904/phase_contracts/t024_freeze.json"

    validated = preflight._validate_cv(ROOT, cv, source)
    contracts = preflight._validate_contract(ROOT, r1_protocol, t024)

    assert validated["config"]["final_valid_accessed"] is False
    assert contracts["phase_contract"] == (
        "01e1ba2f74627216a19c02ad47dbc5bbf35e72fe4530ce18ede76072328c49b1"
    )


def test_model_digest_reproduces_the_pinned_backbone_address() -> None:
    # The 4090 snapshot carried no upstream revision, so P1 r9 made the directory
    # name the content address itself.  These are the six recorded file digests of
    # /data/TJK/models/local/roberta-base/71be7419...; the pin must fall out of them.
    recorded = {
        "config.json": "ef0185e2aae6e06c5f105a285006952c340e20c7dbf43c86ec82601b13fc45e9",
        "merges.txt": "1ce1664773c50f3e0cc8842619a93edc4624525b728b188a9e0be33b7726adc5",
        "pytorch_model.bin": "278b7a95739c4392fae9b818bb5343dde20be1b89318f37a6d939e1e1b9e461b",
        "tokenizer.json": "847bbeab6174d66a88898f729d52fa8d355fafe1bea101cf960dd404581df70e",
        "tokenizer_config.json": "dfef66475ba1a217ceab1a29ba012843041e11627cab56f5f83c7b9804cfa5c5",
        "vocab.json": "9e7f63c2d15d666b52e21d250d2e513b87c9b713cfa6987a82ed89e5e6e50655",
    }

    assert content_digest(recorded) == preflight.EXPECTED_MODEL_SHA256


def test_model_digest_reads_every_file_under_the_directory(tmp_path: Path) -> None:
    model = tmp_path / "model"
    (model / "nested").mkdir(parents=True)
    (model / "config.json").write_text("config", encoding="utf-8")
    (model / "nested/weights.bin").write_bytes(b"weights")

    expected = content_digest(
        {
            "config.json": hashlib.sha256(b"config").hexdigest(),
            "nested/weights.bin": hashlib.sha256(b"weights").hexdigest(),
        }
    )

    assert model_content_digest(model) == expected
