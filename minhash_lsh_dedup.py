"""
MinHash + LSH near-duplicate deduplication simulator for the quality-
filtered corpus. Runs against one track at a time -- "indic" or "web",
selected by an optional CLI arg (`python minhash_lsh_dedup.py web`;
defaults to "indic"). build_code_corpus.py imports the functions below
directly for the code track rather than invoking this file, since code's
pipeline shape (single pass, no separate stage scripts) differs from the
prose tracks'.

Shingles are character n-grams, not word n-grams -- Hindi/Bengali/Tamil/
Telugu compound and inflect differently from each other and from English,
so a fixed shingle definition that works across all five without
per-language tokenization rules is a character window. MinHash signatures
approximate Jaccard similarity
between two documents' shingle sets without storing the sets themselves;
LSH banding turns "find all pairs above similarity s" from an O(n^2)
all-pairs comparison into candidate lookups via shared-bucket hashing.
Duplicate clusters are resolved with union-find; the longest document in
each cluster is kept as the representative.

This is a from-scratch, in-memory simulator built to make the MinHash/LSH
mechanics visible and tunable -- not a production-scale implementation
(no persistence, no sharding, no MapReduce). Fine for tens of thousands of
documents; real pipelines at billions-of-docs scale use datasketch/Spark.

Input: shards/<TRACK>/quality_filter/*.parquet (quality_filter.py's
output), the `keep` column, and the `cleaned` text column; those shards are
deleted once read. Output: shards/<TRACK>/minhash_lsh_dedup/*.parquet, plus
one provenance manifest record per output shard.
"""

from __future__ import annotations

import hashlib
import sys
from collections import defaultdict

import numpy as np
import pandas as pd

from pipeline_stats import save_stats, token_summary
from provenance import delete_consumed_shards, read_shards, write_shards

TRACK = sys.argv[1] if len(sys.argv) > 1 else "indic"  # "indic" or "web"
TEXT_COL = "cleaned"

SHINGLE_SIZE = 5             # character n-gram width
NUM_HASHES = 128              # MinHash signature length
SIMILARITY_THRESHOLD = 0.8    # Jaccard similarity treated as "near-duplicate"
MAX_SHINGLES = 20_000         # per-doc cap, guards against pathological outliers
PRIME = (1 << 31) - 1         # small enough that a*x+b stays inside int64
SEED = 42


def shingles(text: str, k: int = SHINGLE_SIZE) -> set[int]:
    """k-character shingles, hashed to ints with a fixed-digest hash
    (Python's built-in hash() is salted per-process, not reproducible)."""
    text = " ".join(text.split())
    raw = {text} if len(text) < k else {text[i : i + k] for i in range(len(text) - k + 1)}
    hashed = {
        int.from_bytes(hashlib.blake2b(s.encode("utf-8"), digest_size=8).digest(), "big") % PRIME
        for s in raw
    }
    if len(hashed) > MAX_SHINGLES:
        seed = int.from_bytes(hashlib.blake2b(text.encode("utf-8"), digest_size=4).digest(), "big")
        rng = np.random.default_rng(seed)
        hashed = set(rng.choice(np.fromiter(hashed, dtype=np.int64), size=MAX_SHINGLES, replace=False))
    return hashed


def best_bands(num_hashes: int, threshold: float) -> tuple[int, int]:
    """Pick (bands, rows_per_band) whose LSH S-curve inflection point
    (1/bands)**(1/rows) is closest to the target similarity threshold."""
    best, best_diff = (num_hashes, 1), float("inf")
    for b in range(1, num_hashes + 1):
        if num_hashes % b:
            continue
        r = num_hashes // b
        diff = abs((1 / b) ** (1 / r) - threshold)
        if diff < best_diff:
            best_diff, best = diff, (b, r)
    return best


class MinHasher:
    """num_hashes independent universal hash functions h(x) = (a*x+b) mod p,
    applied to a shingle-hash set; the signature is the per-function min."""

    def __init__(self, num_hashes: int = NUM_HASHES, seed: int = SEED):
        rng = np.random.default_rng(seed)
        self.a = rng.integers(1, PRIME - 1, size=num_hashes, dtype=np.int64)
        self.b = rng.integers(0, PRIME - 1, size=num_hashes, dtype=np.int64)
        self.num_hashes = num_hashes

    def signature(self, shingle_hashes: set[int]) -> np.ndarray:
        if not shingle_hashes:
            return np.full(self.num_hashes, PRIME, dtype=np.int64)
        x = np.fromiter(shingle_hashes, dtype=np.int64, count=len(shingle_hashes))
        combined = (self.a[:, None] * x[None, :] + self.b[:, None]) % PRIME
        return combined.min(axis=1)


