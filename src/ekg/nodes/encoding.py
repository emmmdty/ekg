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

__all__ = [
    "TORCH_AVAILABLE",
    "OffsetMapping",
    "locate_span_token",
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
    hidden = encoder(**inputs).last_hidden_state  # (n_windows, seq, hidden)
    index = torch.tensor(located, device=hidden.device)
    return hidden[index[:, 0], index[:, 1]]
