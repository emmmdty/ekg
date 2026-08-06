"""Discriminative supervised relation extractor (RoBERTa pair-classification).

Reproduces the official MAVEN-ERE strong baseline: gold event mentions are
given and the model labels every candidate mention pair. A RoBERTa encoder pools
each trigger's representation `h_i` (mean over every token of the trigger span,
not just its first token -- multi-token triggers like "took place" need every
piece); the pair feature `[h_i; h_j; h_i⊙h_j; |h_i−h_j|]` feeds a small MLP
(2 hidden layers + dropout, matching the official baseline's classifier
capacity) per relation family (index 0 = NONE).

torch/transformers are imported behind an availability guard (as in
`succession/model.py`), so the module imports and the extractor **registers** on a
CPU box; only running `extract` (encoding + scoring) needs the `llm` extra + GPU.

`locate_trigger_span` (pure-Python, fail-fast) and `encode_trigger_reps` (the
shared encoder pooling) are reused by both inference and training so a mention is
pooled identically either way; an unlocatable trigger raises rather than reading a
wrong token (as in `succession/encode.py`).
"""

from __future__ import annotations

import re
from pathlib import Path

from ekg.core.schema import EventNode, RelationEdge, RelationType
from ekg.relations.data.maven_ere import RelationDocument
from ekg.relations.extractor.base import (
    ExtractionContext,
    RelationExtractor,
    relation_extractors,
)
from ekg.relations.pairs import candidate_pairs, mention_order

__all__ = [
    "TORCH_AVAILABLE",
    "FAMILY_SUBTYPES",
    "DISTANCE_BUCKETS",
    "SupervisedRelationExtractor",
    "distance_bucket",
    "encode_trigger_reps",
    "locate_trigger_span",
]

# family value (RelationType.value) -> contract RelationType
_FAMILY_TYPE = {
    "temporal": RelationType.TEMPORAL,
    "causal": RelationType.CAUSAL,
    "subevent": RelationType.SUBEVENT,
}

# Ordered labels per family; index 0 is the negative (NONE) class. Subtypes match
# what `data/maven_ere.py` emits (upper-cased temporal/causal keys; SUBEVENT_OF).
FAMILY_SUBTYPES: dict[str, tuple[str, ...]] = {
    "temporal": ("NONE", "BEFORE", "CONTAINS", "OVERLAP", "BEGINS-ON", "ENDS-ON", "SIMULTANEOUS"),
    "causal": ("NONE", "CAUSE", "PRECONDITION"),
    "subevent": ("NONE", "SUBEVENT_OF"),
}


def locate_trigger_span(
    sentence: str, trigger: str, offsets: list[tuple[int, int]]
) -> tuple[int, int]:
    """Token range `[start, end)` covering the trigger; fail-fast if unlocatable.

    `offsets` is a tokenizer's `offset_mapping` for `sentence`. Matching is
    **case-insensitive on a word boundary**: MAVEN-ERE's `trigger_word` is
    lower-cased while the sentence keeps its original casing, so a sentence-initial
    or proper-noun trigger ("armed" in "Armed police officers ...") only matches
    case-insensitively -- 0.65% of mentions, which an exact `find` loses. The
    boundary stops a substring ("arm" inside "armed") from pooling a wrong token.

    The boundary is a pair of lookarounds rather than `\b`, because `\b` is
    defined against *word* characters and so can never match a trigger that
    starts or ends with punctuation: `\b%\b` matches nothing at all. MAVEN-ERE's
    test split has 154 such triggers ("%", ".45", "a.m."), 0.37% of its mentions,
    which `\b` turned into hard failures; valid happens to have none, which is
    why this only surfaced on the submission run. For word-delimited triggers the
    two forms are equivalent, so no previously-located mention moves.

    Returns every token overlapping the trigger's full character range, not just
    the one covering its start: multi-token triggers ("took place", "came under
    fire") need every piece mean-pooled, matching the official baseline's span
    pooling rather than pooling a single token.

    Anything still unlocatable raises rather than silently reading position 0;
    shared by inference and training so both pool identically.
    """
    match = re.search(rf"(?<!\w){re.escape(trigger)}(?!\w)", sentence, re.IGNORECASE)
    if match is None:
        raise ValueError(f"trigger {trigger!r} not in sentence -- unlocatable mention")
    toks = [i for i, (s, e) in enumerate(offsets) if s < match.end() and e > match.start()]
    if not toks:
        raise ValueError(f"trigger {trigger!r} fell outside the tokenised span (truncated)")
    return toks[0], toks[-1] + 1


