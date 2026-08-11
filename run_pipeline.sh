#!/usr/bin/env bash
# Runs the full pipeline end to end: raw corpus -> cleaned/deduped/routed/
# PII-scrubbed text -> packed 2048-token training sequences -> a real
# TinyTransformer checkpoint save + OPUS admission scoring pass -> a full
# audit that exercises every subsystem (including its own
# checkpoint/crash/resume/replay/fork cycle) and writes
# submission_artifacts/{run.log,evidence.json,evidence.md,performance.json}.
# Same order and per-track arguments used to build the current routed/,
# shards/, packed/ and submission_artifacts/ output -- this is just a
# convenience wrapper around the individual scripts' own docstrings.
#
# Idempotency notes for reruns:
#   - build_corpus.py / build_web_corpus.py / build_code_corpus.py use a
#     fixed SEED, so re-downloading + re-sampling reproduces the same rows.
#   - submission_artifacts/manifests/shard_manifest.jsonl (provenance.py) is
#     append-only by design -- every full rerun adds a fresh set of records
#     rather than replacing the previous run's. That's the intended
#     audit-trail behavior, not a bug.
#   - submission_artifacts/manifests/registry_manifest.jsonl
#     (tokenize_and_admit.py) and submission_artifacts/ledgers/
#     opus_decisions.jsonl + opus_rejected.jsonl (opus.py, via
#     train_tiny_transformer.py) are fully rewritten each run, since they
#     represent current state, not history. submission_artifacts/ledgers/
#     tt_training_log.jsonl + tt_console.log are APPENDED to, not
#     rewritten -- meant to span every run/resume, each row/entry tagged
#     with (or printed under) its run_id.
#   - train_tiny_transformer.py's run_id/checkpoint_id are freshly
#     generated (a random suffix) every run, so it writes a new
#     submission_artifacts/checkpoints/ckpt-tt-.../ directory each time
#     rather than overwriting the previous one.
#
# This script only runs train_tiny_transformer.py (a fresh training run
# from step 0), not restart.py -- resuming is a separate, on-demand
# trigger by design (see its docstring), not something a from-scratch
# pipeline run should invoke automatically. Run this yourself whenever you
# want to continue from the latest checkpoint:
#   .venv/bin/python restart.py [n_steps]
#
# run_audit.py (the final step) does its own self-contained
# checkpoint/crash/resume/replay/fork cycle internally -- it doesn't
# require train_tiny_transformer.py/restart.py to have been run first, and
# its checkpoints land in submission_artifacts/checkpoints/ alongside (not
# instead of) anything already there.
#
# Usage: ./run_pipeline.sh   (or: bash run_pipeline.sh)

set -euo pipefail
cd "$(dirname "$0")"

PY=.venv/bin/python
STEPS=13
PIPELINE_START=$SECONDS

# Rough guidance, not a promise -- steps 1/2/9 download real data from
# HuggingFace, so their time depends on your connection (network-bound,
# typically several minutes each on a normal connection). Everything else
# is local CPU work on data already on disk (typically well under a
# minute each). Actual per-step timing is measured and printed for real
# as each step finishes, below -- this banner is just what to expect
# before anything has run yet.
echo "=== run_pipeline.sh: $STEPS steps, dataset -> audit ==="
echo "  1  build_corpus.py            (indic download)      network-bound, several min"
echo "  2  build_web_corpus.py        (web download)        network-bound, several min"
echo "  3  quality_filter.py indic                          local, fast"
echo "  4  quality_filter.py web                             local, fast"
echo "  5  minhash_lsh_dedup.py indic                        local, fast"
echo "  6  minhash_lsh_dedup.py web                           local, fast"
echo "  7  language_router.py indic                          local, fast"
echo "  8  language_router.py web                             local, fast"
echo "  9  build_code_corpus.py       (code download)        network-bound, ~1 min"
echo " 10  pii_scrub.py                (all 3 tracks)        local, fast"
echo " 11  tokenize_and_admit.py       (pack + admit)        local, fast"
echo " 12  train_tiny_transformer.py   (train + OPUS)        local, fast"
echo " 13  run_audit.py                (full audit)          local, fast"
echo "  overall: ~15-20 min on a normal connection, almost all of it in steps 1/2/9"
echo "  real per-step timing is printed as each one finishes below"

step_start=$SECONDS
step() {
    if [ "$1" != "1" ]; then
        echo "    (step $((10#$1 - 1)) took $((SECONDS - step_start))s)"
    fi
    step_start=$SECONDS
    echo
    echo "=== [$1/$STEPS] $2 ==="
}

step 1  "build_corpus.py (indic track)";        $PY build_corpus.py
step 2  "build_web_corpus.py (web track)";      $PY build_web_corpus.py
step 3  "quality_filter.py indic";              $PY quality_filter.py indic
step 4  "quality_filter.py web";                $PY quality_filter.py web
step 5  "minhash_lsh_dedup.py indic";           $PY minhash_lsh_dedup.py indic
step 6  "minhash_lsh_dedup.py web";             $PY minhash_lsh_dedup.py web
step 7  "language_router.py indic";             $PY language_router.py indic
step 8  "language_router.py web";               $PY language_router.py web
step 9  "build_code_corpus.py (code track)";    $PY build_code_corpus.py
step 10 "pii_scrub.py (all tracks)";            $PY pii_scrub.py
step 11 "tokenize_and_admit.py (pack + admit)"; $PY tokenize_and_admit.py
step 12 "train_tiny_transformer.py (train + OPUS)"; $PY train_tiny_transformer.py
step 13 "run_audit.py (full audit + evidence)";  $PY run_audit.py
echo "    (step 13 took $((SECONDS - step_start))s)"

echo
echo "=== pipeline complete: total time $((SECONDS - PIPELINE_START))s ==="
echo "corpus:              routed/{indic,web,code}/<lang>/*.txt"
echo "provenance manifest:  submission_artifacts/manifests/shard_manifest.jsonl"
echo "registry manifest:    submission_artifacts/manifests/registry_manifest.jsonl"
echo "packed sequences:     packed/<lane>/*.npz + packed/<lane>/doc_manifest.jsonl"
echo "training log:         submission_artifacts/ledgers/tt_training_log.jsonl"
echo "training console log: submission_artifacts/ledgers/tt_console.log"
echo "checkpoint (resumable state + manifest): submission_artifacts/checkpoints/ckpt-tt-*/{model_state.pt,optimizer_state.pt,trainer_state.json,checkpoint_manifest.json}"
echo "OPUS decisions:       submission_artifacts/ledgers/opus_decisions.jsonl"
echo "OPUS rejected shards: submission_artifacts/ledgers/opus_rejected.jsonl"
echo "audit trail:          submission_artifacts/{run.log,evidence.json,evidence.md,performance.json}"
echo
echo "to resume training from the latest checkpoint:"
echo "  .venv/bin/python restart.py [n_steps]"
