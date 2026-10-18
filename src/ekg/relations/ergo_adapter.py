"""MAVEN-ERE interfaces for external ERGO; no encoder, trainer or original code copy.

Class order follows the frozen original MAVEN joint model, not other local heads.
Gold event clusters are used only to expand training targets; model features accept
an explicitly unlabelled document. The original RGT/focal bodies stay external.
"""

from collections import defaultdict
from collections.abc import Mapping, Sequence

from ekg.relations.maven_ere_official import (
    empty_official_prediction,
    gold_to_official_prediction,
)

CAUSAL_CLASSES = ("NONE", "PRECONDITION", "CAUSE")


def _ordered_mentions(raw: Mapping) -> list[dict]:
    if set(raw) != {"id", "tokens", "TIMEX", "event_mentions"}:
        raise ValueError("explicit unlabelled native document required")
    mentions = raw["event_mentions"]
    ids = [m["id"] for m in mentions]
    if len(ids) < 2 or len(set(ids)) != len(ids):
        raise ValueError("at least two unique event mentions required")
    for m in mentions:
        sid, (a, b) = m["sent_id"], m["offset"]
        if not (0 <= sid < len(raw["tokens"]) and 0 <= a < b <= len(raw["tokens"][sid])):
            raise ValueError("invalid native mention offset")
    return sorted(mentions, key=lambda m: (m["sent_id"], m["offset"][0], m["id"]))


def marked_document(raw: Mapping) -> tuple[str, list[str]]:
    """Insert a distinct start marker for every mention, retaining every word."""
    mentions = _ordered_mentions(raw)
    words = [word for sentence in raw["tokens"] for word in sentence]
    if any("<t>" in word or "</t>" in word for word in words):
        raise ValueError("literal marker collision")
    shifts = [0]
    for sentence in raw["tokens"]:
        shifts.append(shifts[-1] + len(sentence))
    starts, ends = defaultdict(list), defaultdict(list)
    for mention in mentions:
        a, b = mention["offset"]
        shift = shifts[mention["sent_id"]]
        starts[shift + a].append(mention["id"])
        ends[shift + b].append(mention["id"])
    pieces, markers = [], []
    for position in range(len(words) + 1):
        pieces.extend("</t>" for _ in ends[position])
        for mid in starts[position]:
            pieces.append("<t>")
            markers.append(mid)
        if position < len(words):
            pieces.append(words[position])
    return " ".join(pieces), markers


def _pairs(raw: Mapping) -> list[tuple[str, str]]:
    ids = [m["id"] for m in _ordered_mentions(raw)]
    return [(a, b) for a in ids for b in ids if a != b]


def native_pair_features(raw: Mapping, marker_positions: Mapping[str, int]) -> dict:
    """Bridge complete ordered MIDs to the original model's t1_pos/t2_pos lists."""
    mids = {m["id"] for m in _ordered_mentions(raw)}
    values = list(marker_positions.values())
    if (set(marker_positions) != mids or len(set(values)) != len(mids)
            or any(type(v) is not int or v <= 0 for v in values)):
        raise ValueError("invalid or incomplete marker positions")
    pairs = _pairs(raw)
    return {"pair_ids": pairs,
            "t1_pos": [marker_positions[a] for a, _ in pairs],
            "t2_pos": [marker_positions[b] for _, b in pairs]}


def causal_targets(raw: Mapping, gold: Mapping) -> list[int]:
    """Expand official causal supervision, independently of model input features."""
    mentions = _ordered_mentions(raw)
    events = gold["events"]
    annotated = [m for event in events for m in event["mention"]]
    if (raw["id"] != gold["id"] or len({e["id"] for e in events}) != len(events)
            or len({m["id"] for m in annotated}) != len(annotated)
            or {m["id"] for m in mentions} != {m["id"] for m in annotated}):
        raise ValueError("gold document/event/mention coverage mismatch")
    spans = {m["id"]: (m["sent_id"], m["offset"]) for m in mentions}
    if any(spans[m["id"]] != (m["sent_id"], m["offset"]) for m in annotated):
        raise ValueError("gold and input mention spans differ")
    relations = gold["causal_relations"]
    if set(relations) != set(CAUSAL_CLASSES[1:]):
        raise ValueError("unknown or missing native subtype")
    seen = set()
    for pairs in relations.values():
        for a, b in pairs:
            if a == b or (a, b) in seen:
                raise ValueError("duplicate/conflicting causal label")
            seen.add((a, b))
    expanded = gold_to_official_prediction({
        "id": gold["id"], "events": events, "TIMEX": [], "causal_relations": relations,
    })["causal_relations"]
    labels = {tuple(pair): CAUSAL_CLASSES.index(subtype)
              for subtype, pairs in expanded.items() for pair in pairs}
    pairs = _pairs(raw)
    if not labels.keys() <= set(pairs):
        raise ValueError("gold causal endpoint outside native candidates")
    return [labels.get(pair, 0) for pair in pairs]  # Native annotation-NONE.


def export_causal_classes(raw: Mapping, labels: Sequence[int]) -> dict:
    """Export every candidate class; wrong subtype remains wrong for official scoring."""
    pairs = _pairs(raw)
    if len(labels) != len(pairs) or any(type(v) is not int or v not in (0, 1, 2) for v in labels):
        raise ValueError("incomplete candidates or unknown native class")
    prediction = empty_official_prediction(raw)
    for (a, b), label in zip(pairs, labels, strict=True):
        if label:
            prediction["causal_relations"][CAUSAL_CLASSES[label]].append([a, b])
    return prediction


def criss_cross_mask(pairs: Sequence[tuple[str, str]]):
    """Original shared-endpoint neighbors with every diagonal masked; CPU bool tensor.

    This makes no numerical repair for an arbitrary disconnected graph. Native
    callers supply the complete directed pair population, including reciprocals.
    """
    if not pairs or len(set(pairs)) != len(pairs) or any(a == b for a, b in pairs):
        raise ValueError("empty, duplicate or self graph nodes")
    import torch

    ids = {mid: i for i, mid in enumerate(sorted({x for pair in pairs for x in pair}))}
    head = torch.tensor([ids[a] for a, _ in pairs])
    tail = torch.tensor([ids[b] for _, b in pairs])
    mask = ((head[:, None] != head[None, :]) & (head[:, None] != tail[None, :])
            & (tail[:, None] != head[None, :]) & (tail[:, None] != tail[None, :]))
    mask.fill_diagonal_(True)
    return mask
