#!/usr/bin/env python
"""Ch4: what does each construction error cost the successor predictor?

One CGEP problem set, many graphs. The query edge, candidate set, label and node
frame stay gold; only the graph context handed to the reasoner changes
(`succession.graph_context`), so the difference between two rows is graph quality
and nothing else. One SeDGPL fit scores every row: training is ~2.5h and scoring
another graph is minutes, so the error-propagation curve costs one training run.

The rows come in four families.

**reference / constructed** -- the three-graph table. `gold` is the published
baseline byte-for-byte (the swap is an identity on gold, checked in
`tests/succession/test_graph_context.py`), `predicted` is our Phase A extractor's
real output, `repaired` is Phase B's consistency solver on top. The two repair
ablations isolate its actions: `repaired_noclose` never adds transitive-closure
edges, `repaired_nobreak` never deletes a causal cycle's weakest edge. Phase B's
R1/R2 analysis predicts `repaired_nobreak` is *identical* to `predicted`
downstream, because ECG topology reads causal+subevent only and temporal closure
is orthogonal to it; that prediction is now testable at the MRR level.

**control** -- every deletion is matched. Breaking causal cycles removes k edges,
so `random_drop_matched` removes k causal edges at random from the same graph
(DropEdge, ICLR'20: random deletion is a strong baseline, not a straw man). A
repair only earns a claim by beating it.

**purification** -- Ch3's open question, answered from both ends: `purified` uses
the Phase D detector's labels (deployable), `purified_oracle` uses gold
MAVEN-FACT labels (the ceiling -- if even that does not help, no better detector
can rescue the idea). Both are matched against uniform and degree-matched random
node removal, because CT- events are low-degree and uniform deletion would
otherwise remove more graph mass and win for free.

**perturbation** -- controlled amplitudes of one error type at a time on the gold
graph (`succession.perturbation`), which a real predicted graph cannot give us
because it makes every error at once. Includes `scramble_temporal`, whose zero is
structural rather than empirical and is reported precisely as such.

    uv run python scripts/evaluate_cgep_propagation.py --predictor frequency \\
        --dump runs/factuality/predicted_edges_valid.jsonl --limit-docs 30
"""

from __future__ import annotations

import argparse
import json
import math
import random
from dataclasses import dataclass, field
from pathlib import Path

from ekg.core.calibration.propagation import compare_cross_stage_methods
from ekg.core.eval.consistency import consistency_report
from ekg.core.io import read_jsonl
from ekg.core.schema import EventGraph, RelationEdge
from ekg.factuality.purification import (
    DEFAULT_POLICY,
    degree_matched_samples,
    purify_graph,
)
from ekg.relations.consistency import consistency_solvers
from ekg.relations.data import load_maven_ere
from ekg.relations.data.maven_ere import RelationDocument
from ekg.succession.data.cgep import CgepInstance, build_cgep, topology_triples
from ekg.succession.graph_context import swap_graph_context
from ekg.succession.linearize import EDGE_BUDGET, EventVocabulary
from ekg.succession.perturbation import graph_perturbations
from ekg.succession.predictor import metrics_of, rank_instances, successor_predictors
from ekg.succession.reconstruction import corpus_reconstruction

_MAVEN = Path("data/processed/maven_ere")

_CAUSAL_SUBTYPES = ("CAUSE", "PRECONDITION")

# Amplitudes per error type. Deletion and insertion sweep the whole useful range
# (a 1.0 insertion rate doubles the topology); the coreference perturbations bite
# much harder per unit, since one merged node rewires all of its relations.
_SWEEPS = {
    "drop_edges": (0.1, 0.25, 0.5, 0.75, 1.0),
    "add_edges": (0.25, 0.5, 1.0),
    "merge_nodes": (0.05, 0.1, 0.25),
    "split_nodes": (0.05, 0.1, 0.25),
}


@dataclass(frozen=True)
class Arm:
    """One graph to score the fixed CGEP problem set against."""

    name: str
    family: str
    edges_by_doc: dict[str, list[RelationEdge]]
    meta: dict[str, float] = field(default_factory=dict)


def _graph(doc: RelationDocument, edges: list[RelationEdge]) -> EventGraph:
    return EventGraph(nodes={n.event_id: n for n in doc.nodes}, edges=list(edges))


def _n_causal(edges_by_doc: dict[str, list[RelationEdge]]) -> int:
    return sum(
        1
        for edges in edges_by_doc.values()
        for _, subtype, _ in topology_triples(edges)
        if subtype in _CAUSAL_SUBTYPES
    )


