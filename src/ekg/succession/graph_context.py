"""Feed a *constructed* graph to the successor predictor, holding CGEP at gold.

Ch4 asks how much downstream loss a construction error costs. Answering it needs
the same successor-prediction problem posed over different graphs -- and that is
exactly what `scripts/evaluate_cgep.py` cannot do, because `build_cgep` reads
`doc.gold_edges` and nothing else.

Three designs were possible and only the third isolates the variable:

1. Rebuild the ECGs *and* their queries on the predicted graph. Rejected: a wrong
   graph poses wrong questions, so the MRRs are not comparable at all -- a graph
   that produced one easy query would "win".
2. Hold the queries at gold and only ask whether the constructed graph still
   contains them. That is Phase B's R1/R2 (`succession.reconstruction`): useful,
   reused below as the ``reachable`` flag, but it never reaches the reasoner, so
   it cannot report MRR.
3. **What this module does.** The query edge, the candidate set, the label and
   the node frame all stay gold; only the *template* -- the graph context the
   prompt renders -- is rebuilt from the constructed graph. Graph quality is then
   the single variable between two runs, and one trained model scores them all.

Two rules make the comparison honest, and both are inherited from gold rather
than invented here:

* **The answer never appears in the prompt.** A gold query edge's tail has
  out-degree 0 and in-degree 1 (`query_edge_indices`), so gold templates never
  render the gold event's token. A constructed graph has no such guarantee, so
  any constructed edge touching the gold successor is dropped and counted
  (``leak_blocked``). Without this a *worse* extractor could score *better* by
  printing the answer into its own prompt.
* **The node frame is gold.** Only constructed edges with both endpoints in the
  gold ECG survive; the rest are counted (``out_of_frame``). This keeps the
  `<a_i>` vocabulary, the sentence encodings and the candidate set byte-identical
  across graphs, so a difference in MRR cannot come from a different vocabulary.
  It is also why a perfect extractor reproduces the gold template exactly.

What the constructed graph *does* get to change: which edges exist, how many
there are (the predicted MAVEN graph is ~5x denser in causal+subevent than gold,
so the 20-edge budget starts to bite), and what they say.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, replace

from ekg.core.schema import RelationEdge
from ekg.succession.data.cgep import CgepInstance, topology_triples
from ekg.succession.linearize import EDGE_BUDGET

__all__ = ["ContextSwap", "swap_graph_context"]

Triple = tuple[int, str, int]


@dataclass(frozen=True)
class ContextSwap:
    """Gold CGEP instances re-templated onto a constructed graph, plus the audit.

    `reachable[i]` is whether instance ``i``'s gold query edge survives in the
    constructed graph -- the per-query flag CS-CRP budgets for, aligned with
    `instances` by construction (unlike `ecg_reachable_flags`, which is aligned
    with gold ECG order and so drifts once `build_cgep` skips an instance).
    """

    instances: tuple[CgepInstance, ...]
    reachable: tuple[bool, ...]
    stats: dict[str, float] = field(default_factory=dict)


def _pairs(triples: Sequence[tuple[str, str, str]]) -> set[tuple[str, str]]:
    return {(head, tail) for head, _, tail in triples}


def swap_graph_context(
    instances: Sequence[CgepInstance],
    edges_by_doc: Mapping[str, Sequence[RelationEdge]],
    *,
    include_subevent: bool = True,
) -> ContextSwap:
    """Re-template `instances` onto the graphs in `edges_by_doc`.

    A document absent from `edges_by_doc` yields empty templates rather than an
    error: an extractor that returned nothing for a document is a real outcome
    and must be scored, not skipped. Instances are never dropped -- the test set
    has to stay identical across graphs or the MRRs stop being comparable.
    """
    swapped: list[CgepInstance] = []
    reachable: list[bool] = []
    totals = {
        "template_edges": 0,
        "empty_templates": 0,
        "over_budget": 0,
        "leak_blocked": 0,
        "out_of_frame": 0,
        "kept_gold_edges": 0,
        "gold_template_edges": 0,
    }

    for instance in instances:
        frame = {node.node_id: index for index, node in enumerate(instance.nodes)}
        gold_index = instance.gold_index
        triples = topology_triples(
            edges_by_doc.get(instance.doc_id, ()), include_subevent=include_subevent
        )

        template: list[Triple] = []
        seen: set[Triple] = set()
        for head, subtype, tail in triples:
            source, target = frame.get(head), frame.get(tail)
            if source is None or target is None:
                totals["out_of_frame"] += 1
                continue
            if gold_index in (source, target):
                totals["leak_blocked"] += 1
                continue
            key = (source, subtype, target)
            if key in seen:
                continue
            seen.add(key)
            template.append(key)

        gold_template = set(instance.template_edges)
        totals["template_edges"] += len(template)
        totals["empty_templates"] += not template
        totals["over_budget"] += len(template) > EDGE_BUDGET
        totals["kept_gold_edges"] += len(seen & gold_template)
        totals["gold_template_edges"] += len(gold_template)

        query = instance.query_edge
        query_pair = (instance.nodes[query[0]].node_id, instance.nodes[query[2]].node_id)
        reachable.append(query_pair in _pairs(triples))
        swapped.append(replace(instance, edges=(*template, query)))

    n = len(swapped) or 1
    return ContextSwap(
        instances=tuple(swapped),
        reachable=tuple(reachable),
        stats={
            "n_instances": float(len(swapped)),
            "mean_template_edges": totals["template_edges"] / n,
            "frac_empty_template": totals["empty_templates"] / n,
            "frac_over_budget": totals["over_budget"] / n,
            "mean_leak_blocked": totals["leak_blocked"] / n,
            "mean_out_of_frame": totals["out_of_frame"] / n,
            # Against the gold template: how much of the real context survived,
            # and how much of what survived is real.
            "template_recall": (
                totals["kept_gold_edges"] / totals["gold_template_edges"]
                if totals["gold_template_edges"]
                else 0.0
            ),
            "template_precision": (
                totals["kept_gold_edges"] / totals["template_edges"]
                if totals["template_edges"]
                else 0.0
            ),
            "reachability_rate": sum(reachable) / n,
        },
    )
