"""Shared span encoding for the node stage: windowed documents, pooled spans.

MAVEN-Arg gives *character* offsets into a flat `document` of up to 11,383
characters — well past any encoder's 512-token limit — so a span is pooled from
an overlapping window of the document rather than from a sentence (the
MAVEN-ERE path in `relations.extractor.supervised` can use `sent_id`; this one
has no sentence segmentation to use).

`locate_span_token` is pure Python and fail-fast, and it is where the subtle bug
lives: a span near a window edge sees truncated context, and a span could be
matched inside a special token's ``(0, 0)`` offset. It therefore picks the
window where the covering token sits *farthest from both edges*, and raises if
no window covers the span rather than pooling position 0 — the same contract as
`locate_trigger_token`, whose silent-failure mode cost Phase A a re-run.

torch/transformers sit behind an availability guard so this module (and the
components that use it) import on a CPU box.
"""

from __future__ import annotations

from collections.abc import Sequence
from inspect import signature

__all__ = [
    "TORCH_AVAILABLE",
    "OffsetMapping",
    "locate_span_token",
    "global_attention_positions",
    "encode_spans",
    "pair_features",
]

# One window's tokenizer `offset_mapping`: (char_start, char_end) per token.
# Special tokens carry (0, 0), which never satisfies `start <= c < end`.
OffsetMapping = Sequence[tuple[int, int]]


def locate_span_token(windows: Sequence[OffsetMapping], char_start: int) -> tuple[int, int]:
    """(window, token) covering `char_start`, chosen for maximum context.

    Ties are broken toward the earlier window so the mapping is deterministic.
    """
    best: tuple[int, int, int] | None = None  # (centrality, window, token)
    for w, offsets in enumerate(windows):
        for t, (start, end) in enumerate(offsets):
            if start <= char_start < end:
                centrality = min(t, len(offsets) - 1 - t)
                if best is None or centrality > best[0]:
                    best = (centrality, w, t)
                break
    if best is None:
        raise ValueError(f"char offset {char_start} is not covered by any encoder window")
    return best[1], best[2]


def global_attention_positions(
    located: Sequence[tuple[int, int]], n_windows: int
) -> list[list[int]]:
    """Per window, the token indices that should attend globally.

    Long-context encoders (Longformer) attend locally by default, so the tokens a
    pair decision is read from must be marked global or two mentions far apart in
    the document never exchange information directly. Sorted and deduplicated so
    the mask is deterministic.
    """
    per_window: list[list[int]] = [[] for _ in range(n_windows)]
    for window, token in located:
        per_window[window].append(token)
    return [sorted(set(tokens)) for tokens in per_window]


try:  # pragma: no cover - exercised on the GPU server
    import torch

    TORCH_AVAILABLE = True
except ImportError:  # pragma: no cover - the local CPU path
    TORCH_AVAILABLE = False


# The two functions below are defined unconditionally and import torch inside, so
# this module (and everything that imports it) stays importable without torch —
# `locate_span_token` above is the part that carries the logic worth CPU-testing.


def pair_features(head: torch.Tensor, tail: torch.Tensor) -> torch.Tensor:
    """`[h_i; h_j; h_i⊙h_j; |h_i−h_j|]`.

    Deliberately the same feature the relation extractor's pair heads use, so a
    coreference decision and a relation decision are read off comparable
    representations.
    """
    import torch

    return torch.cat([head, tail, head * tail, (head - tail).abs()], dim=-1)


