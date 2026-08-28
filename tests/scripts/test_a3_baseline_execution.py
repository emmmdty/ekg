"""CPU contracts for the A3 materializer, launcher, and normalization boundary."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from ekg.core.schema import RelationEdge, RelationType
from ekg.relations.maven_ere_official import candidate_population_digest, records_by_id

_REPO = Path(__file__).resolve().parents[2]
_GOLD = _REPO / "data/fixtures/maven_ere/sample.jsonl"


def _load_script(name: str):
    path = _REPO / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


prepare = _load_script("prepare_a3_baselines")
launcher = _load_script("run_a3_baseline")


def _records(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _digest() -> str:
    return candidate_population_digest(records_by_id(_records(_GOLD), source=str(_GOLD)))[0]


def test_local_empty_edges_normalize_to_complete_official_schema(tmp_path: Path) -> None:
    raw = tmp_path / "edges.jsonl"
    raw.write_text(
        "".join(json.dumps({"doc_id": row["id"], "edges": []}) + "\n" for row in _records(_GOLD)),
        encoding="utf-8",
    )
    output = tmp_path / "official.jsonl"

    launcher.normalize_predictions(
        baseline="local_pair",
        raw_path=raw,
        gold_path=_GOLD,
        output=output,
        candidate_digest=_digest(),
    )

    normalized = _records(output)
    assert len(normalized) == len(_records(_GOLD))
    assert all(set(row["causal_relations"]) == {"CAUSE", "PRECONDITION"} for row in normalized)
    assert all(row["subevent_relations"] == [] for row in normalized)


def test_official_single_partial_payload_is_completed(tmp_path: Path) -> None:
    raw = tmp_path / "single.jsonl"
    raw.write_text(
        "".join(
            json.dumps(
                {
                    "id": row["id"],
                    "causal_relations": {"CAUSE": [], "PRECONDITION": []},
                }
            )
            + "\n"
            for row in _records(_GOLD)
        ),
        encoding="utf-8",
    )
    output = tmp_path / "official.jsonl"

    launcher.normalize_predictions(
        baseline="official_single",
        raw_path=raw,
        gold_path=_GOLD,
        output=output,
        candidate_digest=_digest(),
    )

    assert all("coreference" in row for row in _records(output))


def test_local_normalizer_rejects_inactive_temporal_head() -> None:
    edge = RelationEdge(
        head_id="d::m1",
        tail_id="d::m2",
        relation_type=RelationType.TEMPORAL,
        subtype="BEFORE",
        directed=True,
        confidence=0.9,
    )
    with pytest.raises(launcher.A3LaunchError, match="inactive family temporal"):
        launcher._local_relation_payload([edge])


def test_model_path_adaptation_is_exact_and_traceable(tmp_path: Path) -> None:
    source = tmp_path / "source"
    contents = {
        "causal/main.py": 'x = "roberta-base"\n',
        "utils/model.py": 'x = "roberta-base"\n',
        "joint/main.py": 'x = "/data/MODELS/roberta-base"\n',
        "joint/src/model.py": 'x = "/data/MODELS/roberta-base"\n',
    }
    for relative, text in contents.items():
        path = source / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    changes = prepare._adapt_model_path(source, "/models/roberta-base")

    assert len(changes) == 4
    assert all(change["before_sha256"] != change["after_sha256"] for change in changes)
    assert all(
        '"/models/roberta-base"' in (source / relative).read_text(encoding="utf-8")
        for relative in contents
    )


def test_execution_plan_uses_frozen_families_and_official_recipes() -> None:
    plan = prepare._commands(
        remote_repo=Path("/repo"),
        remote_preflight=Path("/repo/runs/stages/A3/run/preflight"),
        python=Path("/repo/.venv/bin/python"),
        model_path="/models/roberta-base",
        p1_hash="a" * 64,
    )

    local = plan["local_pair"]["13"]["argv"]
    assert local[local.index("--families") + 1 : local.index("--families") + 3] == [
        "causal",
        "subevent",
    ]
    single = plan["official_single"]["13"]["argv"]
    assert single[single.index("--epochs") + 1] == "50"
    joint = plan["official_joint"]["13"]["argv"]
    assert joint[joint.index("--epochs") + 1] == "100"
    assert joint[joint.index("--accumulation_steps") + 1] == "4"
    assert plan["local_pair"]["13"]["run_dir"] == (
        "/repo/runs/stages/A3/run/local_pair/seed-13"
    )
    planned_run = Path(plan["official_single"]["13"]["run_dir"])
    cwd, _, outputs = launcher._selected_command(
        {"commands": plan},
        baseline="official_single",
        seed=13,
        run_dir=planned_run,
    )
    assert str(cwd).startswith("/repo/runs/stages/A3/run/official_single/seed-13")
    assert all(str(path).startswith(str(planned_run)) for path in outputs)


def test_launcher_binds_plan_hash_and_exact_file_sets(tmp_path: Path) -> None:
    preflight = tmp_path / "preflight"
    data = preflight / "data/MAVEN_ERE"
    source = preflight / "source"
    data.mkdir(parents=True)
    source.mkdir(parents=True)
    (data / "train.jsonl").write_text("{}\n", encoding="utf-8")
    (source / "main.py").write_text("pass\n", encoding="utf-8")
    p1_hash = "b" * 64
    plan = {
        "schema_version": "ekg.a3_baseline_preflight.v1",
        "status": "pass",
        "final_valid_accessed": False,
        "p1_bundle_protocol_sha256": p1_hash,
        "hashes": {
            "data": {"train.jsonl": launcher.sha256_file(data / "train.jsonl")},
            "adapted_official_source": {
                "main.py": launcher.sha256_file(source / "main.py")
            },
        },
    }
    plan_path = preflight / "execution_plan.json"
    plan_path.write_text(json.dumps(plan), encoding="utf-8")
    plan_hash = launcher.sha256_file(plan_path)

    assert launcher._load_plan(plan_path, p1_hash, plan_hash)["status"] == "pass"
    with pytest.raises(launcher.A3LaunchError, match="plan hash mismatch"):
        launcher._load_plan(plan_path, p1_hash, "0" * 64)

    (source / "unplanned.py").write_text("raise RuntimeError\n", encoding="utf-8")
    with pytest.raises(launcher.A3LaunchError, match="file set differs"):
        launcher._load_plan(plan_path, p1_hash, plan_hash)