def _topology_nodes(edges_by_doc: dict[str, list[RelationEdge]]) -> dict[str, list[str]]:
    """Per document, the events that carry ECG topology.

    Perturbations are aimed here rather than at every mention in the document:
    an amplitude spent on nodes with no causal or subevent edge would be
    invisible downstream and would silently weaken the sweep.
    """
    return {
        doc_id: sorted({node for head, _, tail in topology_triples(edges) for node in (head, tail)})
        for doc_id, edges in edges_by_doc.items()
    }


def _repair_arms(
    docs: list[RelationDocument], predicted: dict[str, list[RelationEdge]]
) -> list[Arm]:
    """Phase B's solver and its two action ablations, on the predicted graph."""
    settings = {
        "repaired": {},
        "repaired_noclose": {"close_temporal": False},
        "repaired_nobreak": {"break_causal_cycles": False},
    }
    arms: list[Arm] = []
    for name, kwargs in settings.items():
        solver = consistency_solvers.create("greedy", **kwargs)
        edges = {
            doc.doc_id: list(solver.solve(_graph(doc, predicted.get(doc.doc_id, []))).edges)
            for doc in docs
        }
        arms.append(Arm(name, "constructed", edges, {"n_causal": float(_n_causal(edges))}))
    return arms


def _matched_drop_arm(arms: list[Arm], seed: int) -> Arm:
    """Delete as many causal edges at random as breaking causal cycles deleted.

    Built on `repaired_nobreak` so the *only* difference from `repaired` is which
    k causal edges left the graph -- targeted versus random.
    """
    by_name = {arm.name: arm for arm in arms}
    base, broken = by_name["repaired_nobreak"], by_name["repaired"]
    k = int(base.meta["n_causal"] - broken.meta["n_causal"])
    result = graph_perturbations.create(
        "drop_edges",
        edges_by_doc=base.edges_by_doc,
        exact=max(k, 0),
        subtypes=_CAUSAL_SUBTYPES,
        seed=seed,
    )
    return Arm(
        "random_drop_matched",
        "control",
        result.edges_by_doc,
        {**result.stats, "matched_to": float(k)},
    )


def _purification_arms(
    docs: list[RelationDocument],
    predicted: dict[str, list[RelationEdge]],
    labels: dict[str, str],
    suffix: str,
    seed: int,
) -> list[Arm]:
    """Drop CT- events, plus the two matched random-removal controls.

    Purification also down-weights hedged events, but confidence never reaches
    the linearised template, so only the node removals can move this table --
    stated here rather than left for a reader to discover.
    """
    purified: dict[str, list[RelationEdge]] = {}
    uniform: dict[str, list[RelationEdge]] = {}
    matched: dict[str, list[RelationEdge]] = {}
    n_dropped = 0
    gaps: list[float] = []
    rng = random.Random(seed)

    for doc in docs:
        graph = _graph(doc, predicted.get(doc.doc_id, []))
        result = purify_graph(graph, labels, DEFAULT_POLICY)
        purified[doc.doc_id] = list(result.graph.edges)
        n_dropped += len(result.dropped_nodes)

        k = len(result.dropped_nodes)
        pool = sorted(graph.nodes)
        blind = set(rng.sample(pool, min(k, len(pool))))
        uniform[doc.doc_id] = [
            e for e in graph.edges if e.head_id not in blind and e.tail_id not in blind
        ]

        samples, doc_gaps = degree_matched_samples(
            graph, result.dropped_nodes, trials=1, seed=seed
        )
        twin = samples[0] if samples else set()
        gaps.extend(doc_gaps)
        matched[doc.doc_id] = [
            e for e in graph.edges if e.head_id not in twin and e.tail_id not in twin
        ]

    meta = {
        "n_dropped_nodes": float(n_dropped),
        "degree_gap": sum(gaps) / len(gaps) if gaps else 0.0,
    }
    return [
        Arm(f"purified{suffix}", "purification", purified, meta),
        Arm(f"purified{suffix}_random_control", "control", uniform, meta),
        Arm(f"purified{suffix}_degree_matched_control", "control", matched, meta),
    ]


