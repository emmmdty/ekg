"""Role compatibility between two mentions, and how much to trust it.

The registered negative control (`qwen3-argument-s13-r2`) showed that pooling
predicted argument *embeddings* into the pair head costs MUC.  The reading this
module acts on is that the useful signal in mention-local arguments is not the
filler's representation but whether the two mentions' fillers can describe the
same event, and that a pair where one side has no prediction at all must not be
scored as if the roles disagreed.

So a pair gets two things: a compatibility vector per role, built only from
source-verbatim spans, and a missingness vector saying which side the extractor
could not answer for.  A learned residual reads both; the uncertainty gate lets
it fall silent when the evidence is absent rather than guess.  Absent and
incompatible are different facts and are kept apart at every step here.

Everything in this file is deterministic and torch-free: the arms differ by the
residual path, not by the features, so the features stay checkable on CPU.
"""

from __future__ import annotations

import random
from collections.abc import Mapping, Sequence

from ekg.core.schema import EventNode

__all__ = [
    "ROLE_NAMES",
    "ROLE_FEATURE_NAMES",
    "ARGUMENT_STATUSES",
    "mention_argument_state",
    "role_compatibility_features",
    "batch_role_compatibility_features",
    "permute_role_features",
    "incompatible_role_merges",
    "argument_sidecar",
]

# Frozen by the mention-local extractor contract: it is asked for these two
# roles and nothing else, so the feature layout cannot drift with the data.
ROLE_NAMES = ("participant", "place")

# Every mention carries exactly one of these; a mention with no state recorded
# is a bug in the input artifact, not a mention to quietly treat as empty.
ARGUMENT_STATUSES = ("ok", "empty", "partial", "rejected")

STATUS_KEY = "argument_prediction_status"

_PER_ROLE_FEATURES = (
    "both_present",
    "one_missing",
    "both_missing",
    "exact_match",
    "token_jaccard",
)
ROLE_FEATURE_NAMES = tuple(
    f"{role}_{feature}" for role in ROLE_NAMES for feature in _PER_ROLE_FEATURES
) + (
    "head_unresolved",
    "tail_unresolved",
    "either_unresolved",
)


def mention_argument_state(node: EventNode) -> str:
    """The extractor's own verdict for this mention, or fail loudly."""
    state = node.metadata.get(STATUS_KEY)
    if state not in ARGUMENT_STATUSES:
        raise ValueError(
            f"{node.event_id}: argument state is {state!r}, expected one of {ARGUMENT_STATUSES}"
        )
    return state


def _fillers(node: EventNode, role: str) -> list[str]:
    """Normalised filler strings for one role, in span order."""
    return [
        span.text.strip().lower()
        for span in node.argument_evidence.get(role, ())
        if span.text.strip()
    ]


# Fillers are noun phrases, so a shared function word says nothing: without this
# "the militia" and "the police" overlap on "the" and the mediator never fires.
# ponytail: closed word list, swap for a lemmatiser/head-word parse if a filler
# family shows up that this cannot separate.
_FUNCTION_WORDS = frozenset(
    {"a", "an", "the", "of", "in", "at", "on", "for", "to", "and", "or", "s", "'s"}
)


def _tokens(fillers: Sequence[str]) -> set[str]:
    """Content tokens of a role's fillers, keeping function words as a fallback.

    A filler made only of function words ("the one") would otherwise compare as
    empty and read as *missing*, which is the one confusion this module exists to
    avoid, so it keeps its raw tokens instead.
    """
    tokens: set[str] = set()
    for filler in fillers:
        raw = filler.split()
        content = {token for token in raw if token not in _FUNCTION_WORDS}
        tokens |= content or set(raw)
    return tokens


def role_compatibility_features(head: EventNode, tail: EventNode) -> list[float]:
    """One vector per candidate pair, in `ROLE_FEATURE_NAMES` order.

    A role where neither side has a filler scores `both_missing`, not
    incompatibility: the extractor declining to answer is not evidence that the
    two mentions disagree, and collapsing the two is how a missing prediction
    turns into a wrong split.
    """
    values: list[float] = []
    for role in ROLE_NAMES:
        left, right = _fillers(head, role), _fillers(tail, role)
        both = bool(left) and bool(right)
        values.append(1.0 if both else 0.0)
        values.append(1.0 if bool(left) != bool(right) else 0.0)
        values.append(1.0 if not left and not right else 0.0)
        if not both:
            # No comparison is possible, so both agreement features stay at zero
            # and only the missingness features carry the pair.
            values.extend((0.0, 0.0))
            continue
        values.append(1.0 if set(left) & set(right) else 0.0)
        left_tokens, right_tokens = _tokens(left), _tokens(right)
        union = left_tokens | right_tokens
        values.append(len(left_tokens & right_tokens) / len(union) if union else 0.0)

    head_unresolved = 1.0 if mention_argument_state(head) != "ok" else 0.0
    tail_unresolved = 1.0 if mention_argument_state(tail) != "ok" else 0.0
    values.extend(
        (head_unresolved, tail_unresolved, 1.0 if head_unresolved or tail_unresolved else 0.0)
    )
    return values