def encode_spans(
    encoder,
    tokenizer,
    doc_text: str,
    char_starts: Sequence[int],
    *,
    max_length: int = 512,
    stride: int = 128,
    device: str = "cpu",
) -> torch.Tensor:
    """Pooled representation per character offset, `(len(char_starts), hidden)`.

    The document is encoded once in overlapping windows and every span is
    gathered out of it, so cost is linear in document length, not in span count.
    Gradient flows when the encoder is in train mode; callers wrap inference in
    `no_grad`.

    **Windows are a defect, not a feature**: two mentions in different windows
    never share an encoding context, so their pair decision is made from
    representations that never saw each other. Measured on MAVEN-Arg valid at
    `max_length=512`, 13.1% of documents need more than one window and **34.7% of
    the gold coreference pairs inside them are split across windows**. Every
    document fits in 4,096 tokens (longest is 2,186), so a long-context encoder
    with `max_length=4096` removes the split entirely — that is the reason to
    prefer one.

    When the encoder accepts a `global_attention_mask` (Longformer and kin), the
    located span tokens plus position 0 are marked global: otherwise a
    long-context model attends only locally and re-creates the very problem the
    long context was meant to solve.
    """
    import torch

    encoded = tokenizer(
        doc_text,
        return_offsets_mapping=True,
        return_overflowing_tokens=True,
        truncation=True,
        max_length=max_length,
        stride=stride,
        padding=True,
        return_tensors="pt",
    )
    windows = [[tuple(o) for o in window] for window in encoded["offset_mapping"].tolist()]
    located = [locate_span_token(windows, c) for c in char_starts]

    inputs = {
        k: v.to(device)
        for k, v in encoded.items()
        if k in ("input_ids", "attention_mask", "token_type_ids")
    }
    if "global_attention_mask" in signature(encoder.forward).parameters:
        mask = torch.zeros_like(inputs["input_ids"])
        mask[:, 0] = 1  # the pooled <s>, as Longformer's own examples do
        for window, tokens in enumerate(global_attention_positions(located, len(windows))):
            if tokens:
                mask[window, tokens] = 1
        inputs["global_attention_mask"] = mask

    hidden = encoder(**inputs).last_hidden_state  # (n_windows, seq, hidden)
    # Longformer pads internally to a multiple of its attention window. It also
    # un-pads the output — but if a version ever stopped, every token index here
    # would silently point at the wrong position, so check instead of trusting.
    if hidden.shape[1] != inputs["input_ids"].shape[1]:
        raise RuntimeError(
            f"encoder returned {hidden.shape[1]} positions for "
            f"{inputs['input_ids'].shape[1]} input tokens -- span indices would misalign"
        )
    index = torch.tensor(located, device=hidden.device)
    return hidden[index[:, 0], index[:, 1]]


def encode_spans_with_context(
    encoder,
    tokenizer,
    doc_text: str,
    char_starts: Sequence[int],
    context_ranges: Sequence[tuple[int, int]],
    *,
    max_length: int = 512,
    stride: int = 128,
    device: str = "cpu",
) -> tuple[torch.Tensor, torch.Tensor]:
    """Trigger vectors plus a mean-pooled vector over each mention's context range.

    Why a second vector at all: the trigger token is contextualised, but when two
    mentions share the *same word form* their trigger vectors are the hardest case
    for the pair head — and that is exactly where the errors are (51.8% of
    over-merges on official-protocol valid are exact-trigger pairs, and 44.4% of
    under-merges are too). Pooling the surrounding sentence gives the head a
    signal that does not collapse when the trigger word is identical.

    One forward pass is shared with the trigger encoding, so this costs pooling,
    not a second encode. Returns `(triggers, contexts)`, both `(n, hidden)`.
    """
    import torch

    encoded = tokenizer(
        doc_text,
        return_offsets_mapping=True,
        return_overflowing_tokens=True,
        truncation=True,
        max_length=max_length,
        stride=stride,
        padding=True,
        return_tensors="pt",
    )
    windows = [[tuple(o) for o in window] for window in encoded["offset_mapping"].tolist()]
    located = [locate_span_token(windows, c) for c in char_starts]

    inputs = {
        k: v.to(device)
        for k, v in encoded.items()
        if k in ("input_ids", "attention_mask", "token_type_ids")
    }
    hidden = encoder(**inputs).last_hidden_state
    if hidden.shape[1] != inputs["input_ids"].shape[1]:
        raise RuntimeError(
            f"encoder returned {hidden.shape[1]} positions for "
            f"{inputs['input_ids'].shape[1]} input tokens -- span indices would misalign"
        )
    index = torch.tensor(located, device=hidden.device)
    triggers = hidden[index[:, 0], index[:, 1]]

    contexts = []
    for (window, token), (start, end) in zip(located, context_ranges, strict=True):
        offsets = windows[window]
        positions = [
            i
            for i, (s0, e0) in enumerate(offsets)
            if e0 > s0 and s0 >= start and e0 <= end
        ]
        if not positions:
            # The sentence fell outside this window; fall back to the trigger's own
            # position rather than a zero vector, which would be a silent signal.
            positions = [token]
        contexts.append(hidden[window, torch.tensor(positions, device=hidden.device)].mean(dim=0))
    return triggers, torch.stack(contexts)
