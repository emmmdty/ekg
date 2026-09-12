"""Pair-specific evidence: does a predicted relation depend on its context at all?

The design here follows this project's own measurements, which rule out the
obvious alternative.  From `docs/results/PHASE_A.md`:

- **Causal errors are false positives, not misses.** TP/FP/FN = 2,706 / 10,659 /
  2,090; false positives are 83.6% of all causal errors and 78.4% of them are
  cross-sentence (8,354), of which 59.4% are long-distance.  Cross-sentence
  precision is .1998 against .2904 same-sentence while recall differs by only
  .062: the model emits 2.6x as many cross-sentence causal edges as there are
  gold ones.  The error profile's own conclusion names the remedy — "下一机制
  应直接提高长距离跨句『是否有因果边』的分离度，例如 evidence/context 选择".
- **Discourse cues are not the missing signal.** Stratifying gold causal recall
  by whether a connective sits between the triggers moves it by .008
  same-sentence and .064 cross-sentence, and the page's verdict is explicit:
  "不做『连接词感知的上下文表示』，它没有余量可拿".  Measured again here on 60
  train documents / 109,234 candidate pairs, a cue lexicon labels **79.3%** of
  all pairs as cue-bearing and 28% of the sentences inside a span, so it also
  cannot rank one sentence above another on the long spans that carry the error
  mass.  A cue-ranked selector was therefore removed from this module.

So evidence is not *selected* here, it is *defined*: a pair's evidence is the
sentences strictly between its two triggers.  Nothing is ranked, nothing is
scored, and there is no budget or threshold to sweep.  Two counterfactual
forwards ask the only question the error profile leaves open:

``necessity``
    Encode the document with the interior removed.  A cross-sentence positive
    that keeps its logit here was never reading the context — which is exactly
    the 2.6x over-emission, stated as something a loss can punish.
``sufficiency``
    Encode the pair's span alone.  A positive must survive on it, which is what
    stops necessity from being satisfied by predicting NONE more often (the
    contract guards causal recall for the same reason).

The two cover complementary ranges and that is deliberate: necessity is
informative when the interior is large (long spans — the error mass), while
sufficiency is informative when the span is small next to the document.
Trigger sentences are *protected*: they anchor the pooling and are never
masked, so a same-sentence or adjacent pair has no necessity term.  Those are
the short distances, which the error profile shows are not where the errors are.

MAVEN-ERE carries no evidence annotation (a record holds only `tokens`,
`sentences`, `events`, `TIMEX` and the three relation tables), so the
supervised-evidence route the DocRED literature takes — EIDER, SAIS, DREEAM —
is not available; DREEAM's self-training variant is the named upgrade path if
the intervention turns out to matter but this granularity is too coarse.

The four frozen A4 arms differ **only** in the objective and in which sentences
are intervened on: ``full`` uses its own interior and trains both consistency
terms; ``remove_core`` passes no evidence stream at all; ``length_matched``
intervenes on equally long sentences from outside the span (the registered
negative control); ``no_constraint`` keeps the evidence representation and drops
the consistency terms.  All four share one head class whose evidence residual is
zero-initialised, so their base logits coincide at init and a gain cannot come
from capacity.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from pathlib import Path

from ekg.core.schema import EventNode
from ekg.relations.pair_heads import LINEAR_HEAD, PAIR_EVIDENCE_HEAD, pair_head_factories

__all__ = [
    "A4_ARMS",
    "CONFIG_FILE",
    "CONSISTENCY_FAMILY",
    "CONSISTENCY_PAIR_CAP",
    "EVIDENCE_RULE",
    "FULL_ARM",
    "LENGTH_MATCHED_ARM",
    "NECESSITY_MARGIN",
    "NO_CONSTRAINT_ARM",
    "REMOVE_CORE_ARM",
    "ArmFlags",
    "PairEvidence",
    "arm_flags",
    "build_pair_evidence",
    "consistency_rows",
    "context_dependence_report",
    "counterfactual_sentence_ids",
    "document_pair_evidence",
    "load_pair_evidence_config",
    "necessity_scoreable",
    "pair_evidence_config",
    "pair_evidence_sidecar",
    "sentence_lengths",
    "validate_a4_arm",
    "with_length_matched_substitutes",
]

CONFIG_FILE = "pair_evidence_config.json"
CONFIG_SCHEMA_VERSION = "ekg.relation_pair_evidence.v2"

# What counts as a pair's evidence.  Recorded in every checkpoint because it is
# code, not data: change it and inference intervenes on different sentences than
# training did, while the numbers still look comparable.
EVIDENCE_RULE = "span_interior"

# The consistency terms run on the causal family alone.  Causal false positives
# are 83.6% of causal errors and causal micro-F1 is the chapter's primary
# metric; temporal carries ~39x the positives and is a guardrail here, so
# including it would pay for most of the counterfactual forwards to supervise
# something the promotion gate only asks us not to break.
CONSISTENCY_FAMILY = "causal"

# How much logit a positive must lose when its evidence is removed.  Frozen, and
# also the margin the context-dependence report counts at, so the loss and the
# mediator are read on one scale.
NECESSITY_MARGIN = 1.0

# Worst-case bound on counterfactual forwards per **training** document, where
# every forward's activations stay alive for the backward pass.  A document with
# more supervised pairs than this takes the first `CONSISTENCY_PAIR_CAP` in
# candidate order and records the rest as skipped, so one training step has a
# bounded cost and the choice is replayable.  Inference must not apply it: the
# scored rule would then depend on candidate order, and the positives past the
# cap would go unrevised and unmeasured.
# ponytail: fixed cap; raise it if the skipped count is ever a large share.
CONSISTENCY_PAIR_CAP = 16

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


def sentence_lengths(doc_text: str) -> list[int]:
    """Token count per sentence of the canonical doc text (one line each).

    Only used to match the negative control's length; the counterfactuals
    themselves address sentences by index, never by content.
    """
    return [len(line.split()) for line in doc_text.split("\n")]


@dataclass(frozen=True)
class PairEvidence:
    """One candidate pair's evidence set and the counterfactuals it licenses."""

    doc_id: str
    head_id: str
    tail_id: str
    head_sent: int
    tail_sent: int
    interior: tuple[int, ...]
    substitutes: tuple[int, ...] = ()
    substitutes_requested: int = 0

    @property
    def protected(self) -> tuple[int, ...]:
        """The trigger sentences; present in every forward, never masked."""
        return tuple(sorted({self.head_sent, self.tail_sent}))

    @property
    def span(self) -> tuple[int, ...]:
        """The closed sentence span the pair covers, triggers included."""
        first, last = sorted((self.head_sent, self.tail_sent))
        return tuple(range(first, last + 1))

    @property
    def cross_sentence(self) -> bool:
        return self.head_sent != self.tail_sent

    def cited(self, arm: str) -> tuple[int, ...]:
        """The sentences this arm actually intervenes on."""
        return self.substitutes if arm_flags(arm).substitute_control else self.interior


