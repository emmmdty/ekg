"""Same-protocol re-runs of the public MAVEN-FACT detectors.

The published numbers (RoBERTa+CLS 45.4, DMRoBERTa 47.1, DMBERT 47.6, Table 3 of
arXiv 2407.15352) are on the **hidden test split**, and this project has already
learned four times over what happens when a valid-split number is subtracted
from a test-split one. `docs/results/PHASE_D.md` puts the point sharply: the
paired MDE on this task is ~5 rare-class instances, while the gap between those
three published systems is 2.2 points -- so a cross-split comparison against
them is not merely imprecise, it is *undecidable*. The main table has to re-run
the opponents on our own split.

Two architectures, both from a different family than our span-pooling detector:

``cls``
    The trigger's sentence with the trigger marked, classified from ``[CLS]``.
    Marking is not optional: a sentence often carries several triggers, and an
    unmarked ``[CLS]`` would hand the same vector to all of them.

``dynamic_multi``
    Dynamic multi-pooling (DMCNN/DMBERT): max-pool the tokens left of the
    trigger, the trigger itself, and the tokens right of it, then concatenate.
    The split point is the event, so the two contexts stay separable instead of
    being averaged into one sentence vector.

Everything outside the architecture is shared with our own detector by
construction -- same manifests, same mention set, same five-class order, same
scorer -- because a baseline that differs in any of those is not a baseline.
Neither predicts supporting evidence: in the public setting that is a separate
task, and inventing an evidence head for the opponent would be scoring it on
something it was never proposed to do.
"""

from __future__ import annotations

import json
from pathlib import Path

from ekg.factuality.detection import (
    FactualityDetector,
    FactualityPrediction,
    factuality_detectors,
)
from ekg.nodes.encoding import TORCH_AVAILABLE
from ekg.relations.data.maven_fact import (
    FACTUALITY_LABELS,
    FactualityDocument,
    FactualityMention,
)

__all__ = [
    "BASELINE_POOLINGS",
    "CLS_POOLING",
    "DYNAMIC_MULTI_POOLING",
    "CONFIG_FILE",
    "HEAD_FILE",
    "TRIGGER_MARKER",
    "validate_pooling",
    "baseline_head_input_dim",
    "marked_sentence",
    "pool_mentions",
    "BaselineFactualityDetector",
]

CONFIG_FILE = "baseline_config.json"
HEAD_FILE = "baseline_head.pt"

CLS_POOLING = "cls"
DYNAMIC_MULTI_POOLING = "dynamic_multi"
BASELINE_POOLINGS = (CLS_POOLING, DYNAMIC_MULTI_POOLING)

# Plain-text trigger markers. RoBERTa has no spare unused-token ids, and the
# asterisk convention is what the relation-extraction literature marks spans
# with, so the encoder has seen the shape in pre-training.
TRIGGER_MARKER = "*"


def validate_pooling(pooling: str) -> str:
    if pooling not in BASELINE_POOLINGS:
        raise ValueError(f"unknown baseline pooling {pooling!r}, expected {BASELINE_POOLINGS}")
    return pooling


def baseline_head_input_dim(hidden_size: int, pooling: str) -> int:
    validate_pooling(pooling)
    return hidden_size if pooling == CLS_POOLING else 3 * hidden_size


def marked_sentence(doc: FactualityDocument, mention: FactualityMention) -> tuple[str, int, int]:
    """The mention's sentence with its trigger marked, plus the trigger's span in it.

    Returns `(text, trigger_start, trigger_end)` with offsets into `text`, so the
    caller can locate the trigger's tokens without re-deriving the tokenisation.
    """
    sent_id = mention.span.sent_id
    if sent_id is None:
        raise ValueError(f"{mention.mention_id}: mention span carries no sent_id")
    tokens = doc.sentence_tokens[sent_id]
    starts = doc.token_starts[sent_id]
    # Token indices the trigger's character span touches. The dataset's own
    # offsets are token-aligned, so an empty result means the record is broken
    # rather than merely awkward, and must not be papered over.
    covered = [
        i
        for i, (token, start) in enumerate(zip(tokens, starts, strict=True))
        if start < mention.span.char_end and start + len(token) > mention.span.char_start
    ]
    if not covered:
        raise ValueError(
            f"{mention.mention_id}: trigger span {mention.span.char_start}-"
            f"{mention.span.char_end} covers no token of sentence {sent_id}"
        )
    first, last = covered[0], covered[-1]
    left = " ".join(tokens[:first])
    trigger = " ".join(tokens[first : last + 1])
    right = " ".join(tokens[last + 1 :])
    prefix = f"{left} {TRIGGER_MARKER} " if left else f"{TRIGGER_MARKER} "
    text = f"{prefix}{trigger} {TRIGGER_MARKER}" + (f" {right}" if right else "")
    return text, len(prefix), len(prefix) + len(trigger)


