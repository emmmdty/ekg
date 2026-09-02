"""Confusability features for context-discriminative event identity.

The official-protocol error profile (`docs/results/PHASE_C.md`) says the gap is
not recall in general: over-merges outnumber under-merges 1,391 to 801, and
**51.8% of the over-merges are pairs whose triggers are byte-identical** (44.4%
of the under-merges are too). On those pairs the trigger representations are
nearly indistinguishable by construction, so a head that reads only trigger
vectors has to guess.

These features name that situation explicitly, so the head can learn a different
decision function for it instead of relying on a similarity that has collapsed.
The context/confusability components are derived only from the mention set the
official protocol already gives us.  The separate ``argument_pooling_oracle``
component deliberately reads MAVEN-Arg's event-level gold arguments and must only
be used as an information upper bound, never as a deployable method score.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence

from ekg.core.schema import EventNode
from ekg.nodes.coref import trigger_similarity

FEATURE_NAMES = (
    "same_trigger_exact",
    "trigger_similarity",
    "same_event_type",
    "same_sentence",
    "log_sentence_distance",
    "log_mention_distance",
)


def _sent_id(node: EventNode) -> int | None:
    if not node.trigger_evidence:
        return None
    return node.trigger_evidence[0].sent_id


def confusability_features(
    head: EventNode, tail: EventNode, order: Mapping[str, int]
) -> list[float]:
    """One feature vector per candidate pair, in `FEATURE_NAMES` order."""
    h_trigger = (head.trigger or "").strip().lower()
    t_trigger = (tail.trigger or "").strip().lower()
    exact = 1.0 if h_trigger and h_trigger == t_trigger else 0.0
    similarity = trigger_similarity(head.trigger or "", tail.trigger or "")
    same_type = 1.0 if head.event_type == tail.event_type else 0.0

    h_sent, t_sent = _sent_id(head), _sent_id(tail)
    if h_sent is None or t_sent is None:
        same_sentence, sent_distance = 0.0, 0.0
    else:
        same_sentence = 1.0 if h_sent == t_sent else 0.0
        sent_distance = math.log1p(abs(h_sent - t_sent))

    mention_distance = math.log1p(abs(order[head.event_id] - order[tail.event_id]))
    return [exact, similarity, same_type, same_sentence, sent_distance, mention_distance]


def batch_confusability_features(
    pairs: Sequence[tuple[str, str]],
    nodes_by_id: Mapping[str, EventNode],
    order: Mapping[str, int],
) -> list[list[float]]:
    return [confusability_features(nodes_by_id[h], nodes_by_id[t], order) for h, t in pairs]


CONFIG_FILE = "coref_config.json"

# The mechanism has two separable parts; ablations switch them independently, and
# the checkpoint records which ones it was trained with. A single boolean would
# have to be widened (and every old checkpoint silently reinterpreted) the first
# time a third component appears.
CONTEXT_POOLING = "context_pooling"
CONFUSABILITY = "confusability"
ARGUMENT_POOLING_ORACLE = "argument_pooling_oracle"
ALL_COMPONENTS = (CONTEXT_POOLING, CONFUSABILITY, ARGUMENT_POOLING_ORACLE)


def validate_components(components) -> tuple[str, ...]:
    selected = tuple(components)
    unknown = set(selected) - set(ALL_COMPONENTS)
    if unknown:
        raise ValueError(f"unknown coreference components: {sorted(unknown)}")
    if len(set(selected)) != len(selected):
        raise ValueError("duplicate coreference components")
    return tuple(c for c in ALL_COMPONENTS if c in selected)


def sentence_char_ranges(doc_text: str) -> list[tuple[int, int]]:
    """Char range of every line of the canonical doc text (one line = one sentence)."""
    ranges: list[tuple[int, int]] = []
    start = 0
    for line in doc_text.split("\n"):
        ranges.append((start, start + len(line)))
        start += len(line) + 1
    return ranges


def context_ranges_for(nodes: Sequence[EventNode], doc_text: str) -> list[tuple[int, int]]:
    """Each mention's own sentence range, falling back to a character window.

    A mention whose `sent_id` is missing gets a symmetric character window instead
    of a zero-length range, so pooling never degenerates silently.
    """
    sentences = sentence_char_ranges(doc_text)
    out: list[tuple[int, int]] = []
    for node in nodes:
        sent = _sent_id(node)
        if sent is not None and 0 <= sent < len(sentences):
            out.append(sentences[sent])
            continue
        start = node.trigger_evidence[0].char_start if node.trigger_evidence else 0
        out.append((max(0, start - 200), start + 200))
    return out


def head_input_dim(hidden_size: int, components=()) -> int:
    selected = validate_components(components)
    dim = hidden_size * 4
    if CONTEXT_POOLING in selected:
        dim += hidden_size * 4
    if CONFUSABILITY in selected:
        dim += len(FEATURE_NAMES)
    if ARGUMENT_POOLING_ORACLE in selected:
        dim += hidden_size * 4
    return dim


def argument_spans_and_counts(
    nodes: Sequence[EventNode],
) -> tuple[list[tuple[int, int]], list[int]]:
    """Deterministic gold argument spans and per-mention counts for the oracle.

    MAVEN-Arg annotates arguments at event level and copies them to every mention
    of that event.  Consequently this is intentionally named an oracle: using it
    at inference exposes cluster-level annotation.  Sorting roles and spans keeps
    the tensor layout stable across training and scoring.
    """
    spans: list[tuple[int, int]] = []
    counts: list[int] = []
    for node in nodes:
        selected = sorted(
            (span.char_start, span.char_end)
            for role in sorted(node.argument_evidence)
            for span in node.argument_evidence[role]
        )
        spans.extend(selected)
        counts.append(len(selected))
    return spans, counts


def pool_argument_features(features, counts: Sequence[int]):
    """Mean-pool flattened argument-span features, using zero for no arguments."""
    import torch

    pooled = []
    cursor = 0
    for count in counts:
        group = features[cursor : cursor + count]
        pooled.append(
            group.mean(dim=0) if count else features.new_zeros(features.shape[-1])
        )
        cursor += count
    if cursor != features.shape[0]:
        raise ValueError(
            f"argument counts cover {cursor} of {features.shape[0]} encoded spans"
        )
    if not pooled:
        return features.new_zeros((0, features.shape[-1]))
    return torch.stack(pooled)


def pair_head_inputs(
    triggers,
    contexts,
    pairs: Sequence[tuple[str, str]],
    nodes_by_id: Mapping[str, EventNode],
    order: Mapping[str, int],
    *,
    components=(),
    arguments=None,
):
    """The single implementation of the head's input, shared by training and scoring.

    Two implementations would drift, and a drifted feature layout is invisible: the
    head still runs, it just reads different numbers than it was trained on.
    """
    import torch

    from ekg.nodes.encoding import pair_features

    selected = validate_components(components)
    device = triggers.device
    head_idx = torch.tensor([order[h] for h, _ in pairs], device=device)
    tail_idx = torch.tensor([order[t] for _, t in pairs], device=device)
    parts = [pair_features(triggers[head_idx], triggers[tail_idx])]
    if CONTEXT_POOLING in selected:
        parts.append(pair_features(contexts[head_idx], contexts[tail_idx]))
    if CONFUSABILITY in selected:
        parts.append(
            torch.tensor(
                batch_confusability_features(pairs, nodes_by_id, order),
                dtype=parts[0].dtype,
                device=device,
            )
        )
    if ARGUMENT_POOLING_ORACLE in selected:
        if arguments is None:
            raise ValueError("argument_pooling_oracle requires argument features")
        if arguments.shape != triggers.shape:
            raise ValueError(
                "argument features must align with trigger features: "
                f"arguments={tuple(arguments.shape)} triggers={tuple(triggers.shape)}"
            )
        parts.append(pair_features(arguments[head_idx], arguments[tail_idx]))
    return parts[0] if len(parts) == 1 else torch.cat(parts, dim=-1)
