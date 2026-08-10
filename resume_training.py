"""
The separate trigger to resume training from the latest checkpoint (as
opposed to save_checkpoint.py, which always starts fresh at step 0).

Finds the checkpoint with the highest global_step under checkpoints/,
restores its model/optimizer state, RNG state, and exact dataloader cursor
(training_state.load_full_checkpoint), and continues training from exactly
the next microbatch -- not from the start of the lane or shard, not
re-drawing the batch that was already trained on.

Proof this is a real resume, not a restart pretending to be one: the
dataloader cursor advances monotonically across runs. Running this script
twice in a row processes two disjoint sets of microbatches, verifiably (see
each run's console output / the shard+rows in stats/training_log.jsonl).

Usage: .venv/bin/python resume_training.py [n_steps]   (default 5 steps)
"""

from __future__ import annotations

import json
import sys

from save_checkpoint import run_opus
from training_state import append_training_log, find_latest_checkpoint, load_full_checkpoint, run_steps, save_full_checkpoint

if __name__ == "__main__":
    n_steps = int(sys.argv[1]) if len(sys.argv) > 1 else 5

    latest = find_latest_checkpoint()
    if latest is None:
        raise SystemExit("no checkpoint found under checkpoints/ -- run save_checkpoint.py first")

    print(f"=== resuming from {latest.name} ===")
    model, schedule, run_id = load_full_checkpoint(latest)
    print(f"restored: run_id={run_id}  global_step={model.step}  "
          f"next_lane={schedule.next_lane_pointer}  "
          f"cursors={ {lane: (c.shard_idx, c.row_idx) for lane, c in schedule.cursors.items()} }")

    print(f"\n=== continuing training: {n_steps} more steps ===")
    records, last_mb = run_steps(model, schedule, n_steps, run_id)
    append_training_log(records)  # appended, not overwritten -- the log spans the whole run across resumes
    print(f"training log appended to stats/training_log.jsonl")

    if last_mb is None:
        raise SystemExit("all lanes exhausted -- nothing left to train on, no new checkpoint saved")

    print("\n=== checkpoint save ===")
    ckpt_dir = save_full_checkpoint(model, schedule, run_id, last_mb)
    print(f"checkpoint written to {ckpt_dir}/ (trainer_state.json + checkpoint_manifest.json)")
    print(json.loads((ckpt_dir / "checkpoint_manifest.json").read_text()))

    print("\n=== OPUS: re-scoring real shards from stats/registry_manifest.jsonl ===")
    decisions = run_opus(ckpt_dir.name)
    for d in decisions:
        print(f"  {d['candidate_id']:24s} score={d['opus_score']:.4f}  status={d['status']:9s}"
              f"  override={d['protected_floor_override']}  eff_tokens={d['effective_token_estimate']}")
    print(f"\n{len(decisions)} OPUS decisions written to stats/opus_decisions.jsonl")
