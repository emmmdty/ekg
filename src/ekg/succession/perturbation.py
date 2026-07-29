"""Controlled construction errors, injected at a chosen amplitude.

The three-graph comparison (`succession.graph_context`) gives *one* point per
graph: gold, predicted, repaired. That answers "how much did our extractor cost
us" but not "which kind of error costs the most", because a real predicted graph
gets every error type at once and at whatever rate the extractor happens to
produce. So the error types are separated here and swept as a controlled
variable, the way `cross_stage.induce_reachability` sweeps reachability loss --
except these perturb the graph itself, so the loss they cause is measured
downstream rather than assumed.

Four generators, one per failure mode a construction pipeline actually has:

* `drop_edges` -- **recall loss** in the relation stage. Also the mandated strong
  control for any targeted deletion: random edge removal is a strong baseline in
  its own right (DropEdge, ICLR'20), so a repair that deletes k edges only earns
  a claim by beating k random deletions. Pass `exact` for an exactly matched
  control, `rate` for a sweep.
* `add_edges` -- **precision loss**: spurious causal edges between events that
  have no relation. Our own predicted MAVEN graph is ~5x denser in
  causal+subevent than gold, so this is the failure mode it actually exhibits.
* `merge_nodes` -- **coreference over-merge** (Ch1): two events become one, and
  every relation of the absorbed event is re-attached to the survivor. Relations
  survive but now point at the wrong event.
* `split_nodes` -- **coreference under-merge** (Ch1): one event becomes two and
  its relations are divided between them. Downstream keeps only what still
  attaches to a recognised event, so relations are silently lost.

And one that is included precisely because it does nothing:

* `scramble_temporal` -- rewrites temporal edges only. ECG topology reads
  causal+subevent (`cgep.topology_triples`), so this is a *structural* zero, not
  a small effect. Phase B spent a probe on that distinction; keeping the
  generator makes the zero checkable instead of asserted.

Amplitudes are corpus-level: ``rate`` is a fraction of the eligible population,
resolved once over all documents so a sweep point means the same thing whatever
the document-size distribution is. Everything is seeded and pure-Python.
"""

from __future__ import annotations

import random
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import TypeVar

from ekg.core.registry import Registry
from ekg.core.schema import RelationEdge, RelationType
from ekg.succession.data.cgep import topology_triples

__all__ = [
    "PerturbedGraphs",
    "add_edges",
    "drop_edges",
    "graph_perturbations",
    "merge_nodes",
    "scramble_temporal",
    "split_nodes",
]

EdgesByDoc = Mapping[str, Sequence[RelationEdge]]
NodesByDoc = Mapping[str, Sequence[str]]

# Spurious edges are asserted at chance confidence: they are not claims the model
# made, so giving them a high confidence would also perturb any downstream
# admission threshold and confound the intervention.
SPURIOUS_CONFIDENCE = 0.5

# Suffix marking the clone `split_nodes` creates. It is deliberately not a valid
# MAVEN mention id, so the gold node frame cannot silently accept it.
SPLIT_SUFFIX = "#split"

T = TypeVar("T")


@dataclass(frozen=True)
class PerturbedGraphs:
    """Perturbed per-document edges plus what the perturbation actually did."""

    edges_by_doc: dict[str, list[RelationEdge]]
    stats: dict[str, float] = field(default_factory=dict)


Perturbation = Callable[..., PerturbedGraphs]

graph_perturbations: Registry[Perturbation] = Registry("graph_perturbation")


def _materialise(edges_by_doc: EdgesByDoc) -> dict[str, list[RelationEdge]]:
    return {doc_id: list(edges) for doc_id, edges in edges_by_doc.items()}


def _is_topology(edge: RelationEdge, subtypes: frozenset[str] | None) -> bool:
    """Does `edge` carry ECG topology (and match an optional subtype filter)?"""
    carries = bool(topology_triples([edge]))
    return carries and (subtypes is None or edge.subtype in subtypes)


def _resolve_count(population: int, rate: float | None, exact: int | None) -> int:
    """How many items to touch: an exact count wins, else `rate` of the population."""
    if rate is not None and exact is not None:
        raise ValueError("give a rate or an exact count, not both")
    if exact is not None:
        if exact < 0:
            raise ValueError("count must be >= 0")
        return min(exact, population)
    if rate is None:
        raise ValueError("give exactly one of rate / exact count")
    if rate < 0.0:
        raise ValueError("rate must be >= 0")
    return min(round(rate * population), population)


def _prefix(pool: Sequence[T], count: int, seed: int) -> list[T]:
    """One seeded shuffle of `pool`, truncated to `count`.

    Sweep points have to be **nested**: whatever a rate of 0.25 touches must
    contain what 0.1 touched, or the curve reports sampling luck as if it were
    an amplitude effect (drawing a fresh `sample` per rate does exactly that --
    it was visible as a non-monotone reachability curve before this).
    """
    order = list(pool)
    random.Random(seed).shuffle(order)
    return order[:count]


