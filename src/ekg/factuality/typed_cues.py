"""Typed-cue factuality decisions with a factorized five-label interface.

The public MAVEN-FACT labels remain exactly ``CT+``, ``PS+``, ``CT-``,
``PS-`` and ``Uu``.  This module changes neither that label space nor its
evaluator.  Instead, it models three binary factors whose deterministic product
is the same five-label distribution:

``unknown``
    Whether the factuality state is unknown (``Uu``).
``modality``
    Conditional on being known, whether the event is possible (``PS``).
``polarity``
    Conditional on being known, whether the event is negative (``-``).

Typed modality/polarity cue spans condition the factor logits through an
explicit residual.  ``remove_core`` uses precisely the same encoder, cue
features and parameter shapes but emits a flat five-way head.  ``permutation``
keeps the full model and permutes cue representations only within a document.
Those are the three frozen D4 arms; no caller may change labels, candidates or
the scoring contract to make the factorization look better.
"""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from ekg.core.schema import EvidenceSpan, RelationEdge
from ekg.factuality.detection import (
    FactualityDetector,
    FactualityPrediction,
    factuality_detectors,
    split_candidate_features,
    structure_contexts,
)
from ekg.factuality.evidence import evidence_candidates
from ekg.nodes.encoding import TORCH_AVAILABLE, encode_spans
from ekg.relations.data.maven_fact import (
    FACTUALITY_LABELS,
    FactualityDocument,
    FactualityMention,
)

__all__ = [
    "CONFIG_FILE",
    "CUE_HEAD_FILE",
    "DECISION_HEAD_FILE",
    "CUE_TYPES",
    "FACTOR_NAMES",
    "TYPED_CUE_ARMS",
    "TypedCueRecord",
    "build_typed_cue_decision_head",
    "cue_sidecar",
    "cue_type_targets",
    "factor_targets",
    "permute_cue_features",
    "permutation_indices",
    "recompose_factor_probabilities",
    "structured_confusion_report",
    "typed_cue_features",
    "typed_cue_logits_per_mention",
    "validate_typed_cue_arm",
    "TypedCueFactualityDetector",
]

CONFIG_FILE = "typed_cue_config.json"
CUE_HEAD_FILE = "typed_cue_head.pt"
DECISION_HEAD_FILE = "typed_cue_decision_head.pt"

CUE_TYPES: tuple[str, ...] = ("modality", "polarity")
FACTOR_NAMES: tuple[str, ...] = ("unknown", "modality", "polarity")
FULL_ARM = "full"
REMOVE_CORE_ARM = "remove_core"
PERMUTATION_ARM = "permutation"
TYPED_CUE_ARMS: tuple[str, ...] = (FULL_ARM, REMOVE_CORE_ARM, PERMUTATION_ARM)

_FACTOR_TARGETS: dict[str, tuple[int, int, int]] = {
    "CT+": (0, 0, 0),
    "PS+": (0, 1, 0),
    "CT-": (0, 0, 1),
    "PS-": (0, 1, 1),
    "Uu": (1, 0, 0),
}
_MODALITY_LABELS = frozenset({"PS+", "PS-"})
_POLARITY_LABELS = frozenset({"CT-", "PS-"})


def validate_typed_cue_arm(arm: str) -> str:
    if arm not in TYPED_CUE_ARMS:
        raise ValueError(f"unknown typed-cue arm {arm!r}, expected one of {TYPED_CUE_ARMS}")
    return arm


def _require_label(label: str) -> None:
    if label not in FACTUALITY_LABELS:
        raise ValueError(f"unknown factuality label {label!r}")


def factor_targets(labels: Sequence[str]) -> list[tuple[int, int, int]]:
    """Map the unchanged five labels to unknown/modality/polarity targets."""
    result: list[tuple[int, int, int]] = []
    for label in labels:
        _require_label(label)
        result.append(_FACTOR_TARGETS[label])
    return result


