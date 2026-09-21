"""Uncertainty-gated residual over *predicted* causal edges.

The D4 v6.2 mechanism family, frozen in
``docs/phases/PHASE_D4_predicted_causal_residual.md``.  Nothing here may read a
gold edge, a gold factuality label or final-valid feedback: the only structural
input is the frozen per-fold natural posterior produced by C-25R3F.

Three arms, differing in exactly one registered variable:

``full``
    trigger representation + ``sum_{e -> v} confidence(e) * message(e)``.
``base``
    the same encoder and head with the residual pathway removed.
``rewired``
    the negative control — endpoints are reconnected inside the document while
    every node's in-degree and out-degree and the joint
    ``(subtype, confidence)`` multiset are preserved exactly.

The gate is the decided subtype's natural posterior, so a mention with no
incoming edge gets an exactly zero residual and a low-confidence edge
contributes proportionally little.  Message projections are zero-initialised:
bolting a fresh stream onto an already-tuned encoder with default initialisation
is what halved the succession MRR in the M2 experiment, and a no-op start makes
the arm a true single-variable contrast at step 0.
"""

from __future__ import annotations

import hashlib
import math
import random
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass

from ekg.relations.data.maven_fact import FACTUALITY_LABELS

__all__ = [
    "ARMS",
    "CLASS_ORDER",
    "EDGE_SUBTYPES",
    "NEGATIVE_LABELS",
    "POSITIVE_LABELS",
    "PROBABILITY_FIELDS",
    "REWIRE_NAMESPACE",
    "CausalEdge",
    "build_causal_residual",
    "consistency_violations",
    "decide_edges",
    "residual_inputs",
    "rewire_edges",
    "rewiring_diagnostics",
    "validate_arm",
]

ARMS: tuple[str, ...] = ("full", "base", "rewired")
CLASS_ORDER: tuple[str, ...] = ("NONE", "CAUSE", "PRECONDITION")
EDGE_SUBTYPES: tuple[str, ...] = ("CAUSE", "PRECONDITION")
PROBABILITY_FIELDS: tuple[str, ...] = ("p_none", "p_cause", "p_precondition")
REWIRE_NAMESPACE = "d4-v62-rewire"

POSITIVE_LABELS = frozenset({"CT+", "PS+"})
NEGATIVE_LABELS = frozenset({"CT-", "PS-"})
_UNKNOWN_LABEL = "Uu"

# A degree- and multiset-preserving rewiring is found by stub shuffling; a few
# documents are so small that most shufflings collide.
# ponytail: bounded retry, raise a partial-shuffle search if some real graph ever exhausts it.
_REWIRE_ATTEMPTS = 1000


@dataclass(frozen=True)
class CausalEdge:
    """One decided directed edge and the confidence that gates its message."""

    head_mention_id: str
    tail_mention_id: str
    subtype: str
    confidence: float

    def __post_init__(self) -> None:
        if self.subtype not in EDGE_SUBTYPES:
            raise ValueError(f"unknown causal subtype {self.subtype!r}")
        if not math.isfinite(self.confidence) or not 0.0 < self.confidence <= 1.0:
            raise ValueError("edge confidence must be a finite probability in (0, 1]")


def validate_arm(arm: str) -> str:
    if arm not in ARMS:
        raise ValueError(f"unknown D4 arm {arm!r}, expected one of {ARMS}")
    return arm


def _probabilities(row: Mapping[str, object], *, location: str) -> tuple[float, ...]:
    values = []
    for field in PROBABILITY_FIELDS:
        value = row.get(field)
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise ValueError(f"{location}: {field} is not a number")
        value = float(value)
        if not math.isfinite(value) or value <= 0.0:
            raise ValueError(f"{location}: {field} is not a strictly positive probability")
        values.append(value)
    if abs(sum(values) - 1.0) > 1e-6:
        raise ValueError(f"{location}: posterior row does not sum to one")
    return tuple(values)


