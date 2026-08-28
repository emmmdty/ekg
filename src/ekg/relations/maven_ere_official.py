"""Strict MAVEN-ERE official-submission conversion and validation.

The organisers' evaluator intentionally tolerates missing documents and unknown
endpoints. That is convenient for a leaderboard, but unsafe for a frozen local
protocol: a truncated prediction file can silently become lower recall. This
module validates the complete candidate population before the unmodified scorer
is called and provides the gold-to-mention-pair converter used by P1 fixtures.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping

TEMPORAL_SUBTYPES = (
    "BEFORE",
    "OVERLAP",
    "CONTAINS",
    "SIMULTANEOUS",
    "ENDS-ON",
    "BEGINS-ON",
)
CAUSAL_SUBTYPES = ("CAUSE", "PRECONDITION")


class OfficialProtocolError(ValueError):
    """Prediction data do not satisfy the frozen official protocol."""


def records_by_id(records: Iterable[dict], *, source: str) -> dict[str, dict]:
    """Index records and reject absent or duplicate document IDs."""
    result: dict[str, dict] = {}
    for index, record in enumerate(records, start=1):
        doc_id = record.get("id")
        if not isinstance(doc_id, str) or not doc_id:
            raise OfficialProtocolError(f"{source} record {index} has no string id")
        if doc_id in result:
            raise OfficialProtocolError(f"{source} contains duplicate document id {doc_id}")
        result[doc_id] = record
    return result


def _event_members(record: Mapping) -> dict[str, tuple[str, ...]]:
    members: dict[str, tuple[str, ...]] = {}
    for event in record.get("events", []):
        event_id = str(event["id"])
        mentions = tuple(str(item["id"]) for item in event.get("mention", []))
        if not mentions:
            raise OfficialProtocolError(f"event {event_id} has no mentions")
        members[event_id] = mentions
    for timex in record.get("TIMEX", []):
        members[str(timex["id"])] = (str(timex["id"]),)
    return members


def _expand_pairs(
    pairs: Iterable[Iterable[str]], members: Mapping[str, tuple[str, ...]]
) -> list[list[str]]:
    expanded: list[list[str]] = []
    for raw_pair in pairs:
        pair = list(raw_pair)
        if len(pair) != 2 or pair[0] not in members or pair[1] not in members:
            raise OfficialProtocolError(f"gold relation has invalid event pair {pair}")
        for head in members[pair[0]]:
            for tail in members[pair[1]]:
                if head != tail:
                    expanded.append([head, tail])
    return expanded


def gold_to_official_prediction(record: Mapping) -> dict:
    """Convert one labelled record to the evaluator's mention-pair shape."""
    members = _event_members(record)
    coreference = [
        [str(mention["id"]) for mention in event.get("mention", [])]
        for event in record.get("events", [])
    ]
    temporal = {
        subtype: _expand_pairs(
            (record.get("temporal_relations") or {}).get(subtype, []), members
        )
        for subtype in TEMPORAL_SUBTYPES
    }
    causal = {
        subtype: _expand_pairs(
            (record.get("causal_relations") or {}).get(subtype, []), members
        )
        for subtype in CAUSAL_SUBTYPES
    }
    subevent = _expand_pairs(record.get("subevent_relations") or [], members)
    return {
        "id": str(record["id"]),
        "coreference": coreference,
        "temporal_relations": temporal,
        "causal_relations": causal,
        "subevent_relations": subevent,
    }


def empty_official_prediction(record: Mapping) -> dict:
    """Complete all-NONE prediction for a labelled record."""
    return {
        "id": str(record["id"]),
        "coreference": [],
        "temporal_relations": {subtype: [] for subtype in TEMPORAL_SUBTYPES},
        "causal_relations": {subtype: [] for subtype in CAUSAL_SUBTYPES},
        "subevent_relations": [],
    }


