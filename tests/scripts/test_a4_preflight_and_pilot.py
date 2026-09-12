"""Contracts for the A4 preflight and the pilot driver it binds."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
R1_PROTOCOL = ROOT / "runs/stages/R1/r1-v61-20260904/protocol.json"
T024 = ROOT / "runs/stages/R1/r1-v61-20260904/phase_contracts/t024_freeze.json"
SOURCE = ROOT / "data/processed/maven_ere/train.jsonl"
DEV_MANIFEST = ROOT / "data/protocols/v6/manifests/maven_ere_internal-dev.json"


def _module(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / f"scripts/{name}.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


preflight = _module("prepare_a4_pair_evidence_preflight")
pilot = _module("run_a4_pair_evidence")

# `runs/` is gitignored and travels by scp, so these are host facts, not code
# facts. A host whose R1 protocol predates E12 carries no phase contracts at
# all (measured on gpu-5090, 2026-09-12) and cannot answer this question.
_artifacts_present = R1_PROTOCOL.is_file() and T024.is_file()
_r1_has_contracts = (
    _artifacts_present
    and "relation" in json.loads(R1_PROTOCOL.read_text(encoding="utf-8")).get(
        "phase_contracts", {}
    )
)
needs_r1 = pytest.mark.skipif(
    not _r1_has_contracts,
    reason="this host's R1 protocol carries no relation phase contract; sync runs/stages/R1",
)
needs_source = pytest.mark.skipif(
    not SOURCE.is_file(), reason="MAVEN-ERE train source not materialised on this host"
)


@needs_r1
def test_the_relation_contract_t024_froze_is_currently_eligible() -> None:
    contracts = preflight._validate_contract(ROOT, R1_PROTOCOL, T024)
    assert set(contracts) == {"r1_protocol", "t024", "phase_contract"}
    assert all(len(value) == 64 for value in contracts.values())


@needs_source
def test_the_materialised_internal_dev_reproduces_the_frozen_candidate_digest(
    tmp_path: Path,
) -> None:
    gold = preflight._materialise_internal_dev(SOURCE, DEV_MANIFEST, tmp_path / "dev.jsonl")

    # The digest is the one thing A4 may not move, so it is recomputed from the
    # materialised file rather than copied out of the contract.
    assert gold["candidate_id_digest"] == preflight.EXPECTED_CANDIDATE_DIGEST
    assert gold["documents"] == 291
    assert gold["population_counts"]["event_mentions"] == 7195


def test_a_training_budget_the_contract_never_approved_is_refused(tmp_path: Path) -> None:
    args = _preflight_args(tmp_path, epochs=12)
    with pytest.raises(preflight.PreflightError, match="epochs is frozen to 50"):
        preflight.prepare(args)


def test_a_seed_other_than_13_is_refused(tmp_path: Path) -> None:
    args = _preflight_args(tmp_path, seed=17)
    with pytest.raises(preflight.PreflightError, match="only for seed 13"):
        preflight.prepare(args)


def test_the_pilot_entry_is_inside_the_hash_set_the_contract_binds() -> None:
    # D4.3 waited a cycle on a pilot entry that the contract named and nobody
    # had written; the same file must also be hashable from the contract.
    assert "scripts/run_a4_pair_evidence.py" in preflight.CODE_FILES
    for relative in preflight.CODE_FILES:
        assert (ROOT / relative).is_file(), relative


def test_bound_code_that_drifted_is_refused(tmp_path: Path) -> None:
    contract = tmp_path / "protocol.json"
    contract.write_text(
        json.dumps(
            {
                "schema_version": "ekg.a4_pair_evidence_preflight.v1",
                "status": "pass",
                "seed": 13,
                "final_valid_accessed": False,
                "training": {"arms": list(pilot.A4_ARMS)},
                "code": {"scripts/run_a4_pair_evidence.py": "0" * 64},
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(pilot.PilotError, match="code hash drift"):
        pilot.verify_contract(ROOT, contract)


def test_a_contract_with_another_arm_set_is_refused(tmp_path: Path) -> None:
    contract = tmp_path / "protocol.json"
    contract.write_text(
        json.dumps(
            {
                "schema_version": "ekg.a4_pair_evidence_preflight.v1",
                "status": "pass",
                "seed": 13,
                "final_valid_accessed": False,
                "training": {"arms": ["full", "remove_core"]},
                "code": {},
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(pilot.PilotError, match="contract arm set"):
        pilot.verify_contract(ROOT, contract)


def test_per_family_selection_keeps_only_each_family_own_edges(tmp_path: Path) -> None:
    paths = {}
    for family in pilot.FAMILIES:
        path = tmp_path / f"{family}.jsonl"
        path.write_text(
            json.dumps(
                {
                    "doc_id": "doc1",
                    # Every checkpoint carries all three heads, so each family's
                    # file holds edges of every family; only its own may survive.
                    "edges": [
                        {"relation_type": other, "subtype": f"{other}-from-{family}"}
                        for other in pilot.FAMILIES
                    ],
                }
            )
            + "\n",
            encoding="utf-8",
        )
        paths[family] = path
    merged = tmp_path / "merged.jsonl"
    pilot._merge_family_edges(paths, merged)

    rows = [json.loads(line) for line in merged.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 1
    assert [edge["subtype"] for edge in rows[0]["edges"]] == [
        f"{family}-from-{family}" for family in pilot.FAMILIES
    ]


def test_predictions_from_a_different_document_set_are_refused(tmp_path: Path) -> None:
    paths = {}
    for index, family in enumerate(pilot.FAMILIES):
        path = tmp_path / f"{family}.jsonl"
        path.write_text(
            json.dumps({"doc_id": f"doc{index}", "edges": []}) + "\n", encoding="utf-8"
        )
        paths[family] = path
    with pytest.raises(pilot.PilotError, match="document order/set differs"):
        pilot._merge_family_edges(paths, tmp_path / "merged.jsonl")


def _preflight_args(tmp_path: Path, **overrides):
    """The frozen defaults, with one knob moved, pointing at real inputs."""
    import argparse

    values = {
        "repo": ROOT,
        "source": SOURCE,
        "train_manifest": ROOT / "data/protocols/v6/manifests/maven_ere_train.json",
        "dev_manifest": DEV_MANIFEST,
        "p1_protocol": ROOT / "runs/stages/P1/p1-v6-20260904-r15/protocol.json",
        "a3_protocol": ROOT / "runs/stages/A3/a3-v6-20260905-r17/protocol.json",
        "r1_protocol": R1_PROTOCOL,
        "t024": T024,
        "fallback_predictions": tmp_path / "fallback.jsonl",
        "taco_predictions": tmp_path / "taco.jsonl",
        "model": tmp_path / "model",
        "evaluator": ROOT / "data/protocols/v6/tools/maven_ere_evaluate.py",
        "output": tmp_path / "preflight/protocol.json",
        "seed": 13,
        "consistency_weight": 1.0,
        **preflight.FROZEN_TRAINING,
    }
    values.update(overrides)
    return argparse.Namespace(**values)
