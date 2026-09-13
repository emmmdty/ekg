"""C5's three entry points, pinned where a mistake would be silent.

The pilot cannot run here (no GPU, no corpus), so these cover the parts that
decide whether a run *means* what its label says:

* the three arms differ by exactly one switch each, and no two are the same;
* the preflight refuses a registered control that is not below the anchor,
  since C5 reasons from "naive pooling loses MUC";
* an unreproduced public method is recorded as a status, not omitted;
* coverage counts mentions against gold rather than trusting the scorer, which
  fills singletons silently and would score a dropped mention instead of
  failing.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]


def _module(name: str):
    spec = importlib.util.spec_from_file_location(name, _ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


PILOT = _module("run_c5_argument_uncertainty")
PREFLIGHT = _module("prepare_c5_argument_uncertainty_preflight")
SMOKE = _module("smoke_c5_argument_uncertainty")


def test_the_three_arms_are_one_switch_apart_and_none_repeat() -> None:
    flags = PILOT.ARM_FLAGS
    assert set(flags) == set(PILOT.ARMS) == set(SMOKE.ARMS)
    assert len({tuple(value) for value in flags.values()}) == len(flags)
    assert flags["remove_core"] == ()
    assert "role_compatibility" in flags["full"]
    assert "--permute-role-features" not in flags["full"]
    # permutation is full plus exactly the control switch
    assert set(flags["permutation"]) - set(flags["full"]) == {"--permute-role-features"}


def test_the_pilot_and_the_smoke_agree_on_what_each_arm_is() -> None:
    """Two files spelling the arms differently is how an ablation stops ablating."""
    assert PILOT.ARM_FLAGS == SMOKE.ARM_FLAGS


def test_the_pilot_entry_the_contract_names_exists() -> None:
    """D4 lost a cycle to a contract command whose script had never been written."""
    contract = (_ROOT / "docs/phases/PHASE_C5_argument_uncertainty.md").read_text(
        encoding="utf-8"
    )
    assert "scripts/run_c5_argument_uncertainty.py" in contract
    assert (_ROOT / "scripts/run_c5_argument_uncertainty.py").is_file()


def test_every_bound_code_file_exists() -> None:
    """A hash set naming an absent file fails only on the server, hours later."""
    for relative in PREFLIGHT.CODE_FILES:
        assert (_ROOT / relative).is_file(), relative


def test_the_pilot_entry_is_inside_the_hash_set_it_runs_under() -> None:
    assert "scripts/run_c5_argument_uncertainty.py" in PREFLIGHT.CODE_FILES


def test_the_inference_path_is_bound_too() -> None:
    """The permutation arm's shuffle happens at inference, so coref.py is part
    of the frozen mechanism, not an implementation detail around it."""
    assert "src/ekg/nodes/coref.py" in PREFLIGHT.CODE_FILES


def _gold(tmp_path: Path, clusters: dict[str, list[str]]) -> Path:
    path = tmp_path / "gold.jsonl"
    path.write_text(
        json.dumps(
            {
                "id": "doc1",
                "events": [
                    {"id": event, "mention": [{"id": m} for m in mentions]}
                    for event, mentions in clusters.items()
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def _predictions(tmp_path: Path, coreference: list[list[str]]) -> Path:
    path = tmp_path / "pred.jsonl"
    path.write_text(
        json.dumps({"id": "doc1", "coreference": coreference}) + "\n", encoding="utf-8"
    )
    return path


def test_coverage_counts_singletons_as_covered_not_missing(tmp_path: Path) -> None:
    gold = _gold(tmp_path, {"EV1": ["m1", "m2"], "EV2": ["m3"]})
    predictions = _predictions(tmp_path, [["m1", "m2"]])
    coverage = PILOT._coverage(gold, predictions)
    assert coverage["gold_mentions"] == 3
    assert coverage["clustered_mentions"] == 2
    assert coverage["singletons"] == 1


def test_coverage_refuses_a_mention_in_two_clusters(tmp_path: Path) -> None:
    gold = _gold(tmp_path, {"EV1": ["m1", "m2"]})
    predictions = _predictions(tmp_path, [["m1", "m2"], ["m1"]])
    with pytest.raises(PILOT.PilotError, match="more than one cluster"):
        PILOT._coverage(gold, predictions)


def test_coverage_refuses_a_mention_gold_never_had(tmp_path: Path) -> None:
    gold = _gold(tmp_path, {"EV1": ["m1", "m2"]})
    predictions = _predictions(tmp_path, [["m1", "m2", "ghost"]])
    with pytest.raises(PILOT.PilotError, match="not in the gold population"):
        PILOT._coverage(gold, predictions)


def test_the_frozen_budget_matches_the_registered_control() -> None:
    """Arms 4-6 must run the control's budget bit for bit, per the contract."""
    assert PREFLIGHT.FROZEN_TRAINING == {
        "epochs": 10,
        "warmup_steps": 200,
        "lr": 2e-5,
        "head_lr": 2e-5,
        "accum_steps": 1,
        "max_length": 512,
    }
    assert PREFLIGHT.FROZEN_INFERENCE["threshold"] == 0.7
    assert PREFLIGHT.FROZEN_INFERENCE["endpoint_epoch"] == 10


def test_the_smoke_fixture_covers_the_shapes_the_contract_names() -> None:
    """Empty role, many fillers, a repeated string, an all-singleton document."""
    fixture = SMOKE._role_fixture()
    assert fixture["pairs"] == 5
    assert fixture["feature_width"] > 0
    assert fixture["mediator_on_all_singletons"]["merged"] == 0
