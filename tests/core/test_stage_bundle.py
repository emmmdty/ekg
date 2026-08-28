"""P1 stage-bundle integrity and propagation-stop tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from ekg.core.stage_bundle import (
    StageBundleError,
    create_stage_bundle,
    sha256_file,
    validate_stage_bundle,
)


def _status(upstream: list[str] | None = None) -> dict:
    return {
        "status": "conditional",
        "global_protocol_status": "pass",
        "phase_status": "conditional",
        "next_entry_status": "conditional",
        "primary_anchor_selection_rule": "frozen rule",
        "primary_anchor": None,
        "historical_final_access_disclosed": True,
        "final_valid_access_ledger": "data/protocols/v6/access_ledger.json",
        "v6_confirmatory_eval_count": 0,
        "exploratory": False,
        "upstream_bundle_ids": upstream or [],
    }


def _make(path: Path, *, predictions: list[dict] | None = None, upstream=None) -> Path:
    records = predictions if predictions is not None else [{"id": "d1"}, {"id": "d2"}]
    evidence = path.parent / "evidence"
    evidence.mkdir(exist_ok=True)
    hashes: dict[str, dict[str, str]] = {}
    for category in ("data", "manifests", "candidate", "evaluator", "config", "code"):
        evidence_path = evidence / f"{category}.json"
        evidence_path.write_text(f'{{"category":"{category}"}}\n', encoding="utf-8")
        relative = str(evidence_path.relative_to(path.parent))
        hashes[category] = {relative: sha256_file(evidence_path)}
    remote = evidence / "remote.json"
    remote.write_text('{"status":"pass"}\n', encoding="utf-8")
    hashes["checkpoint"] = {"runs/remote/model.safetensors": "f" * 64}
    create_stage_bundle(
        path,
        phase="P1",
        predictions=records,
        metrics={"gate": "pass"},
        status=_status(upstream),
        hashes=hashes,
        expected_ids=["d1", "d2"],
        candidate_id_digest="c" * 64,
        population_counts={"documents": 2, "ordered_mention_pairs": 10},
        local_hash_categories=("data", "manifests", "candidate", "evaluator", "config", "code"),
        remote_evidence_sha256={
            str(remote.relative_to(path.parent)): sha256_file(remote)
        },
    )
    return path.parent


def _validate(bundle: Path, root: Path, **kwargs):
    return validate_stage_bundle(
        bundle,
        evidence_root=root,
        expected_protocol_sha256=sha256_file(bundle / "protocol.json"),
        **kwargs,
    )


def test_valid_bundle_passes(tmp_path: Path) -> None:
    bundle = tmp_path / "p1-test"
    root = _make(bundle)
    result = _validate(bundle, root, known_upstream_bundle_ids=set())
    assert result["status"]["global_protocol_status"] == "pass"


def test_bad_artifact_hash_stops_validation(tmp_path: Path) -> None:
    bundle = tmp_path / "p1-test"
    root = _make(bundle)
    (bundle / "metrics.json").write_text('{"gate":"changed"}\n', encoding="utf-8")
    with pytest.raises(StageBundleError, match="artifact hash mismatch"):
        _validate(bundle, root)


def test_duplicate_and_missing_prediction_ids_stop_validation(tmp_path: Path) -> None:
    duplicate = tmp_path / "duplicate"
    duplicate_root = _make(duplicate, predictions=[{"id": "d1"}, {"id": "d1"}])
    with pytest.raises(StageBundleError, match="duplicate IDs"):
        _validate(duplicate, duplicate_root)

    missing = tmp_path / "missing"
    missing_root = _make(missing, predictions=[{"id": "d1"}])
    with pytest.raises(StageBundleError, match="prediction ID set mismatch"):
        _validate(missing, missing_root)


def test_unknown_upstream_bundle_stops_validation(tmp_path: Path) -> None:
    bundle = tmp_path / "p1-test"
    root = _make(bundle, upstream=["unknown-a3"])
    with pytest.raises(StageBundleError, match="unknown upstream"):
        _validate(bundle, root, known_upstream_bundle_ids={"known-p1"})


def test_protocol_hash_is_a_required_trust_root(tmp_path: Path) -> None:
    bundle = tmp_path / "p1-test"
    root = _make(bundle)
    trusted = sha256_file(bundle / "protocol.json")
    protocol = (bundle / "protocol.json").read_text(encoding="utf-8")
    (bundle / "protocol.json").write_text(protocol.replace('"phase": "P1"', '"phase": "X"'))
    with pytest.raises(StageBundleError, match="protocol hash mismatch"):
        validate_stage_bundle(
            bundle,
            evidence_root=root,
            expected_protocol_sha256=trusted,
        )


def test_external_evidence_tampering_stops_validation(tmp_path: Path) -> None:
    bundle = tmp_path / "p1-test"
    root = _make(bundle)
    (root / "evidence/data.json").write_text('{"changed":true}\n', encoding="utf-8")
    with pytest.raises(StageBundleError, match="external evidence hash mismatch"):
        _validate(bundle, root)


def test_fabricated_declared_external_hash_stops_even_with_updated_protocol_hash(
    tmp_path: Path,
) -> None:
    bundle = tmp_path / "p1-test"
    root = _make(bundle)
    protocol_path = bundle / "protocol.json"
    import json

    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    key = next(iter(protocol["hashes"]["data"]))
    protocol["hashes"]["data"][key] = "0" * 64
    protocol_path.write_text(json.dumps(protocol, indent=2, sort_keys=True) + "\n")
    with pytest.raises(StageBundleError, match="external evidence hash mismatch"):
        _validate(bundle, root)


def test_status_fields_must_agree(tmp_path: Path) -> None:
    bundle = tmp_path / "p1-test"
    root = _make(bundle)
    import json

    status_path = bundle / "status.json"
    status = json.loads(status_path.read_text(encoding="utf-8"))
    status["phase_status"] = "pass"
    status_path.write_text(json.dumps(status, sort_keys=True) + "\n")
    protocol_path = bundle / "protocol.json"
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    protocol["artifact_sha256"]["status.json"] = sha256_file(status_path)
    protocol_path.write_text(json.dumps(protocol, indent=2, sort_keys=True) + "\n")
    with pytest.raises(StageBundleError, match="status and phase_status disagree"):
        _validate(bundle, root)
