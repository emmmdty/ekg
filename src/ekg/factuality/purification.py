"""Factuality-driven graph purification: acting on the labels, not just scoring.

A constructed event graph treats every extracted mention as an event that
happened. MAVEN-FACT says that is wrong for ~5.6% of them — some are negated
(CT−), some hedged (PS−/PS+), some unknown (Uu) — and an edge resting on a
non-event is a fabricated relation no matter how confidently it was extracted.

The policy separates two things that are easy to conflate:

- **counter-evidence** (CT−: asserted *not* to have happened) removes the node
  and every edge touching it. There is nothing to reason over.
- **uncertainty** (PS−, Uu) down-weights instead. Hedged is not false, and
  deleting an event because the text was cautious would lose real structure —
  so the confidence drops and the decision stays recoverable downstream.

An unlabelled node is left untouched: no label is not counter-evidence, and a
detector that skipped a mention must not thereby delete it.

Every action is recorded in `PurificationResult.trace`, so a downstream number
can always be traced to the node that changed and the label that changed it —
the same auditability contract the repair stage carries.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from ekg.core.eval.consistency import consistency_report
from ekg.core.schema import EventGraph, RelationEdge
from ekg.relations.data.maven_fact import FACTUALITY_LABELS

__all__ = [
    "PurificationPolicy",
    "PurificationResult",
    "DEFAULT_POLICY",
    "purify_graph",
    "purification_report",
]


@dataclass(frozen=True)
class PurificationPolicy:
    """Which labels remove a node, and what the rest do to edge confidence."""

    drop_labels: frozenset[str] = frozenset({"CT-"})
    weights: Mapping[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        unknown = (set(self.drop_labels) | set(self.weights)) - set(FACTUALITY_LABELS)
        if unknown:
            raise ValueError(f"unknown factuality label(s): {sorted(unknown)}")
        bad = {label: w for label, w in self.weights.items() if not 0.0 <= w <= 1.0}
        if bad:
            raise ValueError(f"edge confidence weight must be in [0, 1]: {bad}")

    def weight_of(self, label: str) -> float:
        """Confidence multiplier for edges touching a node with `label`."""
        return self.weights.get(label, 1.0)


# CT- is the only label that asserts the event did *not* happen; PS- and Uu are
# hedges, so they cost confidence rather than existence.
DEFAULT_POLICY = PurificationPolicy(
    drop_labels=frozenset({"CT-"}),
    weights={"CT+": 1.0, "PS+": 1.0, "PS-": 0.5, "Uu": 0.3},
)


@dataclass
class PurificationResult:
    """The purified graph plus what it cost, per decision."""

    graph: EventGraph
    dropped_nodes: tuple[str, ...] = ()
    n_dropped_edges: int = 0
    n_downweighted_edges: int = 0
    trace: dict[str, dict[str, str]] = field(default_factory=dict)


def purify_graph(
    graph: EventGraph,
    factuality: Mapping[str, str],
    policy: PurificationPolicy = DEFAULT_POLICY,
) -> PurificationResult:
    """Drop counter-factual nodes, down-weight uncertain ones, keep the trace."""
    dropped = tuple(
        node_id for node_id in graph.nodes if factuality.get(node_id) in policy.drop_labels
    )
    dropped_set = set(dropped)
    trace: dict[str, dict[str, str]] = {
        node_id: {"label": factuality[node_id], "action": "drop"} for node_id in dropped
    }
    for node_id in graph.nodes:
        label = factuality.get(node_id)
        if node_id in dropped_set or label is None:
            continue
        if policy.weight_of(label) < 1.0:
            trace[node_id] = {"label": label, "action": "downweight"}

    edges: list[RelationEdge] = []
    n_dropped_edges = n_downweighted = 0
    for edge in graph.edges:
        if edge.head_id in dropped_set or edge.tail_id in dropped_set:
            n_dropped_edges += 1
            continue
        # The less certain endpoint governs: a relation is only as believable as
        # the shakier of the two events it connects.
        weight = (
            min(
                policy.weight_of(factuality[endpoint])
                for endpoint in (edge.head_id, edge.tail_id)
                if endpoint in factuality
            )
            if any(e in factuality for e in (edge.head_id, edge.tail_id))
            else 1.0
        )
        if weight < 1.0:
            n_downweighted += 1
            edges.append(edge.model_copy(update={"confidence": edge.confidence * weight}))
        else:
            edges.append(edge)

    return PurificationResult(
        graph=EventGraph(
            nodes={k: v for k, v in graph.nodes.items() if k not in dropped_set},
            edges=edges,
            metadata=dict(graph.metadata),
        ),
        dropped_nodes=dropped,
        n_dropped_edges=n_dropped_edges,
        n_downweighted_edges=n_downweighted,
        trace=trace,
    )


def purification_report(before: EventGraph, result: PurificationResult) -> dict:
    """Size and consistency of the graph on both sides of the purification.

    Consistency is reported before *and* after because shrinking a graph
    trivially removes violations: without both numbers a purification that
    fixed something is indistinguishable from one that just deleted edges.
    """
    n_nodes_before = len(before.nodes)
    n_edges_before = len(before.edges)
    n_edges_after = len(result.graph.edges)
    return {
        "n_nodes_before": n_nodes_before,
        "n_nodes_after": len(result.graph.nodes),
        "n_edges_before": n_edges_before,
        "n_edges_after": n_edges_after,
        "node_retention": len(result.graph.nodes) / n_nodes_before if n_nodes_before else 1.0,
        "edge_retention": n_edges_after / n_edges_before if n_edges_before else 1.0,
        "n_dropped_nodes": len(result.dropped_nodes),
        "n_dropped_edges": result.n_dropped_edges,
        "n_downweighted_edges": result.n_downweighted_edges,
        "consistency_before": consistency_report(before),
        "consistency_after": consistency_report(result.graph),
    }
