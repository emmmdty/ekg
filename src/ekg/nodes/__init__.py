"""Canonical event nodes: detection, coreference, canonicalization, confidence.

The identity layer of the graph. It turns raw text into deduplicated,
evidence-grounded event records whose ``node_confidence`` is a *calibrated*
score downstream stages can spend as an error budget — the difference from plain
event coreference.

Importing this package registers the CPU implementations. Neural components
import torch lazily (as in `relations.extractor.supervised`), so the package is
importable on a machine without a GPU.
"""

from ekg.nodes.canonical import CanonicalizationResult, CanonicalNode, canonicalize
from ekg.nodes.coref import (
    CoreferenceScorer,
    CorefPair,
    LexicalCoreferenceScorer,
    SupervisedCoreferenceScorer,
    candidate_coref_pairs,
    cluster_of_nodes,
    coreference_scorers,
    labelled_coref_pairs,
    sample_training_pairs,
)
from ekg.nodes.detection import (
    EventDetector,
    LexiconEventDetector,
    SupervisedEventDetector,
    TypedSpan,
    detection_prf,
    event_detectors,
)
from ekg.nodes.metrics import merge_prf, mis_merge_report

__all__ = [
    # detection
    "EventDetector",
    "event_detectors",
    "TypedSpan",
    "detection_prf",
    "LexiconEventDetector",
    "SupervisedEventDetector",
    # coreference / similar-event discrimination
    "CorefPair",
    "CoreferenceScorer",
    "coreference_scorers",
    "LexicalCoreferenceScorer",
    "SupervisedCoreferenceScorer",
    "candidate_coref_pairs",
    "labelled_coref_pairs",
    "sample_training_pairs",
    "cluster_of_nodes",
    # canonicalization
    "CanonicalNode",
    "CanonicalizationResult",
    "canonicalize",
    # metrics
    "merge_prf",
    "mis_merge_report",
]
