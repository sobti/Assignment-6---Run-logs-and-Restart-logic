"""
Download Sangraha's curated ("verified") Indic + English shards one at a
time, reshuffle to SAMPLES_PER_LANG rows/language, and run them through the
indic_normalize cleaning pipeline with pre/post token counts. Output is
written as fixed-size shards (see provenance.write_shards) instead of one
monolithic parquet, with one provenance manifest record per shard.

This is the curated "indic" track, sized to be ~25% of the overall
web/indic/code corpus by token count -- see the module-level comment above
SAMPLES_PER_LANG for how that number was derived. The much larger "web"
track (Sangraha's raw/unverified split) is built by build_web_corpus.py.

Each ~350-390MB shard is deleted from the local HF cache right after
sampling from it, so peak extra disk usage stays around one shard's size
instead of needing all five (~1.75G) at once -- this machine runs close to
full.

Usage: .venv/bin/python build_corpus.py
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pandas as pd
from huggingface_hub import hf_hub_download

from indic_normalize import count_tokens, preprocess
from pipeline_stats import save_stats
from provenance import write_shards

TRACK = "indic"
LANGS = {
    "hin": "Hindi",
    "tam": "Tamil",
    "tel": "Telugu",
    "ben": "Bengali",
    "eng": "English",
}
LANG_CODES = {"Hindi": "hi", "Tamil": "ta", "Telugu": "te", "Bengali": "bn", "English": "en"}

# Target corpus ratio (see build_web_corpus.py / build_code_corpus.py for
# the other two legs) is web:indic:code = 50:25:25 by *token* count, not
# doc count. code's dataset (the-stack-smol-xs) is hard-capped at ~100
# rows/language and measured ~5.18M tokens after the full pipeline -- since
# that can't be scaled up without switching to a gated dataset, it fixes
# the total budget: total = 5.18M / 0.25 ~= 20.7M, so indic's target is
# also ~5.18M tokens (25%). The previous 4-language-only run (SAMPLES_PER_LANG
# = 10_000, no English) measured ~834 post-pipeline tokens/doc; at that
# rate, ~5.18M tokens needs ~6,200 docs total, ~1,250/language across 5
# languages. This is a calibrated estimate, not a guarantee -- check
# stats/pipeline_stats.json after running to see the actual ratio achieved.
SAMPLES_PER_LANG = 1_250
SEED = 42
TEXT_COL_CANDIDATES = ("text", "content", "raw_content")
REPO_CACHE_DIR = (
    Path.home() / ".cache" / "huggingface" / "hub" / "datasets--ai4bharat--sangraha"
)

SOURCE_URL_TEMPLATE = (
    "https://huggingface.co/datasets/ai4bharat/sangraha/blob/main/verified/{code}/data-0.parquet"
)
LICENSE_CLASS = "CC-BY-4.0"  # Sangraha repo-level license (see its dataset card)


def _text_column(df: pd.DataFrame) -> str:
    for col in TEXT_COL_CANDIDATES:
        if col in df.columns:
            return col
    raise KeyError(f"no text column found among {list(df.columns)}")


def load_sample(code: str) -> pd.DataFrame:
    """Download one shard, sample from it, then delete it from the local
    cache before returning -- keeps only one shard on disk at a time."""
    file_path = hf_hub_download(
        "ai4bharat/sangraha", f"verified/{code}/data-0.parquet", repo_type="dataset"
    )
    df = pd.read_parquet(file_path)
    text_col = _text_column(df)
    df = df.sample(n=SAMPLES_PER_LANG, random_state=SEED).reset_index(drop=True)
    df = df.rename(columns={text_col: "text"})
    keep_cols = ["text"] + (["type"] if "type" in df.columns else [])
    df = df[keep_cols]
    if "type" not in df.columns:
        df["type"] = "unknown"
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
    print(f"\n{len(corpus)} rows, {SAMPLES_PER_LANG} per language")
    print(summary.round(1).to_string())

    type_dist = corpus.groupby(["lang", "type"]).size().unstack(fill_value=0)
    print("\nsource type distribution:")
    print(type_dist)

    save_stats(
        "build_corpus",
        {
            "total_rows": len(corpus),
            "samples_per_lang": SAMPLES_PER_LANG,
            "seed": SEED,
            "token_counts_by_language": summary.round(1).to_dict(orient="index"),
            "type_distribution": type_dist.to_dict(orient="index"),
        },
    )


if __name__ == "__main__":
    print("downloading + sampling Sangraha verified shards one at a time...")
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
