"""
Trains the real tiny_transformer.py model (2 layers, single-head causal
attention) for a handful of steps on real packed training data, then stops
and saves a checkpoint. Always starts fresh at step 0 with freshly
initialized weights -- to continue from a checkpoint this writes, run
restart.py (a separate trigger, as requested), not this script again.

Data: real microbatches from packed/<lane>/*.npz via training_state.py's
TrainingSchedule (round-robins indic/web/code deterministically), each row
sliced to the model's context_len (64) out of the full 2048-token packed
sequence -- "just a few data" per this task's ask, not the whole corpus.

Also runs OPUS (opus.py's dummy data-admission scoring pass -- no real proxy
model exists in this project, see that module's docstring) over every real
shard in submission_artifacts/manifests/registry_manifest.jsonl, using this
run's checkpoint as the nominal "scoring checkpoint".

Usage: .venv/bin/python train_tiny_transformer.py [n_steps]   (default 5)
"""

from __future__ import annotations

import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

import torch

from opus import run_opus
from tiny_transformer import TinyTransformer, TinyTransformerConfig
from training_state import TrainingSchedule
from tt_checkpoint import save_full_checkpoint

TRAINING_LOG = "submission_artifacts/ledgers/tt_training_log.jsonl"
CONSOLE_LOG = Path("submission_artifacts/ledgers/tt_console.log")
LEARNING_RATE = 0.1
MOMENTUM = 0.9
SEED = 0


def log(msg: str = "") -> None:
    """Prints msg and appends it to CONSOLE_LOG -- the human-readable
    narrative companion to TRAINING_LOG's structured per-step rows, appended
    to (not overwritten) so it spans fresh runs and resumes the same way."""
    print(msg)
    CONSOLE_LOG.parent.mkdir(parents=True, exist_ok=True)
    with CONSOLE_LOG.open("a", encoding="utf-8") as f:
        f.write(msg + "\n")


def to_batch(mb: dict, context_len: int) -> tuple[torch.Tensor, torch.Tensor]:
    token_ids = torch.from_numpy(mb["token_id"][:, :context_len].astype("int64"))
    loss_mask = torch.from_numpy(mb["loss_mask"][:, :context_len].astype("int64"))
    return token_ids, loss_mask


if __name__ == "__main__":
    n_steps = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    run_id = f"run-tt-{uuid.uuid4().hex[:8]}"

    torch.manual_seed(SEED)
    config = TinyTransformerConfig()
    model = TinyTransformer(config)
    optimizer = torch.optim.SGD(model.parameters(), lr=LEARNING_RATE, momentum=MOMENTUM)
    schedule = TrainingSchedule.fresh()

    n_params = sum(p.numel() for p in model.parameters())
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    log(f"=== {ts} fresh run {run_id}: TinyTransformer({config}) ===")
    log(f"    {n_params:,} parameters, SGD(lr={LEARNING_RATE}, momentum={MOMENTUM})")
    log(f"=== training {n_steps} steps ===")

    records = []
    last_mb = None
    for step in range(1, n_steps + 1):
        mb = schedule.next_microbatch()
        if mb is None:
            log("  all lanes exhausted -- stopping early")
            break
        token_ids, loss_mask = to_batch(mb, config.context_len)

        optimizer.zero_grad()
        loss = model.compute_loss(token_ids, loss_mask)
        loss.backward()
        optimizer.step()

        loss_val = loss.item()
        perplexity = float(torch.exp(loss.detach()))
        last_mb = mb
        record = {
            "run_id": run_id, "step": step, "lane": mb["lane"], "shard_id": mb["shard_id"],
            "rows": mb["rows"], "loss": round(loss_val, 4), "perplexity": round(perplexity, 4),
        }
        records.append(record)
        log(f"  step {step:4d}  lane={mb['lane']:6s}  shard={mb['shard_id']:20s}"
            f"  loss={loss_val:.4f}  perplexity={perplexity:.4f}")

    if last_mb is None:
        raise SystemExit("no steps ran -- nothing to checkpoint")

    Path(TRAINING_LOG).parent.mkdir(parents=True, exist_ok=True)
    with open(TRAINING_LOG, "a", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
    log(f"\ntraining log appended to {TRAINING_LOG}")

    ckpt_dir = save_full_checkpoint(model, optimizer, schedule, run_id, step, last_mb)
    log(f"checkpoint written to {ckpt_dir}/")
    log(f"  model_state.pt, optimizer_state.pt (real torch state_dicts)")
    log(f"  trainer_state.json (RNG + dataloader cursor + config + integrity hashes)")
    log(f"  checkpoint_manifest.json:")
    log(json.dumps(json.loads((ckpt_dir / "checkpoint_manifest.json").read_text()), indent=2))

    log("\n=== OPUS (dummy): scoring real shards from submission_artifacts/manifests/registry_manifest.jsonl ===")
    decisions = run_opus(ckpt_dir.name)
    for d in decisions:
        log(f"  {d['candidate_id']:24s} score={d['opus_score']:.4f}  status={d['status']:9s}"
            f"  override={d['protected_floor_override']}  eff_tokens={d['effective_token_estimate']}")
    log(f"\n{len(decisions)} OPUS decisions written to submission_artifacts/ledgers/opus_decisions.jsonl")
    n_rejected = sum(1 for d in decisions if d["status"] == "rejected")
    log(f"{n_rejected} rejected shard(s) (shard_id + doc_ids) written to submission_artifacts/ledgers/opus_rejected.jsonl")
