# Corpus Pipeline

Builds a three-lane (web / indic / code) pretraining corpus from public
sources, cleans and deduplicates it, packs it into fixed-length training
sequences, trains a real small model on it with resumable checkpoints, and
produces the provenance, admission, and audit evidence needed to treat the
result as training-ready data.

## Quick start

```
python3 -m venv .venv          # skip if .venv/ already exists
.venv/bin/pip install -r requirements.txt
./run_pipeline.sh
```

Every script in this project runs via `.venv/bin/python` explicitly (see
`run_pipeline.sh`), not whatever `python`/`pip` happens to be first on your
`PATH` — so install with `.venv/bin/pip`, not a bare `pip install`, or
`run_pipeline.sh` will fail with `ModuleNotFoundError` even though the
install "succeeded" (into the wrong Python). `.venv/` itself isn't checked
into git, so a fresh clone needs the `python3 -m venv .venv` step; skip it
if `.venv/` is already there.

That's it from there — one command runs everything, dataset to audit: downloads and
cleans all three lanes, dedupes, routes, PII-scrubs, tokenizes and packs
into 2048-token training sequences, trains a dummy checkpoint pass + OPUS
scoring, then runs a full audit (`run.log`, `evidence.json`, `evidence.md`).

Before it runs, it prints all 13 steps with rough timing guidance; as each
step finishes it prints how long that step actually took, and a total at
the end. Expect ~3GB of downloads and 15-20+ minutes on a fresh run —
almost all of it in the three download steps (1, 2, 9); everything else is
local CPU work on data already on disk and finishes in seconds.

### How to restart training if it stops

This project has **two separate training systems**, each with its own
checkpoint format and its own resume trigger — use the one matching what
you were running:

| | Fresh run | Resume/restart |
|---|---|---|
| Dummy scalar model (toy, `training_state.py`) | `.venv/bin/python save_checkpoint.py [n_steps]` | `.venv/bin/python resume_training.py [n_steps]` |
| **Real TinyTransformer** (PyTorch, `tiny_transformer.py`) | `.venv/bin/python train_tiny_transformer.py [n_steps]` | `.venv/bin/python restart.py [n_steps]` |

Both resume scripts work the same way: find the checkpoint with the
highest `global_step` under their checkpoint directory
(`checkpoints/` for the dummy model, `checkpoints_tt/` for
TinyTransformer), restore model weights, optimizer state, RNG state
(python/numpy/torch), and the *exact* dataloader position (which lane,
which shard, which row) from it, and continue training from precisely the
next microbatch — never repeating or skipping data. Neither is part of
`run_pipeline.sh`; resuming is deliberately a separate, on-demand action
you trigger yourself, not something a from-scratch pipeline run should do
automatically.

```
# example: interrupt training after a few steps, then continue it
.venv/bin/python train_tiny_transformer.py 5     # trains steps 1-5, saves a checkpoint, stops
.venv/bin/python restart.py 5                     # finds that checkpoint, trains steps 6-10, saves a new one
```

To verify a restart genuinely continued (rather than quietly starting
over), check `stats/tt_training_log.jsonl` (or `stats/training_log.jsonl`
for the dummy model) — every row is tagged with its `run_id` and the exact
`shard_id`/`rows` it trained on; a real resume never repeats a
`(lane, shard_id, rows)` tuple across the fresh-run/resume boundary.
`run_audit.py`'s `resume_next_batch_matched` and `replay_hash_matched`
checks verify this automatically every pipeline run (see below).

## Lanes

