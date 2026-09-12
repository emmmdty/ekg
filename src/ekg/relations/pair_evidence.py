"""Pair-specific evidence: what licenses a relation, and what removing it costs.

`docs/results/PHASE_A.md` records where Ch2 actually stands: window encoding
lifted cross-sentence causal F1 from 19.99 to 24.11, and **three further rounds
of optimisation moved it by less than a point** while same-sentence pairs sit at
38.07 and cross-sentence pairs carry 75% of the positives.  `crosssentence.py`
measured the next hypothesis: for a cross-sentence pair the discourse cue lies
*between* the two triggers, and nothing in the pair feature `[h; t; h*t; |h-t|]`
points at it.

So a pair here gets an explicit evidence set — sentences it may cite — and two
counterfactual forwards over that set:

``necessity``
    Encode the document with the cited sentences removed.  A supported positive
    must lose logit when its evidence is gone.
``sufficiency``
    Encode only the trigger sentences plus the cited ones.  A supported positive
    must survive on its evidence alone.

The four frozen A4 arms differ **only** in the objective and in which sentences
are cited: ``full`` cites its own evidence and trains both consistency terms;
``remove_core`` passes no evidence stream at all; ``length_matched`` cites
non-evidence sentences of matched token length (the registered negative
control); ``no_constraint`` keeps the evidence representation and drops the
consistency terms.  Every arm shares one head class, whose evidence residual is
zero-initialised, so the base pair logits of all four coincide at init — the
assertion `PHASE_A4` smoke makes — and a gain cannot come from capacity.

The selector is deterministic and torch-free: candidate sentences are ranked by
pair-conditioned lexical evidence (the frozen causal/ordering lexicons of
`crosssentence.py`, plus whether a trigger is named again) and the top
`EVIDENCE_BUDGET` are cited.  Nothing here has a threshold to sweep, and the
whole selection path is checkable on CPU — which is where D4's cycle was lost.
The learned part is the encoder and the residual, shaped by the consistency
terms; the registered causal chain in `design_briefs.json` is that supervision,
not the selector's parameterisation.

Sentences hosting the two triggers are *protected*: they anchor the pooling and
are never masked.  A same-sentence pair therefore has nothing maskable and no
necessity term, which is honest — its 38.07 is not the gap this addresses.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from pathlib import Path

from ekg.core.schema import EventNode
from ekg.relations.crosssentence import CAUSAL_CUES, ORDERING_CUES, find_cues
from ekg.relations.pair_heads import LINEAR_HEAD, PAIR_EVIDENCE_HEAD, pair_head_factories

__all__ = [
    "A4_ARMS",
    "CONFIG_FILE",
    "EVIDENCE_BUDGET",
    "FULL_ARM",
    "LENGTH_MATCHED_ARM",
    "NO_CONSTRAINT_ARM",
    "REMOVE_CORE_ARM",
    "ArmFlags",
    "PairEvidence",
    "arm_flags",
    "build_pair_evidence",
    "counterfactual_sentence_ids",
    "document_pair_evidence",
    "lexicon_digest",
    "load_pair_evidence_config",
    "necessity_scoreable",
    "pair_evidence_config",
    "pair_evidence_sidecar",
    "sentence_tokens",
    "unsupported_cross_sentence_causal",
    "validate_a4_arm",
    "with_length_matched_substitutes",
]

CONFIG_FILE = "pair_evidence_config.json"
CONFIG_SCHEMA_VERSION = "ekg.relation_pair_evidence.v1"

# How many sentences a pair may cite.  Frozen rather than tuned: A4's stop
# conditions forbid a threshold sweep, and a fixed budget has nothing to sweep.
EVIDENCE_BUDGET = 2

FULL_ARM = "full"
REMOVE_CORE_ARM = "remove_core"
LENGTH_MATCHED_ARM = "length_matched"
NO_CONSTRAINT_ARM = "no_constraint"
A4_ARMS: tuple[str, ...] = (FULL_ARM, REMOVE_CORE_ARM, LENGTH_MATCHED_ARM, NO_CONSTRAINT_ARM)


@dataclass(frozen=True)
class ArmFlags:
    """What one arm switches on.  Exactly one axis moves between neighbours."""

    evidence_stream: bool
    consistency_loss: bool
    substitute_control: bool


_ARM_FLAGS: dict[str, ArmFlags] = {
    FULL_ARM: ArmFlags(True, True, False),
    REMOVE_CORE_ARM: ArmFlags(False, False, False),
    LENGTH_MATCHED_ARM: ArmFlags(True, True, True),
    NO_CONSTRAINT_ARM: ArmFlags(True, False, False),
}


def validate_a4_arm(arm: str) -> str:
    if arm not in _ARM_FLAGS:
        raise ValueError(f"unknown A4 arm {arm!r}, expected one of {A4_ARMS}")
    return arm


def arm_flags(arm: str) -> ArmFlags:
    return _ARM_FLAGS[validate_a4_arm(arm)]


# Tokens are compared against the frozen lexicons, so trailing punctuation must
# not hide a cue: "because," never equals "because".
_EDGE_PUNCTUATION = ".,;:!?\"'`()[]{}"


def sentence_tokens(doc_text: str) -> list[list[str]]:
    """One token list per sentence of the canonical doc text (one line each)."""
    return [
        [token for token in (raw.strip(_EDGE_PUNCTUATION) for raw in line.split()) if token]
        for line in doc_text.split("\n")
    ]


def lexicon_digest() -> str:
    """Identity of the frozen selector inputs, for train/inference drift."""
    payload = json.dumps(
        {
            "causal": [list(entry) for entry in CAUSAL_CUES],
            "ordering": [list(entry) for entry in ORDERING_CUES],
            "budget": EVIDENCE_BUDGET,
        },
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class PairEvidence:
    """One candidate pair's evidence set and the counterfactuals it licenses."""

    doc_id: str
    head_id: str
    tail_id: str
    head_sent: int
    tail_sent: int
    candidates: tuple[int, ...]
    selected: tuple[int, ...]
    selected_cues: tuple[str, ...]
    protected_cues: tuple[str, ...]
    substitutes: tuple[int, ...] = ()
    substitutes_requested: int = 0

    @property
    def protected(self) -> tuple[int, ...]:
        """The trigger sentences; present in every forward, never masked."""
        return tuple(sorted({self.head_sent, self.tail_sent}))

    @property
    def cross_sentence(self) -> bool:
        return self.head_sent != self.tail_sent

    @property
    def supported(self) -> bool:
        """Whether any cue licensed this pair, cited or inside a trigger sentence."""
        return bool(self.selected_cues or self.protected_cues)

    def cited(self, arm: str) -> tuple[int, ...]:
        """The sentences this arm actually intervenes on."""
        return self.substitutes if arm_flags(arm).substitute_control else self.selected


