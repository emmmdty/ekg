"""Structure-aware event factuality detection over the constructed graph.

The task is per *mention*: label each event mention CT+/PS+/CT−/PS−/Uu. The
textual signal (negation, modals, reporting verbs) is the encoder's job; what
this module adds is the **graph context** a constructed event graph provides —
whether the mention is asserted as a cause or an effect, whether it has a parent
event, how often it is co-referred, how many arguments it was given.

`structure_contexts` takes the edge list as an argument rather than reading it
off the document, and that is the point: passing the gold edges measures the
setting MAVEN-FACT itself reports, passing Phase A/B's *predicted* edges
measures what the number becomes on a graph the pipeline actually built. The
gap between the two is Ch3's robustness result, so the two runs must differ in
nothing but this argument.

Direction is never pooled. "Asserted as the cause of something" and "asserted as
the effect of something" are different evidence about whether an event happened,
so in/out degrees stay separate features.

`LexiconFactualityDetector` is the CPU memorization floor (most frequent label
per trigger word, backing off to CT+). It exists so the pipeline runs and is
testable without a GPU and so the neural number has a floor to be judged
against — on a corpus that is 94.4% CT+, a detector that merely beats accuracy
has demonstrated nothing.
"""

from __future__ import annotations

import json
import math
from abc import ABC, abstractmethod
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from ekg.core.registry import Registry
from ekg.core.schema import EventNode, EvidenceSpan, RelationEdge, RelationType
from ekg.factuality.evidence import evidence_candidates
from ekg.nodes.encoding import TORCH_AVAILABLE, encode_spans, pair_features
from ekg.relations.data.maven_fact import (
    FACTUALITY_LABELS,
    FactualityDocument,
    FactualityMention,
)

__all__ = [
    "STRUCTURE_FEATURE_NAMES",
    "StructureContext",
    "structure_contexts",
    "FactualityPrediction",
    "FactualityDetector",
    "factuality_detectors",
    "LexiconFactualityDetector",
    "SupervisedFactualityDetector",
    "predictions_to_labels",
]

# Files a trained detector checkpoint carries next to the encoder/tokenizer.
# The evidence head is optional: a checkpoint without it predicts labels only.
HEAD_FILE = "head.pt"
EVIDENCE_HEAD_FILE = "evidence_head.pt"
LABELS_FILE = "labels.json"

# The class an unseen trigger backs off to, and what a trivial system collapses
# to (94.4% of train).
BACKOFF_LABEL = FACTUALITY_LABELS[0]

STRUCTURE_FEATURE_NAMES: tuple[str, ...] = (
    "causal_out",
    "causal_in",
    "temporal_out",
    "temporal_in",
    "subevent_out",
    "subevent_in",
    "coref_degree",
    "n_arguments",
)


@dataclass(frozen=True)
class StructureContext:
    """One mention's position in the event graph, as directed degree counts."""

    mention_id: str
    causal_out: int = 0
    causal_in: int = 0
    temporal_out: int = 0
    temporal_in: int = 0
    subevent_out: int = 0
    subevent_in: int = 0
    coref_degree: int = 0
    n_arguments: int = 0

    def as_vector(self) -> list[float]:
        """`log1p`-compressed counts, in `STRUCTURE_FEATURE_NAMES` order.

        Raw degrees are unbounded — MAVEN-ERE's transitively closed temporal
        relations give some mentions hundreds of edges — and concatenating an
        unbounded feature onto a unit-scale encoder representation lets one hub
        mention dominate the head. `log1p` keeps every feature inside [0, ~5].
        """
        return [math.log1p(getattr(self, name)) for name in STRUCTURE_FEATURE_NAMES]


def structure_contexts(
    mentions: Sequence[FactualityMention],
    edges: Iterable[RelationEdge],
    *,
    nodes: Sequence[EventNode] | None = None,
) -> dict[str, StructureContext]:
    """Graph context per mention, from *whichever* edge set is passed in.

    Every mention gets an entry: an isolated mention is an all-zero context, not
    a missing key, so a sparser predicted graph shifts the features instead of
    silently dropping mentions from the evaluation.
    """
    counts: dict[str, dict[str, int]] = {
        m.mention_id: dict.fromkeys(STRUCTURE_FEATURE_NAMES, 0) for m in mentions
    }
    outgoing = {
        RelationType.CAUSAL: "causal_out",
        RelationType.TEMPORAL: "temporal_out",
        RelationType.SUBEVENT: "subevent_out",
    }
    incoming = {
        RelationType.CAUSAL: "causal_in",
        RelationType.TEMPORAL: "temporal_in",
        RelationType.SUBEVENT: "subevent_in",
    }
    for edge in edges:
        if edge.relation_type is RelationType.COREFERENCE:
            # Symmetric: both endpoints gain a neighbour.
            for endpoint in (edge.head_id, edge.tail_id):
                if endpoint in counts:
                    counts[endpoint]["coref_degree"] += 1
            continue
        if edge.head_id in counts:
            counts[edge.head_id][outgoing[edge.relation_type]] += 1
        if edge.tail_id in counts:
            counts[edge.tail_id][incoming[edge.relation_type]] += 1

    for node in nodes or ():
        if node.event_id in counts:
            counts[node.event_id]["n_arguments"] = len(node.arguments)

    return {
        mention_id: StructureContext(mention_id=mention_id, **fields)
        for mention_id, fields in counts.items()
    }


