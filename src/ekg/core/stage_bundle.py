"""Hash-bound four-file stage bundles for v6 experiment handoffs.

``protocol.json`` cannot authenticate itself.  A caller must therefore supply a
trusted protocol digest (normally from the protocol registry) and a repository
root from which every locally resolvable evidence hash is recomputed.
"""

from __future__ import annotations

import hashlib
import json
import string
from collections.abc import Iterable, Mapping
from pathlib import Path

SCHEMA_VERSION = "ekg.stage_bundle.v2"
STATUS_VALUES = {"pass", "conditional", "failed", "blocked"}
GLOBAL_STATUS_VALUES = {"pass", "conditional", "blocked"}
FILES = ("protocol.json", "predictions.jsonl", "metrics.json", "status.json")
HASH_KEYS = {"data", "manifests", "candidate", "evaluator", "config", "code", "checkpoint"}


class StageBundleError(ValueError):
    """A stage bundle is incomplete, inconsistent, or has drifted."""


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def is_sha256(value: object) -> bool:
    """Return whether *value* is a lowercase/uppercase SHA-256 hex digest."""
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in string.hexdigits for character in value)
    )


def tree_sha256(root: Path, paths: Iterable[Path]) -> str:
    """Hash a deterministic set of repository-relative files and their contents."""
    digest = hashlib.sha256()
    relative_paths = sorted({Path(path) for path in paths}, key=lambda item: item.as_posix())
    for relative_path in relative_paths:
        if relative_path.is_absolute() or ".." in relative_path.parts:
            raise ValueError(f"tree hash path must be repository-relative: {relative_path}")
        target = root / relative_path
        if not target.is_file():
            raise FileNotFoundError(target)
        digest.update(f"{relative_path.as_posix()}\0".encode())
        digest.update(target.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def id_digest(ids: Iterable[str]) -> str:
    digest = hashlib.sha256()
    for item in sorted(ids):
        digest.update(f"{item}\n".encode())
    return digest.hexdigest()


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _prediction_ids(path: Path) -> list[str]:
    ids: list[str] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise StageBundleError(f"predictions line {line_number} is invalid JSON") from exc
        prediction_id = record.get("id")
        if not isinstance(prediction_id, str) or not prediction_id:
            raise StageBundleError(f"predictions line {line_number} has no string id")
        ids.append(prediction_id)
    if len(ids) != len(set(ids)):
        raise StageBundleError("predictions.jsonl contains duplicate IDs")
    return ids


def create_stage_bundle(
    path: Path,
    *,
    phase: str,
    predictions: Iterable[Mapping],
    metrics: Mapping,
    status: Mapping,
    hashes: Mapping[str, object],
    expected_ids: Iterable[str],
    candidate_id_digest: str,
    population_counts: Mapping[str, int],
    local_hash_categories: Iterable[str],
    remote_evidence_sha256: Mapping[str, str] | None = None,
    protocol_extra: Mapping[str, object] | None = None,
) -> None:
    """Write a complete bundle; validation remains a separate mandatory step."""
    path.mkdir(parents=True, exist_ok=True)
    prediction_records = list(predictions)
    (path / "predictions.jsonl").write_text(
        "".join(json.dumps(item, sort_keys=True) + "\n" for item in prediction_records),
        encoding="utf-8",
    )
    _write_json(path / "metrics.json", metrics)
    status_payload = dict(status)
    status_payload.setdefault("schema_version", SCHEMA_VERSION)
    _write_json(path / "status.json", status_payload)
    expected = list(expected_ids)
    protocol = {
        "schema_version": SCHEMA_VERSION,
        "bundle_id": path.name,
        "phase": phase,
        "hashes": dict(hashes),
        "local_hash_categories": sorted(set(local_hash_categories)),
        "remote_evidence_sha256": dict(remote_evidence_sha256 or {}),
        "candidate_id_digest": candidate_id_digest,
        "population_counts": dict(population_counts),
        "expected_prediction_ids": expected,
        "prediction_id_digest_sha256": id_digest(expected),
        "prediction_count": len(expected),
        "artifact_sha256": {
            name: sha256_file(path / name)
            for name in ("predictions.jsonl", "metrics.json", "status.json")
        },
    }
    if protocol_extra:
        protocol.update(protocol_extra)
    _write_json(path / "protocol.json", protocol)


def validate_stage_bundle(
    path: Path,
    *,
    evidence_root: Path,
    expected_protocol_sha256: str,
    known_upstream_bundle_ids: set[str] | None = None,
) -> dict[str, object]:
    """Validate the trust root, external evidence, bundle contents, and IDs."""
    missing_files = [name for name in FILES if not (path / name).is_file()]
    if missing_files:
        raise StageBundleError(f"bundle is missing files: {missing_files}")
    if not is_sha256(expected_protocol_sha256):
        raise StageBundleError("expected_protocol_sha256 must be a SHA-256 hex digest")
    actual_protocol_sha256 = sha256_file(path / "protocol.json")
    if actual_protocol_sha256 != expected_protocol_sha256:
        raise StageBundleError(
            "protocol hash mismatch: "
            f"expected {expected_protocol_sha256}, got {actual_protocol_sha256}"
        )
    protocol = json.loads((path / "protocol.json").read_text(encoding="utf-8"))
    metrics = json.loads((path / "metrics.json").read_text(encoding="utf-8"))
    status = json.loads((path / "status.json").read_text(encoding="utf-8"))
    if not isinstance(metrics, dict):
        raise StageBundleError("metrics.json must contain an object")
    if protocol.get("schema_version") != SCHEMA_VERSION:
        raise StageBundleError("protocol schema_version mismatch")
    if protocol.get("bundle_id") != path.name:
        raise StageBundleError("protocol bundle_id does not match directory name")
    if status.get("schema_version") != SCHEMA_VERSION:
        raise StageBundleError("status schema_version mismatch")
    if status.get("status") not in STATUS_VALUES:
        raise StageBundleError(f"invalid status {status.get('status')!r}")
    required_status = {
        "global_protocol_status",
        "phase_status",
        "next_entry_status",
        "primary_anchor_selection_rule",
        "primary_anchor",
        "historical_final_access_disclosed",
        "final_valid_access_ledger",
        "v6_confirmatory_eval_count",
        "exploratory",
        "upstream_bundle_ids",
    }
    absent_status = required_status - status.keys()
    if absent_status:
        raise StageBundleError(f"status.json missing keys: {sorted(absent_status)}")
    if status["global_protocol_status"] not in GLOBAL_STATUS_VALUES:
        raise StageBundleError("invalid global_protocol_status")
    if status["phase_status"] not in STATUS_VALUES:
        raise StageBundleError("invalid phase_status")
    if status["next_entry_status"] not in STATUS_VALUES:
        raise StageBundleError("invalid next_entry_status")
    if status["status"] != status["phase_status"]:
        raise StageBundleError("status and phase_status disagree")
    if "a3_entry_status" in status and status["a3_entry_status"] != status["next_entry_status"]:
        raise StageBundleError("a3_entry_status and next_entry_status disagree")
    for key in ("historical_final_access_disclosed", "exploratory"):
        if not isinstance(status[key], bool):
            raise StageBundleError(f"{key} must be boolean")
    if not isinstance(status["v6_confirmatory_eval_count"], int) or status[
        "v6_confirmatory_eval_count"
    ] < 0:
        raise StageBundleError("v6_confirmatory_eval_count must be a non-negative integer")
    if not isinstance(status["final_valid_access_ledger"], str) or not status[
        "final_valid_access_ledger"
    ]:
        raise StageBundleError("final_valid_access_ledger must be a non-empty path")
    if set(protocol.get("hashes", {})) != HASH_KEYS:
        raise StageBundleError(f"protocol hashes must contain exactly {sorted(HASH_KEYS)}")

    local_categories = protocol.get("local_hash_categories")
    if not isinstance(local_categories, list) or not all(
        isinstance(category, str) for category in local_categories
    ):
        raise StageBundleError("local_hash_categories must be a string list")
    if len(local_categories) != len(set(local_categories)):
        raise StageBundleError("local_hash_categories contains duplicates")
    unknown_local_categories = set(local_categories) - HASH_KEYS
    if unknown_local_categories:
        raise StageBundleError(
            f"unknown local hash categories: {sorted(unknown_local_categories)}"
        )

    def validate_hash_mapping(name: str, value: object) -> dict[str, str]:
        if not isinstance(value, dict):
            raise StageBundleError(f"{name} must map paths to SHA-256 digests")
        for raw_path, digest in value.items():
            if not isinstance(raw_path, str) or not raw_path:
                raise StageBundleError(f"{name} contains an invalid path")
            if not is_sha256(digest):
                raise StageBundleError(f"{name}[{raw_path!r}] is not a SHA-256 digest")
        return value

    hash_groups = {
        category: validate_hash_mapping(f"hashes.{category}", protocol["hashes"][category])
        for category in sorted(HASH_KEYS)
    }

    def resolve_evidence(relative_path: str, expected_hash: str, *, field: str) -> None:
        path_object = Path(relative_path)
        if path_object.is_absolute() or ".." in path_object.parts:
            raise StageBundleError(f"{field} path must be repository-relative: {relative_path}")
        resolved = evidence_root / path_object
        if not resolved.is_file():
            raise StageBundleError(f"{field} file is missing: {relative_path}")
        actual_hash = sha256_file(resolved)
        if actual_hash != expected_hash:
            raise StageBundleError(
                f"external evidence hash mismatch for {relative_path}: "
                f"expected {expected_hash}, got {actual_hash}"
            )

    for category in local_categories:
        if not hash_groups[category]:
            raise StageBundleError(f"local hash category {category} must not be empty")
        for relative_path, digest in hash_groups[category].items():
            resolve_evidence(relative_path, digest, field=f"hashes.{category}")

    remote_categories = HASH_KEYS - set(local_categories)
    remote_evidence = validate_hash_mapping(
        "remote_evidence_sha256", protocol.get("remote_evidence_sha256")
    )
    if any(hash_groups[category] for category in remote_categories) and not remote_evidence:
        raise StageBundleError("remote hash categories require a local evidence snapshot")
    for relative_path, digest in remote_evidence.items():
        resolve_evidence(relative_path, digest, field="remote_evidence_sha256")

    artifact_hashes = protocol.get("artifact_sha256")
    artifact_hashes = validate_hash_mapping("artifact_sha256", artifact_hashes)
    expected_artifacts = {"predictions.jsonl", "metrics.json", "status.json"}
    if set(artifact_hashes) != expected_artifacts:
        raise StageBundleError(
            f"artifact_sha256 must contain exactly {sorted(expected_artifacts)}"
        )
    for name in ("predictions.jsonl", "metrics.json", "status.json"):
        expected_hash = artifact_hashes.get(name)
        actual_hash = sha256_file(path / name)
        if expected_hash != actual_hash:
            raise StageBundleError(
                f"artifact hash mismatch for {name}: expected {expected_hash}, got {actual_hash}"
            )

    prediction_ids = _prediction_ids(path / "predictions.jsonl")
    expected_ids = protocol.get("expected_prediction_ids")
    if not isinstance(expected_ids, list) or not all(
        isinstance(item, str) for item in expected_ids
    ):
        raise StageBundleError("expected_prediction_ids must be a string list")
    if len(expected_ids) != len(set(expected_ids)):
        raise StageBundleError("expected_prediction_ids contains duplicates")
    if set(prediction_ids) != set(expected_ids):
        raise StageBundleError(
            "prediction ID set mismatch: "
            f"missing={sorted(set(expected_ids) - set(prediction_ids))} "
            f"extra={sorted(set(prediction_ids) - set(expected_ids))}"
        )
    if protocol.get("prediction_count") != len(prediction_ids):
        raise StageBundleError("prediction_count does not match predictions.jsonl")
    if protocol.get("prediction_id_digest_sha256") != id_digest(prediction_ids):
        raise StageBundleError("prediction ID digest mismatch")
    counts = protocol.get("population_counts")
    if not isinstance(counts, dict) or counts.get("documents") != len(prediction_ids):
        raise StageBundleError("population_counts.documents does not match prediction IDs")
    if not all(isinstance(value, int) and value >= 0 for value in counts.values()):
        raise StageBundleError("population_counts values must be non-negative integers")
    candidate_digest = protocol.get("candidate_id_digest")
    if not is_sha256(candidate_digest):
        raise StageBundleError("candidate_id_digest must be a SHA-256 hex digest")

    upstream = status["upstream_bundle_ids"]
    if not isinstance(upstream, list) or not all(isinstance(item, str) for item in upstream):
        raise StageBundleError("upstream_bundle_ids must be a string list")
    if known_upstream_bundle_ids is not None:
        unknown = set(upstream) - known_upstream_bundle_ids
        if unknown:
            raise StageBundleError(f"unknown upstream bundle IDs: {sorted(unknown)}")
    return {"protocol": protocol, "metrics": metrics, "status": status}