def _rank_key(
    sent_id: int, tokens: Sequence[str], triggers: Sequence[str], protected: Sequence[int]
) -> tuple[int, int, int, int, int]:
    """Ranking is lexicographic on counts, so there is no weight to tune."""
    lowered = [token.lower() for token in tokens]
    named = sum(1 for trigger in triggers if trigger.lower() in lowered)
    nearest = min(abs(sent_id - anchor) for anchor in protected)
    return (
        len(find_cues(tokens, CAUSAL_CUES)),
        len(find_cues(tokens, ORDERING_CUES)),
        named,
        -nearest,
        -sent_id,
    )


def build_pair_evidence(
    doc_id: str,
    head_id: str,
    tail_id: str,
    *,
    head_sent: int,
    tail_sent: int,
    head_trigger: str,
    tail_trigger: str,
    sentences: Sequence[Sequence[str]],
    budget: int = EVIDENCE_BUDGET,
) -> PairEvidence:
    """Rank the sentences between the two triggers and cite the top `budget`.

    Candidates are the closed sentence span the pair spans; the two trigger
    sentences are protected and so are not citable — citing them would change
    neither counterfactual.  Their cues are reported separately instead, so a
    pair whose only cue is unmaskable is not counted as unsupported.
    """
    if budget < 0:
        raise ValueError("evidence budget must not be negative")
    for sent_id in (head_sent, tail_sent):
        if not 0 <= sent_id < len(sentences):
            raise ValueError(f"{doc_id}: sent_id {sent_id} outside {len(sentences)} sentences")
    first, last = sorted((head_sent, tail_sent))
    candidates = tuple(range(first, last + 1))
    protected = tuple(sorted({head_sent, tail_sent}))
    triggers = (head_trigger, tail_trigger)

    selectable = [sent_id for sent_id in candidates if sent_id not in protected]
    ranked = sorted(
        selectable,
        key=lambda sent_id: _rank_key(sent_id, sentences[sent_id], triggers, protected),
        reverse=True,
    )
    selected = tuple(sorted(ranked[:budget]))
    selected_cues = tuple(
        sorted(
            {
                cue
                for sent_id in selected
                for lexicon in (CAUSAL_CUES, ORDERING_CUES)
                for cue in find_cues(sentences[sent_id], lexicon)
            }
        )
    )
    protected_cues = tuple(
        sorted(
            {
                cue
                for sent_id in protected
                for lexicon in (CAUSAL_CUES, ORDERING_CUES)
                for cue in find_cues(sentences[sent_id], lexicon)
            }
        )
    )
    return PairEvidence(
        doc_id=doc_id,
        head_id=head_id,
        tail_id=tail_id,
        head_sent=head_sent,
        tail_sent=tail_sent,
        candidates=candidates,
        selected=selected,
        selected_cues=selected_cues,
        protected_cues=protected_cues,
    )


