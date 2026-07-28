"""Uncertainty-aware canonicalization: mentions -> canonical event nodes.

Average-link agglomerative clustering over pair probabilities, with one
deliberate difference from plain coreference: a merge whose score lands in the
**abstention band** around the threshold is refused rather than guessed. The
band is the uncertainty knob — widening it trades merge recall for a lower
mis-merge rate *explicitly*, and every refusal is recorded so the cost is
auditable instead of buried in a threshold.

Each canonical node reports a raw confidence with a single meaning: *how sure am
I that this cluster is exactly right*.

- merged cluster -> its **weakest internal link** (one bad merge ruins it);
- singleton      -> ``1 - its strongest external link`` (the merge most nearly made).

That raw score is monotone but not a probability; `IsotonicProbabilityCalibrator`
maps it to `node_confidence` on a held-out split, and the ECE of the result is
what makes it spendable as a downstream error budget.

Cluster-level aggregation picks the canonical trigger by **evidence weight**
(the mention with the highest summed link support), unions the evidence spans,
and merges arguments role-wise, keeping conflicting fillers instead of silently
picking one — evidence conflict is reported, not resolved by luck.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from ekg.core.schema import EventNode, EvidenceSpan
from ekg.nodes.coref import PairKey

__all__ = [
    "CanonicalNode",
    "CanonicalizationResult",
    "canonicalize",
    "raw_node_confidence",
]


@dataclass
class CanonicalNode:
    """One deduplicated event: its mentions, aggregated evidence and confidence."""

    node_id: str
    event_type: str
    doc_id: str
    canonical_trigger: str
    mention_cluster: list[str]
    evidence_spans: list[EvidenceSpan]
    arguments: dict[str, str]
    argument_evidence: dict[str, list[EvidenceSpan]]
    raw_confidence: float
    node_confidence: float
    conflicting_roles: list[str] = field(default_factory=list)

    def to_event_node(self) -> EventNode:
        """Project onto the frozen contract; extras go in `metadata` only."""
        return EventNode(
            event_id=self.node_id,
            event_type=self.event_type,
            doc_id=self.doc_id,
            trigger=self.canonical_trigger,
            trigger_evidence=self.evidence_spans,
            arguments=self.arguments,
            argument_evidence=self.argument_evidence,
            confidence=self.node_confidence,
            metadata={
                "mention_cluster": ",".join(self.mention_cluster),
                "raw_confidence": f"{self.raw_confidence:.6f}",
                "node_confidence": f"{self.node_confidence:.6f}",
                "conflicting_roles": ",".join(self.conflicting_roles),
                "provenance": "nodes.canonical",
            },
        )


@dataclass
class CanonicalizationResult:
    """Canonical nodes plus the decisions that produced them."""

    nodes: list[CanonicalNode]
    abstained_merges: list[tuple[str, str, float]] = field(default_factory=list)

    def clusters(self) -> list[set[str]]:
        return [set(node.mention_cluster) for node in self.nodes]


def _symmetric(scores: Mapping[PairKey, float]) -> dict[PairKey, float]:
    """Coreference is symmetric; index both directions once, max-wins on clashes."""
    out: dict[PairKey, float] = {}
    for (head, tail), score in scores.items():
        for key in ((head, tail), (tail, head)):
            out[key] = max(out.get(key, 0.0), float(score))
    return out


def _average_link(
    left: Sequence[str], right: Sequence[str], scores: Mapping[PairKey, float]
) -> float:
    """Mean pair score across the two clusters; unscored pairs count as 0."""
    return sum(scores.get((a, b), 0.0) for a in left for b in right) / (len(left) * len(right))


def _cluster_mentions(
    mention_ids: Sequence[str],
    scores: Mapping[PairKey, float],
    threshold: float,
    band: float,
) -> tuple[list[list[str]], list[float], list[tuple[str, str, float]]]:
    """Agglomerate while the best average link clears `threshold + band`.

    Merging stops at the maximum remaining link, so the surviving cluster pairs
    whose link sits in ``[threshold - band, threshold + band)`` are exactly the
    merges the band refused — collected afterwards rather than mutated into the
    score table mid-loop. With ``band = 0`` this is plain average-link
    clustering at ``threshold`` and the refusal list is empty.

    Returns the clusters, each cluster's weakest accepted internal link, and the
    refused merges.
    """
    clusters: list[list[str]] = [[m] for m in mention_ids]
    weakest: list[float] = [1.0] * len(clusters)

    while len(clusters) > 1:
        link, i, j = max(
            (_average_link(clusters[i], clusters[j], scores), i, j)
            for i in range(len(clusters))
            for j in range(i + 1, len(clusters))
        )
        if link < threshold + band:
            break
        clusters[i] = clusters[i] + clusters[j]
        weakest[i] = min(weakest[i], weakest[j], link)
        clusters.pop(j)
        weakest.pop(j)

    abstained = [
        (clusters[i][0], clusters[j][0], link)
        for i in range(len(clusters))
        for j in range(i + 1, len(clusters))
        if threshold - band <= (link := _average_link(clusters[i], clusters[j], scores))
        < threshold + band
    ]
    return clusters, weakest, abstained


def raw_node_confidence(
    cluster: Sequence[str],
    others: Sequence[str],
    scores: Mapping[PairKey, float],
    weakest_link: float,
) -> float:
    """Weakest internal link for a merged cluster; `1 - strongest external` for a singleton."""
    if len(cluster) > 1:
        return weakest_link
    if not others:
        return 1.0
    return 1.0 - max(scores.get((cluster[0], other), 0.0) for other in others)


def _aggregate(
    cluster: Sequence[str],
    by_id: Mapping[str, EventNode],
    scores: Mapping[PairKey, float],
) -> tuple[str, list[EvidenceSpan], dict[str, str], dict[str, list[EvidenceSpan]], list[str]]:
    """Canonical trigger, unioned evidence, role-wise arguments, conflicting roles."""
    support = {
        m: sum(scores.get((m, other), 0.0) for other in cluster if other != m) for m in cluster
    }
    # Highest evidence weight wins; ties fall back to id so the pick is stable.
    canonical = max(cluster, key=lambda m: (support[m], m))

    spans: list[EvidenceSpan] = []
    arguments: dict[str, list[str]] = {}
    argument_evidence: dict[str, list[EvidenceSpan]] = {}
    for mention in cluster:
        node = by_id[mention]
        spans.extend(node.trigger_evidence)
        for role, value in node.arguments.items():
            if value not in arguments.setdefault(role, []):
                arguments[role].append(value)
            argument_evidence.setdefault(role, []).extend(node.argument_evidence.get(role, []))

    conflicting = sorted(role for role, values in arguments.items() if len(values) > 1)
    return (
        by_id[canonical].trigger,
        spans,
        {role: " | ".join(values) for role, values in arguments.items()},
        argument_evidence,
        conflicting,
    )


def canonicalize(
    nodes: Sequence[EventNode],
    scores: Mapping[PairKey, float],
    *,
    threshold: float = 0.5,
    band: float = 0.0,
    calibrator=None,
) -> CanonicalizationResult:
    """Cluster mentions into canonical nodes with (optionally calibrated) confidence.

    `calibrator` is an `IsotonicProbabilityCalibrator` fitted on a *held-out*
    split; without one `node_confidence` equals the raw score and must not be
    reported as calibrated.
    """
    if not nodes:
        return CanonicalizationResult(nodes=[])
    if band < 0:
        raise ValueError("band must be non-negative")

    by_id = {node.event_id: node for node in nodes}
    symmetric = _symmetric(scores)
    mention_ids = [node.event_id for node in nodes]
    clusters, weakest, abstained = _cluster_mentions(mention_ids, symmetric, threshold, band)

    raw = [
        raw_node_confidence(
            cluster,
            [m for m in mention_ids if m not in set(cluster)],
            symmetric,
            link,
        )
        for cluster, link in zip(clusters, weakest, strict=True)
    ]
    calibrated = calibrator.transform(raw) if calibrator is not None else list(raw)

    canonical_nodes: list[CanonicalNode] = []
    for cluster, raw_score, confidence in zip(clusters, raw, calibrated, strict=True):
        trigger, spans, arguments, argument_evidence, conflicting = _aggregate(
            cluster, by_id, symmetric
        )
        ordered = sorted(cluster)
        canonical_nodes.append(
            CanonicalNode(
                node_id=ordered[0],
                event_type=by_id[ordered[0]].event_type,
                doc_id=by_id[ordered[0]].doc_id,
                canonical_trigger=trigger,
                mention_cluster=ordered,
                evidence_spans=spans,
                arguments=arguments,
                argument_evidence=argument_evidence,
                raw_confidence=raw_score,
                node_confidence=confidence,
                conflicting_roles=conflicting,
            )
        )
    canonical_nodes.sort(key=lambda n: n.node_id)
    return CanonicalizationResult(nodes=canonical_nodes, abstained_merges=abstained)
