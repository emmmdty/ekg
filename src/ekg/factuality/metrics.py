"""Factuality metrics — macro-F1 by construction, accuracy only as a footnote.

MAVEN-FACT is 94.9% CT+ on valid, so accuracy carries almost no information:
predicting CT+ for everything scores **.9487 accuracy and .1947 macro-F1**.
`majority_baseline_report` computes that floor from the gold labels themselves
so any report can print it next to the system number instead of asserting it.

Two contracts follow from that imbalance:

- every one of the five classes appears in `per_class`, including ones the
  system never predicted (f1 = 0) and — during development on subsets — ones
  with no gold instances. A class dropping out of the macro average would
  quietly inflate it;
- predictions must cover exactly the scored mentions. A missing prediction is
  an error, not an implicit abstention, because "skip the ones you are unsure
  about" is precisely how a macro-F1 gets inflated on the rare classes.
"""

from __future__ import annotations

from collections.abc import Mapping, Set

from ekg.core.eval.relation import PRF
from ekg.relations.data.maven_fact import FACTUALITY_LABELS

__all__ = [
    "MAJORITY_LABEL",
    "EVIDENCE_BEARING_LABELS",
    "factuality_report",
    "majority_baseline_report",
    "evidence_span_prf",
    "evidence_span_report",
]

# The classes MAVEN-FACT annotates supporting evidence for. Its Table 4 macro-
# averages the evidence score over exactly these three "because only they have
# supporting evidence in the given input text"; CT+ carries evidence on 0.1% of
# mentions and Uu on 11%, so pooling over all five would not be comparable.
EVIDENCE_BEARING_LABELS: tuple[str, ...] = ("CT-", "PS+", "PS-")

# The class a trivial classifier collapses to (94.4% of train, 94.9% of valid).
MAJORITY_LABEL = FACTUALITY_LABELS[0]

# An evidence span as scored here: the (char_start, char_end) of one word.
Span = tuple[int, int]


def factuality_report(predicted: Mapping[str, str], gold: Mapping[str, str]) -> dict:
    """Per-class P/R/F1, macro-F1 (the headline) and accuracy (the footnote)."""
    missing = set(gold) - set(predicted)
    if missing:
        raise ValueError(f"{len(missing)} mention(s) without a prediction: {sorted(missing)[:5]}")
    unknown = set(predicted) - set(gold)
    if unknown:
        raise ValueError(f"prediction on unknown mention(s): {sorted(unknown)[:5]}")
    bad = {label for label in predicted.values() if label not in FACTUALITY_LABELS} | {
        label for label in gold.values() if label not in FACTUALITY_LABELS
    }
    if bad:
        raise ValueError(f"unknown factuality label(s): {sorted(bad)}")

    per_class: dict[str, PRF] = {}
    for label in FACTUALITY_LABELS:
        tp = sum(1 for m, g in gold.items() if g == label and predicted[m] == label)
        n_pred = sum(1 for p in predicted.values() if p == label)
        n_gold = sum(1 for g in gold.values() if g == label)
        per_class[label] = PRF.from_counts(tp, n_pred, n_gold)

    correct = sum(1 for m, g in gold.items() if predicted[m] == g)
    return {
        "macro_f1": sum(p["f1"] for p in per_class.values()) / len(FACTUALITY_LABELS),
        "accuracy": correct / len(gold) if gold else 0.0,
        "per_class": per_class,
        "n_mentions": len(gold),
    }


def majority_baseline_report(gold: Mapping[str, str]) -> dict:
    """The all-CT+ floor, computed on the same gold the system is scored on."""
    return factuality_report(dict.fromkeys(gold, MAJORITY_LABEL), gold)


def evidence_span_prf(predicted: Mapping[str, Set[Span]], gold: Mapping[str, Set[Span]]) -> PRF:
    """Exact-match P/R/F1 over evidence spans, pooled across mentions.

    ``n_mentions_with_evidence`` is carried in the result because the gold
    denominator is small and easy to misstate: only 843 of the 17,780 valid
    mentions (4.7%) are annotated with evidence at all.
    """
    unknown = set(predicted) - set(gold)
    if unknown:
        raise ValueError(f"evidence predicted for unknown mention(s): {sorted(unknown)[:5]}")

    tp = n_pred = n_gold = 0
    annotated = 0
    for mention, gold_spans in gold.items():
        predicted_spans = predicted.get(mention, set())
        tp += len(predicted_spans & gold_spans)
        n_pred += len(predicted_spans)
        n_gold += len(gold_spans)
        annotated += bool(gold_spans)
    prf = PRF.from_counts(tp, n_pred, n_gold)
    prf["n_mentions_with_evidence"] = annotated
    return prf


def evidence_span_report(
    predicted: Mapping[str, Set[Span]],
    gold: Mapping[str, Set[Span]],
    gold_labels: Mapping[str, str],
) -> dict:
    """Evidence scores in both the pooled and the published reporting.

    ``pooled`` is every mention's spans in one P/R/F1 — the number that says
    what the head does overall. ``macro_evidence_bearing`` restricts to CT−/PS+/
    PS− and macro-averages them, which is what MAVEN-FACT Table 4 reports
    (DMRoBERTa 45.4, GenEFD 44.7, GPT-4 19.5). Reporting only the pooled figure
    against those would compare two different quantities.

    Mentions are bucketed by their **gold** label so the denominator is fixed
    across systems; a system that mislabels a mention is charged for its
    evidence under the class the mention actually belongs to.
    """
    per_class: dict[str, PRF] = {}
    for label in EVIDENCE_BEARING_LABELS:
        members = {m for m, g in gold_labels.items() if g == label}
        per_class[label] = evidence_span_prf(
            {m: s for m, s in predicted.items() if m in members},
            {m: s for m, s in gold.items() if m in members},
        )
    return {
        "pooled": dict(evidence_span_prf(predicted, gold)),
        "per_class": {label: dict(prf) for label, prf in per_class.items()},
        "macro_evidence_bearing": sum(p["f1"] for p in per_class.values())
        / len(EVIDENCE_BEARING_LABELS),
    }
