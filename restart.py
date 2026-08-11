"""
The trigger to restart/resume tiny_transformer.py training from the latest
checkpoint under submission_artifacts/checkpoints/ (as opposed to
train_tiny_transformer.py, which always starts fresh with newly initialized
weights).

Restores real model weights, real optimizer momentum buffers, RNG state
(python/numpy/torch), and the exact dataloader cursor
(training_state.TrainingSchedule) from tt_checkpoint.load_full_checkpoint,
then continues training from exactly the next microbatch.

Proof this is a real restart, not a relabeled fresh run: the loss picks up
from where it left off (not back at the random-init loss), and the
dataloader cursor advances monotonically -- running this twice in a row
processes two disjoint sets of microbatches, verifiable in
submission_artifacts/ledgers/tt_training_log.jsonl (every row tagged with
its run_id).

Also re-runs OPUS (still dummy -- see opus.py) over
submission_artifacts/manifests/registry_manifest.jsonl, pointed at the new
checkpoint this resume produces.

Usage: .venv/bin/python restart.py [n_steps]   (default 5 steps)
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import torch

from opus import run_opus
from train_tiny_transformer import TRAINING_LOG, log, to_batch
from tt_checkpoint import find_latest_checkpoint, load_full_checkpoint, save_full_checkpoint

if __name__ == "__main__":
    n_steps = int(sys.argv[1]) if len(sys.argv) > 1 else 5

    latest = find_latest_checkpoint()
    if latest is None:
        raise SystemExit("no checkpoint found under submission_artifacts/checkpoints/ -- run train_tiny_transformer.py first")

    log(f"=== {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')} restarting from {latest.name} ===")
    model, optimizer, schedule, run_id, global_step = load_full_checkpoint(latest)
    log(f"restored: run_id={run_id}  global_step={global_step}  "
        f"next_lane={schedule.next_lane_pointer}  "
        f"cursors={ {lane: (c.shard_idx, c.row_idx) for lane, c in schedule.cursors.items()} }")

    log(f"\n=== continuing training: {n_steps} more steps ===")
    records = []
    last_mb = None
    step = global_step
    for _ in range(n_steps):
        mb = schedule.next_microbatch()
        if mb is None:
            log("  all lanes exhausted -- stopping early")
            break
        token_ids, loss_mask = to_batch(mb, model.config.context_len)

        optimizer.zero_grad()
        loss = model.compute_loss(token_ids, loss_mask)
        loss.backward()
        optimizer.step()

        step += 1
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
        raise SystemExit("all lanes exhausted -- nothing left to train on, no new checkpoint saved")

    Path(TRAINING_LOG).parent.mkdir(parents=True, exist_ok=True)
    with open(TRAINING_LOG, "a", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
    log(f"\ntraining log appended to {TRAINING_LOG}")

    ckpt_dir = save_full_checkpoint(model, optimizer, schedule, run_id, step, last_mb)
    log(f"checkpoint written to {ckpt_dir}/")
    log(json.dumps(json.loads((ckpt_dir / "checkpoint_manifest.json").read_text()), indent=2))

    log("\n=== OPUS (dummy): re-scoring real shards from submission_artifacts/manifests/registry_manifest.jsonl ===")
    decisions = run_opus(ckpt_dir.name)
    for d in decisions:
        log(f"  {d['candidate_id']:24s} score={d['opus_score']:.4f}  status={d['status']:9s}"
            f"  override={d['protected_floor_override']}  eff_tokens={d['effective_token_estimate']}")
    log(f"\n{len(decisions)} OPUS decisions written to submission_artifacts/ledgers/opus_decisions.jsonl")
    n_rejected = sum(1 for d in decisions if d["status"] == "rejected")
    log(f"{n_rejected} rejected shard(s) (shard_id + doc_ids) written to submission_artifacts/ledgers/opus_rejected.jsonl")
