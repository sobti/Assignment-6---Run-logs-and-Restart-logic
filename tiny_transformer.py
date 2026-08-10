"""
A real, small language model in PyTorch: 2 transformer layers, each with
single-head causal self-attention + a feedforward block, weight-tied
embedding/output projection over the project's actual tokenizer vocab
(o200k_base, 200,019 tokens).

Real PyTorch throughout -- nn.Module, autograd (.backward()), torch.optim.
No hand-derived backward pass: an earlier from-scratch NumPy version of
this (see git history / test_tiny_transformer.py) hand-implemented
forward+backward and hit real trouble finite-difference-checking gradients
through ReLU near-zero pre-activations (a well-known gradient-check
artifact, not a wrong derivative) -- switching to autograd sidesteps that
class of problem entirely and is the more standard tool for this anyway.

Deliberately omitted for simplicity (documented, not hidden): LayerNorm,
multi-head attention, dropout. "Two layers, single-layer attention" is a
minimal-but-real architecture, not a production one.

Loss masking reuses this project's established loss_mask convention from
tokenize_and_admit.py: next-token prediction at position t is only scored
if the *target* position (t+1) has loss_mask==1, i.e. PAD positions never
contribute to the loss or gradient.
"""

from __future__ import annotations

from dataclasses import dataclass

import torch
import torch.nn as nn
import torch.nn.functional as F


@dataclass(frozen=True)
class TinyTransformerConfig:
    vocab_size: int = 200_019  # o200k_base's real n_vocab
    d_model: int = 48
    d_ff: int = 96
    n_layers: int = 2
    context_len: int = 64


class SingleHeadCausalAttention(nn.Module):
    """One attention head (not one of several -- "single-layer attention"
    per block, as requested). Uses torch's fused scaled_dot_product_attention
    (is_causal=True) rather than hand-rolled matmuls -- same computation,
    real autograd support, no separate causal-mask tensor to manage."""

    def __init__(self, d_model: int):
        super().__init__()
        self.q_proj = nn.Linear(d_model, d_model, bias=False)
        self.k_proj = nn.Linear(d_model, d_model, bias=False)
        self.v_proj = nn.Linear(d_model, d_model, bias=False)
        self.out_proj = nn.Linear(d_model, d_model, bias=False)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        q, k, v = self.q_proj(x), self.k_proj(x), self.v_proj(x)
        # (batch, 1, seq, d_model) -- a "1" head dimension, since this is
        # single-head, not multi-head split across d_model.
        q, k, v = (t.unsqueeze(1) for t in (q, k, v))
        ctx = F.scaled_dot_product_attention(q, k, v, is_causal=True)
        ctx = ctx.squeeze(1)
        return self.out_proj(ctx)


class TransformerBlock(nn.Module):
    def __init__(self, config: TinyTransformerConfig):
        super().__init__()
        self.attn = SingleHeadCausalAttention(config.d_model)
        self.ff = nn.Sequential(
            nn.Linear(config.d_model, config.d_ff),
            nn.ReLU(),
            nn.Linear(config.d_ff, config.d_model),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = x + self.attn(x)
        x = x + self.ff(x)
        return x


class TinyTransformer(nn.Module):
    def __init__(self, config: TinyTransformerConfig):
        super().__init__()
        self.config = config
        self.token_emb = nn.Embedding(config.vocab_size, config.d_model)
        self.pos_emb = nn.Embedding(config.context_len, config.d_model)
        self.blocks = nn.ModuleList([TransformerBlock(config) for _ in range(config.n_layers)])
        # No separate output layer: logits = x @ token_emb.weight.T (tied),
        # applied via F.linear in forward().
        nn.init.normal_(self.token_emb.weight, std=0.02)
        nn.init.normal_(self.pos_emb.weight, std=0.02)

    def forward(self, token_ids: torch.Tensor) -> torch.Tensor:
        """token_ids: (batch, seq_len) int64. Returns logits (batch, seq_len, vocab_size)."""
        batch, seq_len = token_ids.shape
        positions = torch.arange(seq_len, device=token_ids.device).unsqueeze(0).expand(batch, seq_len)
        x = self.token_emb(token_ids) + self.pos_emb(positions)
        for block in self.blocks:
            x = block(x)
        return F.linear(x, self.token_emb.weight)  # weight-tied output projection

    def compute_loss(self, token_ids: torch.Tensor, loss_mask: torch.Tensor) -> torch.Tensor:
        """Masked next-token cross-entropy, same loss_mask convention as
        packed/<lane>/*.npz: PAD positions (loss_mask==0) never contribute."""
        logits = self.forward(token_ids)
        pred_logits = logits[:, :-1, :]
        targets = token_ids[:, 1:]
        target_mask = loss_mask[:, 1:].float()

        losses = F.cross_entropy(
            pred_logits.reshape(-1, self.config.vocab_size), targets.reshape(-1), reduction="none"
        ).reshape(targets.shape)
        n_valid = target_mask.sum().clamp(min=1.0)
        return (losses * target_mask).sum() / n_valid