def candidate_population_digest(gold: Mapping[str, Mapping]) -> tuple[str, dict[str, int]]:
    """Hash the exact scorer candidate IDs and report population counts."""
    digest = hashlib.sha256()
    counts = {"documents": 0, "event_mentions": 0, "timex": 0, "relation_pairs": 0}
    for doc_id in sorted(gold):
        record = gold[doc_id]
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
        event_mentions = [str(mention["id"]) for mention in mentions]
        timex = sorted(str(item["id"]) for item in record.get("TIMEX", []))
        counts["documents"] += 1
        counts["event_mentions"] += len(event_mentions)
        counts["timex"] += len(timex)
        counts["relation_pairs"] += len(event_mentions) * (len(event_mentions) - 1)
        for head in event_mentions:
            for tail in event_mentions:
                if head != tail:
                    digest.update(f"{doc_id}::{head}->{doc_id}::{tail}\n".encode())
    return digest.hexdigest(), counts


def _add_candidate_labels(
    raw_pairs: Iterable[Iterable[str]],
    *,
    family: str,
    subtype: str,
    members: Mapping[str, tuple[str, ...]],
    labels: dict[tuple[str, str], list[str]],
) -> None:
    for raw_pair in raw_pairs:
        head_event, tail_event = list(raw_pair)
        for head in members[str(head_event)]:
            for tail in members[str(tail_event)]:
                if head != tail:
                    labels[(head, tail)].append(f"{family}:{subtype}")


# Official MAVEN-ERE scores SIMULTANEOUS/BEGINS-ON in both directions
# (joint/src/data.py::BIDIRECTIONAL_REL).
BIDIRECTIONAL_TEMPORAL = ("SIMULTANEOUS", "BEGINS-ON")


def _mention_sort_key(item: Mapping) -> tuple:
    return (
        item.get("sent_id", 10**9),
        (item.get("offset") or [10**9])[0],
        str(item.get("id")),
    )


def _event_mentions(record: Mapping) -> list[Mapping]:
    mentions = [
        mention for event in record.get("events", []) for mention in event.get("mention", [])
    ]
    mentions.sort(key=_mention_sort_key)
    return mentions


def _event_cluster_members(record: Mapping) -> dict[str, tuple[str, ...]]:
    """Event-cluster membership only. Distinct from `_event_members`, which also
    exposes TIMEX ids for the official-prediction converter."""
    return {
        str(event["id"]): tuple(str(item["id"]) for item in event.get("mention", []))
        for event in record.get("events", [])
    }


def temporal_candidate_summary(records: Iterable[Mapping]) -> dict:
    """Hash the temporal candidate/label population, which includes TIMEX endpoints.

    Official MAVEN-ERE builds a *different* candidate universe per relation family
    (`joint/src/data.py`): temporal uses ``ignore_timex=False`` so TIMEX mentions are
    scoreable endpoints, while causal/subevent use ``ignore_timex=True``. Hashing one
    merged universe would silently change the causal/subevent denominators, so the two
    populations are frozen separately.
    """
    candidate_hash = hashlib.sha256()
    label_hash = hashlib.sha256()
    counts: Counter[str] = Counter()
    for record in sorted(records, key=lambda item: str(item["id"])):
        doc_id = str(record["id"])
        mentions = _event_mentions(record) + list(record.get("TIMEX", []))
        mentions.sort(key=_mention_sort_key)
        mention_ids = [str(item["id"]) for item in mentions]
        members = _event_cluster_members(record)
        members.update({str(item["id"]): (str(item["id"]),) for item in record.get("TIMEX", [])})
        labels: dict[tuple[str, str], list[str]] = defaultdict(list)

        for subtype, pairs in (record.get("temporal_relations") or {}).items():
            name = str(subtype).upper()
            _add_candidate_labels(
                pairs,
                family="temporal",
                subtype=name,
                members=members,
                labels=labels,
            )
            if name in BIDIRECTIONAL_TEMPORAL:
                _add_candidate_labels(
                    [tuple(reversed(list(pair))) for pair in pairs],
                    family="temporal",
                    subtype=name,
                    members=members,
                    labels=labels,
                )

        counts["documents"] += 1
        counts["event_mentions"] += len(_event_mentions(record))
        counts["timex_mentions"] += len(record.get("TIMEX", []))
        counts["scoreable_mentions"] += len(mention_ids)
        for head in mention_ids:
            for tail in mention_ids:
                if head == tail:
                    continue
                candidate_id = f"{doc_id}::{head}->{doc_id}::{tail}"
                candidate_hash.update(f"{candidate_id}\n".encode())
                pair_labels = tuple(sorted(set(labels.get((head, tail), ()))))
                rendered = ",".join(pair_labels) if pair_labels else "NONE"
                label_hash.update(f"{candidate_id}\t{rendered}\n".encode())
                counts["ordered_mention_pairs"] += 1
                for label in pair_labels:
                    counts[f"positive_{label}"] += 1
    return {
        "candidate_id_format": "{doc_id}::{head_mention_id}->{doc_id}::{tail_mention_id}",
        "candidate_id_digest_sha256": candidate_hash.hexdigest(),
        "candidate_label_digest_sha256": label_hash.hexdigest(),
        "population_counts": dict(sorted(counts.items())),
        "endpoint_universe": "event mentions + TIMEX (official ignore_timex=False)",
        "bidirectional_subtypes": list(BIDIRECTIONAL_TEMPORAL),
        "mention_order": "(sent_id, offset[0], mention_id); all ordered pairs excluding self",
        "event_relation_expansion": "Cartesian product of both gold event clusters",
    }


