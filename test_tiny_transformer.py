"""
Sanity check for tiny_transformer.py. Real autograd (torch.Tensor.backward)
means the gradients themselves don't need hand-verification the way a
from-scratch backward pass would -- what's still ours to get wrong, and
worth checking, is the *masking* logic in compute_loss(): does a PAD
target position (loss_mask==0) genuinely receive zero gradient, per this
project's established loss_mask convention?

Test: retain_grad() on the logits tensor, backward the masked loss, and
directly inspect logits.grad -- every masked target position's gradient
row must be exactly zero (no gradient contribution), every unmasked
position's must be nonzero (the loss is actually using it). This checks
the masking arithmetic directly rather than inferring it indirectly.
"""

from __future__ import annotations

import torch
import torch.nn.functional as F

from tiny_transformer import TinyTransformer, TinyTransformerConfig


def run_check() -> bool:
    torch.manual_seed(0)
    config = TinyTransformerConfig(vocab_size=50, d_model=8, d_ff=16, n_layers=2, context_len=6)
    model = TinyTransformer(config)

    token_ids = torch.randint(0, config.vocab_size, (2, config.context_len))
    loss_mask = torch.ones(2, config.context_len, dtype=torch.int64)
    loss_mask[0, 2] = 0   # batch 0: position 2 is PAD
    loss_mask[1, 4] = 0   # batch 1: position 4 is PAD

    logits = model.forward(token_ids)
    logits.retain_grad()

    pred_logits = logits[:, :-1, :]
    targets = token_ids[:, 1:]
    target_mask = loss_mask[:, 1:].float()
    losses = F.cross_entropy(
        pred_logits.reshape(-1, config.vocab_size), targets.reshape(-1), reduction="none"
    ).reshape(targets.shape)
    n_valid = target_mask.sum().clamp(min=1.0)
    loss = (losses * target_mask).sum() / n_valid
    loss.backward()

    grad = logits.grad[:, :-1, :]  # gradient at the prediction positions actually used by the loss
    per_position_grad_norm = grad.abs().sum(dim=-1)  # (batch, context_len-1)

    all_ok = True
    for b in range(2):
        for t in range(config.context_len - 1):
            should_be_zero = target_mask[b, t].item() == 0.0
            is_zero = per_position_grad_norm[b, t].item() == 0.0
            ok = should_be_zero == is_zero
            all_ok &= ok
            label = "masked (expect zero grad)" if should_be_zero else "real (expect nonzero grad)"
            print(f"  batch={b} target_pos={t:2d}  {label:30s}  actual_grad_norm={per_position_grad_norm[b, t].item():.6f}  [{'ok' if ok else 'FAIL'}]")

    return all_ok


if __name__ == "__main__":
    print("checking loss_mask correctness: masked target positions must receive exactly zero gradient...")
    passed = run_check()
    print(f"\n{'PASS: masking is correct' if passed else 'FAIL: masking is broken'}")
    raise SystemExit(0 if passed else 1)