def with_length_matched_substitutes(
    record: PairEvidence, sentences: Sequence[Sequence[str]]
) -> PairEvidence:
    """The negative control's citation: non-evidence sentences of matched length.

    Matching length keeps the amount of text the counterfactuals move constant,
    so a mediator improvement that survives this came from moving *text*, not
    from moving evidence.  A document with too few sentences outside the pair's
    span cannot supply a match; the shortfall is recorded rather than padded,
    because a silently shorter control is a control that no longer matches.
    """
    outside = [
        sent_id for sent_id in range(len(sentences)) if sent_id not in set(record.candidates)
    ]
    substitutes: list[int] = []
    for target in record.selected:
        want = len(sentences[target])
        available = [sent_id for sent_id in outside if sent_id not in substitutes]
        if not available:
            break
        substitutes.append(
            min(
                available,
                key=lambda sent_id: (
                    abs(len(sentences[sent_id]) - want),
                    abs(sent_id - target),
                    sent_id,
                ),
            )
        )
    return replace(
        record,
        substitutes=tuple(sorted(substitutes)),
        substitutes_requested=len(record.selected),
    )


def _trigger_sentence(node: EventNode) -> int:
    """The mention's sentence, or fail loudly rather than cite the wrong span."""
    span = node.trigger_evidence[0] if node.trigger_evidence else None
    if span is None or span.sent_id is None:
        raise ValueError(f"{node.event_id}: no sentence-anchored trigger to cite evidence for")
    return span.sent_id


def document_pair_evidence(
    nodes: Sequence[EventNode],
    doc_text: str,
    pairs: Sequence[tuple[str, str]],
    *,
    budget: int = EVIDENCE_BUDGET,
) -> list[PairEvidence]:
    """One record per candidate pair, in the order the candidates were given.

    The frozen candidate universe is the one thing A4 may not touch, so this
    returns exactly as many records as it was given pairs, in the same order,
    and fails on a pair whose endpoints it cannot place.  Every record carries
    its length-matched substitutes too, so all four arms read one record rather
    than each rebuilding the selection they intervene on.
    """
    sentences = sentence_tokens(doc_text)
    by_id = {node.event_id: node for node in nodes}
    records: list[PairEvidence] = []
    for head_id, tail_id in pairs:
        if head_id not in by_id or tail_id not in by_id:
            raise ValueError(f"candidate pair ({head_id}, {tail_id}) references an unknown node")
        head, tail = by_id[head_id], by_id[tail_id]
        record = build_pair_evidence(
            head.doc_id,
            head_id,
            tail_id,
            head_sent=_trigger_sentence(head),
            tail_sent=_trigger_sentence(tail),
            head_trigger=head.trigger,
            tail_trigger=tail.trigger,
            sentences=sentences,
            budget=budget,
        )
        records.append(with_length_matched_substitutes(record, sentences))
    return records


def counterfactual_sentence_ids(
    record: PairEvidence, n_sentences: int, *, arm: str
) -> dict[str, tuple[int, ...]]:
    """The sentence sets of the three forwards this arm needs.

    ``base`` is the document as the reproduction baseline encodes it, ``masked``
    drops the cited sentences, ``retained`` keeps only the trigger sentences and
    the cited ones.  ``remove_core`` has no evidence stream and therefore only a
    base forward.
    """
    if n_sentences <= max(record.candidates):
        raise ValueError(f"{record.doc_id}: {n_sentences} sentences cannot hold the pair's span")
    base = tuple(range(n_sentences))
    if not arm_flags(arm).evidence_stream:
        return {"base": base}
    cited = set(record.cited(arm)) - set(record.protected)
    return {
        "base": base,
        "masked": tuple(sent_id for sent_id in base if sent_id not in cited),
        "retained": tuple(sorted(set(record.protected) | cited)),
    }


