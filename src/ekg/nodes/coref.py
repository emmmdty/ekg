"""Similar-event discrimination: the coreference decision and its hard cases.

Coreference here is a *pair* decision over event mentions in one document, and
the decision that matters is the hard one. A MAVEN event carries a single type,
so every gold coreferent pair shares its type and cross-type pairs are trivially
negative — which means the informative negatives are exactly the same-type pairs
with near-identical triggers ("attacked" vs "attack" of two *different*
attacks). Those are what a trigger-matching baseline merges wrongly, and the
`hard` flag marks them so the mis-merge rate can be reported on that subset
instead of being diluted by the easy majority.

`LexicalCoreferenceScorer` is that trigger-matching baseline (pure CPU) and the
number the neural scorer has to beat; `SupervisedCoreferenceScorer` is the
encoder pair classifier, torch-lazy like the rest of the node stage.
"""

from __future__ import annotations

import json
import random
from abc import ABC, abstractmethod
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from difflib import SequenceMatcher
from itertools import combinations
from pathlib import Path

from ekg.core.registry import Registry
from ekg.core.schema import EventNode
from ekg.nodes.encoding import TORCH_AVAILABLE, encode_spans

__all__ = [
    "HARD_SIMILARITY",
    "CorefPair",
    "PairKey",
    "trigger_similarity",
    "candidate_coref_pairs",
    "labelled_coref_pairs",
    "sample_training_pairs",
    "cluster_of_nodes",
    "CoreferenceScorer",
    "coreference_scorers",
    "LexicalCoreferenceScorer",
    "SupervisedCoreferenceScorer",
]

PairKey = tuple[str, str]

# A negative pair at or above this trigger similarity is a *hard* negative: the
# lexical cue points at a merge and only context can refuse it.
HARD_SIMILARITY = 0.8

HEAD_FILE = "coref_head.pt"


@dataclass(frozen=True)
class CorefPair:
    """One candidate mention pair with its gold label and hardness."""

    doc_id: str
    head_id: str
    tail_id: str
    label: bool
    similarity: float

    @property
    def hard(self) -> bool:
        """A negative whose triggers all but say 'merge us'."""
        return not self.label and self.similarity >= HARD_SIMILARITY

    def key(self) -> PairKey:
        return (self.head_id, self.tail_id)


def trigger_similarity(left: str, right: str) -> float:
    """Case-insensitive surface similarity of two triggers, in [0, 1]."""
    return SequenceMatcher(None, left.lower(), right.lower()).ratio()


def _ordered(nodes: Sequence[EventNode]) -> list[EventNode]:
    """Mentions in textual order — pairs are emitted (earlier, later)."""

    def key(node: EventNode) -> tuple[int, str]:
        span = node.trigger_evidence[0] if node.trigger_evidence else None
        return (span.char_start if span else 10**9, node.event_id)

    return sorted(nodes, key=key)


def candidate_coref_pairs(
    nodes: Sequence[EventNode], *, same_type_only: bool = True
) -> list[PairKey]:
    """Unordered mention pairs the scorer has to decide on.

    ``same_type_only`` exploits the fact that a MAVEN event has one type, so it
    never drops a gold pair when types are gold. Under *predicted* types it can:
    two mentions of one event typed differently become unpairable, which is a
    real recall cost of the pipeline and is reported rather than hidden.
    """
    ordered = _ordered(nodes)
    return [
        (a.event_id, b.event_id)
        for a, b in combinations(ordered, 2)
        if not same_type_only or a.event_type == b.event_type
    ]


def labelled_coref_pairs(
    nodes: Sequence[EventNode],
    cluster_of: Mapping[str, str],
    *,
    same_type_only: bool = True,
) -> list[CorefPair]:
    """Candidate pairs plus gold labels; `cluster_of` maps node id -> gold event."""
    by_id = {node.event_id: node for node in nodes}
    doc_id = nodes[0].doc_id if nodes else ""
    pairs: list[CorefPair] = []
    for head, tail in candidate_coref_pairs(nodes, same_type_only=same_type_only):
        gold_head, gold_tail = cluster_of.get(head), cluster_of.get(tail)
        pairs.append(
            CorefPair(
                doc_id=doc_id,
                head_id=head,
                tail_id=tail,
                label=gold_head is not None and gold_head == gold_tail,
                similarity=trigger_similarity(by_id[head].trigger, by_id[tail].trigger),
            )
        )
    return pairs