def recompose_factor_probabilities(factor_logits):
    """Return normalized five-label probabilities in ``FACTUALITY_LABELS`` order.

    The factors are logits for ``unknown``, modality and polarity.  The latter
    two are conditional on known, so their four products together have mass
    ``1 - P(Uu)``; adding ``P(Uu)`` is exactly one.  A flat softmax is therefore
    neither needed nor permitted for the full/permutation arm.
    """
    import torch

    if factor_logits.shape[-1] != len(FACTOR_NAMES):
        raise ValueError(
            f"factor logits last dimension must be {len(FACTOR_NAMES)}, got {factor_logits.shape}"
        )
    unknown, modality, polarity = torch.sigmoid(factor_logits).unbind(dim=-1)
    known = 1.0 - unknown
    return torch.stack(
        (
            known * (1.0 - modality) * (1.0 - polarity),  # CT+
            known * modality * (1.0 - polarity),  # PS+
            known * (1.0 - modality) * polarity,  # CT-
            known * modality * polarity,  # PS-
            unknown,  # Uu
        ),
        dim=-1,
    )


def cue_type_targets(
    candidates: Sequence[EvidenceSpan], mention: FactualityMention
) -> list[tuple[int, int]]:
    """Typed supervision for annotated cue spans.

    MAVEN-FACT annotates supporting words only for non-factual/possible labels.
    Existing evidence training therefore skips mentions without annotations;
    this helper preserves that distinction rather than inventing negative spans
    for CT+ or Uu.  PS cues supervise modality, negative cues supervise
    polarity and PS- supervises both types.
    """
    _require_label(mention.factuality)
    gold = {(span.char_start, span.char_end) for span in mention.evidence}
    modality = int(mention.factuality in _MODALITY_LABELS)
    polarity = int(mention.factuality in _POLARITY_LABELS)
    return [
        (
            modality * int((cue.char_start, cue.char_end) in gold),
            polarity * int((cue.char_start, cue.char_end) in gold),
        )
        for cue in candidates
    ]


def typed_cue_logits_per_mention(triggers, candidate_features: Sequence, cue_head) -> list:
    """Two cue-type logits per candidate: modality then polarity."""
    from ekg.nodes.encoding import pair_features

    logits: list = []
    for index, features in enumerate(candidate_features):
        if not len(features):
            logits.append(features.new_zeros((0, len(CUE_TYPES))))
            continue
        trigger = triggers[index].expand(features.shape[0], -1)
        logits.append(cue_head(pair_features(features, trigger)))
    return logits


def _typed_cue_summary(span_features, cue_logits):
    """Pool typed cue representations and retain each type's cue mass."""
    import torch

    if cue_logits.ndim != 2 or cue_logits.shape[-1] != len(CUE_TYPES):
        raise ValueError(f"cue logits must be (n, {len(CUE_TYPES)}), got {cue_logits.shape}")
    if span_features.shape[0] != cue_logits.shape[0]:
        raise ValueError("cue feature/logit count mismatch")
    hidden = span_features.shape[-1]
    if not span_features.shape[0]:
        return span_features.new_zeros(len(CUE_TYPES) * hidden + len(CUE_TYPES))
    weights = torch.sigmoid(cue_logits)
    # Candidate-count normalization preserves absence/mass information instead
    # of making one weak cue look like one certain cue.
    pooled = weights.transpose(0, 1).matmul(span_features) / span_features.shape[0]
    masses = weights.mean(dim=0)
    return torch.cat((pooled.reshape(-1), masses), dim=-1)


def typed_cue_features(candidate_features: Sequence, cue_logits: Sequence):
    """One fixed-width cue vector per mention."""
    if len(candidate_features) != len(cue_logits):
        raise ValueError("candidate/cue-logit mention count mismatch")
    if not candidate_features:
        raise ValueError("cannot infer typed-cue width from zero mentions")
    import torch

    return torch.stack(
        [
            _typed_cue_summary(features, logits)
            for features, logits in zip(candidate_features, cue_logits, strict=True)
        ]
    )


def permutation_indices(doc_ids: Sequence[str], seed: int) -> list[int]:
    """A deterministic permutation that never moves a cue across documents."""
    grouped: dict[str, list[int]] = defaultdict(list)
    for index, doc_id in enumerate(doc_ids):
        if not doc_id:
            raise ValueError("typed-cue permutation needs non-empty document IDs")
        grouped[doc_id].append(index)
    source = list(range(len(doc_ids)))
    for doc_id, indices in grouped.items():
        # Do not use Python's randomized hash: this must replay byte-for-byte
        # across processes and machines from the registered seed.
        digest = hashlib.sha256(f"{seed}:{doc_id}".encode()).digest()
        state = int.from_bytes(digest[:8], "big")
        shuffled = list(indices)
        for offset in range(len(shuffled) - 1, 0, -1):
            state = (state * 6364136223846793005 + 1442695040888963407) & ((1 << 64) - 1)
            swap = state % (offset + 1)
            shuffled[offset], shuffled[swap] = shuffled[swap], shuffled[offset]
        for destination, origin in zip(indices, shuffled, strict=True):
            source[destination] = origin
    return source