def _coin(seed: int, *parts: str) -> float:
    """A stable draw in [0, 1) keyed by `parts`, independent of call order.

    A shared RNG stream would make one edge's outcome depend on how many other
    edges happened to be processed before it, so adding a sweep point would
    silently rewrite the earlier ones. Keying by identity keeps nesting exact.
    """
    return random.Random(f"{seed}:" + "\x1f".join(parts)).random()


@graph_perturbations.register("drop_edges")
def drop_edges(
    edges_by_doc: EdgesByDoc,
    nodes_by_doc: NodesByDoc | None = None,
    *,
    rate: float | None = None,
    exact: int | None = None,
    subtypes: Sequence[str] | None = None,
    seed: int = 209,
) -> PerturbedGraphs:
    """Delete topology edges uniformly at random, corpus-wide.

    `exact` deletes an exact number, which is what makes this the matched
    control for a targeted deletion of the same size; `rate` deletes a fraction
    of the eligible population and is what a sweep uses. `subtypes` narrows
    eligibility (e.g. to ``CAUSE``/``PRECONDITION`` when matching a causal
    repair), leaving every other edge untouched.
    """
    wanted = frozenset(subtypes) if subtypes is not None else None
    graphs = _materialise(edges_by_doc)
    eligible = [
        (doc_id, index)
        for doc_id in sorted(graphs)
        for index, edge in enumerate(graphs[doc_id])
        if _is_topology(edge, wanted)
    ]
    k = _resolve_count(len(eligible), rate, exact)
    victims = set(_prefix(eligible, k, seed))
    return PerturbedGraphs(
        edges_by_doc={
            doc_id: [edge for index, edge in enumerate(edges) if (doc_id, index) not in victims]
            for doc_id, edges in graphs.items()
        },
        stats={"eligible": float(len(eligible)), "dropped": float(k)},
    )


@graph_perturbations.register("add_edges")
def add_edges(
    edges_by_doc: EdgesByDoc,
    nodes_by_doc: NodesByDoc,
    *,
    rate: float | None = None,
    exact: int | None = None,
    seed: int = 209,
    subtype: str = "CAUSE",
) -> PerturbedGraphs:
    """Insert spurious causal edges between event pairs that have no relation.

    Candidate pairs exclude every pair the document already asserts *in either
    direction* under any relation type, so an insertion fabricates a relation
    rather than duplicating or reversing a real one -- different errors, which
    would blur the attribution. ``rate`` is a fraction of the existing topology,
    so 1.0 doubles it.
    """
    graphs = _materialise(edges_by_doc)
    free: list[tuple[str, str, str]] = []
    for doc_id in sorted(graphs):
        nodes = sorted(nodes_by_doc.get(doc_id, ()))
        taken = {
            frozenset((edge.head_id, edge.tail_id))
            for edge in graphs[doc_id]
            if edge.head_id != edge.tail_id
        }
        free.extend(
            (doc_id, head, tail)
            for i, head in enumerate(nodes)
            for tail in nodes[i + 1 :]
            if frozenset((head, tail)) not in taken
        )

    population = sum(len(topology_triples(edges)) for edges in graphs.values())
    k = min(_resolve_count(population, rate, exact), len(free))
    for doc_id, head, tail in _prefix(free, k, seed):
        # Direction is itself arbitrary for a fabricated relation, and is drawn
        # per pair so it does not shift when the sweep amplitude changes.
        if _coin(seed, doc_id, head, tail) < 0.5:
            head, tail = tail, head
        graphs[doc_id].append(
            RelationEdge(
                head_id=head,
                tail_id=tail,
                relation_type=RelationType.CAUSAL,
                subtype=subtype,
                directed=True,
                confidence=SPURIOUS_CONFIDENCE,
            )
        )
    return PerturbedGraphs(
        edges_by_doc=graphs,
        stats={"eligible": float(population), "free_pairs": float(len(free)), "added": float(k)},
    )