def build_pair_evidence(
    doc_id: str,
    head_id: str,
    tail_id: str,
    *,
    head_sent: int,
    tail_sent: int,
    n_sentences: int,
) -> PairEvidence:
    """A pair's evidence: the sentences strictly between its two triggers.

    Definition, not selection.  There is nothing to rank here, which is the
    point: the cue lexicon that would have done the ranking labels four pairs in
    five as cue-bearing and cannot separate sentences inside a long span (see
    the module docstring for the measurement).
    """
    for sent_id in (head_sent, tail_sent):
        if not 0 <= sent_id < n_sentences:
            raise ValueError(f"{doc_id}: sent_id {sent_id} outside {n_sentences} sentences")
    first, last = sorted((head_sent, tail_sent))
    return PairEvidence(
        doc_id=doc_id,
        head_id=head_id,
        tail_id=tail_id,
        head_sent=head_sent,
        tail_sent=tail_sent,
        interior=tuple(range(first + 1, last)),
    )


def with_length_matched_substitutes(
    record: PairEvidence, lengths: Sequence[int]
) -> PairEvidence:
    """The negative control's target: equally long sentences from outside the span.

    Matching length keeps the amount of text the counterfactuals move constant,
    so a mediator improvement that survives this came from moving *text*, not
    from moving the pair's own context.  A span that leaves too few sentences
    outside it cannot be matched; the shortfall is recorded rather than padded,
    because a silently shorter control is a control that no longer matches — and
    it is the long spans, the ones carrying the error mass, that run short, so
    this count has to be read alongside the arm.
    """
    outside = [sent_id for sent_id in range(len(lengths)) if sent_id not in set(record.span)]
    substitutes: list[int] = []
    for target in record.interior:
        want = lengths[target]
        available = [sent_id for sent_id in outside if sent_id not in substitutes]
        if not available:
            break
        substitutes.append(
            min(
                available,
                key=lambda sent_id: (
                    abs(lengths[sent_id] - want),
                    abs(sent_id - target),
                    sent_id,
                ),
            )
        )
    return replace(
        record,
        substitutes=tuple(sorted(substitutes)),
        substitutes_requested=len(record.interior),
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
) -> list[PairEvidence]:
    """One record per candidate pair, in the order the candidates were given.

    The frozen candidate universe is the one thing A4 may not touch, so this
    returns exactly as many records as it was given pairs, in the same order,
    and fails on a pair whose endpoints it cannot place.  Every record carries
    its length-matched substitutes too, so all four arms read one record rather
    than each rebuilding the intervention they act on.
    """
    lengths = sentence_lengths(doc_text)
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
            n_sentences=len(lengths),
        )
        records.append(with_length_matched_substitutes(record, lengths))
    return records


