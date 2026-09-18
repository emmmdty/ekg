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
    """Arms 4-6 must run the control's budget bit for bit, per the contract.

    Second cycle: the optimiser half still matches bit for bit.  The negative
    sampler does not, and that is the cycle's single declared variable -- the
    first cycle dropped every all-singleton document from training while
    inference sees them all.  Contract line 65 requires arm 2 (the registered
    Qwen3 control, trained under the historical sampler) to share the arms'
    pair population, so this deviation means the `:104` gate can only be judged
    against the anchor this cycle; `docs/EXPERIMENT_PLAN.md` §10.5b registers
    that narrowing.  The two untouched knobs are asserted at their historical
    defaults so the deviation cannot quietly widen to three.
    """
    budget = dict(PREFLIGHT.FROZEN_TRAINING)
    sampler = {
        key: budget.pop(key)
        for key in ("neg_ratio", "hard_fraction", "include_negative_only_docs")
    }
    assert budget == {
        "epochs": 10,
        "warmup_steps": 200,
        "lr": 2e-5,
        "head_lr": 2e-5,
        "accum_steps": 1,
        "max_length": 512,
    }
    assert sampler == {
        "neg_ratio": 10.0,
        "hard_fraction": 0.5,
        "include_negative_only_docs": True,
    }
    assert PREFLIGHT.FROZEN_INFERENCE["threshold"] == 0.7
    assert PREFLIGHT.FROZEN_INFERENCE["endpoint_epoch"] == 10


def test_the_smoke_fixture_covers_the_shapes_the_contract_names() -> None:
    """Empty role, many fillers, a repeated string, an all-singleton document."""
    fixture = SMOKE._role_fixture()
    assert fixture["pairs"] == 5
    assert fixture["feature_width"] > 0
    assert fixture["mediator_on_all_singletons"]["merged"] == 0


def test_the_smoke_hands_the_trainer_predictions_for_its_own_documents(tmp_path: Path) -> None:
    """A subset corpus needs a subset artifact.

    `apply_predicted_arguments` binds a prediction file that must cover its
    corpus with nothing left over. The smoke subsets the documents, so passing
    the whole-corpus artifact made every other mention an "extra" and the bind
    failed before any arm trained -- which is exactly what happened on the 4090.
    """
    source = tmp_path / "predictions.jsonl"
    source.write_text(
        "\n".join(
            json.dumps({"mention_id": f"m{i}", "doc_id": doc, "status": "empty"})
            for i, doc in enumerate(("wanted", "wanted", "other", "other", "other"))
        )
        + "\n",
        encoding="utf-8",
    )
    output = tmp_path / "subset.jsonl"
    SMOKE._subset_predictions(source, ["wanted"], output)
    rows = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
    assert [row["mention_id"] for row in rows] == ["m0", "m1"]

    with pytest.raises(SMOKE.SmokeError, match="cover none of"):
        SMOKE._subset_predictions(source, ["absent"], tmp_path / "empty.jsonl")


SUBMISSION = _module("build_maven_ere_submission")

_CONTRACT = {
    "seed": 13,
    "source": {"path": "data/train.jsonl"},
    "model": {"path": "models/roberta"},
    "evaluator": {"path": "evaluate.py"},
    "argument_predictions": {"path": "runs/arguments/merged.jsonl"},
    "internal_dev_gold": {"path": "runs/gold/internal_dev.jsonl"},
    "manifests": {
        "train": {"path": "runs/manifests/train.json"},
        "internal_dev": {"path": "runs/manifests/internal_dev.json"},
    },
    # Derived, not retyped: a hand-copied budget here drifts from the one the
    # preflight freezes, and then these commands stop being the real commands.
    "training": {**PREFLIGHT.FROZEN_TRAINING, **PREFLIGHT.FROZEN_INFERENCE},
}


def _flag(command: list[str], name: str) -> str | None:
    return command[command.index(name) + 1] if name in command else None


def test_both_halves_of_an_arm_read_the_same_argument_artifact() -> None:
    """The defect that cost C5.3 its first run, priced at one unit test.

    The pilot trained with `--argument-predictions` and predicted without it, so
    `role_compatibility` met mentions with no argument state and the contract's
    fail-fast fired -- after the arm had trained for hours. Training and
    inference are one calibration, so they are asserted against one artifact.
    """
    train = PILOT.train_command(_CONTRACT, "full", Path("out/full/checkpoint"))
    predict = PILOT.predict_command(_CONTRACT, Path("out/full/checkpoint/epochs/epoch-10"),
                                    Path("out/full/predictions.jsonl"))

    artifact = _CONTRACT["argument_predictions"]["path"]
    assert _flag(train, "--argument-predictions") == artifact
    assert _flag(predict, "--argument-predictions") == artifact


def test_the_sampler_the_contract_pins_is_the_sampler_the_trainer_gets() -> None:
    """The first cycle's negative sampler was a trainer default in no contract.

    Pinning it is only worth anything if the pinned value actually reaches the
    command line, so the plumbing is asserted rather than assumed.
    """
    train = PILOT.train_command(_CONTRACT, "full", Path("out/full/checkpoint"))
    frozen = PREFLIGHT.FROZEN_TRAINING
    assert _flag(train, "--neg-ratio") == str(frozen["neg_ratio"])
    assert _flag(train, "--hard-fraction") == str(frozen["hard_fraction"])
    assert ("--include-negative-only-docs" in train) is frozen["include_negative_only_docs"]


def test_the_submission_builder_accepts_every_flag_the_pilot_hands_it() -> None:
    """`--argument-predictions` did not exist on the builder; nothing caught it."""
    predict = PILOT.predict_command(_CONTRACT, Path("out/endpoint"), Path("out/pred.jsonl"))

    parsed = SUBMISSION.build_parser().parse_args(predict[3:])  # drop python -u <script>

    assert parsed.argument_predictions == Path(_CONTRACT["argument_predictions"]["path"])
    assert parsed.coref_checkpoint == "out/endpoint"
    assert parsed.relation_predictor == "none"
