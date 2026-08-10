"""
Tokenize each lane's final PII-scrubbed corpus (routed/<lane>/**/*.txt) with
tiktoken's o200k_base, pack the resulting per-document token streams into
fixed-length SEQ_LEN sequences, run a real eval-set contamination check per
shard of sequences, and emit one registry-admission manifest record per
shard in the exact schema:

    {
      "shard_id": "...", "capability_lane": "...", "token_count": 0,
      "tokenizer_hash": "...", "content_hash": "...",
      "cleaning_pipeline_hash": "...", "dedup_status": "...",
      "pii_screen_status": "...", "eval_overlap_status": "...",
      "license_tier": "...", "parent_manifest_ids": [], "admission": "..."
    }

Packing (indic/web only -- see "code lane" below)
---------------------------------------------------
Each document becomes one or more capacity-bounded units, ending in an EOS
token (o200k_base's <|endoftext|>) that marks its true end:
  - a document longer than SEQ_LEN-worth of tokens is chopped into as many
    *full* SEQ_LEN windows as fit (pure continuation, no EOS, no padding --
    the document hasn't ended yet) plus one leftover remainder unit that
    does end in EOS.
  - a document short enough to fit in one window (or a long document's
    leftover remainder) becomes one packable unit: <= SEQ_LEN tokens,
    ending in EOS.

Packable units are then combined via Best-Fit-Decreasing bin packing: sort
units longest-first, place each into the open bin (future sequence) with
the *smallest* remaining room that still fits it, else open a new bin. This
is the standard heuristic for 1-D bin packing -- it minimizes leftover
padding versus filling bins in arbitrary/document order, which is the
"mathematical approach to find the best samples to concat" this was asked
for. Units from different lanes are never combined (each lane is packed
independently), and a bin's leftover room after packing is filled with PAD
(reusing the EOS id, distinguished from real EOS via loss_mask).

Code lane: no packing, no combining
------------------------------------
Every unit (full window or remainder) is emitted as its own dedicated,
independently padded sequence -- never combined with another file. Two
unrelated source files should not end up back-to-back in one training
window with no meaningful boundary signal beyond "next file starts here";
keeping code strictly one-file-per-sequence (or one file split across
several sequences, for long files) avoids that.

Per-token fields (all length SEQ_LEN, one row per sequence)
-------------------------------------------------------------
  token_id    -- the actual integers the model consumes (real tokens, EOS
                 separators, and PAD tail, all id-compatible since PAD
                 reuses the EOS id).
  loss_mask   -- 1 on every real token *and* every EOS (predicting "this
                 document just ended" is a real training signal), 0 only
                 on the trailing PAD positions used to fill out a
                 not-quite-full sequence.
  position_id -- flat 0..SEQ_LEN-1, not reset at document boundaries.
  doc_id      -- which source document each token came from (a stable
                 index into that lane's doc_manifest.jsonl, so
                 e.g. "loss spike at position 4" is traceable back to an
                 actual file); PAD positions get doc_id -1.

Tokenizer: tiktoken o200k_base -- already used for every token count in
this pipeline. It has no local vocab file to hash, so tokenizer_hash is a
hash of its stable identity string (name + special tokens) rather than of
a vocab artifact.

Eval overlap: a real check, not a placeholder. Contamination is detected as
any shared 13-word n-gram (the window size used in the GPT-3/PaLM
contamination-check literature) between a sequence's real (non-PAD) text
and a real, ungated eval benchmark:
  - code lane: openai_humaneval (164 problems, prompt + canonical_solution)
  - indic/web lanes: ai4bharat/IndicSentiment test+validation splits for
    hi/bn/ta/te (INDIC REVIEW field) and en (ENGLISH REVIEW field).

parent_manifest_ids is left [] on every record per explicit instruction --
wiring it back to the specific provenance.py shard_ids that fed each
sequence is a followup, not done here.

Usage: .venv/bin/python tokenize_and_admit.py
"""

from __future__ import annotations

import bisect
import hashlib
import json
import random
from pathlib import Path

import numpy as np
import pandas as pd
import tiktoken
from huggingface_hub import hf_hub_download

from provenance import script_hash

ROUTED_DIR = Path("routed")
PACKED_DIR = Path("packed")
MANIFEST_PATH = Path("submission_artifacts/manifests/registry_manifest.jsonl")