def counterfactual_sentence_ids(
    record: PairEvidence, n_sentences: int, *, arm: str
) -> dict[str, tuple[int, ...]]:
    """The sentence sets of the three forwards this arm needs.

    ``base`` is the document as the reproduction baseline encodes it, ``masked``
    drops the intervened sentences, ``retained`` keeps the pair's span (with the
    control's substitutes in place of the interior, when that arm is running).
    ``remove_core`` has no evidence stream and therefore only a base forward.
    """
    if n_sentences <= max(record.span):
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
    """Whether the intervention changes the document at all.

    A pair with an empty interior would contribute the full margin as a
    constant, which is gradient on nothing; it is excluded rather than absorbed.
    Same-sentence and adjacent pairs are exactly that case.
    """
    if not arm_flags(arm).evidence_stream:
        return False
    return bool(set(record.cited(arm)) - set(record.protected))


def consistency_rows(
    records: Sequence[PairEvidence],
    positive: Sequence[bool],
    *,
    arm: str,
    cap: int = CONSISTENCY_PAIR_CAP,
) -> tuple[tuple[int, ...], int]:
    """Which rows carry the consistency terms, and how many the cap dropped.

    Only scoreable causal positives: the claim is about what supports a positive
    prediction, and the counterfactual forwards are the expensive part, so
    spending them on negatives would buy nothing.  Selection is by candidate
    order, so a capped document supervises the same rows on every replay.
    """
    if len(records) != len(positive):
        raise ValueError(f"{len(positive)} labels for {len(records)} candidate pairs")
    if cap < 0:
        raise ValueError("consistency pair cap must not be negative")
    if not arm_flags(arm).evidence_stream:
        return (), 0
    eligible = [index for index, flag in enumerate(positive) if flag]
    return tuple(eligible[:cap]), max(0, len(eligible) - cap)