class UnionFind:
    def __init__(self, n: int):
        self.parent = list(range(n))

    def find(self, x: int) -> int:
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, x: int, y: int) -> None:
        rx, ry = self.find(x), self.find(y)
        if rx != ry:
            self.parent[rx] = ry


def lsh_cluster(signatures: np.ndarray, bands: int, rows: int, threshold: float) -> np.ndarray:
    """Bucket docs by identical band contents (candidate generation), then
    verify each candidate pair's estimated Jaccard similarity (fraction of
    matching signature entries) before union-find-merging its cluster."""
    n = signatures.shape[0]
    uf = UnionFind(n)
    buckets: dict[tuple[int, bytes], list[int]] = defaultdict(list)
    for band_idx in range(bands):
        band = signatures[:, band_idx * rows : (band_idx + 1) * rows]
        for doc_idx in range(n):
            buckets[(band_idx, band[doc_idx].tobytes())].append(doc_idx)

    for members in buckets.values():
        if len(members) < 2:
            continue
        rep = members[0]
        for other in members[1:]:
            if uf.find(rep) == uf.find(other):
                continue
            sim = (signatures[rep] == signatures[other]).mean()
            if sim >= threshold:
                uf.union(rep, other)

    return np.array([uf.find(i) for i in range(n)])


def main() -> None:
    df = read_shards(TRACK, "quality_filter")
    if "keep" in df.columns:
        df = df[df["keep"]].reset_index(drop=True)
    print(f"deduplicating {len(df)} quality-filtered docs")

    bands, rows = best_bands(NUM_HASHES, SIMILARITY_THRESHOLD)
    approx = (1 / bands) ** (1 / rows)
    print(f"LSH: {bands} bands x {rows} rows/band (S-curve inflection ~{approx:.3f})")

    hasher = MinHasher()
    print("computing shingle sets + MinHash signatures...")
    signatures = np.stack([hasher.signature(shingles(t)) for t in df[TEXT_COL]])

    print("LSH banding + union-find clustering...")
    df["dup_cluster"] = lsh_cluster(signatures, bands, rows, SIMILARITY_THRESHOLD)

    doc_len = df[TEXT_COL].str.len()
    keep_idx = doc_len.groupby(df["dup_cluster"]).idxmax()
    df["dedup_keep"] = df.index.isin(set(keep_idx))

    n_clusters = df["dup_cluster"].nunique()
    n_dupes = len(df) - n_clusters
    print(
        f"\n{len(df)} docs -> {n_clusters} clusters "
        f"({n_dupes} near-duplicates removed, {100 * n_dupes / len(df):.1f}%)"
    )
    by_lang = df.groupby("lang")["dedup_keep"].agg(kept="sum", total="count")
    print("\nby language:")
    print(by_lang)

    token_stats = token_summary(
        int(df["post_tokens"].sum()), int(df.loc[df["dedup_keep"], "post_tokens"].sum())
    )
    tokens_by_lang = {
        lang: token_summary(
            int(g["post_tokens"].sum()), int(g.loc[g["dedup_keep"], "post_tokens"].sum())
        )
        for lang, g in df.groupby("lang")
    }
    print(
        f"\ntokens: {token_stats['tokens_before']} -> {token_stats['tokens_after']} "
        f"(-{token_stats['tokens_dropped']}, -{token_stats['pct_dropped']:.2f}%)"
    )

    save_stats(
        f"minhash_lsh_dedup_{TRACK}",
        {
            "input_docs": len(df),
            "clusters": int(n_clusters),
            "near_duplicates_removed": int(n_dupes),
            "lsh_bands": bands,
            "lsh_rows_per_band": rows,
            "similarity_threshold": SIMILARITY_THRESHOLD,
            "by_language": {
                lang: {"kept": int(row.kept), "total": int(row.total)}
                for lang, row in by_lang.iterrows()
            },
            "tokens": token_stats,
            "tokens_by_language": tokens_by_lang,
        },
    )

    df = df[df["dedup_keep"]].drop(columns=["dedup_keep", "dup_cluster"]).reset_index(drop=True)
    write_shards(
        df,
        track=TRACK,
        stage="minhash_lsh_dedup",
        text_col=TEXT_COL,
        lang_col="lang_code",
        source_url_col="source_url",
        license_class_col="license_class",
        cleaning_script="dedup",
        cleaning_script_path=__file__,
        status="BLOCKED",
        token_col="post_tokens",
    )
    print(f"\nsaved {len(df)} deduplicated rows as shards under shards/{TRACK}/minhash_lsh_dedup/")

    delete_consumed_shards(TRACK, "quality_filter")


if __name__ == "__main__":
    main()