# Upper bounds of the mention-order distance buckets; index len(...) is the overflow
# bucket. Geometric-ish because the pair count decays that way (31% of causal pairs
# are same-sentence, then a long tail out past 10 sentences).
DISTANCE_BUCKETS = (0, 1, 2, 3, 4, 6, 9, 14, 22, 35)


def distance_bucket(distance: int) -> int:
    """Bucket a `mention_order` separation. Deterministic and vocabulary-free.

    Deliberately not a learned vocabulary: a bucket id computed the same way at
    train and inference time cannot drift out of alignment, which is the failure
    mode a learned event-type vocabulary would have introduced here.
    """
    for i, upper in enumerate(DISTANCE_BUCKETS):
        if distance <= upper:
            return i
    return len(DISTANCE_BUCKETS)


try:  # pragma: no cover - exercised on the GPU server
    import torch
    import torch.nn as nn
    from transformers import AutoModel, AutoTokenizer

    TORCH_AVAILABLE = True
except ImportError:  # pragma: no cover - the local CPU path
    TORCH_AVAILABLE = False


if TORCH_AVAILABLE:

    class PairClassifier(nn.Module):
        """Per-family MLP head over the 4-way pair feature plus a distance embedding.

        Two hidden layers + dropout (`Linear -> ReLU -> Dropout -> Linear -> ReLU
        -> Dropout -> Linear`), matching the official MAVEN-ERE baseline's scorer
        capacity (`utils/model.py::Score`).

        **The distance stream** carries `mention_order` separation, bucketed. The
        pair feature is permutation-symmetric in magnitude and says nothing about
        how far apart the two triggers are, yet 75% of gold causal pairs are
        cross-sentence and their F1 trails same-sentence pairs by ~11 points --
        "location information" is the standard remedy in the document-level RE
        literature. `PairExample.distance` was already computed and never used.

        The embedding is **zero-initialised so the stream starts as a no-op** and
        has to earn its weight: a default `N(0,1)` stream can swamp a tuned
        feature path before it learns anything (cost us an MRR halving once).
        """

        def __init__(
            self,
            hidden_size: int,
            subtype_counts: dict[str, int],
            mlp_hidden: int = 150,
            dist_dim: int = 32,
        ) -> None:
            super().__init__()
            self.distance = nn.Embedding(len(DISTANCE_BUCKETS) + 1, dist_dim)
            nn.init.zeros_(self.distance.weight)
            in_dim = hidden_size * 4 + dist_dim
            self.heads = nn.ModuleDict(
                {
                    fam: nn.Sequential(
                        nn.Linear(in_dim, mlp_hidden),
                        nn.ReLU(),
                        nn.Dropout(0.2),
                        nn.Linear(mlp_hidden, mlp_hidden),
                        nn.ReLU(),
                        nn.Dropout(0.2),
                        nn.Linear(mlp_hidden, n),
                    )
                    for fam, n in subtype_counts.items()
                }
            )

        def forward(
            self, pair_feats: torch.Tensor, dist_ids: torch.Tensor
        ) -> dict[str, torch.Tensor]:
            feats = torch.cat([pair_feats, self.distance(dist_ids)], dim=-1)
            return {fam: head(feats) for fam, head in self.heads.items()}

    def _pair_features(head_emb: torch.Tensor, tail_emb: torch.Tensor) -> torch.Tensor:
        """`[h_i; h_j; h_i⊙h_j; |h_i−h_j|]` — the standard pair-classification feature."""
        return torch.cat(
            [head_emb, tail_emb, head_emb * tail_emb, (head_emb - tail_emb).abs()], dim=-1
        )

    def encode_trigger_reps(encoder, tokenizer, nodes, doc_text, max_length, device="cpu"):
        """Per-node trigger representation, mean-pooled from **document windows**.

        Consecutive sentences are packed into one `<= max_length` window (CLS in
        front, SEP after each sentence) and encoded in a **single forward pass**,
        so triggers in different sentences attend to each other.

        **This is not a detail.** Measured on MAVEN-ERE valid, **68.8% of causal
        pairs and 85.8% of subevent pairs are cross-sentence**. Encoding one
        sentence at a time leaves every one of those pairs holding two
        representations that never met in an attention map, and no amount of
        pair-head capacity downstream recovers what the encoder never mixed --
        which is why enlarging the head and fixing span pooling both moved causal
        F1 by ~0 (see `docs/results/PHASE_A.md`). Mirrors the official baseline
        (`THU-KEG/MAVEN-ERE`, `causal/src/data.py`), which packs sentences up to
        its own `max_length` and records event spans in the packed sequence.

        `max_length` is therefore a **window** budget, not a per-sentence one --
        the same quantity the official baseline's 256 refers to.

        Gradient flows when the encoder is in train mode; callers wrap inference in
        `no_grad`. Fail-fast on unlocatable triggers and on any sentence too long
        to ever fit a window.
        """
        if not nodes:
            return {}
        lines = doc_text.split("\n")
        doc_id = nodes[0].doc_id
        by_sent: dict[int, list] = {}
        for node in nodes:
            span = node.trigger_evidence[0] if node.trigger_evidence else None
            if span is None or span.sent_id is None:
                raise ValueError(
                    f"supervised: node {node.event_id} lacks a sentence-anchored trigger"
                )
            if not 0 <= span.sent_id < len(lines):
                raise ValueError(f"supervised: sent_id {span.sent_id} out of range in {doc_id}")
            by_sent.setdefault(span.sent_id, []).append(node)

        embs: dict[str, torch.Tensor] = {}
        window: list[int] = [tokenizer.cls_token_id]
        pending: list[tuple] = []

        def flush() -> None:
            """Encode the packed window and pool every trigger recorded in it."""
            if not pending:
                return
            ids = torch.tensor([window], device=device)
            hidden = encoder(
                input_ids=ids, attention_mask=torch.ones_like(ids)
            ).last_hidden_state[0]
            for node, start, end in pending:
                embs[node.event_id] = hidden[start:end].mean(dim=0)

        for sent_id, sentence in enumerate(lines):
            enc = tokenizer(sentence, add_special_tokens=False, return_offsets_mapping=True)
            sent_ids, offsets = enc["input_ids"], enc["offset_mapping"]
            if len(sent_ids) + 2 > max_length:  # CLS + sentence + SEP
                raise ValueError(
                    f"supervised: sentence {sent_id} of {doc_id} needs {len(sent_ids) + 2} "
                    f"tokens, over the {max_length} window budget"
                )
            # Locate in the sentence's own token coords, then shift into the window.
            located = [
                (node, *locate_trigger_span(sentence, node.trigger, offsets))
                for node in by_sent.get(sent_id, [])
            ]
            if len(window) + len(sent_ids) + 1 > max_length:
                flush()
                window = [tokenizer.cls_token_id]
                pending = []
            base = len(window)
            window.extend(sent_ids)
            window.append(tokenizer.sep_token_id)
            pending.extend((node, base + s, base + e) for node, s, e in located)
        flush()
        return embs