@dataclass(frozen=True)
class FactualityPrediction:
    """A labelled mention with the model's confidence and supporting evidence."""

    mention_id: str
    factuality: str
    confidence: float
    evidence: tuple[EvidenceSpan, ...] = ()


class FactualityDetector(ABC):
    """Labels every mention of a document with one of the five classes."""

    @abstractmethod
    def predict(self, doc: FactualityDocument) -> dict[str, FactualityPrediction]:
        """Mention id -> prediction, covering *every* mention of the document.

        Unlike event detection there is no NONE class to fall back to, so the
        mapping is dense: `factuality_report` rejects a missing prediction
        rather than treating it as an abstention.
        """


factuality_detectors: Registry[FactualityDetector] = Registry("factuality_detector")


@factuality_detectors.register("lexicon")
class LexiconFactualityDetector(FactualityDetector):
    """Most-frequent-label-per-trigger baseline (pure CPU, no torch).

    Takes the same ``checkpoint_path`` argument as the neural detector so both
    are built identically from a config.
    """

    def __init__(self, checkpoint_path: str | Path | None = None) -> None:
        self.counts: dict[str, dict[str, int]] = (
            json.loads(Path(checkpoint_path).read_text()) if checkpoint_path else {}
        )

    def fit(self, docs: Iterable[FactualityDocument]) -> LexiconFactualityDetector:
        counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        for doc in docs:
            for mention in doc.mentions:
                counts[mention.trigger.lower()][mention.factuality] += 1
        self.counts = {trigger: dict(labels) for trigger, labels in counts.items()}
        return self

    def predict(self, doc: FactualityDocument) -> dict[str, FactualityPrediction]:
        predictions: dict[str, FactualityPrediction] = {}
        for mention in doc.mentions:
            labels = self.counts.get(mention.trigger.lower())
            if not labels:
                predictions[mention.mention_id] = FactualityPrediction(
                    mention.mention_id, BACKOFF_LABEL, 0.0
                )
                continue
            total = sum(labels.values())
            label, count = max(labels.items(), key=lambda kv: (kv[1], kv[0]))
            predictions[mention.mention_id] = FactualityPrediction(
                mention.mention_id, label, count / total
            )
        return predictions

    def save(self, path: str | Path) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(json.dumps(self.counts, sort_keys=True))