def pool_mentions(
    encoder,
    tokenizer,
    texts: list[str],
    trigger_spans: list[tuple[int, int]],
    *,
    pooling: str,
    max_length: int = 128,
    device: str = "cpu",
):
    """`(len(texts), baseline_head_input_dim(hidden, pooling))`.

    One batched forward over the marked sentences. Gradient flows when the
    encoder is in train mode; callers wrap inference in `no_grad`.
    """
    import torch

    validate_pooling(pooling)
    encoded = tokenizer(
        texts,
        return_offsets_mapping=True,
        return_tensors="pt",
        padding=True,
        truncation=True,
        max_length=max_length,
    )
    offsets = encoded.pop("offset_mapping")
    encoded = {k: v.to(device) for k, v in encoded.items()}
    hidden = encoder(**encoded).last_hidden_state
    if pooling == CLS_POOLING:
        return hidden[:, 0]

    attention = encoded["attention_mask"].bool()
    starts, ends = offsets[..., 0].to(device), offsets[..., 1].to(device)
    # Special tokens carry an empty (0, 0) offset and must not join any segment.
    real = attention & (ends > starts)
    span_start = torch.tensor([s for s, _ in trigger_spans], device=device).unsqueeze(1)
    span_end = torch.tensor([e for _, e in trigger_spans], device=device).unsqueeze(1)
    at = real & (starts < span_end) & (ends > span_start)
    before = real & (ends <= span_start)
    after = real & (starts >= span_end)

    def segment_max(mask):
        # A segment can legitimately be empty -- a trigger at the start of a
        # sentence has no left context -- so masked positions go to -inf for the
        # max and the all-empty rows are then zeroed, rather than letting -inf
        # reach the head.
        filled = hidden.masked_fill(~mask.unsqueeze(-1), float("-inf")).max(dim=1).values
        return torch.where(mask.any(dim=1).unsqueeze(-1), filled, torch.zeros_like(filled))

    return torch.cat([segment_max(before), segment_max(at), segment_max(after)], dim=-1)


@factuality_detectors.register("baseline")
class BaselineFactualityDetector(FactualityDetector):
    """A trained public-architecture baseline, loaded from its own checkpoint.

    Labels only: `evidence` is always empty, matching what these architectures
    were proposed to do.
    """

    def __init__(
        self,
        checkpoint_path: str | None = None,
        pooling: str = CLS_POOLING,
        max_length: int = 128,
        batch_size: int = 64,
    ) -> None:
        self.checkpoint_path = checkpoint_path
        self.pooling = validate_pooling(pooling)
        self.max_length = max_length
        self.batch_size = batch_size
        self._encoder = None
        self._tokenizer = None
        self._head = None
        self._labels: list[str] = []
        self._device = "cpu"

    def _ensure_model(self) -> None:
        if self._head is not None:
            return
        if not TORCH_AVAILABLE:
            raise RuntimeError("baseline factuality detection needs torch + transformers")
        import torch
        from torch import nn
        from transformers import AutoModel, AutoTokenizer

        if not self.checkpoint_path:
            raise ValueError("baseline factuality detector: checkpoint_path is required")
        ckpt = Path(self.checkpoint_path)
        config = json.loads((ckpt / CONFIG_FILE).read_text(encoding="utf-8"))
        if config["pooling"] != self.pooling:
            raise ValueError(
                f"{ckpt / CONFIG_FILE} was trained with pooling={config['pooling']!r}, "
                f"but this detector asks for {self.pooling!r}"
            )
        self._labels = list(config["labels"])
        if tuple(self._labels) != FACTUALITY_LABELS:
            raise ValueError(f"{ckpt / CONFIG_FILE} holds labels {self._labels}")
        self._tokenizer = AutoTokenizer.from_pretrained(str(ckpt))
        self._encoder = AutoModel.from_pretrained(str(ckpt))
        width = baseline_head_input_dim(self._encoder.config.hidden_size, self.pooling)
        self._head = nn.Linear(width, len(self._labels))
        self._head.load_state_dict(torch.load(ckpt / HEAD_FILE, map_location="cpu"))
        self._device = "cuda" if torch.cuda.is_available() else "cpu"
        self._encoder.to(self._device).eval()
        self._head.to(self._device).eval()

    def predict(self, doc: FactualityDocument) -> dict[str, FactualityPrediction]:
        if not doc.mentions:
            return {}
        self._ensure_model()
        import torch

        predictions: dict[str, FactualityPrediction] = {}
        with torch.no_grad():
            for start in range(0, len(doc.mentions), self.batch_size):
                batch = doc.mentions[start : start + self.batch_size]
                marked = [marked_sentence(doc, m) for m in batch]
                features = pool_mentions(
                    self._encoder,
                    self._tokenizer,
                    [t for t, _, _ in marked],
                    [(s, e) for _, s, e in marked],
                    pooling=self.pooling,
                    max_length=self.max_length,
                    device=self._device,
                )
                probs = torch.softmax(self._head(features), dim=-1)
                confidence, index = probs.max(dim=-1)
                for mention, i, p in zip(
                    batch, index.tolist(), confidence.tolist(), strict=True
                ):
                    predictions[mention.mention_id] = FactualityPrediction(
                        mention.mention_id, self._labels[i], float(p)
                    )
        return predictions
