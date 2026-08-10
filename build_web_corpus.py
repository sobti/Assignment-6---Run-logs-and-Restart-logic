"""
Download Sangraha's raw ("unverified") web/OCR-crawled Indic shards one at
a time, reshuffle to SAMPLES_PER_LANG rows/language, and run them through
the same indic_normalize cleaning pipeline as build_corpus.py. Output is
written as fixed-size shards (see provenance.write_shards), one provenance
manifest record per shard.

This is the "web" track: the least-curated of the three legs of the
corpus (web/indic/code), targeted at ~50% of the overall corpus by token
count -- see SAMPLES_PER_LANG below for how that number was derived.
"unverified" has no English split (Sangraha's raw-web collection is
Indic-only), so this track covers Hindi/Tamil/Telugu/Bengali only.

Deliberately NOT sourced from a fabricated commoncrawl.org URL: this
dataset's real, verifiable provenance is the Sangraha HF mirror, so that's
what source_url records. A provenance log pointing at a source the data
didn't actually come through would be worse than no log at all.

Usage: .venv/bin/python build_web_corpus.py
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pandas as pd
from huggingface_hub import hf_hub_download

from indic_normalize import count_tokens, preprocess
from pipeline_stats import save_stats
from provenance import write_shards

TRACK = "web"
LANGS = {
    "hin": "Hindi",
    "tam": "Tamil",
    "tel": "Telugu",
    "ben": "Bengali",
}
LANG_CODES = {"Hindi": "hi", "Tamil": "ta", "Telugu": "te", "Bengali": "bn"}

# web:indic:code target ratio is 50:25:25 by token count (see build_corpus.py
# for the full derivation from code's fixed ~5.18M-token ceiling). web's
# target is therefore ~10.36M tokens. Using the same ~834 post-pipeline
# tokens/doc measured on the prior prose run: ~10.36M / 834 ~= 12,400 docs
# total, ~3,100/language across 4 languages. Raw/unverified text is noisier
# than verified prose, so actual post-quality-filter attrition will likely
# be higher than the verified track's -- check stats/pipeline_stats.json
# after running rather than trusting this estimate blindly.
SAMPLES_PER_LANG = 3_100
SEED = 42
TEXT_COL_CANDIDATES = ("text", "content", "raw_content")
REPO_CACHE_DIR = (
    Path.home() / ".cache" / "huggingface" / "hub" / "datasets--ai4bharat--sangraha"
)

SOURCE_URL_TEMPLATE = (
    "https://huggingface.co/datasets/ai4bharat/sangraha/blob/main/unverified/{code}/data-0.parquet"
)
LICENSE_CLASS = "CC-BY-4.0"  # Sangraha repo-level license (same repo as the verified split)


def _text_column(df: pd.DataFrame) -> str:
    for col in TEXT_COL_CANDIDATES:
        if col in df.columns:
            return col
    raise KeyError(f"no text column found among {list(df.columns)}")


def load_sample(code: str) -> pd.DataFrame:
    """Download one shard, sample from it, then delete it from the local
    cache before returning -- keeps only one shard on disk at a time."""
    file_path = hf_hub_download(
        "ai4bharat/sangraha", f"unverified/{code}/data-0.parquet", repo_type="dataset"
    )
    df = pd.read_parquet(file_path)
    text_col = _text_column(df)
    n = min(SAMPLES_PER_LANG, len(df))
    df = df.sample(n=n, random_state=SEED).reset_index(drop=True)
    df = df.rename(columns={text_col: "text"})
    df = df[["text"]]
    df["type"] = "web"
    df["lang"] = LANGS[code]
    df["lang_code"] = LANG_CODES[LANGS[code]]
    df["source_url"] = SOURCE_URL_TEMPLATE.format(code=code)
    df["license_class"] = LICENSE_CLASS
    shutil.rmtree(REPO_CACHE_DIR, ignore_errors=True)
    return df


def build_corpus() -> pd.DataFrame:
    parts = []
    for code, name in LANGS.items():
        print(f"  downloading + sampling {name} ({code})...")
        parts.append(load_sample(code))
    corpus = pd.concat(parts, ignore_index=True)
    return corpus.sample(frac=1.0, random_state=SEED).reset_index(drop=True)


def clean_corpus(corpus: pd.DataFrame) -> pd.DataFrame:
    corpus = corpus.copy()
    corpus["pre_tokens"] = corpus["text"].map(count_tokens)
    corpus["cleaned"] = corpus["text"].map(preprocess)
    corpus["post_tokens"] = corpus["cleaned"].map(count_tokens)
    return corpus


def report(corpus: pd.DataFrame) -> None:
    summary = corpus.groupby("lang")[["pre_tokens", "post_tokens"]].sum()
    summary["delta"] = summary["post_tokens"] - summary["pre_tokens"]
    summary["pct_change"] = 100.0 * summary["delta"] / summary["pre_tokens"]
    totals = summary.sum(numeric_only=True)
    totals["pct_change"] = 100.0 * totals["delta"] / totals["pre_tokens"]
    summary.loc["TOTAL"] = totals
    print(f"\n{len(corpus)} rows, target {SAMPLES_PER_LANG} per language")
    print(summary.round(1).to_string())

    save_stats(
        "build_web_corpus",
        {
            "total_rows": len(corpus),
            "samples_per_lang_target": SAMPLES_PER_LANG,
            "seed": SEED,
            "token_counts_by_language": summary.round(1).to_dict(orient="index"),
        },
    )


if __name__ == "__main__":
    print("downloading + sampling Sangraha unverified (web) shards one at a time...")
    corpus = build_corpus()

    print("running cleaning pipeline + token counts...")
    corpus = clean_corpus(corpus)

    report(corpus)

    print("\nwriting shards + provenance manifest...")
    write_shards(
        corpus,
        track=TRACK,
        stage="build_corpus",
        text_col="cleaned",
        lang_col="lang_code",
        source_url_col="source_url",
        license_class_col="license_class",
        cleaning_script="indic",
        cleaning_script_path=__file__,
        status="BLOCKED",
        token_col="post_tokens",
    )
    print(f"done -- {len(corpus)} rows written as shards under shards/{TRACK}/build_corpus/")