def frozen_candidate_protocol(records: Iterable[Mapping]) -> dict:
    """The complete per-family frozen candidate protocol for one split role.

    Top-level fields stay the causal/subevent (event-only) universe so previously
    frozen digests remain byte-identical; `temporal` carries the TIMEX-inclusive
    universe that official MAVEN-ERE scores separately.
    """
    records = list(records)
    summary = candidate_protocol_summary(records)
    summary["temporal"] = temporal_candidate_summary(records)
    return summary


def candidate_protocol_summary(records: Iterable[Mapping]) -> dict:
    """Hash v6's complete causal/subevent candidate and expanded-label population."""
    candidate_hash = hashlib.sha256()
    label_hash = hashlib.sha256()
    counts: Counter[str] = Counter()
    for record in sorted(records, key=lambda item: str(item["id"])):
        doc_id = str(record["id"])
        mentions = _event_mentions(record)
        mention_ids = [str(item["id"]) for item in mentions]
        members = _event_cluster_members(record)
        labels: dict[tuple[str, str], list[str]] = defaultdict(list)

        for subtype, pairs in (record.get("causal_relations") or {}).items():
            _add_candidate_labels(
                pairs,
                family="causal",
                subtype=str(subtype).upper(),
                members=members,
                labels=labels,
            )
        _add_candidate_labels(
            record.get("subevent_relations") or [],
            family="subevent",
            subtype="SUBEVENT_OF",
            members=members,
            labels=labels,
        )

        counts["documents"] += 1
        counts["event_mentions"] += len(mention_ids)
        for head in mention_ids:
            for tail in mention_ids:
                if head == tail:
                    continue
                candidate_id = f"{doc_id}::{head}->{doc_id}::{tail}"
                candidate_hash.update(f"{candidate_id}\n".encode())
                pair_labels = tuple(sorted(labels.get((head, tail), ())))
                rendered = ",".join(pair_labels) if pair_labels else "NONE"
                label_hash.update(f"{candidate_id}\t{rendered}\n".encode())
                counts["ordered_mention_pairs"] += 1
                for label in pair_labels:
                    counts[f"positive_{label}"] += 1
    return {
        "candidate_id_format": "{doc_id}::{head_mention_id}->{doc_id}::{tail_mention_id}",
        "candidate_id_digest_sha256": candidate_hash.hexdigest(),
        "candidate_label_digest_sha256": label_hash.hexdigest(),
        "population_counts": dict(sorted(counts.items())),
        "mention_order": "(sent_id, offset[0], mention_id); all ordered pairs excluding self",
        "event_relation_expansion": "Cartesian product of both gold event clusters",
    }