def context_dependence_report(
    records: Sequence[PairEvidence],
    predicted: Mapping[tuple[str, str], str],
    gold: Mapping[tuple[str, str], str],
    *,
    logit_drop: Mapping[tuple[str, str], float] | None = None,
    margin: float = NECESSITY_MARGIN,
) -> dict[str, float | int]:
    """The registered mediator, plus how much the predictions used their context.

    `cross_sentence_false_positives` is the quantity the frozen causal chain
    registers, and it needs no interventions.  The context-dependence counters
    refine it with what the counterfactual forwards measure: a false positive
    whose causal logit barely moves when its interior is removed was not reading
    the context at all, which is the 2.6x cross-sentence over-emission stated as
    a per-instance fact.

    That refinement is deliberately **behavioural rather than lexical** — an
    earlier version of this function called a pair "unsupported" when no
    discourse cue appeared in its span, and measured on real data that labels
    79.3% of pairs supported, so it could not have separated anything.

    Only pairs with a measured drop enter the context counters, and their own
    denominator travels with them: the per-document cap means not every false
    positive is measured, and a rate over the wrong denominator is how a cap
    turns into an apparent effect.
    """
    drops = dict(logit_drop or {})
    counts: dict[str, float | int] = {
        "pairs": 0,
        "cross_sentence": 0,
        "predicted_causal": 0,
        "false_positives": 0,
        "cross_sentence_false_positives": 0,
        "measured_cross_sentence_false_positives": 0,
        "context_independent_cross_sentence_false_positives": 0,
        "measured_true_positives": 0,
    }
    false_positive_drops: list[float] = []
    true_positive_drops: list[float] = []
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
        drop = drops.get(key)
        if drop is None:
            continue
        if cross_false:
            counts["measured_cross_sentence_false_positives"] += 1
            false_positive_drops.append(drop)
            counts["context_independent_cross_sentence_false_positives"] += int(drop < margin)
        elif is_causal and predicted[key] == gold[key]:
            counts["measured_true_positives"] += 1
            true_positive_drops.append(drop)
    counts["margin"] = margin
    counts["mean_false_positive_logit_drop"] = (
        sum(false_positive_drops) / len(false_positive_drops) if false_positive_drops else 0.0
    )
    counts["mean_true_positive_logit_drop"] = (
        sum(true_positive_drops) / len(true_positive_drops) if true_positive_drops else 0.0
    )
    return counts