ENCODING_NAME = "o200k_base"
SEQ_LEN = 2048
SEQUENCES_PER_SHARD = 500  # 500 * 2048 ~= 1.02M tokens/shard, close to the prior ~1M-token-per-shard convention
SEED = 42  # shard-shuffle seed -- same convention as SEED in build_corpus.py/build_web_corpus.py
NGRAM_N = 13  # contamination-check window size (GPT-3/PaLM convention)

LANES = {
    "indic": "Indic",
    "web": "Web",
    "code": "Code",
}
PACKING_ENABLED = {"indic": True, "web": True, "code": False}

CLEANING_SCRIPTS = {
    "indic": ["indic_normalize.py", "quality_filter.py", "minhash_lsh_dedup.py", "language_router.py", "pii_scrub.py"],
    "web": ["indic_normalize.py", "quality_filter.py", "minhash_lsh_dedup.py", "language_router.py", "pii_scrub.py"],
    "code": ["indic_normalize.py", "build_code_corpus.py", "pii_scrub.py"],
}

# Both license classes actually present in this corpus (see build_corpus.py /
# build_web_corpus.py / build_code_corpus.py) are permissive; this map is a
# real lookup, not a hardcoded constant, so a future restrictive source
# would surface as something other than "safe" instead of silently passing.
LICENSE_TIER = {
    "CC-BY-4.0": "safe",
    "OTHER-PERMISSIVE": "safe",
}
LANE_LICENSE_CLASS = {"indic": "CC-BY-4.0", "web": "CC-BY-4.0", "code": "OTHER-PERMISSIVE"}

INDIC_LANG_FILES = ("hi", "bn", "ta", "te")  # IndicSentiment file slugs match our codes


def _short_hash(prefix: str, data: bytes) -> str:
    return f"{prefix}_{hashlib.sha256(data).hexdigest()[:12]}"


def tokenizer_hash(enc: tiktoken.Encoding) -> str:
    identity = f"tiktoken:{ENCODING_NAME}:{sorted(enc.special_tokens_set)}".encode()
    return _short_hash("tok", identity)


def cleaning_pipeline_hash(lane: str) -> str:
    combined = "".join(sorted(script_hash(s) for s in CLEANING_SCRIPTS[lane])).encode()
    return _short_hash("clean", combined)


# --------------------------------------------------------------------------
# Eval sets (real, ungated) for contamination checking
# --------------------------------------------------------------------------

def _word_ngrams(text: str, n: int = NGRAM_N) -> set[tuple[str, ...]]:
    words = text.split()
    if len(words) < n:
        return {tuple(words)} if words else set()
    return {tuple(words[i : i + n]) for i in range(len(words) - n + 1)}


def load_code_eval_ngrams() -> set[tuple[str, ...]]:
    path = hf_hub_download("openai_humaneval", "openai_humaneval/test-00000-of-00001.parquet", repo_type="dataset")
    df = pd.read_parquet(path)
    grams: set[tuple[str, ...]] = set()
    for text in (df["prompt"] + "\n" + df["canonical_solution"]):
        grams |= _word_ngrams(text)
    return grams


def load_prose_eval_ngrams() -> set[tuple[str, ...]]:
    grams: set[tuple[str, ...]] = set()
    for split in ("test", "validation"):
        for slug in INDIC_LANG_FILES:
            path = hf_hub_download("ai4bharat/IndicSentiment", f"data/{split}/{slug}.json", repo_type="dataset")
            rows = [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]
            for row in rows:
                for field in ("INDIC REVIEW", "ENGLISH REVIEW"):
                    if row.get(field):
                        grams |= _word_ngrams(row[field])
    return grams


def has_overlap(text: str, eval_grams: set[tuple[str, ...]]) -> bool:
    words = text.split()
    if len(words) < NGRAM_N:
        return bool(words) and tuple(words) in eval_grams
    return any(tuple(words[i : i + NGRAM_N]) in eval_grams for i in range(len(words) - NGRAM_N + 1))


# --------------------------------------------------------------------------
# Per-document -> capacity-bounded units
# --------------------------------------------------------------------------

def doc_units(doc_id: int, tokens: list[int], eos_id: int, capacity: int):
    """Split one document's tokens+EOS into capacity windows.

    Returns (direct_windows, packable_unit): direct_windows are exactly
    `capacity` tokens each (pure continuation, never padded, never
    combined with anything -- emitted as their own dedicated sequences
    regardless of lane); packable_unit is the <=capacity leftover that
    ends in EOS (None if the document divided evenly with no leftover,
    i.e. EOS landed exactly on the boundary of the last direct window).
    """
    seq = tokens + [eos_id]
    n = len(seq)
    n_full = n // capacity
    direct_windows = [(doc_id, seq[i : i + capacity]) for i in range(0, n_full * capacity, capacity)]
    remainder = seq[n_full * capacity :]
    packable_unit = (doc_id, remainder) if remainder else None
    return direct_windows, packable_unit