def batch_role_compatibility_features(
    pairs: Sequence[tuple[str, str]], nodes_by_id: Mapping[str, EventNode]
) -> list[list[float]]:
    return [role_compatibility_features(nodes_by_id[h], nodes_by_id[t]) for h, t in pairs]


def permute_role_features(
    pairs: Sequence[tuple[str, str]],
    nodes_by_id: Mapping[str, EventNode],
    features: Sequence[Sequence[float]],
    *,
    seed: int,
) -> list[list[float]]:
    """Negative control: shuffle whole vectors within one document and event type.

    Permuting inside the stratum keeps every marginal the residual could exploit
    — how often roles are present, how often they agree — and destroys only the
    link between a vector and the pair it describes.  A gain that survives this
    came from capacity, not from role compatibility.
    """
    if len(features) != len(pairs):
        raise ValueError(f"features cover {len(features)} of {len(pairs)} pairs")
    strata: dict[tuple[str, str], list[int]] = {}
    for index, (head_id, tail_id) in enumerate(pairs):
        head, tail = nodes_by_id[head_id], nodes_by_id[tail_id]
        if head.doc_id != tail.doc_id:
            raise ValueError(f"cross-document candidate pair: {head_id} {tail_id}")
        strata.setdefault((head.doc_id, head.event_type), []).append(index)

    permuted = [list(row) for row in features]
    rng = random.Random(seed)
    for _, indices in sorted(strata.items()):
        shuffled = list(indices)
        rng.shuffle(shuffled)
        for target, source in zip(indices, shuffled, strict=True):
            permuted[target] = list(features[source])
    return permuted


def incompatible_role_merges(
    pairs: Sequence[tuple[str, str]],
    nodes_by_id: Mapping[str, EventNode],
    merged: Mapping[tuple[str, str], bool],
    gold: Mapping[tuple[str, str], bool],
) -> dict[str, int]:
    """The registered mediator: merges made across roles that cannot both hold.

    A pair is role-incompatible when some role has a filler on both sides and
    they share no token.  Counting only the *false* merges of that kind is the
    quantity the mechanism claims to reduce; the denominators travel with it so
    a rate can be recomputed without re-reading predictions.
    """
    counts: dict[str, int] = {
        "pairs": 0,
        "role_incompatible": 0,
        "merged": 0,
        "false_merges": 0,
        "incompatible_merges": 0,
        "incompatible_false_merges": 0,
    }
    for pair in pairs:
        head, tail = nodes_by_id[pair[0]], nodes_by_id[pair[1]]
        if pair not in merged or pair not in gold:
            raise ValueError(f"pair {pair} is missing a prediction or a gold label")
        incompatible = any(
            _fillers(head, role)
            and _fillers(tail, role)
            and not (_tokens(_fillers(head, role)) & _tokens(_fillers(tail, role)))
            for role in ROLE_NAMES
        )
        is_merged, is_gold = bool(merged[pair]), bool(gold[pair])
        counts["pairs"] += 1
        counts["role_incompatible"] += int(incompatible)
        counts["merged"] += int(is_merged)
        counts["false_merges"] += int(is_merged and not is_gold)
        counts["incompatible_merges"] += int(incompatible and is_merged)
        counts["incompatible_false_merges"] += int(incompatible and is_merged and not is_gold)
    return counts


def argument_sidecar(nodes: Sequence[EventNode]) -> dict[str, dict]:
    """Per-mention record of what the extractor produced, for every mention.

    Coverage is the gate this feeds, so a mention is never omitted: one with no
    fillers is written with an explicit state and an empty role map instead of
    being left out and counted as scored.
    """
    sidecar: dict[str, dict] = {}
    for node in nodes:
        if node.event_id in sidecar:
            raise ValueError(f"duplicate mention in sidecar: {node.event_id}")
        roles = {
            role: [
                {"char_start": span.char_start, "char_end": span.char_end, "text": span.text}
                for span in node.argument_evidence.get(role, ())
            ]
            for role in ROLE_NAMES
            if node.argument_evidence.get(role)
        }
        sidecar[node.event_id] = {
            "doc_id": node.doc_id,
            "event_type": node.event_type,
            "state": mention_argument_state(node),
            "roles": roles,
            "filler_count": sum(len(spans) for spans in roles.values()),
        }
    return sidecar
