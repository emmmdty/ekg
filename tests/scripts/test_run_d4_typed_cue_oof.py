"""Contracts the D4 seed-13 pilot driver has to hold before it occupies a card."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "run_d4_typed_cue_oof", ROOT / "scripts/run_d4_typed_cue_oof.py"
)
assert SPEC and SPEC.loader
pilot = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(pilot)


def contract(tmp_path: Path, **overrides) -> Path:
    payload = {
        "schema_version": "ekg.d4_typed_cue_preflight.v1",
        "status": "pass",
        "seed": 13,
        "final_valid_accessed": False,
        "training": {"arms": ["full", "remove_core", "permutation"]},
        "code": {},
    }
    payload.update(overrides)
    path = tmp_path / "protocol.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_the_frozen_population_is_stated_not_inferred() -> None:
    # These are the numbers the contract's Done-when clause names; reading them
    # off whatever happens to be on disk would make the check vacuous.
    assert pilot.EXPECTED_DOCUMENTS == 2913
    assert pilot.EXPECTED_MENTIONS == 73939
    assert pilot.ARMS == ("full", "remove_core", "permutation")


def test_a_contract_that_did_not_pass_is_refused(tmp_path: Path) -> None:
    with pytest.raises(pilot.PilotError, match="contract status"):
        pilot._verify_contract(ROOT, contract(tmp_path, status="failed"))


def test_another_seed_is_refused_even_if_the_contract_says_so(tmp_path: Path) -> None:
    with pytest.raises(pilot.PilotError, match="contract seed"):
        pilot._verify_contract(ROOT, contract(tmp_path, seed=17))


def test_a_contract_that_touched_final_valid_is_refused(tmp_path: Path) -> None:
    with pytest.raises(pilot.PilotError, match="final-valid"):
        pilot._verify_contract(ROOT, contract(tmp_path, final_valid_accessed=True))


def test_a_reordered_or_reduced_arm_set_is_refused(tmp_path: Path) -> None:
    with pytest.raises(pilot.PilotError, match="arm set"):
        pilot._verify_contract(tmp_path, contract(tmp_path, training={"arms": ["full"]}))


def test_bound_code_that_drifted_is_refused(tmp_path: Path) -> None:
    path = contract(tmp_path, code={"scripts/run_d4_typed_cue_oof.py": "0" * 64})
    with pytest.raises(pilot.PilotError, match="code hash drift"):
        pilot._verify_contract(ROOT, path)


def test_the_real_contract_shape_verifies_against_this_repository(tmp_path: Path) -> None:
    from ekg.core.stage_bundle import sha256_file

    code = {
        relative: sha256_file(ROOT / relative)
        for relative in ("scripts/run_d4_typed_cue_oof.py", "scripts/train_d4_typed_cue.py")
    }
    verified = pilot._verify_contract(ROOT, contract(tmp_path, code=code))
    assert verified["seed"] == 13


def test_training_source_refuses_to_silently_drop_a_document(tmp_path: Path) -> None:
    source = tmp_path / "source.jsonl"
    source.write_text('{"id": "a"}\n{"id": "b"}\n', encoding="utf-8")
    with pytest.raises(pilot.PilotError, match="training source"):
        pilot._training_source(source, {"a", "missing"}, tmp_path / "out.jsonl")


def test_training_source_holds_exactly_the_train_and_selection_documents(tmp_path: Path) -> None:
    source = tmp_path / "source.jsonl"
    source.write_text('{"id": "a"}\n{"id": "b"}\n{"id": "c"}\n', encoding="utf-8")
    output = tmp_path / "out.jsonl"

    pilot._training_source(source, {"a", "c"}, output)

    written = [json.loads(line)["id"] for line in output.read_text(encoding="utf-8").splitlines()]
    # The evaluation document is not merely unused by the trainer; it is absent.
    assert written == ["a", "c"]