def decide_edges(
    rows: Iterable[Mapping[str, object]],
    class_weights: Mapping[str, float],
) -> list[CausalEdge]:
    """Apply the frozen cost-aware Bayes rule ``argmax_k w_k p_k``.

    ``NONE`` means no edge — the sidecar is the exhaustive ordered candidate
    universe, so most rows produce nothing.  Ties fall to the earlier class in
    ``CLASS_ORDER``, matching ``aggregate_d4_relation_crossfit.py``; no
    threshold, temperature or top-k is applied anywhere.
    """
    if set(class_weights) != set(CLASS_ORDER):
        raise ValueError(f"class weights must cover exactly {CLASS_ORDER}")
    weights = tuple(float(class_weights[name]) for name in CLASS_ORDER)
    if not all(math.isfinite(w) and w > 0.0 for w in weights):
        raise ValueError("class weights must be finite and positive")

    edges: list[CausalEdge] = []
    for index, row in enumerate(rows, start=1):
        location = f"posterior row {index}"
        probabilities = _probabilities(row, location=location)
        scores = [w * p for w, p in zip(weights, probabilities, strict=True)]
        decided = max(range(len(CLASS_ORDER)), key=scores.__getitem__)
        if decided == 0:
            continue
        head = row.get("head_mention_id")
        tail = row.get("tail_mention_id")
        if not isinstance(head, str) or not isinstance(tail, str):
            raise ValueError(f"{location}: missing mention identifiers")
        edges.append(
            CausalEdge(
                head_mention_id=head,
                tail_mention_id=tail,
                subtype=CLASS_ORDER[decided],
                confidence=probabilities[decided],
            )
        )
    return edges


def _rewire_seed(*, fold: int, doc_id: str) -> int:
    digest = hashlib.sha256(f"{REWIRE_NAMESPACE}|{fold}|{doc_id}".encode()).hexdigest()
    return int(digest[:16], 16)


def rewire_edges(edges: Sequence[CausalEdge], *, fold: int, doc_id: str) -> list[CausalEdge]:
    """The negative control: same degrees, same payloads, different endpoints.

    Out-stubs and in-stubs are re-paired by a shuffle, so every mention keeps
    its exact in-degree and out-degree; the ``(subtype, confidence)`` payloads
    are permuted over the new pairs, so the document's joint multiset is
    untouched.  The stream is seeded from ``SHA256(namespace|fold|doc_id)`` and
    is therefore independent of the training seed and recomputable on its own.

    Self-loops and duplicated ``(head, tail, subtype)`` triples are rejected
    rather than repaired, because a repaired control is no longer the control
    that was frozen.  A document whose graph admits no such rewiring raises.
    """
    if not edges:
        return []
    stream = random.Random(_rewire_seed(fold=fold, doc_id=doc_id))
    heads = [edge.head_mention_id for edge in edges]
    tails = [edge.tail_mention_id for edge in edges]
    payloads = [(edge.subtype, edge.confidence) for edge in edges]

    for _ in range(_REWIRE_ATTEMPTS):
        stream.shuffle(heads)
        stream.shuffle(tails)
        stream.shuffle(payloads)
        candidate = [
            CausalEdge(
                head_mention_id=head,
                tail_mention_id=tail,
                subtype=subtype,
                confidence=confidence,
            )
            for head, tail, (subtype, confidence) in zip(heads, tails, payloads, strict=True)
        ]
        if any(edge.head_mention_id == edge.tail_mention_id for edge in candidate):
            continue
        keys = {(e.head_mention_id, e.tail_mention_id, e.subtype) for e in candidate}
        if len(keys) == len(candidate):
            return candidate
    raise ValueError(
        f"{doc_id}: no degree-preserving rewiring found in {_REWIRE_ATTEMPTS} attempts"
    )


def rewiring_diagnostics(
    original: Sequence[CausalEdge], rewired: Sequence[CausalEdge]
) -> dict[str, object]:
    """What the bundle has to show: the control really is structure-matched.

    ``identical_edges`` is not a defect — a small graph can only be rewired onto
    itself — but it bounds how much signal the control can possibly remove, so
    it is reported rather than hidden.
    """

    def degrees(edges: Sequence[CausalEdge]) -> tuple[dict[str, int], dict[str, int]]:
        out: dict[str, int] = {}
        into: dict[str, int] = {}
        for edge in edges:
            out[edge.head_mention_id] = out.get(edge.head_mention_id, 0) + 1
            into[edge.tail_mention_id] = into.get(edge.tail_mention_id, 0) + 1
        return out, into

    original_out, original_in = degrees(original)
    rewired_out, rewired_in = degrees(rewired)
    payloads = sorted((e.subtype, e.confidence) for e in original)
    identical = len(
        {(e.head_mention_id, e.tail_mention_id, e.subtype) for e in original}
        & {(e.head_mention_id, e.tail_mention_id, e.subtype) for e in rewired}
    )
    return {
        "edges": len(original),
        "out_degree_preserved": original_out == rewired_out,
        "in_degree_preserved": original_in == rewired_in,
        "payload_multiset_preserved": payloads
        == sorted((e.subtype, e.confidence) for e in rewired),
        "identical_edges": identical,
    }