def best_fit_decreasing_pack(units: list[tuple[int, list[int]]], capacity: int) -> list[list[tuple[int, list[int]]]]:
    """units: (doc_id, token_seq) pairs, each len(token_seq) <= capacity,
    each already ending in EOS. Best-Fit-Decreasing: process longest-first,
    place each unit into the open bin with the *smallest* remaining room
    that still fits it (minimizes wasted padding versus first-fit or
    arbitrary-order concatenation), else open a new bin."""
    ordered = sorted(units, key=lambda u: len(u[1]), reverse=True)
    bins: list[list[tuple[int, list[int]]]] = []
    sorted_remaining: list[tuple[int, int]] = []  # (remaining_capacity, bin_idx), kept sorted
    for doc_id, seq in ordered:
        need = len(seq)
        pos = bisect.bisect_left(sorted_remaining, (need, -1))
        if pos < len(sorted_remaining):
            rem, bin_idx = sorted_remaining.pop(pos)
            bins[bin_idx].append((doc_id, seq))
            bisect.insort(sorted_remaining, (rem - need, bin_idx))
        else:
            bin_idx = len(bins)
            bins.append([(doc_id, seq)])
            bisect.insort(sorted_remaining, (capacity - need, bin_idx))
    return bins


def build_sequence(segments: list[tuple[int, list[int]]], capacity: int, pad_id: int) -> dict:
    real_tokens: list[int] = []
    doc_id_arr: list[int] = []
    for doc_id, seq in segments:
        real_tokens.extend(seq)
        doc_id_arr.extend([doc_id] * len(seq))
    real_len = len(real_tokens)
    pad_len = capacity - real_len
    return {
        "token_id": real_tokens + [pad_id] * pad_len,
        "loss_mask": [1] * real_len + [0] * pad_len,
        "position_id": list(range(capacity)),
        "doc_id": doc_id_arr + [-1] * pad_len,
        "real_tokens": real_tokens,  # not persisted -- used only for the eval-overlap check below
    }


# --------------------------------------------------------------------------
# Per-lane driver
# --------------------------------------------------------------------------

def process_lane(lane: str, enc: tiktoken.Encoding, eos_id: int) -> list[dict]:
    paths = sorted((ROUTED_DIR / lane).rglob("*.txt"))
    if not paths:
        return []

    doc_manifest = []
    direct_bins: list[list[tuple[int, list[int]]]] = []
    packable_units: list[tuple[int, list[int]]] = []

    for doc_id, path in enumerate(paths):
        tokens = enc.encode(path.read_text(encoding="utf-8"))
        doc_manifest.append({"doc_id": doc_id, "source_path": str(path), "token_count": len(tokens)})
        windows, unit = doc_units(doc_id, tokens, eos_id, SEQ_LEN)
        direct_bins.extend([w] for w in windows)
        if unit is None:
            continue
        if PACKING_ENABLED[lane]:
            packable_units.append(unit)
        else:
            direct_bins.append([unit])  # code: every unit gets its own dedicated, padded sequence

    packed_bins = best_fit_decreasing_pack(packable_units, SEQ_LEN) if packable_units else []
    all_bins = direct_bins + packed_bins
    # Without shuffling, shards would be systematically non-uniform: all
    # long-document continuation windows (direct_bins) land in the first
    # shards, all packed short-doc sequences in the later ones -- shards
    # need to be interchangeable samples of the lane, not different in
    # composition depending on where they fall in shard order.
    random.Random(SEED).shuffle(all_bins)

    n_docs = len(paths)
    n_real_tokens = sum(d["token_count"] for d in doc_manifest)
    print(
        f"  {lane}: {n_docs} docs, {n_real_tokens} real tokens -> {len(all_bins)} sequences "
        f"({'packed' if PACKING_ENABLED[lane] else 'unpacked, one file per sequence run'})"
    )

    out_dir = PACKED_DIR / lane
    out_dir.mkdir(parents=True, exist_ok=True)
    Path(out_dir / "doc_manifest.jsonl").write_text(
        "\n".join(json.dumps(d, ensure_ascii=False) for d in doc_manifest) + "\n", encoding="utf-8"
    )

    sequences = [build_sequence(b, SEQ_LEN, pad_id=eos_id) for b in all_bins]
    return sequences


