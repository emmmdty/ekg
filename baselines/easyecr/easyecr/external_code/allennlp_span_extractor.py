"""Minimal Apache-2.0-compatible port of AllenNLP's self-attentive span extractor.

EasyECR's pinned torch/transformers stack cannot resolve an AllenNLP release that
provides this class.  Global-Local Topic uses its default, no-width-embedding
configuration only, so this module ports exactly that execution path from
AllenNLP v2.10.1 instead of changing the published model.
"""

from __future__ import annotations

import torch
from torch import nn


class SelfAttentiveSpanExtractor(nn.Module):
    """Pool inclusive token spans using a globally learned scalar attention."""

    def __init__(self, input_dim: int) -> None:
        super().__init__()
        self._input_dim = input_dim
        self._global_attention = nn.Linear(input_dim, 1)

    def get_output_dim(self) -> int:
        return self._input_dim

    def forward(
        self,
        sequence_tensor: torch.Tensor,
        span_indices: torch.Tensor,
        sequence_mask: torch.Tensor | None = None,
        span_indices_mask: torch.Tensor | None = None,
    ) -> torch.Tensor:
        del sequence_mask
        if sequence_tensor.ndim != 3:
            raise ValueError("sequence_tensor must have shape (batch, sequence, embedding)")
        if span_indices.ndim != 3 or span_indices.shape[-1] != 2:
            raise ValueError("span_indices must have shape (batch, spans, 2)")
        if sequence_tensor.shape[0] != span_indices.shape[0]:
            raise ValueError("sequence_tensor and span_indices batch sizes differ")
        if span_indices.dtype != torch.long:
            raise ValueError("span_indices must use torch.long")

        span_starts, span_ends = span_indices.unbind(dim=-1)
        widths = span_ends - span_starts
        if torch.any(widths < 0):
            raise ValueError("span end precedes span start")
        max_width = int(widths.max().item()) + 1
        offsets = torch.arange(max_width, device=sequence_tensor.device).view(1, 1, -1)
        raw_indices = span_starts.unsqueeze(-1) + offsets
        valid_tokens = (offsets <= widths.unsqueeze(-1)) & (raw_indices < sequence_tensor.shape[1])
        valid_tokens &= raw_indices >= 0
        safe_indices = raw_indices.masked_fill(~valid_tokens, 0)

        batch_indices = torch.arange(sequence_tensor.shape[0], device=sequence_tensor.device).view(-1, 1, 1)
        span_embeddings = sequence_tensor[batch_indices, safe_indices]
        attention_logits = self._global_attention(sequence_tensor).squeeze(-1)[batch_indices, safe_indices]
        masked_logits = attention_logits.masked_fill(~valid_tokens, torch.finfo(attention_logits.dtype).min)
        attention = torch.softmax(masked_logits, dim=-1) * valid_tokens
        attended = (span_embeddings * attention.unsqueeze(-1)).sum(dim=-2)

        if span_indices_mask is not None:
            if span_indices_mask.shape != span_indices.shape[:2]:
                raise ValueError("span_indices_mask must have shape (batch, spans)")
            attended = attended * span_indices_mask.unsqueeze(-1)
        return attended
