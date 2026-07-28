"""Event detection: the labelled decision over MAVEN's candidate universe.

MAVEN scores detection as *candidate classification*: every gold trigger mention
plus every official ``negative_triggers`` span is one decision, labelled with an
event type or NONE. Reporting only over gold spans would silently drop the
79,661 negatives in the valid split and inflate the number, so
`detection_prf` always takes the full candidate list and rejects predictions on
spans outside it.

Two numbers are reported: **typed** micro-F1 (the headline — span *and* type must
match) and **identification** micro-F1 (span only), whose gap isolates typing
errors from missed triggers.

`LexiconEventDetector` is the CPU baseline: the most frequent type each trigger
string was annotated with in training. It is deliberately weak — it exists so the
whole canonicalization pipeline runs and is testable without a GPU, and as the
memorization floor the neural detector has to beat.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from collections import defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path

from ekg.core.eval.relation import PRF
from ekg.core.registry import Registry
from ekg.nodes.encoding import TORCH_AVAILABLE, encode_spans
from ekg.relations.data.maven_arg import NONE_TYPE, ArgumentDocument, TriggerCandidate

__all__ = [
    "TypedSpan",
    "EventDetector",
    "event_detectors",
    "detection_prf",
    "LexiconEventDetector",
    "SupervisedEventDetector",
]

# Files a trained detector checkpoint carries next to the encoder/tokenizer.
HEAD_FILE = "head.pt"
LABELS_FILE = "labels.json"


@dataclass(frozen=True)
class TypedSpan:
    """A candidate the detector fired on, with its type and confidence."""

    candidate_id: str
    event_type: str
    confidence: float


class EventDetector(ABC):
    """Labels a document's trigger candidates with event types."""

    @abstractmethod
    def detect(self, doc: ArgumentDocument) -> dict[str, TypedSpan]:
        """Candidate id -> prediction, for the candidates predicted to be events.

        A candidate absent from the mapping is predicted NONE, so the return value
        is sparse over the (mostly negative) candidate universe.
        """


event_detectors: Registry[EventDetector] = Registry("event_detector")


def detection_prf(
    predicted: Mapping[str, TypedSpan], candidates: Iterable[TriggerCandidate]
) -> dict:
    """Typed and identification-only micro P/R/F1 over the candidate universe."""
    gold = {c.candidate_id: c.event_type for c in candidates}
    unknown = set(predicted) - set(gold)
    if unknown:
        raise ValueError(f"prediction on unknown candidate(s): {sorted(unknown)[:5]}")

    n_gold = sum(1 for t in gold.values() if t != NONE_TYPE)
    n_pred = sum(1 for span in predicted.values() if span.event_type != NONE_TYPE)
    typed_tp = ident_tp = 0
    for cid, span in predicted.items():
        if span.event_type == NONE_TYPE or gold[cid] == NONE_TYPE:
            continue
        ident_tp += 1
        typed_tp += int(span.event_type == gold[cid])
    return {
        "typed": PRF.from_counts(typed_tp, n_pred, n_gold),
        "identification": PRF.from_counts(ident_tp, n_pred, n_gold),
        "n_candidates": len(gold),
    }


@event_detectors.register("lexicon")
class LexiconEventDetector(EventDetector):
    """Most-frequent-type-per-trigger baseline (pure CPU, no torch).

    Takes the same ``checkpoint_path`` argument as the neural detector so both
    are created identically from a config; an unfitted detector predicts nothing
    rather than pretending to.
    """

    def __init__(self, checkpoint_path: str | Path | None = None) -> None:
        self.counts: dict[str, dict[str, int]] = (
            json.loads(Path(checkpoint_path).read_text()) if checkpoint_path else {}
        )

    def fit(self, docs: Iterable[ArgumentDocument]) -> LexiconEventDetector:
        counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        for doc in docs:
            for candidate in doc.candidates:
                counts[candidate.trigger.lower()][candidate.event_type] += 1
        self.counts = {trigger: dict(types) for trigger, types in counts.items()}
        return self

    def detect(self, doc: ArgumentDocument) -> dict[str, TypedSpan]:
        predictions: dict[str, TypedSpan] = {}
        for candidate in doc.candidates:
            types = self.counts.get(candidate.trigger.lower())
            if not types:
                continue
            total = sum(types.values())
            event_type, count = max(types.items(), key=lambda kv: (kv[1], kv[0]))
            if event_type == NONE_TYPE:
                continue
            predictions[candidate.candidate_id] = TypedSpan(
                candidate.candidate_id, event_type, count / total
            )
        return predictions

    def save(self, path: str | Path) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(json.dumps(self.counts, sort_keys=True))


@event_detectors.register("supervised")
class SupervisedEventDetector(EventDetector):
    """Encoder + linear head over the candidate universe (index 0 = NONE).

    The encoder and head load lazily on the first `detect`, so the class
    instantiates and registers on a CPU box; only running it needs the `llm`
    extra. The whole document is encoded once per call and every candidate is
    gathered out of it (see `encoding.encode_spans`), so a 136-candidate
    document costs one forward pass, not 136.
    """

    def __init__(
        self,
        checkpoint_path: str | None = None,
        max_length: int = 512,
        stride: int = 128,
    ) -> None:
        self.checkpoint_path = checkpoint_path
        self.max_length = max_length
        self.stride = stride
        self._encoder = None
        self._tokenizer = None
        self._head = None
        self._labels: list[str] = []
        self._device = "cpu"

    def _ensure_model(self) -> None:
        if self._head is not None:
            return
        if not TORCH_AVAILABLE:
            raise RuntimeError(
                "supervised detection needs torch + transformers: install the `llm` extra. "
                "This is a GPU-only path."
            )
        import torch
        from torch import nn
        from transformers import AutoModel, AutoTokenizer

        if not self.checkpoint_path:
            raise ValueError("supervised detector: checkpoint_path is required")
        ckpt = Path(self.checkpoint_path)
        head_file = ckpt / HEAD_FILE
        if not head_file.exists():
            raise FileNotFoundError(f"supervised detector: trained head not found at {head_file}")
        self._labels = json.loads((ckpt / LABELS_FILE).read_text())
        if self._labels[0] != NONE_TYPE:
            raise ValueError(f"{LABELS_FILE}: index 0 must be {NONE_TYPE!r}")
        self._tokenizer = AutoTokenizer.from_pretrained(str(ckpt))
        self._encoder = AutoModel.from_pretrained(str(ckpt))
        self._head = nn.Linear(self._encoder.config.hidden_size, len(self._labels))
        self._head.load_state_dict(torch.load(head_file, map_location="cpu"))
        self._device = "cuda" if torch.cuda.is_available() else "cpu"
        self._encoder.to(self._device).eval()
        self._head.to(self._device).eval()

    def detect(self, doc: ArgumentDocument) -> dict[str, TypedSpan]:
        if not doc.candidates:
            return {}
        self._ensure_model()
        import torch

        with torch.no_grad():
            embeddings = encode_spans(
                self._encoder,
                self._tokenizer,
                doc.doc_text,
                [c.span.char_start for c in doc.candidates],
                max_length=self.max_length,
                stride=self.stride,
                device=self._device,
            )
            probs = torch.softmax(self._head(embeddings), dim=-1)
        confidence, index = probs.max(dim=-1)

        predictions: dict[str, TypedSpan] = {}
        for candidate, i, p in zip(
            doc.candidates, index.tolist(), confidence.tolist(), strict=True
        ):
            if i == 0:  # NONE
                continue
            predictions[candidate.candidate_id] = TypedSpan(
                candidate.candidate_id, self._labels[i], float(p)
            )
        return predictions