@relation_extractors.register("supervised")
class SupervisedRelationExtractor(RelationExtractor):
    """Labels every document-level candidate mention pair via per-family heads.

    The encoder + heads are torch-backed and loaded lazily on the first `extract`;
    `__init__` stays torch-free so the pipeline instantiates on CPU.

    `max_length` is 512 because MAVEN-ERE's longest sentence is 1691 chars = 322 BPE
    tokens: at 256 such a sentence is truncated before its trigger, and
    `locate_trigger_span` (correctly) refuses to pool a wrong token instead.
    """

    def __init__(
        self,
        checkpoint_path: str | None = None,
        max_distance: int | None = None,
        max_length: int = 512,
    ) -> None:
        self.checkpoint_path = checkpoint_path
        self.max_distance = max_distance
        self.max_length = max_length
        self._model = None  # heads; lazy-loaded on first extract (needs torch)
        self._encoder = None
        self._tokenizer = None
        self._device = "cpu"

    def _candidate_pairs(self, nodes: list[EventNode]) -> list[tuple[str, str]]:
        if not nodes:
            return []
        doc = RelationDocument(doc_id=nodes[0].doc_id, nodes=nodes, gold_edges=[])
        return candidate_pairs(doc, self.max_distance)

    def extract(
        self, nodes: list[EventNode], context: ExtractionContext | None = None
    ) -> list[RelationEdge]:
        pairs = self._candidate_pairs(nodes)
        if not pairs:
            return []
        by_id = {n.event_id: n for n in nodes}
        scored = self._score_pairs(nodes, pairs, context)
        edges: list[RelationEdge] = []
        for (head, tail), families in scored.items():
            for family, (subtype, prob) in families.items():
                edges.append(
                    RelationEdge(
                        head_id=head,
                        tail_id=tail,
                        relation_type=_FAMILY_TYPE[family],
                        subtype=subtype,
                        directed=True,
                        confidence=prob,
                        evidence=list(by_id[head].trigger_evidence)
                        + list(by_id[tail].trigger_evidence),
                    )
                )
        return edges

    # ---- torch-backed scoring (lazy) ------------------------------------- #

    def _ensure_model(self) -> None:
        if self._model is not None:
            return
        if not TORCH_AVAILABLE:
            raise RuntimeError(
                "supervised extract needs torch + transformers: install the `llm` extra "
                "(uv sync --extra llm). This is a GPU-only path."
            )
        if not self.checkpoint_path:
            raise ValueError("supervised: checkpoint_path is required to run extract")
        ckpt = Path(self.checkpoint_path)
        heads_file = ckpt / "heads.pt"
        if not heads_file.exists():
            raise FileNotFoundError(f"supervised: trained heads not found at {heads_file}")
        self._tokenizer = AutoTokenizer.from_pretrained(str(ckpt))
        self._encoder = AutoModel.from_pretrained(str(ckpt))
        counts = {fam: len(subs) for fam, subs in FAMILY_SUBTYPES.items()}
        self._model = PairClassifier(self._encoder.config.hidden_size, counts)
        self._model.load_state_dict(torch.load(heads_file, map_location="cpu"))
        self._device = "cuda" if torch.cuda.is_available() else "cpu"
        self._encoder.to(self._device).eval()
        self._model.to(self._device).eval()

    def _encode_mentions(self, nodes: list[EventNode], doc_text: str) -> dict[str, torch.Tensor]:
        """Trigger reps for inference: the shared encoder pooling under `no_grad`."""
        with torch.no_grad():
            return encode_trigger_reps(
                self._encoder, self._tokenizer, nodes, doc_text, self.max_length, self._device
            )

    def _score_pairs(
        self,
        nodes: list[EventNode],
        pairs: list[tuple[str, str]],
        context: ExtractionContext | None,
    ) -> dict[tuple[str, str], dict[str, tuple[str, float]]]:
        """Per non-NONE family, the (subtype, prob) each candidate pair is assigned."""
        self._ensure_model()
        doc_text = context.doc_text.get(nodes[0].doc_id, "") if context and nodes else ""
        if not doc_text:
            raise ValueError("supervised: extract needs context.doc_text for the document")
        embs = self._encode_mentions(nodes, doc_text)
        # Build the pair feature for the whole candidate set at once: doing it per
        # pair launches a kernel per candidate (thousands in a single document).
        head_emb = torch.stack([embs[h] for h, _ in pairs])
        tail_emb = torch.stack([embs[t] for _, t in pairs])
        # Same mention_order the training rows were bucketed from, so a bucket id
        # means the same thing on both sides.
        order = mention_order(RelationDocument(doc_id=nodes[0].doc_id, nodes=nodes, gold_edges=[]))
        dist_ids = torch.tensor(
            [distance_bucket(abs(order[h] - order[t])) for h, t in pairs], device=self._device
        )
        with torch.no_grad():
            logits = self._model(_pair_features(head_emb, tail_emb), dist_ids)
        result: dict[tuple[str, str], dict[str, tuple[str, float]]] = {}
        for family, subtypes in FAMILY_SUBTYPES.items():
            probs = torch.softmax(logits[family], dim=-1)
            conf, idx = probs.max(dim=-1)
            for pair, i, c in zip(pairs, idx.tolist(), conf.tolist(), strict=True):
                if i == 0:  # NONE
                    continue
                result.setdefault(pair, {})[family] = (subtypes[i], float(c))
        return result