def residual_inputs(
    edges: Iterable[CausalEdge], mention_ids: Sequence[str]
) -> dict[str, tuple[list[int], list[int], list[float]]]:
    """Per-subtype ``(source rows, target rows, gates)`` into the trigger matrix.

    Pure Python so the indexing contract is testable without torch.  Edges whose
    endpoints are outside the scored mention set are a bug in the caller, not
    something to drop quietly.
    """
    index = {mention_id: position for position, mention_id in enumerate(mention_ids)}
    if len(index) != len(mention_ids):
        raise ValueError("mention ids must be unique")
    grouped: dict[str, tuple[list[int], list[int], list[float]]] = {
        subtype: ([], [], []) for subtype in EDGE_SUBTYPES
    }
    for edge in edges:
        if edge.head_mention_id not in index or edge.tail_mention_id not in index:
            raise KeyError(
                f"edge {edge.head_mention_id}->{edge.tail_mention_id} leaves the mention set"
            )
        sources, targets, gates = grouped[edge.subtype]
        sources.append(index[edge.head_mention_id])
        targets.append(index[edge.tail_mention_id])
        gates.append(edge.confidence)
    return grouped


def build_causal_residual(hidden_size: int):
    """Lazily build the gated residual module (torch only on this path)."""
    if hidden_size <= 0:
        raise ValueError("hidden_size must be positive")
    import torch
    from torch import nn

    class UncertaintyGatedCausalResidual(nn.Module):
        """``h_v + sum_{e -> v} confidence(e) * W_subtype h_source``."""

        def __init__(self) -> None:
            super().__init__()
            self.messages = nn.ModuleDict(
                {subtype: nn.Linear(hidden_size, hidden_size) for subtype in EDGE_SUBTYPES}
            )
            for message in self.messages.values():
                nn.init.zeros_(message.weight)
                nn.init.zeros_(message.bias)

        def forward(self, triggers, inputs: Mapping[str, tuple]):
            if triggers.ndim != 2 or triggers.shape[-1] != hidden_size:
                raise ValueError(f"trigger features must be (n, {hidden_size})")
            if set(inputs) != set(EDGE_SUBTYPES):
                raise ValueError(f"residual inputs must cover exactly {EDGE_SUBTYPES}")
            residual = torch.zeros_like(triggers)
            for subtype in EDGE_SUBTYPES:
                sources, targets, gates = inputs[subtype]
                if not sources:
                    continue
                source_index = torch.as_tensor(sources, dtype=torch.long, device=triggers.device)
                target_index = torch.as_tensor(targets, dtype=torch.long, device=triggers.device)
                gate = torch.as_tensor(gates, dtype=triggers.dtype, device=triggers.device)
                messages = self.messages[subtype](triggers.index_select(0, source_index))
                residual = residual.index_add(0, target_index, gate.unsqueeze(-1) * messages)
            return triggers + residual

    return UncertaintyGatedCausalResidual()


def consistency_violations(
    gold_pairs: Mapping[tuple[str, str], str],
    predicted_labels: Mapping[str, str],
) -> dict[str, dict[str, float | int]]:
    """The two project-defined mediators, exactly as frozen in the contract.

    A violation is a gold-expanded pair whose *target* is predicted to occur
    (``CT+``/``PS+``) while its *source* is predicted not to
    (``CT-``/``PS-``).  Pairs with an ``Uu`` endpoint enter neither numerator nor
    denominator.  Gold relations are read here and nowhere else — never by a
    model arm.
    """
    report = {
        subtype: {"violations": 0, "pairs": 0, "rate": 0.0} for subtype in EDGE_SUBTYPES
    }
    for (head, tail), subtype in gold_pairs.items():
        if subtype not in EDGE_SUBTYPES:
            raise ValueError(f"unexpected gold causal subtype {subtype!r}")
        try:
            source_label = predicted_labels[head]
            target_label = predicted_labels[tail]
        except KeyError as exc:
            raise KeyError(f"mediator pair {head}->{tail} has an unscored mention") from exc
        for label in (source_label, target_label):
            if label not in FACTUALITY_LABELS:
                raise ValueError(f"unknown factuality label {label!r}")
        if _UNKNOWN_LABEL in (source_label, target_label):
            continue
        entry = report[subtype]
        entry["pairs"] += 1
        if target_label in POSITIVE_LABELS and source_label in NEGATIVE_LABELS:
            entry["violations"] += 1
    for entry in report.values():
        if entry["pairs"]:
            entry["rate"] = entry["violations"] / entry["pairs"]
    return report
