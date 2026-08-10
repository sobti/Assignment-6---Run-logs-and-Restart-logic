"""
OPUS: a dummy data-admission scoring pass over every real shard in
submission_artifacts/manifests/registry_manifest.jsonl, pointed at whichever
checkpoint the calling script (train_tiny_transformer.py / restart.py /
run_audit.py) just produced.

OPUS itself doesn't exist as a real system in this project -- there is no
trained proxy model. See opus_score()'s docstring for exactly what's mocked
(the scoring formula) vs grounded in real data (the signals it's computed
from).

Usage: imported by train_tiny_transformer.py and restart.py, not run directly.
"""

from __future__ import annotations

import hashlib
import inspect
import json
from pathlib import Path

REGISTRY_MANIFEST = Path("submission_artifacts/manifests/registry_manifest.jsonl")
OPUS_MANIFEST = Path("submission_artifacts/ledgers/opus_decisions.jsonl")

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

    OPUS_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    with OPUS_MANIFEST.open("w", encoding="utf-8") as f:
        for d in decisions:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")
    return decisions