def necessity_scoreable(record: PairEvidence, *, arm: str) -> bool:
    """Whether masking this pair's citation changes the document at all.

    A pair with nothing maskable would contribute the full margin as a constant,
    which is gradient on nothing; it is excluded rather than absorbed.
    """
    if not arm_flags(arm).evidence_stream:
        return False
    return bool(set(record.cited(arm)) - set(record.protected))


def unsupported_cross_sentence_causal(
    records: Sequence[PairEvidence],
    predicted: Mapping[tuple[str, str], str],
    gold: Mapping[tuple[str, str], str],
) -> dict[str, int]:
    """The registered mediator: unsupported cross-sentence causal false positives.

    A false positive is *unsupported* when no cue licensed the pair anywhere in
    its span — neither in a cited sentence nor in a trigger sentence.  The
    denominators travel with the counts so a rate can be recomputed without
    re-reading predictions, and so a drop cannot be read as progress when it
    came from predicting fewer causal edges overall.
    """
    counts: dict[str, int] = {
        "pairs": 0,
        "cross_sentence": 0,
        "predicted_causal": 0,
        "false_positives": 0,
        "cross_sentence_false_positives": 0,
        "unsupported_cross_sentence_false_positives": 0,
    }
    for record in records:
        key = (record.head_id, record.tail_id)
        if key not in predicted or key not in gold:
            raise ValueError(f"pair {key} is missing a prediction or a gold label")
        is_causal = predicted[key] != "NONE"
        false_positive = is_causal and predicted[key] != gold[key]
        counts["pairs"] += 1
        counts["cross_sentence"] += int(record.cross_sentence)
        counts["predicted_causal"] += int(is_causal)
        counts["false_positives"] += int(false_positive)
        cross_false = false_positive and record.cross_sentence
        counts["cross_sentence_false_positives"] += int(cross_false)
        counts["unsupported_cross_sentence_false_positives"] += int(
            cross_false and not record.supported
        )
    return counts


def pair_evidence_sidecar(records: Sequence[PairEvidence], *, arm: str) -> dict[str, dict]:
    """Per-pair record of what was cited, for every pair — never a subset.

    Coverage is what A4.1 gates on, so a pair with an empty citation is written
    with its empty citation instead of being left out and counted as scored.
    """
    validate_a4_arm(arm)
    sidecar: dict[str, dict] = {}
    for record in records:
        key = f"{record.head_id}::{record.tail_id}"
        if key in sidecar:
            raise ValueError(f"duplicate candidate pair in sidecar: {key}")
        sidecar[key] = {
            "doc_id": record.doc_id,
            "position": "cross_sentence" if record.cross_sentence else "same_sentence",
            "candidates": len(record.candidates),
            "selected": list(record.selected),
            "cited": list(record.cited(arm)),
            "selected_cues": list(record.selected_cues),
            "protected_cues": list(record.protected_cues),
            "substitutes_requested": record.substitutes_requested,
            "supported": record.supported,
            "necessity_scoreable": necessity_scoreable(record, arm=arm),
        }
    return sidecar


def pair_evidence_config(arm: str, *, budget: int = EVIDENCE_BUDGET) -> dict[str, object]:
    """The arm identity a checkpoint carries, so an arm cannot be mistaken."""
    return {
        "schema_version": CONFIG_SCHEMA_VERSION,
        "arm": validate_a4_arm(arm),
        "budget": budget,
        "lexicon_sha256": lexicon_digest(),
    }


def load_pair_evidence_config(checkpoint: Path) -> dict[str, object]:
    """Read an arm identity and refuse it if the selector drifted underneath it.

    The selector's lexicon and budget are code, not data: if they change after a
    checkpoint was trained, inference cites different sentences than training
    did, and the run's numbers silently stop meaning what they claim.
    """
    path = Path(checkpoint) / CONFIG_FILE
    if not path.is_file():
        raise FileNotFoundError(f"{path} is missing; the arm identity is unknown")
    payload = json.loads(path.read_text(encoding="utf-8"))
    expected = {"schema_version", "arm", "budget", "lexicon_sha256"}
    if not isinstance(payload, dict) or set(payload) != expected:
        raise ValueError(f"{path} must contain exactly {sorted(expected)}")
    if payload["schema_version"] != CONFIG_SCHEMA_VERSION:
        raise ValueError(f"{path} has an unsupported schema_version")
    validate_a4_arm(payload["arm"])
    current = lexicon_digest()
    if payload["lexicon_sha256"] != current or payload["budget"] != EVIDENCE_BUDGET:
        raise ValueError(
            f"{path} evidence selector hash drift: checkpoint "
            f"{payload['lexicon_sha256']}/{payload['budget']} vs code {current}/{EVIDENCE_BUDGET}"
        )
    return payload


