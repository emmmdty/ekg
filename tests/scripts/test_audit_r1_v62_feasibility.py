import importlib.util
import random
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "audit_r1_v62_feasibility", ROOT / "scripts/audit_r1_v62_feasibility.py"
)
assert SPEC is not None and SPEC.loader is not None
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


def test_partition_map_covers_every_non_anchor_once() -> None:
    mentions = [f"m{index}" for index in range(68)]
    mapping = audit._partition_map(mentions, "m0", k=30, rng=random.Random(42))

    assert set(mapping) == set(mentions) - {"m0"}
    group_sizes = {}
    for group in mapping.values():
        group_sizes[group] = group_sizes.get(group, 0) + 1
    assert max(group_sizes.values()) <= 30
    assert max(group_sizes.values()) - min(group_sizes.values()) <= 1


def test_causal_inference_matches_llmere_rule() -> None:
    assert audit._infer_causal("CAUSE", "CAUSE") == "CAUSE"
    assert audit._infer_causal("CAUSE", "PRECONDITION") == "PRECONDITION"
    assert audit._infer_causal("PRECONDITION", "CAUSE") == "PRECONDITION"
    assert audit._infer_causal("PRECONDITION", "PRECONDITION") == "PRECONDITION"


def test_exact_power_is_preregistered_and_sufficient() -> None:
    result = audit._exact_binomial_power(213 / 912, 0.415, alpha=0.05, target=0.80)

    assert result["n"] <= 912
    assert result["actual_alpha"] <= 0.05
    assert result["power_at_target_precision"] >= 0.80


def test_prediction_dump_incident_coverage() -> None:
    records = [
        {
            "doc_id": "d1",
            "edges": [
                {
                    "head_id": "d1::m1",
                    "tail_id": "d1::m2",
                    "relation_type": "causal",
                }
            ],
        }
    ]

    incident, incident_by_family, edge_counts, invalid = audit._predicted_incident_from_dump(
        records, {"d1": {"m1", "m2", "m3"}}
    )

    assert incident == {("d1", "m1"), ("d1", "m2")}
    assert incident_by_family == {"causal": {("d1", "m1"), ("d1", "m2")}}
    assert edge_counts == {"causal": 1}
    assert invalid == 0


def test_crossfit_partition_rejects_leakage() -> None:
    audit._validate_partition({"a"}, {"b"}, {"c"}, {"a", "b", "c"}, name="ok")

    with pytest.raises(SystemExit, match="train/evaluation overlap"):
        audit._validate_partition({"a", "c"}, {"b"}, {"c"}, {"a", "b", "c"}, name="bad")


def test_d4_crossfit_plan_defaults_to_frozen_relation_backbone() -> None:
    args = audit.build_parser().parse_args(["d4-plan", "--output", "plan.json"])

    assert (
        args.relation_model_content_sha256
        == audit.D4_RELATION_MODEL_CONTENT_SHA256
        == "71be7419a60dcce0fc276654c8f9213b41f8def71a0c3465d7fed2352c961ea9"
    )


def test_generation_sample_is_balanced_and_deterministic() -> None:
    candidates = {
        "hard_noncoreferent": [
            {"doc_id": "d", "left_id": f"h{i}", "right_id": f"x{i}"} for i in range(4)
        ],
        "divergent_coreferent": [
            {"doc_id": "d", "left_id": f"p{i}", "right_id": f"y{i}"} for i in range(4)
        ],
    }

    first = audit._sample_strata(candidates, per_stratum=2, seed=7)
    second = audit._sample_strata(candidates, per_stratum=2, seed=7)

    assert first == second
    assert len(first) == 4
    assert sum(item["left_id"].startswith("h") for item in first) == 2
    assert sum(item["left_id"].startswith("p") for item in first) == 2
