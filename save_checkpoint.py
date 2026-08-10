"""
Starts a fresh (dummy) training run from step 0 and saves a checkpoint that
captures everything training_state.py considers necessary to resume from
exactly that point: model/optimizer state, RNG state, and the exact
dataloader cursor (lane, shard, row) for the next microbatch. To continue
training from the checkpoint this writes, run resume_training.py -- a
separate script/trigger, as requested, rather than a flag on this one.

Also runs OPUS (a dummy data-admission scoring pass) over every real shard
in stats/registry_manifest.jsonl, using the checkpoint just saved as its
nominal "scoring checkpoint". OPUS itself doesn't exist as a real system in
this project -- see opus_score()'s docstring for exactly what's mocked vs
grounded in real data.

Usage: .venv/bin/python save_checkpoint.py [n_steps]   (default 5 steps)
"""

from __future__ import annotations

import hashlib
import inspect
import json
import sys
import uuid
from pathlib import Path

from training_state import DummyModel, TrainingSchedule, append_training_log, run_steps, save_full_checkpoint

REGISTRY_MANIFEST = Path("stats/registry_manifest.jsonl")
OPUS_MANIFEST = Path("stats/opus_decisions.jsonl")

# Data protected from being scored out regardless of OPUS score -- code is
# by far the smallest lane (25.8% of tokens vs 50/22 for web/indic; see
# build_code_corpus.py's docstring on why it can't be scaled up), so a
# perplexity-style proxy that systematically favors prose could starve it
# entirely without an explicit floor.
PROTECTED_LANES = {"Code"}


def opus_score(shard: dict) -> float:
    """Illustrative-only scoring formula -- there is no trained proxy model
    in this project. Grounded in real signals already computed by
    tokenize_and_admit.py (eval_overlap_status, license_tier, token_count),
    plus a deterministic (not random) jitter derived from the shard_id so
    scores aren't all identical, and reruns are reproducible."""
    if shard["eval_overlap_status"] != "clear":
        return 0.0
    if shard["license_tier"] != "safe":
        return 0.1
    size_component = min(1.0, shard["token_count"] / 1_000_000)
    jitter = (int(hashlib.sha256(shard["shard_id"].encode()).hexdigest()[:8], 16) % 1000) / 1000.0
    return round(0.5 * size_component + 0.5 * jitter, 4)


def opus_decide(shard: dict, checkpoint_id: str, proxy_version: str) -> dict:
    score = opus_score(shard)
    lane = shard["capability_lane"]
    protected = lane in PROTECTED_LANES

    if protected:
        status, reason, override = "accepted", None, True
    elif score >= 0.7:
        status, reason, override = "accepted", None, False
    elif score >= 0.4:
        status, reason, override = "deferred", "borderline_score_pending_review", False
    else:
        status, reason, override = "rejected", "score_below_admission_threshold", False

    quality_weight = 0.5 + 0.5 * score  # dummy: low-scoring shards count for less of their raw tokens
    effective_token_estimate = round(shard["token_count"] * quality_weight)

    return {
        "candidate_id": f"cand-{shard['shard_id']}",
        "shard_ids": [shard["shard_id"]],
        "capability_lane": lane,
        "curriculum_stage": "stage_0_uniform",
        "model_checkpoint_used_for_scoring": checkpoint_id,
        "proxy_version": proxy_version,
        "opus_score": score,
        "status": status,
        "rejection_reason": reason,
        "protected_floor_override": override,
        "effective_token_estimate": effective_token_estimate,
    }


def run_opus(checkpoint_id: str) -> list[dict]:
    proxy_version = "proxy_" + hashlib.sha256(inspect.getsource(opus_score).encode()).hexdigest()[:12]
    shards = [json.loads(line) for line in REGISTRY_MANIFEST.read_text().splitlines() if line.strip()]
    decisions = [opus_decide(s, checkpoint_id, proxy_version) for s in shards]

    OPUS_MANIFEST.parent.mkdir(exist_ok=True)
    with OPUS_MANIFEST.open("w", encoding="utf-8") as f:
        for d in decisions:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")
    return decisions


if __name__ == "__main__":
    n_steps = int(sys.argv[1]) if len(sys.argv) > 1 else 5

    run_id = f"run-v5-{uuid.uuid4().hex[:8]}"
    model = DummyModel()
    schedule = TrainingSchedule.fresh()

    print(f"=== fresh training run {run_id}: {n_steps} steps ===")
    records, last_mb = run_steps(model, schedule, n_steps, run_id)
    append_training_log(records)
    print(f"training log appended to stats/training_log.jsonl")

    if last_mb is None:
        raise SystemExit("no steps ran -- nothing to checkpoint")

    print("\n=== checkpoint save ===")
    ckpt_dir = save_full_checkpoint(model, schedule, run_id, last_mb)
    print(f"checkpoint written to {ckpt_dir}/ (trainer_state.json + checkpoint_manifest.json)")
    print(json.loads((ckpt_dir / "checkpoint_manifest.json").read_text()))

    print("\n=== OPUS: scoring real shards from stats/registry_manifest.jsonl ===")
    checkpoint_id = ckpt_dir.name
    decisions = run_opus(checkpoint_id)
    for d in decisions:
        print(f"  {d['candidate_id']:24s} score={d['opus_score']:.4f}  status={d['status']:9s}"
              f"  override={d['protected_floor_override']}  eff_tokens={d['effective_token_estimate']}")
    print(f"\n{len(decisions)} OPUS decisions written to {OPUS_MANIFEST}")
