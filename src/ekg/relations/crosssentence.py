"""What sits between two triggers, and whether the pair head can see it.

`docs/results/PHASE_A.md` records the state of Ch2's main bottleneck: after
window encoding lifted cross-sentence causal F1 from 19.99 to 24.11, **three
further rounds of optimisation moved it by less than one point** (24.42 / 24.17
/ 25.00), while same-sentence sits at 38.07 and cross-sentence carries 75% of
the positives. The same file also rules out the obvious structural suspect --
only 3.3% of gold causal pairs straddle an encoder window, so overlapping
windows cannot be the answer.

This module measures the next hypothesis before anything is built on it. The
pair head reads `[h; t; h*t; |h-t|]` plus a distance bucket: two pooled trigger
vectors and how far apart they are. For a same-sentence pair the connective
("because", "as a result") lies inside the local context both triggers were
contextualised by. For a cross-sentence pair it lies *between* them, possibly
several sentences from either, and nothing in the pair feature points at it.

So: enumerate the tokens between the two triggers in **document order** and ask
whether a discourse cue is there. If recall on cue-bearing cross-sentence pairs
is no better than on cue-less ones, the model is not using the cue, and a
pair-specific context representation has something to recover. If it is already
better, this hypothesis is wrong and the gap is elsewhere.
"""

from __future__ import annotations

from collections.abc import Sequence

__all__ = [
    "CAUSAL_CUES",
    "ORDERING_CUES",
    "MentionSpan",
    "document_order",
    "between_tokens",
    "find_cues",
]

# Explicit causal discourse markers. Kept small and literal on purpose: this is
# a diagnostic probe, not a feature -- a fuzzy lexicon would blur the very
# contrast it is meant to measure.
CAUSAL_CUES: tuple[tuple[str, ...], ...] = (
    ("because",), ("since",), ("therefore",), ("thus",), ("hence",),
    ("consequently",), ("thereby",), ("so",),
    ("as", "a", "result"), ("due", "to"), ("owing", "to"), ("in", "response", "to"),
    ("led", "to"), ("leading", "to"), ("resulted", "in"), ("resulting", "in"),
    ("caused",), ("causing",), ("cause",), ("triggered",), ("sparked",),
    ("prompted",), ("forced",),
)

# Ordering markers, reported separately: they often accompany causation in this
# corpus but are not causal claims, and folding them in would inflate the
# "cue present" cell.
ORDERING_CUES: tuple[tuple[str, ...], ...] = (
    ("after",), ("following",), ("subsequently",), ("then",), ("later",),
    ("before",), ("prior", "to"),
)


class MentionSpan:
    """A trigger's position: sentence index and half-open token range."""

    __slots__ = ("sent_id", "start", "end")

    def __init__(self, sent_id: int, start: int, end: int) -> None:
        if sent_id < 0 or start < 0 or end <= start:
            raise ValueError(f"invalid mention span sent={sent_id} [{start}, {end})")
        self.sent_id, self.start, self.end = sent_id, start, end

    def key(self) -> tuple[int, int]:
        return (self.sent_id, self.start)

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"MentionSpan({self.sent_id}, {self.start}, {self.end})"


def document_order(a: MentionSpan, b: MentionSpan) -> tuple[MentionSpan, MentionSpan]:
    """The two spans in reading order.

    Gold pairs are stored as (cause, effect), which is *not* reading order --
    an effect is often written first. Measuring "what lies between" against the
    gold ordering would splice the document backwards.
    """
    return (a, b) if a.key() <= b.key() else (b, a)


def between_tokens(
    sentences: Sequence[Sequence[str]], first: MentionSpan, second: MentionSpan
) -> list[str]:
    """Tokens strictly between two triggers, in document order.

    Same sentence: the tokens separating them. Cross-sentence: the tail of the
    first trigger's sentence, every sentence in between, and the head of the
    second trigger's sentence. Overlapping or nested mentions give an empty
    list rather than a negative slice.
    """
    first, second = document_order(first, second)
    for span in (first, second):
        if not 0 <= span.sent_id < len(sentences):
            raise IndexError(f"sent_id {span.sent_id} outside {len(sentences)} sentences")
    if first.sent_id == second.sent_id:
        return list(sentences[first.sent_id][first.end : second.start])
    tokens = list(sentences[first.sent_id][first.end :])
    for sent_id in range(first.sent_id + 1, second.sent_id):
        tokens.extend(sentences[sent_id])
    tokens.extend(sentences[second.sent_id][: second.start])
    return tokens


def find_cues(tokens: Sequence[str], lexicon: Sequence[Sequence[str]]) -> list[str]:
    """Every lexicon entry present as a contiguous, case-insensitive token run."""
    lowered = [token.lower() for token in tokens]
    found = []
    for entry in lexicon:
        width = len(entry)
        if any(
            tuple(lowered[i : i + width]) == tuple(entry)
            for i in range(len(lowered) - width + 1)
        ):
            found.append(" ".join(entry))
    return found