def sample_training_pairs(
    pairs: Sequence[CorefPair],
    *,
    neg_ratio: float = 10.0,
    hard_fraction: float = 0.5,
    seed: int = 0,
) -> list[CorefPair]:
    """Keep every positive, plus a negative sample enriched with hard cases.

    Same-type coreference candidates are already overwhelmingly negative, so
    training on all of them teaches "never merge". ``hard_fraction`` is the share
    of the sampled negatives drawn from the hard subset — the knob that trades
    merge recall for a lower mis-merge rate at training time rather than by
    moving a threshold afterwards.
    """
    if not 0.0 <= hard_fraction <= 1.0:
        raise ValueError("hard_fraction must be in [0, 1]")
    rng = random.Random(seed)
    positives = [p for p in pairs if p.label]
    hard = [p for p in pairs if p.hard]
    easy = [p for p in pairs if not p.label and not p.hard]

    budget = int(round(len(positives) * neg_ratio))
    # Capping hard first means an exhausted hard pool spends its remainder on
    # easy negatives instead of shrinking the negative budget.
    n_hard = min(len(hard), int(round(budget * hard_fraction)))
    n_easy = min(len(easy), budget - n_hard)
    sampled = positives + rng.sample(hard, n_hard) + rng.sample(easy, n_easy)
    rng.shuffle(sampled)
    return sampled


class CoreferenceScorer(ABC):
    """Assigns each candidate pair the probability that it is coreferent."""

    @abstractmethod
    def score(
        self, nodes: Sequence[EventNode], pairs: Sequence[PairKey], doc_text: str = ""
    ) -> dict[PairKey, float]:
        """Pair -> P(coreferent)."""


coreference_scorers: Registry[CoreferenceScorer] = Registry("coreference_scorer")


@coreference_scorers.register("lexical")
class LexicalCoreferenceScorer(CoreferenceScorer):
    """Trigger-similarity baseline: the merge rule hard negatives are built to fool."""

    def score(
        self, nodes: Sequence[EventNode], pairs: Sequence[PairKey], doc_text: str = ""
    ) -> dict[PairKey, float]:
        by_id = {node.event_id: node for node in nodes}
        return {
            (head, tail): trigger_similarity(by_id[head].trigger, by_id[tail].trigger)
            for head, tail in pairs
        }