def _perturbation_arms(gold: dict[str, list[RelationEdge]], seed: int) -> list[Arm]:
    nodes = _topology_nodes(gold)
    arms: list[Arm] = []
    for name, rates in _SWEEPS.items():
        for rate in rates:
            result = graph_perturbations.create(
                name, edges_by_doc=gold, nodes_by_doc=nodes, rate=rate, seed=seed
            )
            arms.append(
                Arm(f"{name}@{rate:g}", "perturbation", result.edges_by_doc,
                    {**result.stats, "rate": rate})
            )
    scrambled = graph_perturbations.create(
        "scramble_temporal", edges_by_doc=gold, nodes_by_doc=nodes, rate=1.0, seed=seed
    )
    arms.append(Arm("scramble_temporal@1", "perturbation", scrambled.edges_by_doc,
                    {**scrambled.stats, "rate": 1.0}))
    return arms


def _structural_report(
    docs: list[RelationDocument], edges_by_doc: dict[str, list[RelationEdge]]
) -> dict:
    """The structural view of one arm: consistency violations plus R1/R2.

    Reported alongside the downstream metrics because Ch4's claim is that the two
    views *disagree* -- purification removes the semantically wrong nodes without
    removing cycles, repair removes cycles without buying reconstructability. A
    claim like that is only checkable if both are measured on the same graphs.
    """
    pairs = [(doc, _graph(doc, edges_by_doc.get(doc.doc_id, []))) for doc in docs]
    consistency: dict[str, float] = {}
    for _, graph in pairs:
        for key, value in consistency_report(graph).items():
            consistency[key] = consistency.get(key, 0.0) + value
    return {
        "consistency": consistency,
        "reconstruction": corpus_reconstruction(pairs),
        "n_edges": float(sum(len(edges) for edges in edges_by_doc.values())),
        "n_topology_edges": float(
            sum(len(topology_triples(edges)) for edges in edges_by_doc.values())
        ),
    }


def _budget_report(
    ranks: list[float], reachable: list[bool], *, alpha_total: float, cal_ratio: float, seed: int
) -> dict[str, dict[str, float]]:
    """CS-CRP composed coverage on *measured* construction loss.

    `cross_stage_sweep` induces reachability loss synthetically because Phase B
    had no extractor strong enough to produce a non-degenerate constructed ECG.
    It now does, so the reachability mask here is the real one: which gold query
    edges this arm's graph actually still contains.
    """
    order = list(range(len(ranks)))
    random.Random(seed).shuffle(order)
    cut = int(len(order) * cal_ratio)
    cal, test = order[:cut], order[cut:]
    if not cal or not test:
        return {}
    results = compare_cross_stage_methods(
        [reachable[i] for i in test],
        [ranks[i] if reachable[i] else math.inf for i in test],
        [ranks[i] for i in cal if reachable[i]],
        alpha_total=alpha_total,
        cal_reachable=[reachable[i] for i in cal],
    )
    return {
        method: {
            "composed_coverage": result.composed_coverage,
            "reasoning_coverage": result.reasoning_coverage,
            "reachable_rate": result.reachable_rate,
            "composed_drift_gap": result.composed_drift_gap,
            "mean_set_size": result.mean_set_size,
            "target": result.target,
        }
        for method, result in results.items()
    }


