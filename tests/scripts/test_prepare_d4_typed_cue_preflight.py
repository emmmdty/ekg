"""Contracts that D4 preflight must verify before any CUDA job runs."""

from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path

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


def test_model_digest_is_a_canonical_map_of_file_digests(tmp_path: Path) -> None:
    model = tmp_path / "model"
    model.mkdir()
    (model / "config.json").write_text("config", encoding="utf-8")
    nested = model / "nested"
    nested.mkdir()
    (nested / "weights.bin").write_bytes(b"weights")

    expected = hashlib.sha256()
    for relative in (Path("config.json"), Path("nested/weights.bin")):
        expected.update(f"{relative.as_posix()}\0".encode())
        expected.update(hashlib.sha256((model / relative).read_bytes()).hexdigest().encode())
        expected.update(b"\0")

    assert preflight._model_tree_hash(model) == expected.hexdigest()
