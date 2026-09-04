from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "freeze_r1_factuality_cv", ROOT / "scripts/freeze_r1_factuality_cv.py"
)
assert SPEC and SPEC.loader
cv = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(cv)


def _three_document_source(tmp_path: Path, fixtures_dir: Path) -> Path:
    records = [
        json.loads(line)
        for line in (fixtures_dir / "maven_fact" / "sample.jsonl").read_text().splitlines()
    ]
    third = {**records[0], "id": "fdoc3"}
    source = tmp_path / "source.jsonl"
    source.write_text(
        "".join(json.dumps(record) + "\n" for record in [*records, third]),
        encoding="utf-8",
    )
    return source


def test_assign_groups_rejects_duplicate_ids(fixtures_dir) -> None:
    from ekg.relations.data.maven_fact import load_maven_fact

    documents = list(load_maven_fact(fixtures_dir / "maven_fact" / "sample.jsonl"))
    with pytest.raises(ValueError, match="duplicate document IDs"):
        cv.assign_groups([*documents, documents[0]], folds=3, seed=7)


def test_freeze_rotates_three_disjoint_roles(tmp_path, fixtures_dir) -> None:
    source = _three_document_source(tmp_path, fixtures_dir)
    report = cv.freeze(source, tmp_path / "cv", folds=3, seed=7)

    assert report["status"] == "pass"
    assert report["config"]["final_valid_accessed"] is False
    assert len(report["folds"]) == 3
    source_ids = set()
    evaluation_ids = []
    for row in report["folds"]:
        roles = []
        for role in ("train", "selection_dev", "evaluation"):
            manifest = json.loads(Path(row[role]["path"]).read_text(encoding="utf-8"))
            assert manifest["final_valid_accessed"] is False
            assert manifest["doc_count"] == len(manifest["doc_ids"])
            roles.append(set(manifest["doc_ids"]))
        assert not (roles[0] & roles[1] or roles[0] & roles[2] or roles[1] & roles[2])
        assert len(set().union(*roles)) == 3
        source_ids.update(*roles)
        evaluation_ids.extend(roles[2])
    assert len(source_ids) == 3
    assert len(evaluation_ids) == len(set(evaluation_ids)) == 3


def test_assignment_is_independent_of_source_order(tmp_path, fixtures_dir) -> None:
    from ekg.relations.data.maven_fact import load_maven_fact

    source = _three_document_source(tmp_path, fixtures_dir)
    documents = list(load_maven_fact(source))
    forward = cv.assign_groups(documents, folds=3, seed=7)
    reverse = cv.assign_groups(list(reversed(documents)), folds=3, seed=7)
    assert [[d.doc_id for d in group] for group in forward] == [
        [d.doc_id for d in group] for group in reverse
    ]
