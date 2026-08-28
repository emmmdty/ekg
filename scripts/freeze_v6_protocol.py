#!/usr/bin/env python
"""Freeze P1 v6 manifests, support statistics, digests, and preregistration."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

from ekg.relations.maven_ere_official import frozen_candidate_protocol

DEV_DOCS = 291
SPLIT_PREFIX = "ekg-v6:"
EXPECTED_FACT_DEV = {"CT+": 6835, "CT-": 129, "PS+": 198, "PS-": 19, "Uu": 14}
EXPECTED_RARE_DOCS = {"PS-": 13, "Uu": 12}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_jsonl(path: Path) -> list[dict]:
    records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    ids = [record.get("id") for record in records]
    if not all(isinstance(item, str) and item for item in ids):
        raise ValueError(f"{path} contains a missing/non-string document ID")
    if len(ids) != len(set(ids)):
        raise ValueError(f"{path} contains duplicate document IDs")
    return records


def _git_commit(repo: Path) -> tuple[str, bool]:
    commit = subprocess.run(
        ("git", "rev-parse", "HEAD"),
        cwd=repo,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    ).stdout.strip()
    dirty = bool(
        subprocess.run(
            ("git", "status", "--porcelain"),
            cwd=repo,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
        ).stdout.strip()
    )
    return commit, dirty


def _write_json(path: Path, payload: object) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return _sha256(path)


def _selection_key(doc_id: str) -> tuple[str, str]:
    return hashlib.sha256(f"{SPLIT_PREFIX}{doc_id}".encode()).hexdigest(), doc_id


def _mention_ids(record: dict) -> list[str]:
    mentions = [
        mention
        for event in record.get("events", [])
        for mention in event.get("mention", [])
    ]
    mentions.sort(
        key=lambda item: (
            item.get("sent_id", 10**9),
            (item.get("offset") or [10**9])[0],
            str(item.get("id")),
        )
    )
    return [str(item["id"]) for item in mentions]


def _event_members(record: dict) -> dict[str, tuple[str, ...]]:
    return {
        str(event["id"]): tuple(str(item["id"]) for item in event.get("mention", []))
        for event in record.get("events", [])
    }


def _expanded_labels(record: dict) -> dict[tuple[str, str], tuple[str, ...]]:
    members = _event_members(record)
    labels: dict[tuple[str, str], list[str]] = defaultdict(list)

    def add(pairs, family: str, subtype: str) -> None:
        for head_event, tail_event in pairs:
            for head in members[str(head_event)]:
                for tail in members[str(tail_event)]:
                    if head != tail:
                        labels[(head, tail)].append(f"{family}:{subtype}")

    for subtype, pairs in (record.get("causal_relations") or {}).items():
        add(pairs, "causal", str(subtype).upper())
    add(record.get("subevent_relations") or [], "subevent", "SUBEVENT_OF")
    return {pair: tuple(sorted(values)) for pair, values in labels.items()}


def _candidate_protocol(records: list[dict]) -> dict:
    return frozen_candidate_protocol(records)


def _ere_support(records: list[dict]) -> dict:
    result: dict[str, dict[str, dict[str, int]]] = {}
    relation_fields = {
        "temporal": "temporal_relations",
        "causal": "causal_relations",
    }
    for family, field in relation_fields.items():
        event_counts: Counter[str] = Counter()
        pair_counts: Counter[str] = Counter()
        doc_sets: dict[str, set[str]] = defaultdict(set)
        for record in records:
            members = _event_members(record)
            if family == "temporal":
                members.update(
                    {str(item["id"]): (str(item["id"]),) for item in record.get("TIMEX", [])}
                )
            for subtype, pairs in (record.get(field) or {}).items():
                event_counts[subtype] += len(pairs)
                for head, tail in pairs:
                    pair_counts[subtype] += len(members[str(head)]) * len(members[str(tail)])
                    doc_sets[subtype].add(str(record["id"]))
        result[family] = {
            subtype: {
                "event_relation_count": event_counts[subtype],
                "mention_pair_count": pair_counts[subtype],
                "document_support": len(doc_sets[subtype]),
            }
            for subtype in sorted(event_counts)
        }

    event_counts = Counter()
    pair_counts = Counter()
    docs = set()
    non_singleton = link_pairs = 0
    for record in records:
        members = _event_members(record)
        pairs = record.get("subevent_relations") or []
        event_counts["SUBEVENT_OF"] += len(pairs)
        for head, tail in pairs:
            pair_counts["SUBEVENT_OF"] += len(members[str(head)]) * len(members[str(tail)])
            docs.add(str(record["id"]))
        for cluster in members.values():
            if len(cluster) > 1:
                non_singleton += 1
                link_pairs += len(cluster) * (len(cluster) - 1) // 2
    result["subevent"] = {
        "SUBEVENT_OF": {
            "event_relation_count": event_counts["SUBEVENT_OF"],
            "mention_pair_count": pair_counts["SUBEVENT_OF"],
            "document_support": len(docs),
        }
    }
    result["coreference"] = {
        "non_singleton_clusters": non_singleton,
        "undirected_link_pairs": link_pairs,
    }
    return result


def _fact_support(records: list[dict]) -> dict:
    mention_counts: Counter[str] = Counter()
    doc_sets: dict[str, set[str]] = defaultdict(set)
    evidence_mentions: Counter[str] = Counter()
    for record in records:
        doc_id = str(record["id"])
        for event in record.get("events", []):
            for mention in event.get("mention", []):
                label = str(mention.get("factuality"))
                mention_counts[label] += 1
                doc_sets[label].add(doc_id)
                if mention.get("evidence_word") or mention.get("evidence_offset"):
                    evidence_mentions[label] += 1
    return {
        label: {
            "mention_count": mention_counts[label],
            "document_support": len(doc_sets[label]),
            "mentions_with_evidence": evidence_mentions[label],
        }
        for label in sorted(mention_counts)
    }


def _manifest(
    *,
    dataset: str,
    role: str,
    source: Path,
    source_records: int,
    doc_ids: list[str],
    code_state: dict,
) -> dict:
    return {
        "schema_version": "ekg.protocol_manifest.v1",
        "dataset": dataset,
        "split_role": role,
        "source_path": str(source),
        "source_records": source_records,
        "source_sha256": _sha256(source),
        "doc_count": len(doc_ids),
        "doc_ids": doc_ids,
        "selection": {
            "algorithm": (
                f"first {DEV_DOCS} by sha256('{SPLIT_PREFIX}' + doc_id), tie doc_id"
                if role == "internal-dev"
                else "set complement of frozen internal-dev"
                if role == "train"
                else "all public original-valid IDs sorted lexicographically"
            ),
            "manual_selection": False,
        },
        "generation_code": code_state,
    }


def _rewrite_processed_manifest(dataset: str, directory: Path, source_name: str) -> None:
    splits = {}
    for path in sorted(directory.glob("*.jsonl")):
        splits[path.stem] = {
            "path": str(path),
            "records": len(path.read_text(encoding="utf-8").splitlines()),
            "sha256": _sha256(path),
        }
    payload = {
        "schema_version": "ekg.processed_dataset_manifest.v2",
        "dataset": dataset,
        "source": source_name,
        "acquisition": "public release; processed files retained locally; verify by SHA-256",
        "processed_dir": str(directory),
        "paths_are_repository_relative": True,
        "splits": splits,
    }
    _write_json(directory / "manifest.json", payload)


def _update_access_ledger(root: Path, valid_paths: list[Path]) -> str:
    path = root / "access_ledger.json"
    ledger = (
        json.loads(path.read_text(encoding="utf-8"))
        if path.exists()
        else {
            "schema_version": "ekg.final_valid_access.v1",
            "historical_final_access_disclosed": True,
            "v6_confirmatory_eval_count": 0,
            "entries": [],
        }
    )
    existing = {(item.get("asset"), item.get("operation")) for item in ledger["entries"]}
    for valid in valid_paths:
        entry = {
            "asset": str(valid),
            "sha256": _sha256(valid),
            "purpose": "protocol_fixture",
            "operation": "freeze_ids_and_support_counts",
            "model_output": False,
        }
        if (entry["asset"], entry["operation"]) not in existing:
            ledger["entries"].append(entry)
    count = ledger.get("v6_confirmatory_eval_count")
    if not isinstance(count, int) or count < 0:
        raise ValueError("access ledger confirmatory count must be a non-negative integer")
    return _write_json(path, ledger)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, default=Path("data/protocols/v6"))
    args = parser.parse_args()
    repo = args.repo.resolve()
    output = args.output
    script = repo / "scripts" / "freeze_v6_protocol.py"
    commit, dirty = _git_commit(repo)
    code_state = {
        "git_commit": commit,
        "working_tree_dirty": dirty,
        "script_path": "scripts/freeze_v6_protocol.py",
        "script_sha256": _sha256(script),
    }

    sources = {
        "maven_ere": {
            "train": Path("data/processed/maven_ere/train.jsonl"),
            "valid": Path("data/processed/maven_ere/valid.jsonl"),
        },
        "maven_fact": {
            "train": Path("data/processed/maven_fact/train.jsonl"),
            "valid": Path("data/processed/maven_fact/valid.jsonl"),
        },
    }
    records = {
        dataset: {split: _read_jsonl(path) for split, path in paths.items()}
        for dataset, paths in sources.items()
    }
    ere_train_ids = {item["id"] for item in records["maven_ere"]["train"]}
    fact_train_ids = {item["id"] for item in records["maven_fact"]["train"]}
    ere_valid_ids = {item["id"] for item in records["maven_ere"]["valid"]}
    fact_valid_ids = {item["id"] for item in records["maven_fact"]["valid"]}
    if ere_train_ids != fact_train_ids or ere_valid_ids != fact_valid_ids:
        raise ValueError("MAVEN-ERE and MAVEN-FACT document IDs are not aligned")
    if ere_train_ids & ere_valid_ids:
        raise ValueError("public train and final-valid document IDs overlap")

    internal_dev_ids = sorted(ere_train_ids, key=_selection_key)[:DEV_DOCS]
    train_ids = sorted(ere_train_ids - set(internal_dev_ids))
    final_valid_ids = sorted(ere_valid_ids)
    selected_records: dict[str, dict[str, list[dict]]] = {}
    id_roles = {
        "train": train_ids,
        "internal-dev": internal_dev_ids,
        "final-valid": final_valid_ids,
    }
    for dataset in sources:
        train_by_id = {item["id"]: item for item in records[dataset]["train"]}
        valid_by_id = {item["id"]: item for item in records[dataset]["valid"]}
        selected_records[dataset] = {
            "train": [train_by_id[item] for item in train_ids],
            "internal-dev": [train_by_id[item] for item in internal_dev_ids],
            "final-valid": [valid_by_id[item] for item in final_valid_ids],
        }

    fact_dev = _fact_support(selected_records["maven_fact"]["internal-dev"])
    actual_fact = {label: item["mention_count"] for label, item in fact_dev.items()}
    actual_rare = {label: fact_dev[label]["document_support"] for label in EXPECTED_RARE_DOCS}
    if actual_fact != EXPECTED_FACT_DEV or actual_rare != EXPECTED_RARE_DOCS:
        raise ValueError(
            "frozen FACT internal-dev support mismatch: "
            f"mentions={actual_fact} rare_doc_support={actual_rare}"
        )

    manifest_hashes: dict[str, str] = {}
    for dataset, paths in sources.items():
        for role, doc_ids in id_roles.items():
            source_split = "valid" if role == "final-valid" else "train"
            payload = _manifest(
                dataset=dataset,
                role=role,
                source=paths[source_split],
                source_records=len(records[dataset][source_split]),
                doc_ids=doc_ids,
                code_state=code_state,
            )
            relative = f"manifests/{dataset}_{role}.json"
            manifest_hashes[relative] = _write_json(output / relative, payload)

    support = {
        dataset: {
            role: (
                _ere_support(role_records)
                if dataset == "maven_ere"
                else _fact_support(role_records)
            )
            for role, role_records in roles.items()
        }
        for dataset, roles in selected_records.items()
    }
    support_hash = _write_json(output / "support_counts.json", support)
    candidate_protocol = {
        role: _candidate_protocol(role_records)
        for role, role_records in selected_records["maven_ere"].items()
    }
    candidate_hash = _write_json(output / "ch2_candidate_protocol.json", candidate_protocol)

    cgep_source = Path("src/ekg/succession/data/cgep.py")
    cgep_cli = Path("scripts/build_cgep.py")
    namespace = {
        "schema_version": "ekg.shared_id_namespace.v1",
        "document_id": "public MAVEN id",
        "event_mention_id": "{doc_id}::{mention_id}",
        "event_cluster_id": "{doc_id}::{event_id}",
        "ch4_query_schema": {
            "class": "ekg.succession.data.cgep.CgepInstance",
            "fields": ["instance_id", "doc_id", "nodes", "edges", "candidates", "label"],
        },
        "ch4_generator": {
            "source_path": str(cgep_source),
            "source_sha256": _sha256(cgep_source),
            "cli_path": str(cgep_cli),
            "cli_sha256": _sha256(cgep_cli),
            "default_candidate_count": 512,
            "query_manifest_freeze_phase": "E3.0",
            "queries_generated_in_p1": False,
        },
    }
    namespace_hash = _write_json(output / "shared_id_namespace.json", namespace)
    preregistration = {
        "schema_version": "ekg.p1_preregistration.v2",
        "primary_eligible_roster": ["maven_ere_official_single", "maven_ere_official_joint"],
        "primary_anchor_selection_rule": (
            "highest internal-dev causal micro-F1 mean among eligible baselines; "
            "ties follow roster order"
        ),
        "local_pair_primary_eligible": False,
        "matched_seeds": [13, 17, 42],
        "document_cluster_paired_bootstrap_resamples": 10000,
        "seed_aggregation": (
            "recompute each seed metric inside each document-cluster resample, then compare "
            "the mean across matched seeds; at least 2/3 seed deltas must agree in direction"
        ),
        # Guardrail anchors must be a baseline that actually predicts the family.
        # official_single is causal-only, so it can win the causal anchor while
        # having no subevent/temporal output at all; joint is the only roster
        # member scoring every family.
        "subevent_guardrail_anchor": "maven_ere_official_joint",
        "subevent_noninferiority_margin": {
            "metric": "micro_f1_percentage_points",
            "value": 1.0,
            "reference": "subevent_guardrail_anchor matched-seed mean",
            "rule": "method_mean >= subevent_guardrail_anchor_mean - 1.0",
        },
        "temporal_guardrail_anchor": "maven_ere_official_joint",
        "temporal_noninferiority_margin": {
            "metric": "micro_f1_percentage_points",
            "value": 1.0,
            "reference": "temporal_guardrail_anchor matched-seed mean",
            "rule": "method_mean >= temporal_guardrail_anchor_mean - 1.0",
        },
        "scored_relation_families": ["causal", "subevent", "temporal"],
        "temporal_candidate_universe": (
            "event mentions + TIMEX (official ignore_timex=False); causal/subevent "
            "remain event-only, matching official ignore_timex=True"
        ),
        "final_valid_unlock": (
            "baseline anchors and method checkpoints/configs/thresholds must be frozen first; "
            "all are unsealed in one batch; infrastructure retry is allowed only when no metrics "
            "were returned and all hashes remain identical"
        ),
    }
    prereg_hash = _write_json(output / "preregistration.json", preregistration)

    _rewrite_processed_manifest(
        "maven_ere", Path("data/processed/maven_ere"), "MAVEN-ERE, EMNLP 2022"
    )
    _rewrite_processed_manifest(
        "maven_fact",
        Path("data/processed/maven_fact"),
        "MAVEN-FACT, Findings of EMNLP 2024",
    )
    access_ledger_hash = _update_access_ledger(
        output,
        [sources["maven_ere"]["valid"], sources["maven_fact"]["valid"]],
    )

    registry = {
        "schema_version": "ekg.protocol_registry.v1",
        "protocol": "v6",
        "global_protocol_status": "conditional",
        "a3_entry_status": "conditional",
        "generation_code": code_state,
        "manifest_sha256": manifest_hashes,
        "support_counts_sha256": support_hash,
        "candidate_protocol_sha256": candidate_hash,
        "shared_id_namespace_sha256": namespace_hash,
        "preregistration_sha256": prereg_hash,
        "access_ledger_sha256": access_ledger_hash,
        "source_sha256": {
            str(path): _sha256(path)
            for paths in sources.values()
            for path in paths.values()
        },
    }
    _write_json(output / "registry.json", registry)
    print(
        f"[p1-freeze] PASS: train={len(train_ids)} internal-dev={len(internal_dev_ids)} "
        f"final-valid={len(final_valid_ids)} manifests={len(manifest_hashes)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
