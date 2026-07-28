"""Node-stage metrics: the mis-merge rate the CoNLL numbers average away.

MUC/B³/CEAFe (in `core.eval.coreference`) summarize a clustering; they do not
say how often the system *wrongly joined* two different events, which is the
error that propagates into the graph as a fabricated identity. This module
reports that directly, as pairwise merge precision/recall, and — the number that
matters for similar-event discrimination — restricted to the **hard** subset
(same type, near-identical triggers), where the easy majority cannot hide it.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from itertools import combinations

from ekg.core.eval.relation import PRF
from ekg.nodes.coref import HARD_SIMILARITY, CorefPair

__all__ = ["merge_prf", "mis_merge_report"]


def _merged_pairs(clusters: Sequence[set[str]]) -> set[tuple[str, str]]:
    """Every merge decision a clustering asserts, as sorted mention pairs."""
    return {
        (a, b) for cluster in clusters for a, b in combinations(sorted(cluster), 2)
    }


def merge_prf(clusters: Sequence[set[str]], cluster_of: Mapping[str, str]) -> PRF:
    """Pairwise precision/recall of the merge decisions against gold clusters."""
    predicted = _merged_pairs(clusters)
    mentions = sorted({m for cluster in clusters for m in cluster})
    gold = {
        (a, b)
        for a, b in combinations(mentions, 2)
        if a in cluster_of and cluster_of[a] == cluster_of.get(b)
    }
    return PRF.from_counts(len(predicted & gold), len(predicted), len(gold))


def mis_merge_report(
    clusters: Sequence[set[str]],
    cluster_of: Mapping[str, str],
    pairs: Sequence[CorefPair],
) -> dict:
    """Mis-merge rate overall and on the hard subset, plus the merge PRF.

    ``mis_merge_rate`` is the share of asserted merges that join different gold
    events (= 1 - merge precision). ``hard_mis_merge_rate`` is the share of hard
    negative pairs the system merged anyway — the similar-event failure mode,
    measured on its own denominator so a large easy majority cannot dilute it.
    """
    predicted = _merged_pairs(clusters)
    prf = merge_prf(clusters, cluster_of)
    hard = [p for p in pairs if p.hard]
    hard_merged = sum(1 for p in hard if tuple(sorted(p.key())) in predicted)
    return {
        "merge": prf,
        "mis_merge_rate": 1.0 - prf["precision"] if prf["n_pred"] else 0.0,
        "n_merges": len(predicted),
        "hard_mis_merge_rate": hard_merged / len(hard) if hard else 0.0,
        "n_hard_pairs": len(hard),
        "hard_similarity_threshold": HARD_SIMILARITY,
    }