@graph_perturbations.register("merge_nodes")
def merge_nodes(
    edges_by_doc: EdgesByDoc,
    nodes_by_doc: NodesByDoc,
    *,
    rate: float | None = None,
    exact: int | None = None,
    seed: int = 209,
) -> PerturbedGraphs:
    """Coreference over-merge: absorb one event into another, keeping its edges.

    Every edge of the absorbed event is re-attached to the survivor, so no
    relation is lost -- they now describe the wrong event. Self-loops the merge
    creates are dropped (an event cannot cause itself, and the linearisation has
    no way to render it) and counted. Pairing is fixed per document before any
    amplitude is applied, so a larger `rate` merges a superset of the pairs.
    """
    graphs = _materialise(edges_by_doc)
    pairs: list[tuple[str, str, str]] = []
    for doc_id in sorted(graphs):
        order = sorted(nodes_by_doc.get(doc_id, ()))
        random.Random(f"{seed}:{doc_id}").shuffle(order)
        pairs.extend((doc_id, survivor, victim)
                     for survivor, victim in zip(order[::2], order[1::2], strict=False))

    k = _resolve_count(len(pairs), rate, exact)
    absorbed: dict[str, dict[str, str]] = {}
    for doc_id, survivor, victim in _prefix(pairs, k, seed):
        absorbed.setdefault(doc_id, {})[victim] = survivor

    self_loops = 0
    for doc_id, mapping in absorbed.items():
        rewired: list[RelationEdge] = []
        for edge in graphs[doc_id]:
            head = mapping.get(edge.head_id, edge.head_id)
            tail = mapping.get(edge.tail_id, edge.tail_id)
            if head == tail:
                self_loops += 1
                continue
            rewired.append(
                edge
                if (head, tail) == (edge.head_id, edge.tail_id)
                else edge.model_copy(update={"head_id": head, "tail_id": tail})
            )
        graphs[doc_id] = rewired
    return PerturbedGraphs(
        edges_by_doc=graphs,
        stats={
            "eligible": float(len(pairs)),
            "merged_nodes": float(k),
            "self_loops_dropped": float(self_loops),
        },
    )


@graph_perturbations.register("split_nodes")
def split_nodes(
    edges_by_doc: EdgesByDoc,
    nodes_by_doc: NodesByDoc,
    *,
    rate: float | None = None,
    exact: int | None = None,
    seed: int = 209,
    share: float = 0.5,
) -> PerturbedGraphs:
    """Coreference under-merge: one event becomes two and its edges divide.

    Each incident edge moves to the clone with probability `share`, drawn per
    edge-endpoint so the split of a given node is the same at every sweep point.
    The clone is not a node the gold frame knows, so downstream those edges are
    simply gone -- which is the point: an under-merge loses relations without
    ever deleting one.
    """
    graphs = _materialise(edges_by_doc)
    pool = [
        (doc_id, node)
        for doc_id in sorted(graphs)
        for node in sorted(nodes_by_doc.get(doc_id, ()))
    ]
    k = _resolve_count(len(pool), rate, exact)

    clones: dict[str, dict[str, str]] = {}
    for doc_id, node in _prefix(pool, k, seed):
        clones.setdefault(doc_id, {})[node] = f"{node}{SPLIT_SUFFIX}"

    moved = 0
    for doc_id, mapping in clones.items():
        rebuilt: list[RelationEdge] = []
        for edge in graphs[doc_id]:
            head, tail = edge.head_id, edge.tail_id
            if head in mapping and _coin(seed, doc_id, edge.head_id, edge.tail_id, "h") < share:
                head = mapping[head]
            if tail in mapping and _coin(seed, doc_id, edge.head_id, edge.tail_id, "t") < share:
                tail = mapping[tail]
            if (head, tail) == (edge.head_id, edge.tail_id):
                rebuilt.append(edge)
                continue
            moved += 1
            rebuilt.append(edge.model_copy(update={"head_id": head, "tail_id": tail}))
        graphs[doc_id] = rebuilt
    return PerturbedGraphs(
        edges_by_doc=graphs,
        stats={"eligible": float(len(pool)), "split_nodes": float(k), "edges_moved": float(moved)},
    )


@graph_perturbations.register("scramble_temporal")
def scramble_temporal(
    edges_by_doc: EdgesByDoc,
    nodes_by_doc: NodesByDoc | None = None,
    *,
    rate: float | None = None,
    exact: int | None = None,
    seed: int = 209,
) -> PerturbedGraphs:
    """Reverse temporal edges -- a structural no-op on ECG topology.

    Kept as a generator rather than an argument because the claim "temporal
    edits cannot reach the successor predictor" is worth being able to *run*.
    Phase B's first probe mistook a temporal-closure change for the cause of a
    downstream drop; the two are orthogonal by construction, and this is how
    that gets demonstrated instead of asserted.
    """
    graphs = _materialise(edges_by_doc)
    eligible = [
        (doc_id, index)
        for doc_id in sorted(graphs)
        for index, edge in enumerate(graphs[doc_id])
        if edge.relation_type is RelationType.TEMPORAL
    ]
    k = _resolve_count(len(eligible), rate, exact)
    for doc_id, index in _prefix(eligible, k, seed):
        edge = graphs[doc_id][index]
        graphs[doc_id][index] = edge.model_copy(
            update={"head_id": edge.tail_id, "tail_id": edge.head_id}
        )
    return PerturbedGraphs(
        edges_by_doc=graphs,
        stats={"eligible": float(len(eligible)), "reversed": float(k)},
    )