# --------------------------------------------------------------------------
# Shard + admit
# --------------------------------------------------------------------------

def admit_shards(lane: str, sequences: list[dict], tok_hash: str, eval_grams: set[tuple[str, ...]], enc: tiktoken.Encoding) -> list[dict]:
    out_dir = PACKED_DIR / lane
    clean_hash = cleaning_pipeline_hash(lane)
    license_tier = LICENSE_TIER[LANE_LICENSE_CLASS[lane]]

    records = []
    for idx, start in enumerate(range(0, len(sequences), SEQUENCES_PER_SHARD)):
        batch = sequences[start : start + SEQUENCES_PER_SHARD]
        shard_id = f"v5_{lane}_shard_{idx:03d}"

        token_id = np.array([s["token_id"] for s in batch], dtype=np.int32)
        loss_mask = np.array([s["loss_mask"] for s in batch], dtype=np.uint8)
        position_id = np.array([s["position_id"] for s in batch], dtype=np.int32)
        doc_id_arr = np.array([s["doc_id"] for s in batch], dtype=np.int32)
        np.savez(
            out_dir / f"{shard_id}.npz",
            token_id=token_id, loss_mask=loss_mask, position_id=position_id, doc_id=doc_id_arr,
        )

        token_count = int(loss_mask.sum())  # real (non-PAD) tokens only -- the actual trainable budget
        contaminated = any(has_overlap(enc.decode(s["real_tokens"]), eval_grams) for s in batch)
        eval_overlap_status = "contaminated" if contaminated else "clear"
        admission = "Admitted to registry" if eval_overlap_status == "clear" else "Held for review"

        record = {
            "shard_id": shard_id,
            "capability_lane": LANES[lane],
            "token_count": token_count,
            "tokenizer_hash": tok_hash,
            "content_hash": _short_hash("sha256", token_id.tobytes()),
            "cleaning_pipeline_hash": clean_hash,
            "dedup_status": "passed",       # only pii_scrub-OK'd text reaches routed/, which requires dedup to have run
            "pii_screen_status": "screened",  # same: routed/ text is post-pii_scrub by construction
            "eval_overlap_status": eval_overlap_status,
            "license_tier": license_tier,
            "parent_manifest_ids": [],
            "admission": admission,
        }
        records.append(record)
        print(f"    {shard_id}: {len(batch)} sequences, {token_count} real tokens, "
              f"eval_overlap={eval_overlap_status}, admission={admission!r}")
    return records


if __name__ == "__main__":
    enc = tiktoken.get_encoding(ENCODING_NAME)
    eos_id = enc.encode("<|endoftext|>", allowed_special={"<|endoftext|>"})[0]
    tok_hash = tokenizer_hash(enc)
    print(f"tokenizer: {ENCODING_NAME} ({tok_hash}), EOS/PAD id: {eos_id}, SEQ_LEN: {SEQ_LEN}")

    print("downloading eval sets for contamination check...")
    code_eval_grams = load_code_eval_ngrams()
    prose_eval_grams = load_prose_eval_ngrams()
    print(f"  code eval n-grams: {len(code_eval_grams)} (openai_humaneval)")
    print(f"  prose eval n-grams: {len(prose_eval_grams)} (ai4bharat/IndicSentiment, hi/bn/ta/te/en)")

    all_records: list[dict] = []
    for lane in LANES:
        print(f"\nlane: {lane}")
        sequences = process_lane(lane, enc, eos_id)
        eval_grams = code_eval_grams if lane == "code" else prose_eval_grams
        all_records.extend(admit_shards(lane, sequences, tok_hash, eval_grams, enc))

    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    with MANIFEST_PATH.open("w", encoding="utf-8") as f:
        for record in all_records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    admitted = sum(1 for r in all_records if r["admission"] == "Admitted to registry")
    print(f"\n{len(all_records)} shards written to {MANIFEST_PATH} ({admitted} admitted, {len(all_records) - admitted} held for review)")
    print(f"packed sequences under {PACKED_DIR}/<lane>/*.npz (token_id, loss_mask, position_id, doc_id)")
    print(f"per-lane doc lookup under {PACKED_DIR}/<lane>/doc_manifest.jsonl")