| Lane | Source | Languages | Why |
|---|---|---|---|
| **web** | `ai4bharat/sangraha`, `unverified` split | Hindi, Tamil, Telugu, Bengali | raw/OCR-crawled web text, least curated of the three |
| **indic** | `ai4bharat/sangraha`, `verified` split | Hindi, Tamil, Telugu, Bengali, English | curated prose |
| **code** | `bigcode/the-stack-smol-xs` | 15 mainstream languages (Python, JS, TS, Java, C, C++, C#, Go, Rust, Ruby, PHP, HTML, CSS, SQL, Shell) | ungated permissively-licensed source samples |

Target ratio is **web 50% / indic 25% / code 25% by token count** (not
document count — code and prose have very different tokens/doc). Code's
dataset is hard-capped at ~100 raw samples/language, so its final token
count (~5.18M) anchors the total budget the other two lanes were sized
against. Actual achieved split: **web 52.0% / indic 22.1% / code 25.8%** —
close, not exact, since it's calibrated from a prior run's tokens/doc
rather than solved for precisely (`run_audit.py`'s `mixture_within_tolerance`
check allows ±10 percentage points). See `build_corpus.py` /
`build_web_corpus.py` docstrings for the derivation.

Current corpus size (post quality-filter, dedup, routing, PII scrub):

```
indic:  5,696 docs   4,433,046 tokens   routed/indic/{hindi,bengali,tamil,telugu,english}/
web:   11,608 docs  10,426,066 tokens   routed/web/{hindi,bengali,tamil,telugu}/   (no English split exists upstream)
code:   1,422 docs   5,179,105 tokens   routed/code/{python,javascript,...15 langs}/
```

## Pipeline stages

`run_pipeline.sh` runs these 13 steps in order:

1-2. **`build_corpus.py`** / **`build_web_corpus.py`** — download one
   Sangraha shard per language at a time (deleted from the HF cache
   immediately after sampling to keep peak disk low), clean via
   `indic_normalize.py`, count tokens with tiktoken (`o200k_base`), write
   output as shards instead of one monolithic file.
3-4. **`quality_filter.py [indic|web]`** — Gopher/MassiveText-style corpus
   heuristics (word count, symbol ratio, n-gram repetition, MLTD, Flesch,
   boilerplate-line detection, ...), thresholds sanity-checked against this
   corpus's own percentile distribution at run time.
5-6. **`minhash_lsh_dedup.py [indic|web]`** — from-scratch MinHash + LSH
   near-duplicate detection (character shingles, so it works across
   scripts without per-language tokenization rules).
7-8. **`language_router.py [indic|web]`** — routes each doc by *detected*
   script purity (not the source label), discarding anything <80% one
   target language. Also doubles as a QC pass against Sangraha's own
   labels (see the printed agreement %).
9. **`build_code_corpus.py`** — code gets its own single-script pipeline
   instead of reusing steps 3-8, because code breaks their assumptions
   differently: whitespace-collapsing normalization would wreck
   indentation, NLP quality metrics (Flesch, akshara counts) don't mean
   anything for source code, and script-purity routing would just dump
   everything into "english". Uses code-appropriate checks instead
   (comment/blank-line ratio) and reuses `minhash_lsh_dedup`'s shingle/
   MinHash functions directly (those *are* language-agnostic).
10. **`pii_scrub.py`** — regex + checksum-validated PII redaction (email,
   URL, IPv4, Indian PAN, phone, Aadhaar via Verhoeff, credit cards via
   Luhn) over every routed `.txt` file, across all three lanes. The only
   stage allowed to mark data "OK" (training-ready) rather than "BLOCKED".
11. **`tokenize_and_admit.py`** — tokenizes with `o200k_base`, packs
   documents into fixed 2048-token sequences (Best-Fit-Decreasing bin
   packing for indic/web; code is *never* combined across files — see
   below), runs a real eval-set contamination check, and admits/holds each
   shard.
12. **`save_checkpoint.py`** — a dummy scalar-model training loop over the
   packed data (real resumable checkpoint state, toy model) + OPUS scoring.
13. **`run_audit.py`** — exercises every subsystem above plus a full real
   TinyTransformer checkpoint/crash/resume/replay/fork cycle, and writes
   `run.log` + `evidence.json` + `evidence.md`.

## Provenance: two manifests, different purposes

- **`stats/shard_manifest.jsonl`** (via `provenance.py`) — one record per
  ~2,000-doc shard at *every* cleaning stage. Schema:
  `shard_id, source_url, license_class, contributor_id, cleaning_script,
  cleaning_script_hash, ingest_timestamp, sha256, token_count,
  lang_distribution, status`. `status` is `"BLOCKED"` for every stage
  before PII scrub, `"OK"` only after — it's a training-readiness flag, not
  a per-stage success flag. `source_url` is always the real HF URL the
  shard came from, never a placeholder.
- **`stats/registry_manifest.jsonl`** (via `tokenize_and_admit.py`) — one
  record per *tokenized* shard (~500 packed sequences each), the final
  admission decision: `tokenizer_hash, content_hash, cleaning_pipeline_hash,
  dedup_status, pii_screen_status, eval_overlap_status, license_tier,
  parent_manifest_ids (currently always []), admission`.
  `eval_overlap_status` is a real 13-word n-gram contamination check
  against `openai_humaneval` (code) or `ai4bharat/IndicSentiment`
  (indic/web) — not a placeholder.

Both hash the *actual* script/content bytes at run time (`script_hash()`),
so a manifest record is tied to the exact code that produced it, not a
version string that can drift out of sync.

## Packed training sequences

`packed/<lane>/v5_<lane>_shard_NNN.npz` — each holds four `(500, 2048)`
arrays:

- `token_id` (int32) — real tokens, EOS separators, and PAD (PAD reuses the
  EOS id `199999`, distinguished by `loss_mask`).
- `loss_mask` (uint8) — `1` on every real token *and* every EOS (predicting
  "this document just ended" is a real training signal), `0` only on
  trailing PAD.
- `position_id` (int32) — flat `0..2047`, not reset at document boundaries.
- `doc_id` (int32) — which source document each token came from (index
  into `packed/<lane>/doc_manifest.jsonl`); `-1` on PAD positions.

**Packing**: indic/web documents are combined via Best-Fit-Decreasing bin
packing (sort longest-first, place each into the open sequence with the
smallest remaining room that still fits) — 99.88%/99.89% packing
efficiency, under 0.2% wasted to padding. **Code is never combined across
files** — one file (or one file's sequential windows, if it's longer than
2048 tokens) per sequence, so two unrelated source files never end up
back-to-back with no boundary signal. That costs code ~28% padding (71.94%
packed); it's the deliberate tradeoff for not silently blending unrelated
files. Recompute these yourself any time with `stats/shard_sequence_counts.json`.

```
indic:  2,170 sequences (5 shards)   4,438,742 real tokens
web:    5,102 sequences (11 shards) 10,437,674 real tokens
code:   3,516 sequences (8 shards)   5,180,527 real tokens
total: 10,788 sequences (24 shards) 20,056,943 real tokens
```

`stats/shard_sequence_counts.json` has the same breakdown as structured JSON.

## Two training systems

### 1. Dummy scalar model (`training_state.py`)

A toy stand-in: one scalar "weight" updated by a momentum rule, real RNG
snapshotting, a real deterministic data iterator. Nothing here learns
anything meaningful — it exists to demonstrate the checkpoint/resume
mechanics cheaply before doing the same thing with a real model.

- **`save_checkpoint.py [n_steps]`** — starts a *fresh* run (step 0),
  trains for `n_steps` (default 5), writes
  `checkpoints/ckpt-<run_id>-step<N>/{trainer_state.json,checkpoint_manifest.json}`,
  then runs OPUS scoring (see below).
- **`resume_training.py [n_steps]`** — finds the checkpoint with the
  highest `global_step`, restores everything, continues from the exact
  next microbatch, then re-runs OPUS pointed at the new checkpoint.

`trainer_state.json` has everything needed to resume: model/optimizer
state, RNG state, exact dataloader cursor (lane/shard/row), and
code-version hashes. `checkpoint_manifest.json` is the human-auditable
15-field record (`run_id, branch_id, global_step, checkpoint_id, rank,
microbatch_id, packed_sample_ids, shard_ids, token_span_ids,
loss_mask_hash, attention_and_position_policy, mixture_lane,
curriculum_stage, tokenizer_version, dataloader_version,
opus_decision_id`).

### 2. Real TinyTransformer (`tiny_transformer.py`)

A real, small PyTorch language model: 2 transformer layers, each with
single-head causal self-attention (`torch.nn.functional.
scaled_dot_product_attention`, `is_causal=True`) + a feedforward block,
weight-tied embedding/output over the real `o200k_base` vocab (200,019
tokens; 9,641,136 total parameters). Real `.backward()`, real
`torch.optim.SGD(lr=0.1, momentum=0.9)` — no hand-derived gradients (an
earlier from-scratch NumPy version hand-implemented backprop and hit a
textbook ReLU-kink finite-difference gradient-check artifact; switching to
autograd sidesteps that). `test_tiny_transformer.py` verifies the
`loss_mask` masking logic directly via gradient introspection (masked
positions get exactly-zero gradient) — run it any time.

- **`train_tiny_transformer.py [n_steps]`** — fresh run, trains
  `n_steps` (default 5) on real microbatches from `packed/`, writes
  `checkpoints_tt/ckpt-tt-<run_id>-step<N>/{model_state.pt,
  optimizer_state.pt, trainer_state.json, checkpoint_manifest.json}`,
  then runs OPUS.
- **`restart.py [n_steps]`** — the separate resume trigger: finds the
  latest checkpoint, restores real weights + optimizer momentum + RNG +
  dataloader cursor, verifies the two `.pt` files' sha256 hashes match
  what `trainer_state.json` recorded (fails loudly on a corrupted
  checkpoint rather than silently loading bad weights), continues
  training, then re-runs OPUS.

`model_state.pt`/`optimizer_state.pt` are real `torch.save()` state
dicts — the standard way to checkpoint a PyTorch model, not reinvented as
JSON. Verified replayable end to end: a fresh run + a restart produce zero
duplicate `(lane, shard_id, rows)` tuples across the boundary, and
`run_audit.py`'s `replay_hash_matched` check confirms reloading the same
checkpoint twice and rerunning identical steps twice produces
byte-identical final weights.

### OPUS (both systems)

`opus_score`/`opus_decide`/`run_opus` in `save_checkpoint.py` — a dummy
data-admission scoring pass over every real shard in
`stats/registry_manifest.jsonl` → `stats/opus_decisions.jsonl`
(`candidate_id, shard_ids, capability_lane, curriculum_stage,
model_checkpoint_used_for_scoring, proxy_version, opus_score, status,
rejection_reason, protected_floor_override, effective_token_estimate`).
There is no trained proxy model — the score is an illustrative formula
over real signals (shard size, `eval_overlap_status`, `license_tier`) plus
a deterministic per-shard jitter. **Code has a protected-floor override**:
it's force-accepted regardless of score, since it's the smallest lane
(25.8% of tokens) and a size-favoring formula would otherwise starve it
inconsistently. Both `save_checkpoint.py`/`resume_training.py` (dummy
model) and `train_tiny_transformer.py`/`restart.py` (real model) run this
same OPUS pass, pointed at whichever checkpoint they just produced.

## Audit & evidence (`run_audit.py`)

The pipeline's last step. Exercises every subsystem above against real
artifacts on disk, plus a few deliberately-constructed real test cases
(not hardcoded passes), and writes:

- **`run.log`** — the full timestamped event sequence: shards created,
  manifests validated, evaluation data blocked, mixture compiled, batches
  packed, OPUS decisions recorded, checkpoint saved, crash simulated, run
  resumed, historical stream replayed, branch forked, audit completed,
  performance measured. `[PASS]`/`[FAIL]` tagged checks include
  `tokenizer_hash_verified`, `eval_shard_blocked`, `checkpoint_saved`,
  `resume_next_batch_matched`, `replay_hash_matched`, and more.
- **`evidence.json`** — machine-readable: every requirement, pass/fail,
  and exactly where the supporting evidence lives.
- **`evidence.md`** — the same, as a short human-readable table
  (Tokenizer integrity, Evaluation firewall, Packing correctness, Mixture
  compliance, OPUS audit trail, Crash recovery, Replay, Learning trace,
  Throughput).

Notably real, not scripted to pass: `eval_shard_blocked` deliberately
injects a real, verbatim `openai_humaneval` example as a poisoned
candidate and confirms the *same* contamination check used for real
admission flags it — proof the firewall blocks bad data, not just that
nothing bad happened to show up. `branch_forked` produces two genuinely
divergent child checkpoints (different learning rates) from one parent and
confirms their resulting weights actually differ, with a `distinct_paths`
guard against the two branches silently overwriting each other on disk
(a real bug this checked caught during development).

`run_audit.py` does its own self-contained checkpoint/crash/resume/
replay/fork cycle internally — it doesn't require
`train_tiny_transformer.py`/`restart.py` to have been run first, and its
checkpoints land in `checkpoints_tt/` alongside (not instead of) anything
already there.

## Honesty notes (things that are real vs deliberately mocked)

- No fabricated `source_url`s anywhere — every provenance record points at
  the real HF dataset URL the data came from. (Explicitly *not* using
  placeholder `commoncrawl.org`-style URLs for data that didn't come from
  Common Crawl.)
- `attention_and_position_policy` in the checkpoint manifest is an honest
  description of what this pipeline actually emits — flat position IDs,
  **no** cross-document attention mask — not an aspirational spec.
- OPUS, the curriculum engine, and the proxy scorer do not exist as real
  systems in this project. The TinyTransformer *is* real (real PyTorch
  forward/backward/optimizer). Every field/system that's mocked is clearly
  marked as such in the relevant script's docstring. Everything else
  (hashes, token counts, shard contents, the dataloader cursor,
  contamination checks, replay determinism) is computed from real data and
  independently checked, not assumed.

## File layout

```
build_corpus.py            indic track: download + clean + shard
build_web_corpus.py        web track: download + clean + shard
build_code_corpus.py       code track: download + clean + quality-filter + dedup + route (single script)
quality_filter.py [indic|web]
minhash_lsh_dedup.py [indic|web]
language_router.py [indic|web]
pii_scrub.py                PII redaction, all 3 lanes, final "OK" status
indic_normalize.py          Unicode normalization + script-agnostic cleanup (shared)
provenance.py                shard-level provenance logging (shared)
pipeline_stats.py            stats/pipeline_stats.json ledger (shared)
tokenize_and_admit.py        tokenize, pack, eval-overlap check, registry manifest

training_state.py            dummy scalar model + resumable training state (shared)
save_checkpoint.py            dummy model: fresh training run + checkpoint + OPUS
resume_training.py            dummy model: resume trigger

tiny_transformer.py          real PyTorch model (2-layer, single-head attention)
test_tiny_transformer.py     loss_mask correctness check (gradient introspection)
tt_checkpoint.py              TinyTransformer checkpoint save/load (shared)
train_tiny_transformer.py    TinyTransformer: fresh training run + checkpoint + OPUS
restart.py                    TinyTransformer: resume trigger

run_audit.py                  full audit: every subsystem + a real checkpoint/crash/resume/replay/fork cycle
run_pipeline.sh                runs steps 1-13 above in order

routed/{indic,web,code}/<lang>/*.txt     final cleaned corpus
shards/<lane>/<stage>/*.parquet          per-stage audit shards (consumed + deleted by the next stage)
packed/<lane>/*.npz                       packed training sequences
packed/<lane>/doc_manifest.jsonl          doc_id -> source file lookup
checkpoints/ckpt-*/                       dummy model: trainer_state.json + checkpoint_manifest.json
checkpoints_tt/ckpt-tt-*/                 TinyTransformer: model_state.pt + optimizer_state.pt + trainer_state.json + checkpoint_manifest.json
stats/pipeline_stats.json                per-stage summary ledger
stats/shard_manifest.jsonl                per-cleaning-stage shard provenance (BLOCKED/OK)
stats/registry_manifest.jsonl             final tokenized-shard admission decisions
stats/opus_decisions.jsonl                OPUS scoring pass
stats/training_log.jsonl                  dummy model per-step training log (append-only, spans resumes)
stats/tt_training_log.jsonl               TinyTransformer per-step training log (append-only, spans resumes)
stats/shard_sequence_counts.json          per-lane/per-shard sequence counts
run.log                                    full audit event sequence
evidence.json / evidence.md                audit pass/fail + supporting evidence
```
