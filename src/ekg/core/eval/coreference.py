"""CoNLL coreference metrics: MUC, B-cubed and CEAFe.

Inputs are clusterings — each a list of sets of event ids. The CoNLL score is
the unweighted mean of the three F1 scores, the standard headline number for
event-coreference benchmarks (MAVEN-ERE, ECB+).
"""

from __future__ import annotations

import numpy as np
from scipy.optimize import linear_sum_assignment

__all__ = ["muc", "muc_link_errors", "b_cubed", "ceafe", "conll_coref_f1"]

Cluster = set[str]


def _prf(p: float, r: float) -> dict[str, float]:
    f1 = 2 * p * r / (p + r) if (p + r) else 0.0
    return {"precision": p, "recall": r, "f1": f1}


def _mention_to_cluster(clusters: list[Cluster]) -> dict[str, frozenset[str]]:
    return {m: frozenset(c) for c in clusters for m in c}


def _muc_counts(key: list[Cluster], response: list[Cluster]) -> tuple[int, int]:
    """MUC's numerator/denominator: links recovered, links available.

    A key cluster of size n needs n-1 links; the response recovers all but one
    per extra piece it scatters that cluster into. A mention the response never
    mentions counts as its own singleton, which is how the official scorer fills
    in unclustered mentions.
    """
    m2c = _mention_to_cluster(response)
    numerator = denominator = 0
    for cluster in key:
        if len(cluster) == 0:
            continue
        partitions = {m2c.get(m, frozenset([m])) for m in cluster}
        numerator += len(cluster) - len(partitions)
        denominator += len(cluster) - 1
    return numerator, denominator


def muc(predicted: list[Cluster], gold: list[Cluster]) -> dict[str, float]:
    r_num, r_den = _muc_counts(gold, predicted)
    p_num, p_den = _muc_counts(predicted, gold)
    return _prf(
        p_num / p_den if p_den else 0.0,
        r_num / r_den if r_den else 0.0,
    )


def muc_link_errors(predicted: list[Cluster], gold: list[Cluster]) -> dict[str, float]:
    """MUC as raw link counts rather than the three ratios it collapses into.

    ``muc`` reports 77.47 without saying *how many* decisions went each way, and
    the two error directions are not interchangeable downstream: a missing link
    splits one event into two nodes, a spurious link fuses two events into one.
    Sizing an asymmetric objective needs the counts, so this returns them:

    * ``missing_links``   -- gold links the prediction failed to assert (under-merge)
    * ``spurious_links``  -- links the prediction asserted that gold does not have
                             (over-merge)

    with their denominators, so ``recall = 1 - missing/gold_links`` and
    ``precision = 1 - spurious/predicted_links`` reconcile exactly with ``muc``.
    """
    r_num, r_den = _muc_counts(gold, predicted)
    p_num, p_den = _muc_counts(predicted, gold)
    return {
        "missing_links": r_den - r_num,
        "gold_links": r_den,
        "spurious_links": p_den - p_num,
        "predicted_links": p_den,
        **_prf(
            p_num / p_den if p_den else 0.0,
            r_num / r_den if r_den else 0.0,
        ),
    }


def b_cubed(predicted: list[Cluster], gold: list[Cluster]) -> dict[str, float]:
    gold_m2c = _mention_to_cluster(gold)
    pred_m2c = _mention_to_cluster(predicted)
    mentions = set(gold_m2c) | set(pred_m2c)

    precision = recall = 0.0
    for m in mentions:
        g = gold_m2c.get(m, frozenset([m]))
        p = pred_m2c.get(m, frozenset([m]))
        overlap = len(g & p)
        precision += overlap / len(p)
        recall += overlap / len(g)
    n = len(mentions)
    return _prf(precision / n if n else 0.0, recall / n if n else 0.0)


def ceafe(predicted: list[Cluster], gold: list[Cluster]) -> dict[str, float]:
    pred = [c for c in predicted if c]
    gld = [c for c in gold if c]
    if not pred or not gld:
        return _prf(0.0, 0.0)

    scores = np.zeros((len(gld), len(pred)))
    for i, g in enumerate(gld):
        for j, p in enumerate(pred):
            scores[i, j] = 2 * len(g & p) / (len(g) + len(p))
    row, col = linear_sum_assignment(-scores)
    total = scores[row, col].sum()
    return _prf(total / len(pred), total / len(gld))


def conll_coref_f1(predicted: list[Cluster], gold: list[Cluster]) -> dict[str, float]:
    """All three metrics plus the CoNLL F1 (mean of MUC/B3/CEAFe F1)."""
    m, b, c = muc(predicted, gold), b_cubed(predicted, gold), ceafe(predicted, gold)
    conll = (m["f1"] + b["f1"] + c["f1"]) / 3
    return {"muc_f1": m["f1"], "b_cubed_f1": b["f1"], "ceafe_f1": c["f1"], "conll_f1": conll}