def _run_structural(
    args, docs: list[RelationDocument], test: list[CgepInstance], arms: list[Arm], stats: dict
) -> int:
    """The torch-free half: what each arm does to the graph, before any reasoning.

    Kept in this script rather than a separate one so both halves are built from
    exactly the same arm definitions -- a structural table assembled from a
    second, drifting copy of the arm code would not be comparable with the
    downstream one, which is the whole point of measuring both.
    """
    report: dict[str, dict] = {}
    for arm in arms:
        swap = swap_graph_context(test, arm.edges_by_doc, order=args.template_order)
        structural = _structural_report(docs, arm.edges_by_doc)
        report[arm.name] = {
            "family": arm.family,
            "graph_meta": arm.meta,
            "swap": swap.stats,
            **structural,
        }
        prf = structural["reconstruction"]["r2_query_prf"]
        r1 = structural["reconstruction"]["r1_reachability_rate"]
        scc = structural["consistency"]["causal_cyclic_scc"]
        print(
            f"[struct] {arm.name:38s} r1={r1:.4f} r2f1={prf['f1']:.4f} "
            f"causal_scc={scc:.0f} topo={structural['n_topology_edges']:.0f}",
            flush=True,
        )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(
            {"mode": "structural", "n_docs": len(docs), "cgep_stats": stats,
             "template_order": args.template_order, "seed": args.seed, "arms": report},
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\n[struct] wrote {args.output}")
    return 0


def _build_predictor(args, train: list[CgepInstance], test: list[CgepInstance]):
    if args.predictor != "sedgpl":
        return successor_predictors.create(args.predictor)
    if not args.model_path:
        raise SystemExit("--predictor sedgpl needs --model-path")
    import ekg.succession.sedgpl  # noqa: F401 - registers "sedgpl"

    return successor_predictors.create(
        "sedgpl", model_path=args.model_path,
        vocabulary=EventVocabulary.build([*train, *test]),
        epochs=args.epochs, sample_rate=args.sample_rate, device=args.device, lr=args.lr,
        edge_selector=args.edge_selector, max_edges=args.max_edges,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dump", type=Path, help="Phase A predicted edges (jsonl)")
    parser.add_argument("--gold", type=Path, default=_MAVEN / "valid.jsonl")
    parser.add_argument("--train", type=Path, default=_MAVEN / "train.jsonl")
    parser.add_argument("--factuality-labels", type=Path,
                        help="{mention_id: label} from the Phase D detector")
    parser.add_argument("--factuality-gold", type=Path,
                        help="MAVEN-FACT valid jsonl, for the oracle purification ceiling")
    parser.add_argument("--predictor", default="sedgpl",
                        choices=("random", "frequency", "sedgpl"))
    parser.add_argument("--model-path", help="roberta-base checkpoint, for sedgpl")
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--sample-rate", type=float, default=0.8)
    parser.add_argument("--lr", type=float, default=1e-6)
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--edge-selector", default="sedgpl", choices=("sedgpl", "distance"))
    parser.add_argument("--max-edges", type=int, default=EDGE_BUDGET)
    parser.add_argument("--also-distance-selector", action="store_true",
                        help="re-score every arm under the distance budget too; separates "
                             "'the graph is wrong' from 'the graph is too dense for the budget'")
    parser.add_argument(
        "--template-order", default="canonical", choices=("source", "canonical"),
        help="'canonical' makes the prompt a function of the edge set alone, which is "
             "what an attribution run needs -- SeDGPL truncates by stored order, so two "
             "arms holding the same edges but serialised differently otherwise score "
             "differently. 'source' keeps document order and reproduces the published "
             "gold baseline byte-for-byte",
    )
    parser.add_argument("--alpha-total", type=float, default=0.2)
    parser.add_argument("--cal-ratio", type=float, default=0.5)
    parser.add_argument("--seed", type=int, default=209)
    parser.add_argument("--limit-docs", type=int, help="first N valid documents (smoke)")
    parser.add_argument("--limit-train", type=int, help="cap train instances (smoke)")
    parser.add_argument("--skip-perturbations", action="store_true")
    parser.add_argument(
        "--structural-only", action="store_true",
        help="skip the predictor and report only what each arm did to the graph "
             "(consistency violations, R1/R2). Torch-free, so it runs on CPU while the "
             "GPU table is still training",
    )
    parser.add_argument("--save-model", type=Path, help="write the fitted weights here")
    parser.add_argument(
        "--load-model",
        type=Path,
        help="score with weights from a previous --save-model instead of fitting. The "
             "vocabulary is rebuilt from the instances, so --train/--gold/--limit-* must "
             "match the run that saved them or every <a_i> token would re-map",
    )
    parser.add_argument("--output", type=Path, default=Path("runs/cgep/ch4_propagation.json"))
    parser.add_argument("--ranks-output", type=Path,
                        help="per-instance gold ranks and reachability, per arm")
    args = parser.parse_args()

    docs = list(load_maven_ere(args.gold))
    if args.limit_docs:
        docs = docs[: args.limit_docs]
    gold_edges = {doc.doc_id: list(doc.gold_edges) for doc in docs}

    test, test_stats = build_cgep(docs)
    train, _ = build_cgep(list(load_maven_ere(args.train)))
    if args.limit_train:
        train = train[: args.limit_train]
    print(f"[prop] {len(docs)} docs  {len(test)} test instances  {len(train)} train instances")

    arms: list[Arm] = [
        Arm("gold", "reference", gold_edges, {"n_causal": float(_n_causal(gold_edges))})
    ]

    if args.dump:
        keep = {doc.doc_id for doc in docs}
        predicted = {
            record["doc_id"]: [RelationEdge.model_validate(e) for e in record["edges"]]
            for record in read_jsonl(args.dump)
            if record["doc_id"] in keep
        }
        missing = keep - set(predicted)
        if missing:
            raise SystemExit(f"dump is missing {len(missing)} of {len(keep)} documents")
        arms.append(
            Arm("predicted", "constructed", predicted, {"n_causal": float(_n_causal(predicted))})
        )
        arms.extend(_repair_arms(docs, predicted))
        arms.append(_matched_drop_arm(arms, args.seed))

        if args.factuality_labels:
            labels = json.loads(args.factuality_labels.read_text(encoding="utf-8"))
            arms.extend(_purification_arms(docs, predicted, labels, "", args.seed))
        if args.factuality_gold:
            from ekg.relations.data.maven_fact import load_maven_fact

            oracle = {
                mention.mention_id: mention.factuality
                for doc in load_maven_fact(args.factuality_gold)
                for mention in doc.mentions
            }
            arms.extend(_purification_arms(docs, predicted, oracle, "_oracle", args.seed))

    if not args.skip_perturbations:
        arms.extend(_perturbation_arms(gold_edges, args.seed))

    if args.structural_only:
        return _run_structural(args, docs, test, arms, test_stats)

    predictor = _build_predictor(args, train, test)
    if args.load_model:
        predictor.load(str(args.load_model))
        print(f"[prop] scoring with weights from {args.load_model}")
    else:
        predictor.fit(train)
        if args.save_model:
            predictor.save(str(args.save_model))
            print(f"[prop] saved weights to {args.save_model}")

    selectors = [args.edge_selector]
    if args.also_distance_selector:
        selectors.append("distance" if args.edge_selector == "sedgpl" else "sedgpl")

    report: dict[str, dict] = {}
    ranks_dump: dict[str, dict] = {}
    header = {
        "predictor": args.predictor,
        "n_docs": len(docs),
        "cgep_stats": test_stats,
        "epochs": args.epochs,
        "template_order": args.template_order,
        "alpha_total": args.alpha_total,
        "seed": args.seed,
    }

    def flush() -> None:
        """Persist after every arm: this loop runs for hours on a shared GPU."""
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps({**header, "arms": report}, indent=2), encoding="utf-8")
        if args.ranks_output:
            args.ranks_output.parent.mkdir(parents=True, exist_ok=True)
            args.ranks_output.write_text(json.dumps(ranks_dump), encoding="utf-8")

    for selector in selectors:
        if args.predictor == "sedgpl":
            predictor.set_edge_selector(selector)
        for arm in arms:
            swap = swap_graph_context(test, arm.edges_by_doc, order=args.template_order)
            ranked = rank_instances(predictor, swap.instances)
            metrics = metrics_of(ranked)
            key = arm.name if selector == args.edge_selector else f"{arm.name}::{selector}"
            reachable = list(swap.reachable)
            ranks = [
                math.inf if bad else float(rank)
                for rank, bad in zip(ranked.optimistic, ranked.unscorable, strict=True)
            ]
            report[key] = {
                "family": arm.family,
                "selector": selector,
                "graph_meta": arm.meta,
                "swap": swap.stats,
                "metrics": metrics,
                "budget": _budget_report(
                    ranks, reachable, alpha_total=args.alpha_total,
                    cal_ratio=args.cal_ratio, seed=args.seed,
                ),
            }
            ranks_dump[key] = {"ranks": ranks, "reachable": reachable}
            flush()
            print(
                f"[prop] {key:38s} mrr={metrics['mrr']:.4f} strict={metrics['mrr_strict']:.4f} "
                f"h@1={metrics['hits@1']:.4f} reach={swap.stats['reachability_rate']:.4f} "
                f"tmpl={swap.stats['mean_template_edges']:.1f}",
                flush=True,
            )

    baseline = report["gold"]["metrics"]["mrr"]
    print(f"\n{'arm':38s}{'mrr':>9}{'d(mrr)':>9}{'strict':>9}{'reach':>8}{'tmpl':>8}")
    for key, row in report.items():
        print(f"{key:38s}{row['metrics']['mrr']:>9.4f}"
              f"{row['metrics']['mrr'] - baseline:>+9.4f}"
              f"{row['metrics']['mrr_strict']:>9.4f}"
              f"{row['swap']['reachability_rate']:>8.4f}"
              f"{row['swap']['mean_template_edges']:>8.1f}")

    flush()
    print(f"\n[prop] wrote {args.output}")
    if args.ranks_output:
        print(f"[prop] wrote {args.ranks_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