def _validate_pairs(
    pairs: object,
    *,
    field: str,
    allowed: set[str],
    seen_family: dict[tuple[str, str], str],
    subtype: str,
) -> None:
    if not isinstance(pairs, list):
        raise OfficialProtocolError(f"{field} must be a list")
    seen: set[tuple[str, str]] = set()
    for raw_pair in pairs:
        if not isinstance(raw_pair, list) or len(raw_pair) != 2:
            raise OfficialProtocolError(f"{field} contains malformed pair {raw_pair!r}")
        pair = (raw_pair[0], raw_pair[1])
        if not all(isinstance(item, str) for item in pair):
            raise OfficialProtocolError(f"{field} pair endpoints must be strings")
        if pair[0] == pair[1]:
            raise OfficialProtocolError(f"{field} contains self pair {pair}")
        if pair[0] not in allowed or pair[1] not in allowed:
            raise OfficialProtocolError(f"{field} contains unknown endpoint {pair}")
        if pair in seen:
            raise OfficialProtocolError(f"{field} contains duplicate pair {pair}")
        if pair in seen_family:
            raise OfficialProtocolError(
                f"{field} conflicts with subtype {seen_family[pair]} on pair {pair}"
            )
        seen.add(pair)
        seen_family[pair] = subtype


def validate_official_predictions(
    gold: Mapping[str, Mapping],
    predictions: Mapping[str, Mapping],
    *,
    expected_candidate_digest: str | None = None,
) -> dict[str, int | str]:
    """Reject any schema, endpoint, ID-set, or candidate-population drift."""
    gold_ids, prediction_ids = set(gold), set(predictions)
    if gold_ids != prediction_ids:
        raise OfficialProtocolError(
            "prediction document IDs differ from gold: "
            f"missing={sorted(gold_ids - prediction_ids)} "
            f"extra={sorted(prediction_ids - gold_ids)}"
        )
    digest, counts = candidate_population_digest(gold)
    if expected_candidate_digest is not None and digest != expected_candidate_digest:
        raise OfficialProtocolError(
            "candidate population digest mismatch: "
            f"expected {expected_candidate_digest}, got {digest}"
        )

    for doc_id, record in gold.items():
        prediction = predictions[doc_id]
        event_mentions = {
            str(mention["id"])
            for event in record.get("events", [])
            for mention in event.get("mention", [])
        }
        temporal_mentions = event_mentions | {
            str(item["id"]) for item in record.get("TIMEX", [])
        }

        clusters = prediction.get("coreference")
        if not isinstance(clusters, list):
            raise OfficialProtocolError(f"{doc_id}.coreference must be a list")
        seen_mentions: set[str] = set()
        for cluster in clusters:
            if not isinstance(cluster, list) or not cluster:
                raise OfficialProtocolError(f"{doc_id}.coreference has an empty/malformed cluster")
            for mention_id in cluster:
                if mention_id not in event_mentions:
                    raise OfficialProtocolError(
                        f"{doc_id}.coreference contains unknown mention {mention_id}"
                    )
                if mention_id in seen_mentions:
                    raise OfficialProtocolError(
                        f"{doc_id}.coreference repeats mention {mention_id}"
                    )
                seen_mentions.add(mention_id)

        for field, subtypes, allowed in (
            ("temporal_relations", TEMPORAL_SUBTYPES, temporal_mentions),
            ("causal_relations", CAUSAL_SUBTYPES, event_mentions),
        ):
            payload = prediction.get(field)
            if not isinstance(payload, dict) or set(payload) != set(subtypes):
                raise OfficialProtocolError(
                    f"{doc_id}.{field} must contain exactly {sorted(subtypes)}"
                )
            seen_family: dict[tuple[str, str], str] = {}
            for subtype in subtypes:
                _validate_pairs(
                    payload[subtype],
                    field=f"{doc_id}.{field}.{subtype}",
                    allowed=allowed,
                    seen_family=seen_family,
                    subtype=subtype,
                )
        seen_subevent: dict[tuple[str, str], str] = {}
        _validate_pairs(
            prediction.get("subevent_relations"),
            field=f"{doc_id}.subevent_relations",
            allowed=event_mentions,
            seen_family=seen_subevent,
            subtype="subevent",
        )
    return {"candidate_id_digest": digest, **counts}


def canonical_json_sha256(payload: object) -> str:
    """Stable JSON hash used in protocol assets."""
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()
