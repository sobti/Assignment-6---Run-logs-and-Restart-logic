"""
Build a small source-code corpus from bigcode/the-stack-smol-xs and route it
into routed/code/<language>/ alongside the Indic+English prose corpus.

Why this is a separate script rather than another language fed through
build_corpus.py's pipeline: that pipeline's cleaning/quality/routing stages
are all tuned for natural-language prose, and code breaks each assumption
differently --

  * indic_normalize.clean_text() collapses horizontal-whitespace runs to a
    single space, which destroys indentation (fatal for Python, cosmetic
    but wrong for everything else). This script skips clean_text()
    entirely and only strips script-agnostic junk (format controls, BOM)
    via indic_normalize.strip_chars.
  * quality_filter.py's metrics (Flesch reading ease, MLTD, akshara/
    syllable counts, sentence splitting) assume prose structure that code
    doesn't have. This script uses code-appropriate checks instead: drop
    empty/near-empty files and files that are almost entirely comments or
    a license header (see _comment_fraction).
  * language_router.py buckets everything by Brahmic-script-or-Latin
    purity, which would just dump all code into the "english" folder.
    This script routes by the dataset's own per-row language label
    instead, one folder per programming language under routed/code/.

Deduplication reuses minhash_lsh_dedup's shingle/MinHash/LSH functions
unchanged -- character-shingle Jaccard similarity doesn't care whether the
bytes are prose or code, so there was no reason to reimplement it.

PII scrubbing is deliberately NOT done here: pii_scrub.py's regex scrub is
also script/content-agnostic, so it has been extended to walk
routed/code/<language>/ too and stays the single place that runs last over
every routed folder.

the-stack-smol-xs (not the larger the-stack-smol) because the latter is a
gated dataset; -xs is ungated but only ~100 rows/language, so this corpus
is intentionally small -- a sample, not a scale match for the Indic shards.
That fixed ceiling (~1,400 files after filtering) is also what anchors the
overall web:indic:code = 50:25:25 token-count target used to size
build_corpus.py and build_web_corpus.py -- code can't be scaled up further
without switching to the gated the-stack-smol, so its measured token total
sets the 25% baseline the other two tracks are sized against.

Unlike the prose tracks, this is a single-pass script rather than four
separate stage scripts, so it logs one "build_code_corpus" provenance
manifest stage (covering clean+quality-filter+dedup+route together) instead
of one manifest stage per step.

Usage: .venv/bin/python build_code_corpus.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from huggingface_hub import hf_hub_download

from indic_normalize import FORMAT_CONTROLS, count_tokens, strip_chars
from minhash_lsh_dedup import best_bands, lsh_cluster, MinHasher, shingles
from pipeline_stats import save_stats
from provenance import write_shards

DATASET = "bigcode/the-stack-smol-xs"
TRACK = "code"
SEED = 42
OUT_DIR = Path("routed") / "code"

SOURCE_URL_TEMPLATE = f"https://huggingface.co/datasets/{DATASET}/blob/main/data/{{slug}}/data.json"
# the-stack curates only permissively-licensed source repos, but doesn't
# stamp one blanket SPDX license on this dataset card -- "OTHER-PERMISSIVE"
# reflects that honestly rather than guessing a specific license class.
LICENSE_CLASS = "OTHER-PERMISSIVE"

# A curated, mainstream subset of the-stack-smol-xs's ~87 available
# languages (the full list also has things like Agda/Isabelle/Thrift/Yacc
# that aren't representative of "a coding corpus" for this project).
CODE_LANGS = [
    "python", "javascript", "typescript", "java", "c", "c++", "c-sharp",
    "go", "rust", "ruby", "php", "html", "css", "sql", "shell",
]

# Comment-line prefix per shard slug, used only to tell real code apart
# from a file that's almost entirely comments/license header. Missing
# entries fall back to the generic marker set in _comment_fraction.
COMMENT_PREFIXES: dict[str, str] = {
    "python": "#", "ruby": "#", "shell": "#",
    "javascript": "//", "typescript": "//", "java": "//", "c": "//",
    "c++": "//", "c-sharp": "//", "go": "//", "rust": "//", "php": "//",
    "sql": "--",
    "html": "<!--", "css": "/*",
}
_GENERIC_MARKERS = ("#", "//", "--", "/*", "*", "<!--")

MIN_CODE_LINES = 3        # below this, a file is boilerplate/near-empty
SIMILARITY_THRESHOLD = 0.8  # same threshold minhash_lsh_dedup uses on prose


def load_language(slug: str) -> pd.DataFrame:
    path = hf_hub_download(DATASET, f"data/{slug}/data.json", repo_type="dataset")
    rows = [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]
    df = pd.DataFrame(rows)[["content", "lang", "ext"]]
    df["slug"] = slug
    df["source_url"] = SOURCE_URL_TEMPLATE.format(slug=slug)
    df["license_class"] = LICENSE_CLASS
    return df


def build_code_corpus() -> pd.DataFrame:
    parts = []
    for slug in CODE_LANGS:
        print(f"  downloading {slug}...")
        parts.append(load_language(slug))
    corpus = pd.concat(parts, ignore_index=True)
    return corpus.sample(frac=1.0, random_state=SEED).reset_index(drop=True)


def clean_code(text: str) -> str:
    """Strip only script-agnostic junk; preserve indentation and formatting
    verbatim -- see module docstring for why clean_text()/normalize_text()
    are not used here."""
    return strip_chars(text, FORMAT_CONTROLS)


def _comment_fraction(text: str, slug: str) -> tuple[int, int]:
    """(code_lines, total_lines): lines that are blank or look like a
    comment (per-language prefix, plus a generic fallback set) don't count
    as code_lines."""
    lines = text.splitlines()
    if not lines:
        return 0, 0
    prefix = COMMENT_PREFIXES.get(slug)
    markers = ((prefix,) if prefix else ()) + _GENERIC_MARKERS
    code_lines = sum(1 for ln in lines if ln.strip() and not ln.strip().startswith(markers))
    return code_lines, len(lines)


def quality_filter(corpus: pd.DataFrame) -> pd.DataFrame:
    corpus = corpus.copy()
    code_lines, total_lines = [], []
    for text, slug in zip(corpus["cleaned"], corpus["slug"]):
        c, t = _comment_fraction(text, slug)
        code_lines.append(c)
        total_lines.append(t)
    corpus["code_lines"] = code_lines
    corpus["total_lines"] = total_lines
    corpus["keep"] = corpus["code_lines"] >= MIN_CODE_LINES
    return corpus


def dedup(corpus: pd.DataFrame) -> pd.DataFrame:
    bands, rows = best_bands(128, SIMILARITY_THRESHOLD)
    hasher = MinHasher(num_hashes=128, seed=SEED)
    signatures = np.stack([hasher.signature(shingles(t)) for t in corpus["cleaned"]])
    corpus = corpus.copy()
    corpus["dup_cluster"] = lsh_cluster(signatures, bands, rows, SIMILARITY_THRESHOLD)
    doc_len = corpus["cleaned"].str.len()
    keep_idx = doc_len.groupby(corpus["dup_cluster"]).idxmax()
    corpus["dedup_keep"] = corpus.index.isin(set(keep_idx))
    return corpus


def route(corpus: pd.DataFrame) -> dict[str, int]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    counts: dict[str, int] = {}
    for i, row in corpus.iterrows():
        lang_dir = OUT_DIR / row["slug"]
        lang_dir.mkdir(exist_ok=True)
        (lang_dir / f"{i:06d}.txt").write_text(row["cleaned"], encoding="utf-8")
        counts[row["slug"]] = counts.get(row["slug"], 0) + 1
    return counts


if __name__ == "__main__":
    print("downloading the-stack-smol-xs shards...")
    corpus = build_code_corpus()

    print("cleaning (format-control strip only -- indentation preserved)...")
    corpus["pre_tokens"] = corpus["content"].map(count_tokens)
    corpus["cleaned"] = corpus["content"].map(clean_code)
    corpus["post_tokens"] = corpus["cleaned"].map(count_tokens)

    print("quality filtering (drop near-empty / boilerplate-only files)...")
    corpus = quality_filter(corpus)
    n_before_quality = len(corpus)
    corpus = corpus[corpus["keep"]].reset_index(drop=True)
    print(f"  {n_before_quality} -> {len(corpus)} after quality filter")

    print("deduplicating (character-shingle MinHash/LSH, reused from minhash_lsh_dedup)...")
    n_before_dedup = len(corpus)
    corpus = dedup(corpus)
    corpus = corpus[corpus["dedup_keep"]].reset_index(drop=True)
    print(f"  {n_before_dedup} -> {len(corpus)} after dedup")

    print("routing to routed/code/<language>/...")
    counts_written = route(corpus)

    print("\n--- routing results ---")
    for slug, n in sorted(counts_written.items()):
        print(f"  {slug:12s} {n:4d} files")

    by_lang = corpus.groupby("lang")["post_tokens"].agg(files="count", tokens="sum")
    print("\n--- token counts by language ---")
    print(by_lang.to_string())

    save_stats(
        "build_code_corpus",
        {
            "dataset": DATASET,
            "languages": CODE_LANGS,
            "raw_rows": n_before_quality,
            "after_quality_filter": n_before_dedup,
            "after_dedup": len(corpus),
            "written_by_language": counts_written,
            "total_tokens": int(corpus["post_tokens"].sum()),
            "tokens_by_language": by_lang.to_dict(orient="index"),
        },
    )

    print("\nwriting shards + provenance manifest...")
    write_shards(
        corpus,
        track=TRACK,
        stage="build_code_corpus",
        text_col="cleaned",
        lang_col="slug",
        source_url_col="source_url",
        license_class_col="license_class",
        cleaning_script="code_clean",
        cleaning_script_path=__file__,
        status="BLOCKED",
        token_col="post_tokens",
    )

    print(f"\ndone -- {len(corpus)} code files written under {OUT_DIR}/")