def pair_evidence_sidecar(records: Sequence[PairEvidence], *, arm: str) -> dict[str, dict]:
    """Per-pair record of what was intervened on, for every pair — never a subset.

    Coverage is what A4.1 gates on, so a pair with an empty interior is written
    with its empty interior instead of being left out and counted as scored.
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
            "span": len(record.span),
            "interior": list(record.interior),
            "cited": list(record.cited(arm)),
            "substitutes_requested": record.substitutes_requested,
            "control_matched": len(record.substitutes) == record.substitutes_requested,
            "necessity_scoreable": necessity_scoreable(record, arm=arm),
        }
    return sidecar


def pair_evidence_config(arm: str) -> dict[str, object]:
    """The arm identity a checkpoint carries, so an arm cannot be mistaken.

    `residual_rows` is the rule by which a row receives the evidence residual,
    and it is recorded because it has to be the same rule at training and at
    inference: the base pass's own causal prediction, never a gold label.
    Training additionally *supervises* the gold positives — supervision only
    exists at train time, so that is not an asymmetry in the scored rule.
    """
    return {
        "schema_version": CONFIG_SCHEMA_VERSION,
        "arm": validate_a4_arm(arm),
        "evidence_rule": EVIDENCE_RULE,
        "consistency_family": CONSISTENCY_FAMILY,
        "consistency_pair_cap": CONSISTENCY_PAIR_CAP,
        "necessity_margin": NECESSITY_MARGIN,
        "residual_rows": "base_predicted_positive",
    }


def load_pair_evidence_config(checkpoint: Path) -> dict[str, object]:
    """Read an arm identity and refuse it if the mechanism drifted underneath it.

    The evidence rule, the supervised family and the margin are code, not data:
    if they change after a checkpoint was trained, inference intervenes on
    different sentences than training did, and the run's numbers silently stop
    meaning what they claim.
    """
    path = Path(checkpoint) / CONFIG_FILE
    if not path.is_file():
        raise FileNotFoundError(f"{path} is missing; the arm identity is unknown")
    payload = json.loads(path.read_text(encoding="utf-8"))
    expected = pair_evidence_config(FULL_ARM)
    if not isinstance(payload, dict) or set(payload) != set(expected):
        raise ValueError(f"{path} must contain exactly {sorted(expected)}")
    if payload["schema_version"] != CONFIG_SCHEMA_VERSION:
        raise ValueError(f"{path} has an unsupported schema_version")
    validate_a4_arm(payload["arm"])
    for field in (
        "evidence_rule",
        "consistency_family",
        "consistency_pair_cap",
        "necessity_margin",
        "residual_rows",
    ):
        if payload[field] != expected[field]:
            raise ValueError(
                f"{path} mechanism drift on {field}: checkpoint {payload[field]!r} "
                f"vs code {expected[field]!r}"
            )
    return payload


try:  # pragma: no cover - exercised on a GPU host
    import torch
    import torch.nn as nn

    from ekg.relations.extractor.supervised import encode_trigger_reps
    from ekg.relations.pair_heads import build_pair_head

    class PairEvidenceClassifier(nn.Module):
        """The reproduction head plus a zero-initialised evidence residual.

        The base path *is* `PairClassifier`, so `full` and `remove_core` do not
        merely agree at init by construction of matched shapes — they run the
        same parameters.  The residual reads how the pair feature moves when only
        the span is in context (`retained` minus `base`), which is the quantity
        the sufficiency term is defined on, and starts at exactly zero so it has
        to earn its weight (an `N(0, 1)` stream over a tuned feature path halved
        MRR once; see `docs/ENGINEERING_NOTES.md`).
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

    def pair_counterfactual_embeddings(
        encoder,
        tokenizer,
        nodes,
        doc_text: str,
        requests: Sequence[tuple[tuple[str, str], tuple[int, ...]]],
        max_length: int,
        device: str = "cpu",
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """Endpoint embeddings for each (pair, sentence set) request.

        Requests sharing a sentence set share one forward, which is what makes
        this affordable: pairs spanning the same sentences intervene on the same
        interior.  It is `encode_trigger_reps` underneath, with the same window
        packing and the same fail-fast on an unlocatable trigger, so a
        counterfactual pools its endpoints exactly the way the base forward does
        — a second packing implementation here is how the two would drift.

        Gradient flows; the caller decides train or eval mode.
        """
        if not requests:
            empty = torch.zeros((0, encoder.config.hidden_size), device=device)
            return empty, empty
        groups: dict[tuple[int, ...], list[int]] = {}
        for index, (_, sentence_ids) in enumerate(requests):
            groups.setdefault(tuple(sentence_ids), []).append(index)
        heads: list[torch.Tensor | None] = [None] * len(requests)
        tails: list[torch.Tensor | None] = [None] * len(requests)
        for sentence_ids, indices in groups.items():
            embeddings = encode_trigger_reps(
                encoder,
                tokenizer,
                list(nodes),
                doc_text,
                max_length,
                device,
                sentence_ids=list(sentence_ids),
            )
            for index in indices:
                head_id, tail_id = requests[index][0]
                if head_id not in embeddings or tail_id not in embeddings:
                    raise ValueError(
                        f"counterfactual context {sentence_ids} does not hold "
                        f"({head_id}, {tail_id}); a trigger sentence was masked"
                    )
                heads[index] = embeddings[head_id]
                tails[index] = embeddings[tail_id]
        return torch.stack(heads), torch.stack(tails)

    def sufficiency_necessity_loss(
        base: torch.Tensor,
        masked: torch.Tensor,
        retained: torch.Tensor,
        target: torch.Tensor,
        *,
        scoreable: torch.Tensor,
        ignore_index: int = -100,
        margin: float = NECESSITY_MARGIN,
        slack: float = 0.5,
    ) -> torch.Tensor:
        """Both consistency terms for one relation family, on positive rows only.

        Necessity: removing the interior must cost the gold subtype at least
        `margin` of logit.  Sufficiency: the span alone must hold it within
        `slack` of the full context.  Negative rows are excluded — the claim is
        about what supports a positive, and asking a NONE row to lose logit when
        its context is removed is a claim about nothing.
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

    __all__ += [
        "PairEvidenceClassifier",
        "pair_counterfactual_embeddings",
        "sufficiency_necessity_loss",
    ]

except ImportError:  # pragma: no cover - the local CPU environment lacks torch
    pass
