#!/usr/bin/env python
"""CPU-only feasibility audits for the 2026-09-20 R1 method refresh.

The three subcommands answer different pre-training questions:

* ``d4``: do deployable relation predictions cover the frozen factuality OOF unit?
* ``a4``: can LLMERE-style rationales be derived from train-only gold without
  changing the full MAVEN-ERE candidate universe?
* ``c5``: is the measured lexical-shortcut bucket large enough to evaluate a
  counterfactual suppressor with useful power?

No subcommand trains a model or reads a proposed-model result for selection.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import sys
from collections import Counter, defaultdict
from collections.abc import Iterable
from itertools import combinations
from pathlib import Path

from scipy.stats import binom

sys.path.insert(0, str(Path(__file__).resolve().parent))

from report_coref_error_profile import official_clusterings  # noqa: E402

from ekg.nodes.coref import trigger_similarity  # noqa: E402


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def _read_jsonl(path: Path) -> list[dict]:
    records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    keys = [record.get("id", record.get("doc_id")) for record in records]
    _require(None not in keys, f"{path}: every record needs id or doc_id")
    _require(len(keys) == len(set(keys)), f"{path}: duplicate document ids")
    return records


def _by_id(path: Path) -> dict[str, dict]:
    return {
        record.get("id", record.get("doc_id")): record
        for record in _read_jsonl(path)
    }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _event_mentions(document: dict) -> tuple[dict[str, list[str]], dict[str, dict]]:
    clusters: dict[str, list[str]] = {}
    mentions: dict[str, dict] = {}
    for event in document["events"]:
        ids = []
        for mention in event["mention"]:
            mention_id = mention["id"]
            _require(mention_id not in mentions, f"{document['id']}: duplicate {mention_id}")
            mentions[mention_id] = mention
            ids.append(mention_id)
        clusters[event["id"]] = ids
    return clusters, mentions


def _relation_pairs(document: dict) -> dict[str, list[tuple[str, str]]]:
    temporal = [pair for pairs in document["temporal_relations"].values() for pair in pairs]
    causal = [pair for pairs in document["causal_relations"].values() for pair in pairs]
    return {
        "temporal": [tuple(pair) for pair in temporal],
        "causal": [tuple(pair) for pair in causal],
        "subevent": [tuple(pair) for pair in document["subevent_relations"]],
    }


def _ratio(part: int, whole: int) -> float:
    return part / whole if whole else 0.0


def _predicted_incident_from_a3(
    records: Iterable[dict], mention_ids_by_doc: dict[str, set[str]]
) -> tuple[set[tuple[str, str]], dict[str, set[tuple[str, str]]], Counter[str], int]:
    incident: set[tuple[str, str]] = set()
    incident_by_family: dict[str, set[tuple[str, str]]] = defaultdict(set)
    edge_counts: Counter[str] = Counter()
    invalid = 0
    for record in records:
        doc_id = record["id"]
        allowed = mention_ids_by_doc.get(doc_id, set())
        relation_fields = {
            "temporal": record["temporal_relations"],
            "causal": record["causal_relations"],
        }
        for family, relations in relation_fields.items():
            for pairs in relations.values():
                for left, right in pairs:
                    edge_counts[family] += 1
                    for mention_id in (left, right):
                        if mention_id.startswith("TIME_"):
                            continue
                        if mention_id not in allowed:
                            invalid += 1
                            continue
                        incident.add((doc_id, mention_id))
                        incident_by_family[family].add((doc_id, mention_id))
        for left, right in record["subevent_relations"]:
            edge_counts["subevent"] += 1
            for mention_id in (left, right):
                if mention_id not in allowed:
                    invalid += 1
                    continue
                incident.add((doc_id, mention_id))
                incident_by_family["subevent"].add((doc_id, mention_id))
        for cluster in record.get("coreference", []):
            for mention_id in cluster:
                if mention_id not in allowed:
                    invalid += 1
                    continue
                incident.add((doc_id, mention_id))
                incident_by_family["coreference"].add((doc_id, mention_id))
            edge_counts["coreference_pairs"] += len(cluster) * (len(cluster) - 1) // 2
    return incident, dict(incident_by_family), edge_counts, invalid


def _predicted_incident_from_dump(
    records: Iterable[dict], mention_ids_by_doc: dict[str, set[str]]
) -> tuple[set[tuple[str, str]], dict[str, set[tuple[str, str]]], Counter[str], int]:
    incident: set[tuple[str, str]] = set()
    incident_by_family: dict[str, set[tuple[str, str]]] = defaultdict(set)
    edge_counts: Counter[str] = Counter()
    invalid = 0
    for record in records:
        doc_id = record["doc_id"]
        allowed = mention_ids_by_doc.get(doc_id, set())
        for edge in record["edges"]:
            edge_counts[edge["relation_type"]] += 1
            head = edge["head_id"].removeprefix(f"{doc_id}::")
            tail = edge["tail_id"].removeprefix(f"{doc_id}::")
            for mention_id in (head, tail):
                if mention_id.startswith("TIME_"):
                    continue
                if mention_id not in allowed:
                    invalid += 1
                    continue
                incident.add((doc_id, mention_id))
                incident_by_family[edge["relation_type"]].add((doc_id, mention_id))
    return incident, dict(incident_by_family), edge_counts, invalid


def audit_d4(args: argparse.Namespace) -> dict:
    fact = _by_id(args.fact_train)
    ere = _by_id(args.ere_train)
    _require(set(fact) == set(ere), "MAVEN-FACT and MAVEN-ERE train document ids differ")

    label_total: Counter[str] = Counter()
    incident_by_family: dict[str, set[tuple[str, str]]] = defaultdict(set)
    mention_ids_by_doc: dict[str, set[str]] = {}
    for doc_id in sorted(fact):
        fact_clusters, fact_mentions = _event_mentions(fact[doc_id])
        ere_clusters, ere_mentions = _event_mentions(ere[doc_id])
        _require(set(fact_mentions) == set(ere_mentions), f"{doc_id}: FACT/ERE mention drift")
        mention_ids_by_doc[doc_id] = set(fact_mentions)
        for mention in fact_mentions.values():
            label_total[mention["factuality"]] += 1

        for family, pairs in _relation_pairs(ere[doc_id]).items():
            for left_event, right_event in pairs:
                for event_id in (left_event, right_event):
                    if event_id.startswith("TIME_"):
                        continue
                    _require(event_id in ere_clusters, f"{doc_id}: unknown relation endpoint")
                    for mention_id in ere_clusters[event_id]:
                        incident_by_family[family].add((doc_id, mention_id))
        for members in fact_clusters.values():
            if len(members) > 1:
                incident_by_family["coreference"].update((doc_id, mid) for mid in members)

    all_gold_incident = set().union(*incident_by_family.values())
    label_incident: Counter[str] = Counter()
    label_incident_by_family: dict[str, Counter[str]] = defaultdict(Counter)
    for doc_id, mention_id in all_gold_incident:
        _, fact_mentions = _event_mentions(fact[doc_id])
        label_incident[fact_mentions[mention_id]["factuality"]] += 1
    for family, family_incident in incident_by_family.items():
        for doc_id, mention_id in family_incident:
            _, fact_mentions = _event_mentions(fact[doc_id])
            label_incident_by_family[family][fact_mentions[mention_id]["factuality"]] += 1

    manifest = json.loads(args.internal_dev_manifest.read_text(encoding="utf-8"))
    heldout_ids = set(manifest["doc_ids"])
    a3_records = _read_jsonl(args.a3_predictions)
    _require({row["id"] for row in a3_records} == heldout_ids, "A3 prediction ids drift")
    a3_incident, a3_incident_by_family, a3_edges, a3_invalid = _predicted_incident_from_a3(
        a3_records, mention_ids_by_doc
    )
    _require(a3_invalid == 0, f"A3 predictions contain {a3_invalid} unknown mention endpoints")
    heldout_mentions = sum(len(mention_ids_by_doc[doc_id]) for doc_id in heldout_ids)

    ere_valid = _by_id(args.ere_valid)
    valid_mentions = {doc_id: set(_event_mentions(doc)[1]) for doc_id, doc in ere_valid.items()}
    public_records = _read_jsonl(args.public_prediction_dump)
    _require(
        {row["doc_id"] for row in public_records} == set(ere_valid),
        "public prediction dump does not cover released valid",
    )
    public_incident, public_incident_by_family, public_edges, public_invalid = (
        _predicted_incident_from_dump(public_records, valid_mentions)
    )
    _require(public_invalid == 0, "public prediction dump contains unknown endpoints")
    public_mention_count = sum(map(len, valid_mentions.values()))

    by_label = {
        label: {
            "mentions": count,
            "gold_relation_incident": label_incident[label],
            "gold_relation_incident_rate": _ratio(label_incident[label], count),
            "gold_incident_by_family": {
                family: label_incident_by_family[family][label]
                for family in sorted(incident_by_family)
            },
            "gold_incident_rate_by_family": {
                family: _ratio(label_incident_by_family[family][label], count)
                for family in sorted(incident_by_family)
            },
        }
        for label, count in sorted(label_total.items())
    }
    return {
        "schema_version": "r1-v62-d4-structural-input-v1",
        "inputs": {
            "fact_train": {"path": str(args.fact_train), "sha256": _sha256(args.fact_train)},
            "ere_train": {"path": str(args.ere_train), "sha256": _sha256(args.ere_train)},
            "a3_predictions": {
                "path": str(args.a3_predictions),
                "sha256": _sha256(args.a3_predictions),
            },
            "public_prediction_dump": {
                "path": str(args.public_prediction_dump),
                "sha256": _sha256(args.public_prediction_dump),
            },
        },
        "identity": {
            "documents": len(fact),
            "mentions": sum(label_total.values()),
            "fact_ere_document_set_equal": True,
            "fact_ere_mention_set_equal": True,
        },
        "gold_structure_upper_bound": {
            "by_label": by_label,
            "incident_mentions_by_family": {
                family: len(mentions) for family, mentions in sorted(incident_by_family.items())
            },
            "warning": "Diagnostic upper bound only; gold relations are forbidden at inference.",
        },
        "deployable_predictions": {
            "oof_train_unit": {
                "required_documents": len(ere),
                "currently_heldout_documents": len(heldout_ids),
                "document_coverage": _ratio(len(heldout_ids), len(ere)),
                "missing_documents": len(ere) - len(heldout_ids),
                "mentions_in_heldout_documents": heldout_mentions,
                "relation_incident_mentions": len(a3_incident),
                "incident_mention_rate_within_covered_documents": _ratio(
                    len(a3_incident), heldout_mentions
                ),
                "incident_mentions_by_family": {
                    family: len(mentions)
                    for family, mentions in sorted(a3_incident_by_family.items())
                },
                "incident_rate_by_family": {
                    family: _ratio(len(mentions), heldout_mentions)
                    for family, mentions in sorted(a3_incident_by_family.items())
                },
                "edge_counts": dict(a3_edges),
                "leakage_status": "held-out A3/P1 internal-dev predictions",
            },
            "released_valid_unit": {
                "documents": len(ere_valid),
                "mentions": public_mention_count,
                "relation_incident_mentions": len(public_incident),
                "incident_mention_rate": _ratio(len(public_incident), public_mention_count),
                "incident_mentions_by_family": {
                    family: len(mentions)
                    for family, mentions in sorted(public_incident_by_family.items())
                },
                "incident_rate_by_family": {
                    family: _ratio(len(mentions), public_mention_count)
                    for family, mentions in sorted(public_incident_by_family.items())
                },
                "edge_counts": dict(public_edges),
                "selection_use": "forbidden; identity/coverage audit only",
            },
        },
        "decision": {
            "status": "conditional_prerequisite",
            "data_available": True,
            "current_oof_input_closed": False,
            "blocker_type": "protocol/input",
            "blocker": (
                "Only the 291-document P1 internal-dev slice has held-out train-split relation "
                "predictions; the frozen 2,913-document factuality OOF unit needs leakage-free "
                "structural inputs for the remaining documents."
            ),
            "required_next": (
                "Freeze a nested or otherwise leakage-free relation-prediction design before "
                "any D4 structural pilot; never substitute gold edges."
            ),
        },
    }


def _infer_causal(left: str, right: str) -> str:
    return "CAUSE" if left == right == "CAUSE" else "PRECONDITION"


def _manifest_ids(path: Path) -> set[str]:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    _require(manifest["doc_count"] == len(manifest["doc_ids"]), f"{path}: count drift")
    return set(manifest["doc_ids"])


def _partition_map(
    mention_ids: list[str], anchor: str, *, k: int, rng: random.Random
) -> dict[str, int]:
    others = [mention_id for mention_id in mention_ids if mention_id != anchor]
    rng.shuffle(others)
    groups = max(1, math.ceil(len(others) / k))
    minimum, extra = divmod(len(others), groups)
    sizes = [minimum + (index < extra) for index in range(groups)]
    mapping: dict[str, int] = {}
    cursor = 0
    for group, size in enumerate(sizes):
        for mention_id in others[cursor : cursor + size]:
            mapping[mention_id] = group
        cursor += size
    _require(cursor == len(others), "partition did not consume all mentions")
    return mapping


def audit_a4(args: argparse.Namespace) -> dict:
    train_ids = _manifest_ids(args.train_manifest)
    documents = [doc for doc in _read_jsonl(args.ere_train) if doc["id"] in train_ids]
    _require(len(documents) == len(train_ids), "P1 train manifest/source mismatch")

    totals: Counter[str] = Counter()
    rng = random.Random(args.seed)
    for document in documents:
        clusters, mentions = _event_mentions(document)
        ordered_mentions = sorted(
            mentions,
            key=lambda mention_id: (
                mentions[mention_id]["sent_id"],
                mentions[mention_id]["offset"][0],
                mention_id,
            ),
        )
        direct_cluster: dict[tuple[str, str], set[str]] = defaultdict(set)
        for label, pairs in document["causal_relations"].items():
            for left, right in pairs:
                direct_cluster[(left, right)].add(label)

        support_cluster: dict[tuple[str, str, str], set[str]] = defaultdict(set)
        adjacency: dict[str, list[tuple[str, str]]] = defaultdict(list)
        for (left, right), labels in direct_cluster.items():
            for label in labels:
                adjacency[left].append((right, label))
        for (left, right), labels in direct_cluster.items():
            for target_label in labels:
                for middle, first_label in adjacency[left]:
                    for tail, second_label in adjacency[middle]:
                        inferred = _infer_causal(first_label, second_label)
                        if tail == right and inferred == target_label:
                            support_cluster[(left, right, target_label)].add(middle)

        direct_mention: set[tuple[str, str, str]] = set()
        support_mentions: dict[tuple[str, str, str], set[str]] = defaultdict(set)
        for (left_event, right_event), labels in direct_cluster.items():
            for left in clusters[left_event]:
                for right in clusters[right_event]:
                    for label in labels:
                        key = (left, right, label)
                        direct_mention.add(key)
                        for middle_event in support_cluster.get(
                            (left_event, right_event, label), set()
                        ):
                            support_mentions[key].update(clusters[middle_event])

        totals["documents"] += 1
        totals["mentions"] += len(mentions)
        totals["ordered_candidate_pairs"] += len(mentions) * (len(mentions) - 1)
        totals["direct_causal_pairs"] += len(direct_mention)
        totals["mentions_with_coref_rationale"] += sum(
            len(members) for members in clusters.values() if len(members) > 1
        )
        totals["direct_pairs_with_two_hop_support"] += len(support_mentions)

        partition_for_anchor = {
            anchor: _partition_map(ordered_mentions, anchor, k=args.partition_k, rng=rng)
            for anchor in ordered_mentions
        }
        retained = 0
        for key, middle_mentions in support_mentions.items():
            left, right, _ = key
            group = partition_for_anchor[left][right]
            if any(partition_for_anchor[left].get(middle) == group for middle in middle_mentions):
                retained += 1
        totals["two_hop_support_retained_by_partition"] += retained

        _require(
            all(right in partition_for_anchor[left] for left, right, _ in direct_mention),
            f"{document['id']}: direct pair missing from anchor partitions",
        )

    converter_text = args.official_converter.read_text(encoding="utf-8")
    _require("k = 30" in converter_text, "LLMERE partition constant drift")
    _require("Coreference information:" in converter_text, "LLMERE coref rationale absent")
    _require("Relevant reasoning information:" in converter_text, "LLMERE chain rationale absent")
    repo_python = list(args.official_repo.rglob("*.py"))
    trainer_names = {
        path.name
        for path in repo_python
        if "train" in path.name.lower() or "finetun" in path.name.lower()
    }
    return {
        "schema_version": "r1-v62-a4-rationale-assets-v1",
        "inputs": {
            "ere_train": {"path": str(args.ere_train), "sha256": _sha256(args.ere_train)},
            "train_manifest": {
                "path": str(args.train_manifest),
                "sha256": _sha256(args.train_manifest),
            },
            "official_converter": {
                "path": str(args.official_converter),
                "sha256": _sha256(args.official_converter),
            },
            "official_repo_head": args.repo_head,
        },
        "train_only_formal_rationales": {
            **dict(totals),
            "direct_pair_partition_coverage": 1.0,
            "two_hop_support_partition_retention": _ratio(
                totals["two_hop_support_retained_by_partition"],
                totals["direct_pairs_with_two_hop_support"],
            ),
            "note": (
                "The direct pair is always queried because each anchor is inserted into every "
                "partition. Partitioning can hide intermediate nodes, not the direct candidate."
            ),
        },
        "official_code_audit": {
            "python_files": len(repo_python),
            "trainer_like_filenames": sorted(trainer_names),
            "released_trainer_present": bool(trainer_names),
            "rationale_source": "gold coreference and causal transitive chains",
            "partition_k": 30,
        },
        "decision": {
            "status": "feasible_for_new_design_brief",
            "data_blocked": False,
            "protocol_blocked": False,
            "external_reproduction_status": "transparent adaptation; official trainer absent",
            "treatment": (
                "Add train-only coreference-equivalence and transitive-support auxiliary labels "
                "to the frozen full-context, full-candidate student."
            ),
            "negative_control": "permute rationale labels within each document",
            "guardrail": "do not partition or prune inference candidates",
        },
    }


def _coref_pair_profile(gold: dict[str, dict], prediction: dict[str, dict]) -> dict:
    counts: Counter[str] = Counter()
    for doc_id, pred_record in prediction.items():
        gold_clusters, predicted, mentions = official_clusterings(gold[doc_id], pred_record)
        predicted_pairs = {
            frozenset((left_id, right_id))
            for cluster in predicted
            for left_id, right_id in combinations(sorted(cluster), 2)
        }
        for cluster in predicted:
            for left_id, right_id in combinations(sorted(cluster), 2):
                left, right = mentions[left_id], mentions[right_id]
                if left.sent_id == right.sent_id:
                    continue
                similarity = trigger_similarity(left.trigger, right.trigger)
                wrong = left.event_id != right.event_id
                counts["cross_sentence_pairs"] += 1
                counts["wrong_pairs"] += wrong
                if similarity >= 0.8:
                    counts["hard_pairs"] += 1
                    counts["hard_wrong"] += wrong
                if similarity == 1.0:
                    counts["exact_pairs"] += 1
                    counts["exact_wrong"] += wrong
        for cluster in gold_clusters:
            for left_id, right_id in combinations(sorted(cluster), 2):
                left, right = mentions[left_id], mentions[right_id]
                if left.sent_id == right.sent_id:
                    continue
                similarity = trigger_similarity(left.trigger, right.trigger)
                missed = frozenset((left_id, right_id)) not in predicted_pairs
                counts["cross_sentence_gold_pairs"] += 1
                counts["missed_gold_pairs"] += missed
                if similarity < 0.8:
                    counts["divergent_gold_pairs"] += 1
                    counts["divergent_missed"] += missed
    return {
        **dict(counts),
        "wrong_rate": _ratio(counts["wrong_pairs"], counts["cross_sentence_pairs"]),
        "hard_wrong_rate": _ratio(counts["hard_wrong"], counts["hard_pairs"]),
        "exact_wrong_rate": _ratio(counts["exact_wrong"], counts["exact_pairs"]),
        "hard_share_of_wrong": _ratio(counts["hard_wrong"], counts["wrong_pairs"]),
        "missed_gold_rate": _ratio(
            counts["missed_gold_pairs"], counts["cross_sentence_gold_pairs"]
        ),
        "divergent_miss_rate": _ratio(
            counts["divergent_missed"], counts["divergent_gold_pairs"]
        ),
        "divergent_share_of_missed": _ratio(
            counts["divergent_missed"], counts["missed_gold_pairs"]
        ),
    }


def _counterfactual_source_pool(path: Path, train_ids: set[str]) -> dict:
    counts: Counter[str] = Counter()
    for document in _read_jsonl(path):
        if document["id"] not in train_ids:
            continue
        _, mentions = _event_mentions(document)
        event_of = {
            mention["id"]: event["id"]
            for event in document["events"]
            for mention in event["mention"]
        }
        for left_id, right_id in combinations(sorted(mentions), 2):
            left, right = mentions[left_id], mentions[right_id]
            counts["all_pairs"] += 1
            if left["sent_id"] == right["sent_id"]:
                continue
            counts["cross_sentence_pairs"] += 1
            coreferent = event_of[left_id] == event_of[right_id]
            similarity = trigger_similarity(left["trigger_word"], right["trigger_word"])
            if similarity >= 0.8 and not coreferent:
                counts["hard_noncoreferent"] += 1
            if similarity < 0.8 and coreferent:
                counts["lexically_divergent_coreferent"] += 1
            if similarity == 1.0 and not coreferent:
                counts["exact_trigger_noncoreferent"] += 1
    return dict(counts)


def _exact_binomial_power(p0: float, p1: float, *, alpha: float, target: float) -> dict:
    _require(0 < p0 < p1 < 1, "binomial alternatives must satisfy 0 < p0 < p1 < 1")
    for n in range(1, 10000):
        critical = int(binom.ppf(1 - alpha, n, p0)) + 1
        actual_alpha = float(binom.sf(critical - 1, n, p0))
        power = float(binom.sf(critical - 1, n, p1))
        if power >= target:
            return {
                "n": n,
                "critical_successes": critical,
                "critical_observed_precision": critical / n,
                "actual_alpha": actual_alpha,
                "power_at_target_precision": power,
            }
    raise AssertionError("power target not reached")


def audit_c5(args: argparse.Namespace) -> dict:
    gold = _by_id(args.gold)
    full = _by_id(args.full_prediction)
    anchor = _by_id(args.anchor_prediction)
    _require(set(gold) == set(full) == set(anchor), "C5 gold/prediction document ids differ")
    full_profile = _coref_pair_profile(gold, full)
    anchor_profile = _coref_pair_profile(gold, anchor)
    _require(full_profile["hard_pairs"] == args.expect_hard_pairs, "C-11 bucket size drift")
    _require(full_profile["hard_wrong"] == args.expect_hard_wrong, "C-11 error count drift")

    train_ids = _manifest_ids(args.train_manifest)
    source_pool = _counterfactual_source_pool(args.ere_train, train_ids)
    p0 = full_profile["hard_wrong_rate"]
    power = _exact_binomial_power(
        p0,
        args.target_precision,
        alpha=args.alpha,
        target=args.target_power,
    )
    return {
        "schema_version": "r1-v62-c5-counterfactual-feasibility-v1",
        "inputs": {
            "gold": {"path": str(args.gold), "sha256": _sha256(args.gold)},
            "full_prediction": {
                "path": str(args.full_prediction),
                "sha256": _sha256(args.full_prediction),
            },
            "anchor_prediction": {
                "path": str(args.anchor_prediction),
                "sha256": _sha256(args.anchor_prediction),
            },
            "ere_train": {"path": str(args.ere_train), "sha256": _sha256(args.ere_train)},
        },
        "measured_shortcut": {
            "full": full_profile,
            "official_joint_anchor": anchor_profile,
            "interpretation": (
                "High lexical similarity concentrates false merges but is not itself a usable "
                "suppressor: most high-similarity predicted pairs are correct. Low-similarity "
                "gold links separately measure the opposite lexical shortcut."
            ),
        },
        "train_source_pool": source_pool,
        "prospective_signal_test": {
            "null_precision": p0,
            "minimum_useful_precision": args.target_precision,
            "one_sided_alpha": args.alpha,
            "target_power": args.target_power,
            "exact_binomial": power,
            "available_evaluation_pairs": full_profile["hard_pairs"],
        },
        "decision": {
            "status": "feasible_for_new_design_brief",
            "data_blocked": False,
            "protocol_blocked": False,
            "generator_fidelity": (
                "open implementation, but the paper used cross-document K-nearest retrieval and "
                "closed-LLM generation; MAVEN adaptation must be labelled transparent"
            ),
            "treatment": (
                "Document-complete asymmetric invariance: keep high-similarity non-coreferent "
                "pairs apart and low-similarity coreferent pairs together under label-preserving "
                "trigger interventions."
            ),
            "mediator": (
                "precision on the frozen >=0.8 cross-sentence false-merge bucket plus recall on "
                "cross-sentence <0.8 gold-coreferent pairs"
            ),
            "negative_control": (
                "shuffle counterfactual pairings within document and label while preserving the "
                "generated examples, forward count and class balance"
            ),
            "pre_gpu_gate": (
                "A blinded 100-item generation audit must pass label preservation, fluency and "
                "single-variable intervention checks before classifier training."
            ),
        },
    }


def _validate_partition(
    train: set[str], selection: set[str], evaluation: set[str], universe: set[str], *, name: str
) -> None:
    _require(not train.intersection(selection), f"{name}: train/selection overlap")
    _require(not train.intersection(evaluation), f"{name}: train/evaluation overlap")
    _require(not selection.intersection(evaluation), f"{name}: selection/evaluation overlap")
    _require(train | selection | evaluation == universe, f"{name}: partition does not cover source")


def audit_d4_crossfit_plan(args: argparse.Namespace) -> dict:
    fact = _by_id(args.fact_train)
    ere = _by_id(args.ere_train)
    universe = set(fact)
    _require(universe == set(ere), "MAVEN-FACT and MAVEN-ERE train ids differ")

    cv = json.loads(args.factuality_cv.read_text(encoding="utf-8"))
    _require(cv["source"]["documents"] == len(universe), "factuality CV source count drift")
    evaluation_membership: Counter[str] = Counter()
    fold_plans = []
    for fold in cv["folds"]:
        fold_id = fold["fold"]
        manifests = {}
        sets = {}
        for role in ("train", "selection_dev", "evaluation"):
            metadata = fold[role]
            path = Path(metadata["path"])
            _require(path.exists(), f"fold {fold_id}: missing {role} manifest")
            _require(_sha256(path) == metadata["sha256"], f"fold {fold_id}: {role} hash drift")
            manifest = json.loads(path.read_text(encoding="utf-8"))
            ids = set(manifest["doc_ids"])
            _require(manifest["doc_count"] == len(ids), f"fold {fold_id}: {role} count drift")
            _require(ids <= universe, f"fold {fold_id}: {role} has unknown ids")
            sets[role] = ids
            manifests[role] = {
                "path": str(path),
                "sha256": metadata["sha256"],
                "documents": len(ids),
            }
        _validate_partition(
            sets["train"],
            sets["selection_dev"],
            sets["evaluation"],
            universe,
            name=f"fold {fold_id}",
        )
        evaluation_membership.update(sets["evaluation"])
        expected_pairs = 0
        expected_mentions = 0
        for doc_id in sets["evaluation"]:
            _, mentions = _event_mentions(ere[doc_id])
            expected_mentions += len(mentions)
            expected_pairs += len(mentions) * (len(mentions) - 1)
        fold_plans.append(
            {
                "fold": fold_id,
                "manifests": manifests,
                "selection_axis": "frozen official-joint development macro over relation families",
                "seed": args.seed,
                "expected_output": {
                    "path": f"relation_crossfit/fold-{fold_id}/causal_posteriors.jsonl",
                    "documents": len(sets["evaluation"]),
                    "mentions": expected_mentions,
                    "ordered_mention_pairs": expected_pairs,
                    "required_fields": [
                        "doc_id",
                        "head_mention_id",
                        "tail_mention_id",
                        "p_none",
                        "p_cause",
                        "p_precondition",
                    ],
                },
            }
        )

    _require(set(evaluation_membership) == universe, "evaluation folds do not cover all documents")
    duplicates = [doc_id for doc_id, count in evaluation_membership.items() if count != 1]
    _require(
        not duplicates,
        f"evaluation membership is not exactly once for {len(duplicates)} docs",
    )
    return {
        "schema_version": "r1-v62-d4-crossfit-plan-v1",
        "inputs": {
            "fact_train": {"path": str(args.fact_train), "sha256": _sha256(args.fact_train)},
            "ere_train": {"path": str(args.ere_train), "sha256": _sha256(args.ere_train)},
            "factuality_cv": {
                "path": str(args.factuality_cv),
                "sha256": _sha256(args.factuality_cv),
            },
        },
        "identity": {
            "documents": len(universe),
            "fact_ere_document_set_equal": True,
            "evaluation_exactly_once": True,
            "folds": len(fold_plans),
        },
        "folds": fold_plans,
        "posterior_contract": {
            "candidate_universe": (
                "every ordered non-self event-mention pair in each evaluation doc"
            ),
            "normalization": "p_none + p_cause + p_precondition must equal 1 within 1e-6",
            "leakage_rule": "an evaluation document must occur in neither train nor selection-dev",
            "gold_fields_forbidden": ["factuality", "gold_causal_relation"],
            "aggregation": "concatenate five evaluation dumps and require exactly 2,913 doc ids",
        },
        "decision": {
            "status": "plan_frozen_predictions_missing",
            "data_blocked": False,
            "protocol_design_closed": True,
            "input_artifact_closed": False,
            "gpu_authorized": False,
            "required_next": (
                "Implement the posterior dump adapter, pass CPU/CUDA smoke, then request the "
                "five-fold official-joint cross-fit run with exact commands and expected outputs."
            ),
        },
    }


def _sample_strata(candidates: dict[str, list[dict]], *, per_stratum: int, seed: int) -> list[dict]:
    rng = random.Random(seed)
    selected = []
    for stratum in sorted(candidates):
        pool = sorted(
            candidates[stratum],
            key=lambda item: (item["doc_id"], item["left_id"], item["right_id"]),
        )
        _require(len(pool) >= per_stratum, f"{stratum}: insufficient candidates")
        selected.extend(rng.sample(pool, per_stratum))
    rng.shuffle(selected)
    return selected


def audit_c5_generation_plan(args: argparse.Namespace) -> dict:
    train_ids = _manifest_ids(args.train_manifest)
    candidates: dict[str, list[dict]] = defaultdict(list)
    for document in _read_jsonl(args.ere_train):
        if document["id"] not in train_ids:
            continue
        _, mentions = _event_mentions(document)
        event_of = {
            mention["id"]: event["id"]
            for event in document["events"]
            for mention in event["mention"]
        }
        for left_id, right_id in combinations(sorted(mentions), 2):
            left, right = mentions[left_id], mentions[right_id]
            if left["sent_id"] == right["sent_id"]:
                continue
            coreferent = event_of[left_id] == event_of[right_id]
            similarity = trigger_similarity(left["trigger_word"], right["trigger_word"])
            if similarity >= 0.8 and not coreferent:
                stratum = "hard_noncoreferent"
                intervention = (
                    "label-preserving trigger/context edit; pair must remain non-coreferent"
                )
            elif similarity < 0.8 and coreferent:
                stratum = "divergent_coreferent"
                intervention = "label-preserving trigger/context edit; pair must remain coreferent"
            else:
                continue
            start = min(left["sent_id"], right["sent_id"])
            end = max(left["sent_id"], right["sent_id"])
            raw_id = f"{document['id']}:{left_id}:{right_id}:{stratum}:{args.seed}"
            candidates[stratum].append(
                {
                    "item_id": hashlib.sha256(raw_id.encode()).hexdigest()[:16],
                    "doc_id": document["id"],
                    "left_id": left_id,
                    "right_id": right_id,
                    "left_trigger": left["trigger_word"],
                    "right_trigger": right["trigger_word"],
                    "left_sent_id": left["sent_id"],
                    "right_sent_id": right["sent_id"],
                    "trigger_similarity": similarity,
                    "stratum": stratum,
                    "requested_intervention": intervention,
                    "context_sentences": document["sentences"][start : end + 1],
                }
            )

    sample = _sample_strata(candidates, per_stratum=args.per_stratum, seed=args.seed)
    return {
        "schema_version": "r1-v62-c5-generation-audit-plan-v1",
        "inputs": {
            "ere_train": {"path": str(args.ere_train), "sha256": _sha256(args.ere_train)},
            "train_manifest": {
                "path": str(args.train_manifest),
                "sha256": _sha256(args.train_manifest),
            },
        },
        "sampling": {
            "seed": args.seed,
            "available_by_stratum": {
                stratum: len(items) for stratum, items in sorted(candidates.items())
            },
            "selected_per_stratum": args.per_stratum,
            "selected_total": len(sample),
            "order_randomized": True,
            "model_outputs_seen_before_freeze": False,
        },
        "generator_output_contract": {
            "one_output_per_item": True,
            "required_fields": [
                "item_id",
                "edited_context",
                "edited_left_trigger",
                "edited_right_trigger",
                "edit_rationale",
            ],
            "forbidden": [
                "change the event-coreference label",
                "delete either target event",
                "add a new fact needed to decide coreference",
                "emit multiple alternatives and select after classifier results",
            ],
        },
        "blind_review": {
            "blinding": "reviewers do not see classifier scores, predictions or promotion outcome",
            "binary_fields": ["label_preserved", "fluent", "single_variable_compliant"],
            "pass_thresholds": {
                "label_preserved_overall": 0.95,
                "label_preserved_each_stratum": 0.90,
                "fluent_overall": 0.95,
                "single_variable_compliant_overall": 0.90,
            },
            "failure_rule": (
                "fail the generation family if any threshold is missed; no prompt repair on "
                "the same audit sample"
            ),
        },
        "items": sample,
        "decision": {
            "status": "rubric_and_sample_frozen_generation_missing",
            "gpu_authorized": False,
            "external_generation_authorized": False,
            "classifier_training_authorized": False,
            "required_next": (
                "Choose and disclose a generator, then generate exactly these 100 items once."
            ),
        },
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="task", required=True)

    d4 = subparsers.add_parser("d4")
    d4.add_argument(
        "--fact-train", type=Path, default=Path("data/processed/maven_fact/train.jsonl")
    )
    d4.add_argument("--ere-train", type=Path, default=Path("data/processed/maven_ere/train.jsonl"))
    d4.add_argument("--ere-valid", type=Path, default=Path("data/processed/maven_ere/valid.jsonl"))
    d4.add_argument(
        "--internal-dev-manifest",
        type=Path,
        default=Path("data/protocols/v6/manifests/maven_ere_internal-dev.json"),
    )
    d4.add_argument(
        "--a3-predictions",
        type=Path,
        default=Path("runs/stages/A3/a3-v6-20260905-r17/predictions.jsonl"),
    )
    d4.add_argument(
        "--public-prediction-dump",
        type=Path,
        default=Path("runs/relations/supervised_dump.jsonl"),
    )
    d4.add_argument("--output", required=True, type=Path)

    a4 = subparsers.add_parser("a4")
    a4.add_argument("--ere-train", type=Path, default=Path("data/processed/maven_ere/train.jsonl"))
    a4.add_argument(
        "--train-manifest",
        type=Path,
        default=Path("data/protocols/v6/manifests/maven_ere_train.json"),
    )
    a4.add_argument(
        "--official-repo",
        type=Path,
        default=Path("runs/stages/R1/r1-v61-20260904/upstream/llmere"),
    )
    a4.add_argument(
        "--official-converter",
        type=Path,
        default=Path(
            "runs/stages/R1/r1-v61-20260904/upstream/llmere/"
            "data_handle_MAVEN_ERE/convert_causal.py"
        ),
    )
    a4.add_argument(
        "--repo-head", default="94d4ef2781ec7e071d38ac7fd8632a8fffbda798"
    )
    a4.add_argument("--partition-k", type=int, default=30)
    a4.add_argument("--seed", type=int, default=42)
    a4.add_argument("--output", required=True, type=Path)

    c5 = subparsers.add_parser("c5")
    c5.add_argument(
        "--gold",
        type=Path,
        default=Path(
            "runs/stages/C5/c5-v61-argument-uncertainty-5090-r1/"
            "preflight-r2/data/MAVEN_ERE/internal-dev.jsonl"
        ),
    )
    c5.add_argument(
        "--full-prediction",
        type=Path,
        default=Path(
            "runs/stages/C5/c5-v61-argument-uncertainty-5090-r1/"
            "pilot-r2/full/predictions.jsonl"
        ),
    )
    c5.add_argument(
        "--anchor-prediction",
        type=Path,
        default=Path(
            "runs/stages/R1/r1-v61-20260904/anchors/identity/"
            "official_joint_prediction.jsonl"
        ),
    )
    c5.add_argument("--ere-train", type=Path, default=Path("data/processed/maven_ere/train.jsonl"))
    c5.add_argument(
        "--train-manifest",
        type=Path,
        default=Path("data/protocols/v6/manifests/maven_ere_train.json"),
    )
    c5.add_argument("--expect-hard-pairs", type=int, default=912)
    c5.add_argument("--expect-hard-wrong", type=int, default=213)
    c5.add_argument("--target-precision", type=float, default=0.415)
    c5.add_argument("--alpha", type=float, default=0.05)
    c5.add_argument("--target-power", type=float, default=0.80)
    c5.add_argument("--output", required=True, type=Path)

    d4_plan = subparsers.add_parser("d4-plan")
    d4_plan.add_argument(
        "--fact-train", type=Path, default=Path("data/processed/maven_fact/train.jsonl")
    )
    d4_plan.add_argument(
        "--ere-train", type=Path, default=Path("data/processed/maven_ere/train.jsonl")
    )
    d4_plan.add_argument(
        "--factuality-cv",
        type=Path,
        default=Path("runs/stages/R1/r1-v61-20260904/factuality_cv/factuality_cv.json"),
    )
    d4_plan.add_argument("--seed", type=int, default=13)
    d4_plan.add_argument("--output", required=True, type=Path)

    c5_plan = subparsers.add_parser("c5-plan")
    c5_plan.add_argument(
        "--ere-train", type=Path, default=Path("data/processed/maven_ere/train.jsonl")
    )
    c5_plan.add_argument(
        "--train-manifest",
        type=Path,
        default=Path("data/protocols/v6/manifests/maven_ere_train.json"),
    )
    c5_plan.add_argument("--per-stratum", type=int, default=50)
    c5_plan.add_argument("--seed", type=int, default=260920)
    c5_plan.add_argument("--output", required=True, type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.task == "d4":
        payload = audit_d4(args)
    elif args.task == "a4":
        payload = audit_a4(args)
    elif args.task == "c5":
        payload = audit_c5(args)
    elif args.task == "d4-plan":
        payload = audit_d4_crossfit_plan(args)
    else:
        payload = audit_c5_generation_plan(args)
    _write_json(args.output, payload)
    print(f"[{args.task}] {payload['decision']['status']}: wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
