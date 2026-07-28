"""Event factuality: detection on the constructed graph, and graph purification.

The factual-reliability layer. It labels each event mention with its factuality
(CT+/PS+/CT−/PS−/Uu) and uses those labels to purify the graph — dropping or
down-weighting events that were never asserted to have happened, along with the
edges that rest on them.

Two things distinguish this from the MAVEN-FACT benchmark setting it reproduces:
detection reads the graph context as a feature and is therefore measured on the
*predicted* graph as well as the gold one, and the labels feed back into the
graph rather than only into a score.

Importing this package registers the CPU implementations. Neural components
import torch lazily, so the package is importable without a GPU.
"""

from ekg.factuality.detection import (
    STRUCTURE_FEATURE_NAMES,
    FactualityDetector,
    FactualityPrediction,
    LexiconFactualityDetector,
    StructureContext,
    SupervisedFactualityDetector,
    factuality_detectors,
    predictions_to_labels,
    structure_contexts,
)
from ekg.factuality.metrics import (
    MAJORITY_LABEL,
    evidence_span_prf,
    factuality_report,
    majority_baseline_report,
)

__all__ = [
    # detection
    "STRUCTURE_FEATURE_NAMES",
    "StructureContext",
    "structure_contexts",
    "FactualityPrediction",
    "FactualityDetector",
    "factuality_detectors",
    "LexiconFactualityDetector",
    "SupervisedFactualityDetector",
    "predictions_to_labels",
    # metrics
    "MAJORITY_LABEL",
    "factuality_report",
    "majority_baseline_report",
    "evidence_span_prf",
]