@factuality_detectors.register("supervised")
class SupervisedFactualityDetector(FactualityDetector):
    """Encoder span representation ⊕ structure features -> 5-way linear head.

    The encoder and head load lazily on the first `predict`, so the class
    instantiates and registers on a CPU box. The document is encoded once per
    call and every mention is gathered out of it (`encoding.encode_spans`), so
    cost is linear in document length rather than in mention count.

    ``use_structure=False`` drops the graph features and keeps everything else
    identical — the ablation that says how much the structure is worth, and the
    control for the gold-vs-predicted graph comparison.
    """

    def __init__(
        self,
        checkpoint_path: str | None = None,
        max_length: int = 512,
        stride: int = 128,
        use_structure: bool = True,
    ) -> None:
        self.checkpoint_path = checkpoint_path
        self.max_length = max_length
        self.stride = stride
        self.use_structure = use_structure
        self._encoder = None
        self._tokenizer = None
        self._head = None
        self._evidence_head = None
        self._labels: list[str] = []
        self._device = "cpu"

    def _ensure_model(self) -> None:
        if self._head is not None:
            return
        if not TORCH_AVAILABLE:
            raise RuntimeError(
                "supervised factuality detection needs torch + transformers: install the "
                "`llm` extra. This is a GPU-only path."
            )
        import torch
        from torch import nn
        from transformers import AutoModel, AutoTokenizer

        if not self.checkpoint_path:
            raise ValueError("supervised factuality detector: checkpoint_path is required")
        ckpt = Path(self.checkpoint_path)
        head_file = ckpt / HEAD_FILE
        if not head_file.exists():
            raise FileNotFoundError(f"trained head not found at {head_file}")
        self._labels = json.loads((ckpt / LABELS_FILE).read_text())
        if tuple(self._labels) != FACTUALITY_LABELS:
            raise ValueError(
                f"{LABELS_FILE} holds {self._labels}, expected {list(FACTUALITY_LABELS)}"
            )
        self._tokenizer = AutoTokenizer.from_pretrained(str(ckpt))
        self._encoder = AutoModel.from_pretrained(str(ckpt))
        hidden = self._encoder.config.hidden_size
        width = hidden + (len(STRUCTURE_FEATURE_NAMES) if self.use_structure else 0)
        self._head = nn.Linear(width, len(self._labels))
        self._head.load_state_dict(torch.load(head_file, map_location="cpu"))
        self._device = "cuda" if torch.cuda.is_available() else "cpu"
        self._encoder.to(self._device).eval()
        self._head.to(self._device).eval()

        evidence_file = ckpt / EVIDENCE_HEAD_FILE
        if evidence_file.exists():
            # `pair_features` widens to 4x hidden -- the same feature the
            # relation and coreference pair heads read, so a (candidate,
            # trigger) decision is made from a comparable representation.
            self._evidence_head = nn.Linear(4 * hidden, 1)
            self._evidence_head.load_state_dict(torch.load(evidence_file, map_location="cpu"))
            self._evidence_head.to(self._device).eval()

    def predict(
        self,
        doc: FactualityDocument,
        edges: Sequence[RelationEdge] | None = None,
    ) -> dict[str, FactualityPrediction]:
        """Label every mention; ``edges`` defaults to the document's gold graph.

        Pass the predicted graph here to run the robustness protocol — it is the
        only input that changes between the two conditions.

        Evidence spans come back only when the checkpoint carries an evidence
        head, and only for mentions predicted non-CT+: evidence is annotated on
        0.1% of CT+ mentions against 88–99% of the other classes, so predicting
        it for an event asserted to have happened would be inventing support for
        a label that rests on none.
        """
        if not doc.mentions:
            return {}
        self._ensure_model()
        import torch

        contexts = structure_contexts(
            doc.mentions, doc.gold_edges if edges is None else edges, nodes=doc.nodes
        )
        candidates = (
            [evidence_candidates(doc, m) for m in doc.mentions]
            if self._evidence_head is not None
            else [[] for _ in doc.mentions]
        )
        char_starts = [m.span.char_start for m in doc.mentions]
        char_starts += [c.char_start for per_mention in candidates for c in per_mention]

        with torch.no_grad():
            # One forward pass covers the triggers *and* every evidence
            # candidate; splitting them would encode the document twice.
            pooled = encode_spans(
                self._encoder,
                self._tokenizer,
                doc.doc_text,
                char_starts,
                max_length=self.max_length,
                stride=self.stride,
                device=self._device,
            )
            triggers = pooled[: len(doc.mentions)]
            features = triggers
            if self.use_structure:
                structure = torch.tensor(
                    [contexts[m.mention_id].as_vector() for m in doc.mentions],
                    dtype=features.dtype,
                    device=features.device,
                )
                features = torch.cat([features, structure], dim=-1)
            probs = torch.softmax(self._head(features), dim=-1)
            confidence, index = probs.max(dim=-1)

            evidence: list[tuple[EvidenceSpan, ...]] = [() for _ in doc.mentions]
            if self._evidence_head is not None:
                cursor = len(doc.mentions)
                for i, per_mention in enumerate(candidates):
                    span_features = pooled[cursor : cursor + len(per_mention)]
                    cursor += len(per_mention)
                    if not len(per_mention) or self._labels[index[i]] == BACKOFF_LABEL:
                        continue
                    trigger = triggers[i].expand(len(per_mention), -1)
                    scores = self._evidence_head(pair_features(span_features, trigger))
                    keep = (scores.squeeze(-1) > 0).tolist()
                    evidence[i] = tuple(c for c, k in zip(per_mention, keep, strict=True) if k)

        return {
            m.mention_id: FactualityPrediction(m.mention_id, self._labels[i], float(p), ev)
            for m, i, p, ev in zip(
                doc.mentions, index.tolist(), confidence.tolist(), evidence, strict=True
            )
        }


def predictions_to_labels(
    predictions: Mapping[str, FactualityPrediction],
) -> dict[str, str]:
    """Drop confidences, giving the mapping `factuality_report` scores."""
    return {mention_id: p.factuality for mention_id, p in predictions.items()}