def permute_cue_features(cue_features, doc_ids: Sequence[str], seed: int):
    """Apply the registered within-document cue representation control."""
    if cue_features.shape[0] != len(doc_ids):
        raise ValueError("cue feature/document count mismatch")
    return cue_features[permutation_indices(doc_ids, seed)]


@dataclass(frozen=True)
class TypedCueRecord:
    """One exported cue, including both type probabilities and exact offsets."""

    span: EvidenceSpan
    modality_probability: float
    polarity_probability: float

    def as_dict(self) -> dict[str, object]:
        return {
            "char_start": self.span.char_start,
            "char_end": self.span.char_end,
            "sent_id": self.span.sent_id,
            "text": self.span.text,
            "types": {
                "modality": self.modality_probability,
                "polarity": self.polarity_probability,
            },
        }


def cue_sidecar(
    mentions: Sequence[FactualityMention],
    candidates: Sequence[Sequence[EvidenceSpan]],
    cue_logits: Sequence,
    *,
    threshold: float = 0.5,
) -> dict[str, dict[str, object]]:
    """Export explicit ``ok``/``empty`` typed-cue state per mention."""
    if not 0.0 <= threshold <= 1.0:
        raise ValueError("cue threshold must be in [0, 1]")
    if len(mentions) != len(candidates) or len(mentions) != len(cue_logits):
        raise ValueError("typed-cue sidecar mention count mismatch")
    result: dict[str, dict[str, object]] = {}
    for mention, per_mention, logits in zip(mentions, candidates, cue_logits, strict=True):
        if len(per_mention) != logits.shape[0]:
            raise ValueError(f"{mention.mention_id}: cue candidate/logit count mismatch")
        probabilities = logits.sigmoid().detach().cpu().tolist()
        records = [
            TypedCueRecord(cue, float(values[0]), float(values[1]))
            for cue, values in zip(per_mention, probabilities, strict=True)
            if max(values) >= threshold
        ]
        result[mention.mention_id] = {
            "state": "ok" if records else "empty",
            "cues": [record.as_dict() for record in records],
        }
    return result


def structured_confusion_report(
    predicted: Mapping[str, str], gold: Mapping[str, str]
) -> dict[str, float | int]:
    """The three pre-registered D4 confusion counts on one identical population."""
    if predicted.keys() != gold.keys():
        missing = sorted(gold.keys() - predicted.keys())
        extra = sorted(predicted.keys() - gold.keys())
        raise ValueError(f"factuality coverage mismatch: missing={len(missing)} extra={len(extra)}")
    counts = {"unknown": 0, "modality_only": 0, "polarity_only": 0}
    modality_pairs = {frozenset(("CT+", "PS+")), frozenset(("CT-", "PS-"))}
    polarity_pairs = {frozenset(("CT+", "CT-")), frozenset(("PS+", "PS-"))}
    for mention_id, expected in gold.items():
        actual = predicted[mention_id]
        _require_label(expected)
        _require_label(actual)
        if (expected == "Uu") != (actual == "Uu"):
            counts["unknown"] += 1
        pair = frozenset((expected, actual))
        if pair in modality_pairs:
            counts["modality_only"] += 1
        if pair in polarity_pairs:
            counts["polarity_only"] += 1
    total = sum(counts.values())
    return {
        **counts,
        "total": total,
        "rate": total / len(gold) if gold else 0.0,
        "mentions": len(gold),
    }