try:  # pragma: no cover - exercised on a GPU host
    import torch
    import torch.nn as nn

    from ekg.relations.pair_heads import build_pair_head

    class PairEvidenceClassifier(nn.Module):
        """The reproduction head plus a zero-initialised evidence residual.

        The base path *is* `PairClassifier`, so `full` and `remove_core` do not
        merely agree at init by construction of matched shapes — they run the
        same parameters.  The residual reads how the pair feature moves when only
        the evidence is in context (`retained` minus `base`), which is the
        quantity the sufficiency term is defined on, and starts at exactly zero
        so it has to earn its weight (an `N(0, 1)` stream over a tuned feature
        path halved MRR once; see `docs/ENGINEERING_NOTES.md`).
        """

        def __init__(
            self,
            hidden_size: int,
            subtype_counts: dict[str, int],
            mlp_hidden: int = 150,
            dist_dim: int = 32,
        ) -> None:
            super().__init__()
            self.base = build_pair_head(
                LINEAR_HEAD,
                hidden_size=hidden_size,
                subtype_counts=subtype_counts,
                mlp_hidden=mlp_hidden,
                dist_dim=dist_dim,
            )
            self.evidence = nn.ModuleDict(
                {
                    family: nn.Linear(hidden_size * 4, count, bias=False)
                    for family, count in subtype_counts.items()
                }
            )
            for layer in self.evidence.values():
                nn.init.zeros_(layer.weight)

        def forward(
            self,
            pair_feats: torch.Tensor,
            dist_ids: torch.Tensor,
            evidence_feats: torch.Tensor | None = None,
        ) -> dict[str, torch.Tensor]:
            logits = self.base(pair_feats, dist_ids)
            if evidence_feats is None:
                return logits
            delta = evidence_feats - pair_feats
            return {
                family: value + self.evidence[family](delta) for family, value in logits.items()
            }

    @pair_head_factories.register(PAIR_EVIDENCE_HEAD)
    def _build_pair_evidence_head(
        hidden_size: int,
        subtype_counts: dict[str, int],
        mlp_hidden: int = 150,
        dist_dim: int = 32,
    ) -> PairEvidenceClassifier:
        return PairEvidenceClassifier(hidden_size, subtype_counts, mlp_hidden, dist_dim)

    def sufficiency_necessity_loss(
        base: torch.Tensor,
        masked: torch.Tensor,
        retained: torch.Tensor,
        target: torch.Tensor,
        *,
        scoreable: torch.Tensor,
        ignore_index: int = -100,
        margin: float = 1.0,
        slack: float = 0.5,
    ) -> torch.Tensor:
        """Both consistency terms for one relation family, on positive rows only.

        Necessity: masking the citation must cost the gold subtype at least
        `margin` of logit.  Sufficiency: the citation alone must hold the gold
        subtype within `slack` of the full context.  Negative rows are excluded —
        the claim is about what supports a positive, and asking a NONE row to
        lose logit when its evidence is removed is a claim about nothing.
        """
        positive = (target != ignore_index) & (target != 0)
        if not torch.any(positive):
            return base.new_zeros(())
        index = target[positive].unsqueeze(1)
        gold_base = base[positive].gather(1, index).squeeze(1)
        gold_retained = retained[positive].gather(1, index).squeeze(1)
        sufficiency = torch.relu((gold_base - gold_retained) - slack).mean()

        necessary = positive & scoreable
        if not torch.any(necessary):
            return sufficiency
        index = target[necessary].unsqueeze(1)
        gold_base = base[necessary].gather(1, index).squeeze(1)
        gold_masked = masked[necessary].gather(1, index).squeeze(1)
        necessity = torch.relu(margin - (gold_base - gold_masked)).mean()
        return sufficiency + necessity

    __all__ += ["PairEvidenceClassifier", "sufficiency_necessity_loss"]

except ImportError:  # pragma: no cover - the local CPU environment lacks torch
    pass