@coreference_scorers.register("supervised")
class SupervisedCoreferenceScorer(CoreferenceScorer):
    """Encoder + pair head over `[h_i; h_j; h_i⊙h_j; |h_i−h_j|]` (torch-lazy)."""

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
        self._device = "cpu"

    def _ensure_model(self) -> None:
        if self._head is not None:
            return
        if not TORCH_AVAILABLE:
            raise RuntimeError(
                "supervised coreference needs torch + transformers: install the `llm` extra. "
                "This is a GPU-only path."
            )
        import torch
        from torch import nn
        from transformers import AutoModel, AutoTokenizer

        if not self.checkpoint_path:
            raise ValueError("supervised coreference: checkpoint_path is required")
        ckpt = Path(self.checkpoint_path)
        head_file = ckpt / HEAD_FILE
        if not head_file.exists():
            raise FileNotFoundError(f"supervised coreference: head not found at {head_file}")
        from ekg.nodes.discriminative import (
            ARGUMENT_POOLING_ORACLE,
            CONFIG_FILE,
            CONFUSABILITY,
            CONTEXT_POOLING,
            FEATURE_NAMES,
            head_input_dim,
        )

        self._tokenizer = AutoTokenizer.from_pretrained(str(ckpt))
        self._encoder = AutoModel.from_pretrained(str(ckpt))
        # The checkpoint declares its own feature layout: a head trained with the
        # context-discriminative inputs and scored without them would still run and
        # silently read different numbers than it was trained on.
        config_file = ckpt / CONFIG_FILE
        config = (
            json.loads(config_file.read_text(encoding="utf-8")) if config_file.exists() else {}
        )
        # Older checkpoints carry only the boolean; map it onto the component list
        # so a checkpoint written before the ablation split still loads correctly.
        if "components" in config:
            self._components = tuple(config["components"])
        else:
            self._components = (
                (CONTEXT_POOLING, CONFUSABILITY)
                if config.get("context_discriminative")
                else ()
            )
        self._context_discriminative = CONTEXT_POOLING in self._components
        self._argument_oracle = ARGUMENT_POOLING_ORACLE in self._components
        declared_argument_source = config.get("argument_source", "none")
        expected_argument_source = (
            "gold_event_level_oracle" if self._argument_oracle else "none"
        )
        if declared_argument_source != expected_argument_source:
            raise ValueError(
                "coreference checkpoint argument source mismatch: "
                f"checkpoint={declared_argument_source!r} expected={expected_argument_source!r}"
            )
        # Feature layouts evolve. A checkpoint trained on a different feature list
        # must fail loudly here rather than let the head read numbers it never saw.
        recorded = config.get("feature_names")
        if recorded is not None and list(recorded) != list(FEATURE_NAMES):
            raise ValueError(
                "coreference checkpoint was trained on a different feature layout: "
                f"checkpoint={list(recorded)} current={list(FEATURE_NAMES)}"
            )
        self._head = nn.Linear(
            head_input_dim(self._encoder.config.hidden_size, self._components), 2
        )
        self._head.load_state_dict(torch.load(head_file, map_location="cpu"))
        self._device = "cuda" if torch.cuda.is_available() else "cpu"
        self._encoder.to(self._device).eval()
        self._head.to(self._device).eval()

    def score(
        self, nodes: Sequence[EventNode], pairs: Sequence[PairKey], doc_text: str = ""
    ) -> dict[PairKey, float]:
        if not pairs:
            return {}
        if not doc_text:
            raise ValueError("supervised coreference: scoring needs the document text")
        self._ensure_model()
        import torch

        from ekg.nodes.discriminative import (
            argument_spans_and_counts,
            context_ranges_for,
            pair_head_inputs,
            pool_argument_features,
        )
        from ekg.nodes.encoding import encode_spans_with_context

        order = {node.event_id: i for i, node in enumerate(nodes)}
        nodes_by_id = {node.event_id: node for node in nodes}
        starts = [n.trigger_evidence[0].char_start for n in nodes]
        argument_spans, argument_counts = argument_spans_and_counts(nodes)
        arguments = None
        with torch.no_grad():
            if self._context_discriminative:
                oracle_starts = (
                    [start for start, _ in argument_spans] if self._argument_oracle else []
                )
                combined_starts = starts + oracle_starts
                combined_ranges = context_ranges_for(nodes, doc_text)
                if self._argument_oracle:
                    combined_ranges += argument_spans
                encoded_spans, encoded_contexts = encode_spans_with_context(
                    self._encoder,
                    self._tokenizer,
                    doc_text,
                    combined_starts,
                    combined_ranges,
                    max_length=self.max_length,
                    stride=self.stride,
                    device=self._device,
                )
                triggers = encoded_spans[: len(starts)]
                contexts = encoded_contexts[: len(starts)]
                if self._argument_oracle:
                    arguments = pool_argument_features(
                        encoded_spans[len(starts) :], argument_counts
                    )
            elif self._argument_oracle:
                combined = encode_spans(
                    self._encoder,
                    self._tokenizer,
                    doc_text,
                    starts + [start for start, _ in argument_spans],
                    max_length=self.max_length,
                    stride=self.stride,
                    device=self._device,
                )
                triggers = combined[: len(starts)]
                contexts = triggers
                arguments = pool_argument_features(
                    combined[len(starts) :], argument_counts
                )
            else:
                triggers = encode_spans(
                    self._encoder,
                    self._tokenizer,
                    doc_text,
                    starts,
                    max_length=self.max_length,
                    stride=self.stride,
                    device=self._device,
                )
                contexts = triggers
            logits = self._head(
                pair_head_inputs(
                    triggers,
                    contexts,
                    list(pairs),
                    nodes_by_id,
                    order,
                    components=self._components,
                    arguments=arguments,
                )
            )
            probs = torch.softmax(logits, dim=-1)[:, 1]
        return dict(zip(pairs, (float(p) for p in probs.tolist()), strict=True))


def cluster_of_nodes(nodes: Iterable[EventNode]) -> dict[str, str]:
    """Gold node id -> event id, read off the loader's `metadata["event"]`."""
    mapping: dict[str, str] = {}
    for node in nodes:
        event = node.metadata.get("event")
        if event is None:
            raise ValueError(f"node {node.event_id} carries no gold event in metadata")
        mapping[node.event_id] = event
    return mapping