def build_typed_cue_decision_head(
    hidden_size: int,
    structure_size: int,
    *,
    arm: str,
):
    """Build capacity-matched full and flat decision heads lazily.

    Both arms use the same ``base -> five latent units -> five output units``
    shapes plus the same cue-conditioned residual.  Full projects all five
    output units onto the three factors with a fixed full-row-rank matrix;
    remove-core reads the five outputs directly as flat label logits.  This
    keeps parameter count, cue input and encoder budget identical.
    """
    validate_typed_cue_arm(arm)
    if hidden_size <= 0 or structure_size < 0:
        raise ValueError("hidden_size must be positive and structure_size non-negative")
    import torch
    from torch import nn

    cue_size = len(CUE_TYPES) * hidden_size + len(CUE_TYPES)
    latent_size = len(FACTUALITY_LABELS)

    class TypedCueDecisionHead(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            # Kept for the pilot's per-instance dump: the factor stage is
            # recomputed nowhere else, so reading it back would mean a second
            # implementation of the same arithmetic.
            self.last_factor_logits = None
            self.base = nn.Linear(hidden_size + structure_size, latent_size)
            self.cue_residual = nn.Linear(cue_size, latent_size)
            self.output = nn.Linear(latent_size, latent_size)
            self.register_buffer(
                "factor_projection",
                torch.tensor(
                    (
                        (1.0, 0.0, 0.0),
                        (0.0, 1.0, 0.0),
                        (0.0, 0.0, 1.0),
                        (1.0, -1.0, 0.0),
                        (0.0, 1.0, -1.0),
                    )
                ),
            )

        def forward(self, triggers, structure, cues):
            if triggers.ndim != 2 or triggers.shape[-1] != hidden_size:
                raise ValueError(f"trigger features must be (n, {hidden_size})")
            if structure_size:
                if structure is None or structure.shape != (triggers.shape[0], structure_size):
                    raise ValueError(f"structure features must be (n, {structure_size})")
                base_input = torch.cat((triggers, structure), dim=-1)
            elif structure is not None:
                raise ValueError("structure was passed to a no-structure decision head")
            else:
                base_input = triggers
            if cues.shape != (triggers.shape[0], cue_size):
                raise ValueError(f"cue features must be (n, {cue_size})")
            logits = self.output(torch.tanh(self.base(base_input) + self.cue_residual(cues)))
            if arm == REMOVE_CORE_ARM:
                # The flat arm has no factor stage; that absence is the ablation,
                # so record it as absent rather than as zeros.
                self.last_factor_logits = None
                return torch.softmax(logits, dim=-1)
            factors = logits.matmul(self.factor_projection)
            self.last_factor_logits = factors
            return recompose_factor_probabilities(factors)

    return TypedCueDecisionHead()


@factuality_detectors.register("typed_cue")
class TypedCueFactualityDetector(FactualityDetector):
    """Lazy checkpoint loader for the D4 typed-cue model family."""

    def __init__(
        self,
        checkpoint_path: str | Path | None = None,
        *,
        arm: str = FULL_ARM,
        max_length: int = 512,
        stride: int = 128,
        use_structure: bool = True,
        permutation_seed: int = 13,
    ) -> None:
        self.checkpoint_path = Path(checkpoint_path) if checkpoint_path else None
        self.arm = validate_typed_cue_arm(arm)
        self.max_length = max_length
        self.stride = stride
        self.use_structure = use_structure
        self.permutation_seed = permutation_seed
        self._encoder = None
        self._tokenizer = None
        self._cue_head = None
        self._decision_head = None
        self._device = "cpu"
        self.last_sidecar: dict[str, dict[str, object]] = {}
        # Per-instance decision trace the seed-13 pilot has to persist: the five
        # class probabilities, and the three factor logits when the arm has them.
        self.last_probabilities: dict[str, list[float]] = {}
        self.last_factor_logits: dict[str, list[float]] = {}

    def _ensure_model(self) -> None:
        if self._decision_head is not None:
            return
        if not TORCH_AVAILABLE:
            raise RuntimeError("typed-cue factuality detection needs torch + transformers")
        if self.checkpoint_path is None:
            raise ValueError("typed-cue factuality detector: checkpoint_path is required")
        import torch
        from torch import nn
        from transformers import AutoModel, AutoTokenizer

        config_path = self.checkpoint_path / CONFIG_FILE
        config = json.loads(config_path.read_text(encoding="utf-8"))
        expected = {
            "schema_version": "ekg.typed_cue_factuality.v1",
            "labels": list(FACTUALITY_LABELS),
            "arm": self.arm,
            "use_structure": self.use_structure,
            "permutation_seed": self.permutation_seed,
        }
        for key, value in expected.items():
            if config.get(key) != value:
                raise ValueError(f"{config_path} has {key}={config.get(key)!r}, expected {value!r}")
        self._tokenizer = AutoTokenizer.from_pretrained(str(self.checkpoint_path))
        self._encoder = AutoModel.from_pretrained(str(self.checkpoint_path))
        hidden = self._encoder.config.hidden_size
        self._cue_head = nn.Linear(4 * hidden, len(CUE_TYPES))
        self._cue_head.load_state_dict(
            torch.load(self.checkpoint_path / CUE_HEAD_FILE, map_location="cpu")
        )
        self._decision_head = build_typed_cue_decision_head(
            hidden,
            8 if self.use_structure else 0,
            arm=self.arm,
        )
        self._decision_head.load_state_dict(
            torch.load(self.checkpoint_path / DECISION_HEAD_FILE, map_location="cpu")
        )
        self._device = "cuda" if torch.cuda.is_available() else "cpu"
        for module in (self._encoder, self._cue_head, self._decision_head):
            module.to(self._device).eval()

    def predict(
        self,
        doc: FactualityDocument,
        edges: Sequence[RelationEdge] | None = None,
    ) -> dict[str, FactualityPrediction]:
        if not doc.mentions:
            self.last_sidecar = {}
            self.last_probabilities = {}
            self.last_factor_logits = {}
            return {}
        self._ensure_model()
        import torch

        candidates = [evidence_candidates(doc, mention) for mention in doc.mentions]
        starts = [mention.span.char_start for mention in doc.mentions]
        starts += [cue.char_start for per_mention in candidates for cue in per_mention]
        with torch.no_grad():
            pooled = encode_spans(
                self._encoder,
                self._tokenizer,
                doc.doc_text,
                starts,
                max_length=self.max_length,
                stride=self.stride,
                device=self._device,
            )
            triggers = pooled[: len(doc.mentions)]
            candidate_features = split_candidate_features(
                pooled, len(doc.mentions), [len(items) for items in candidates]
            )
            cue_logits = typed_cue_logits_per_mention(
                triggers, candidate_features, self._cue_head
            )
            cues = typed_cue_features(candidate_features, cue_logits)
            if self.arm == PERMUTATION_ARM:
                cues = permute_cue_features(
                    cues, [doc.doc_id] * len(doc.mentions), self.permutation_seed
                )
            structure = None
            if self.use_structure:
                contexts = structure_contexts(
                    doc.mentions, doc.gold_edges if edges is None else edges, nodes=doc.nodes
                )
                structure = torch.tensor(
                    [contexts[mention.mention_id].as_vector() for mention in doc.mentions],
                    dtype=triggers.dtype,
                    device=self._device,
                )
            probabilities = self._decision_head(triggers, structure, cues)
            confidence, labels = probabilities.max(dim=-1)
            self.last_sidecar = cue_sidecar(doc.mentions, candidates, cue_logits)
            factor_logits = self._decision_head.last_factor_logits
            self.last_probabilities = {
                mention.mention_id: [float(value) for value in row]
                for mention, row in zip(doc.mentions, probabilities.tolist(), strict=True)
            }
            self.last_factor_logits = (
                {}
                if factor_logits is None
                else {
                    mention.mention_id: [float(value) for value in row]
                    for mention, row in zip(doc.mentions, factor_logits.tolist(), strict=True)
                }
            )
            evidence = [
                tuple(
                    EvidenceSpan(
                        doc_id=doc.doc_id,
                        char_start=int(record["char_start"]),
                        char_end=int(record["char_end"]),
                        sent_id=record["sent_id"],
                        text=str(record["text"]),
                    )
                    for record in self.last_sidecar[mention.mention_id]["cues"]
                )
                for mention in doc.mentions
            ]
        return {
            mention.mention_id: FactualityPrediction(
                mention.mention_id,
                FACTUALITY_LABELS[label],
                float(score),
                spans,
            )
            for mention, label, score, spans in zip(
                doc.mentions,
                labels.tolist(),
                confidence.tolist(),
                evidence,
                strict=True,
            )
        }
