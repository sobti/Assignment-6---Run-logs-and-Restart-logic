"""
Language identification + folder routing for the deduplicated corpus. Runs
against one track at a time -- "indic" or "web", selected by an optional
CLI arg (`python language_router.py web`; defaults to "indic"). Output
lands under routed/<TRACK>/<language>/ so the two prose tracks never mix
on disk even though they share this same routing logic (build_code_corpus.py
does its own routing for the code track, into routed/code/<language>/,
since its routing key is a dataset-provided language label, not detected
script).

Classifies each document by character-based script detection (reusing
indic_normalize.detect_brahmic_script, which is a per-character Unicode
block tally, plus a Latin-letter fallback for English) rather than trusting
any pre-existing language label: for every whitespace-split word, count
which target script its characters mostly fall in, then take the document's
dominant script as whichever target language wins the most words. A
document is routed into that language's folder only if that language
accounts for more than 80% of its words; otherwise it's discarded as
script-mixed / too ambiguous to label confidently. This also works as a QC
pass, independent of Sangraha's own hin/tam/tel/ben/eng directory split --
see the agreement check at the end.

Input: shards/<TRACK>/minhash_lsh_dedup/*.parquet (minhash_lsh_dedup.py's
output) and its `cleaned` text column; those shards are deleted once read.
Two outputs, both scoped to routed/kept docs only: the per-document .txt
files under routed/<TRACK>/<language>/ (the corpus itself), and shard
parquet files + provenance manifest records under shards/<TRACK>/
language_router/ (an auditable copy, status "BLOCKED" since PII scrub
hasn't run yet).
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

import pandas as pd

from indic_normalize import detect_brahmic_script
from pipeline_stats import save_stats, token_summary
from provenance import delete_consumed_shards, read_shards, write_shards

TRACK = sys.argv[1] if len(sys.argv) > 1 else "indic"  # "indic" or "web"
TEXT_COL = "cleaned"
OUT_DIR = Path("routed") / TRACK
PURITY_THRESHOLD = 0.8  # user-specified: >80% of words must match the language

TARGET_SCRIPTS = {
    "Devanagari": "hindi",
    "Bengali": "bengali",
    "Tamil": "tamil",
    "Telugu": "telugu",
    "Latin": "english",
}
FOLDER_LANG_CODES = {"hindi": "hi", "bengali": "bn", "tamil": "ta", "telugu": "te", "english": "en"}


def detect_word_script(word: str) -> str | None:
    """Brahmic script via indic_normalize's per-character block tally, with a
    Latin-letter fallback so English words route too (detect_brahmic_script
    only knows about Brahmic Unicode blocks and returns None for them)."""
    script = detect_brahmic_script(word)
    if script is not None:
        return script
    if any(ch.isascii() and ch.isalpha() for ch in word):
        return "Latin"
    return None


def classify(text: str) -> tuple[str | None, float]:
    """(folder, purity) for the document's dominant target-script words, or
    (None, purity) if that dominant share doesn't clear PURITY_THRESHOLD."""
    doc_words = text.split()
    if not doc_words:
        return None, 0.0

    word_scripts = [detect_word_script(w) for w in doc_words]
    target_counts = Counter(s for s in word_scripts if s in TARGET_SCRIPTS)
    if not target_counts:
        return None, 0.0

    dominant_script, dominant_count = target_counts.most_common(1)[0]
    purity = dominant_count / len(doc_words)
    if purity > PURITY_THRESHOLD:
        return TARGET_SCRIPTS[dominant_script], purity
    return None, purity


def main() -> None:
    df = read_shards(TRACK, "minhash_lsh_dedup")
    print(f"routing {len(df)} deduplicated docs")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for folder in TARGET_SCRIPTS.values():
        (OUT_DIR / folder).mkdir(exist_ok=True)

    folders: list[str | None] = []
    purities: list[float] = []
    counts_written: Counter[str] = Counter()

    for i, text in enumerate(df[TEXT_COL]):
        folder, purity = classify(text)
        folders.append(folder)
        purities.append(purity)
        if folder is None:
            continue
        (OUT_DIR / folder / f"{i:06d}.txt").write_text(text, encoding="utf-8")
        counts_written[folder] += 1

    routed_folder = pd.Series(folders, index=df.index)
    discarded = int(routed_folder.isna().sum())

    print("\n--- routing results ---")
    for folder in TARGET_SCRIPTS.values():
        print(f"  {folder:10s} {counts_written[folder]:6d} files")
    print(f"  {'discarded':10s} {discarded:6d} ({100 * discarded / len(df):.1f}%)")

    agreement = None
    if "lang" in df.columns:
        expected_folder = df["lang"].str.lower()
        agree = int((routed_folder == expected_folder).sum())
        agreement = {"agree": agree, "total": len(df), "pct": 100 * agree / len(df)}
        print(
            f"\nagreement with source 'lang' label: {agree}/{len(df)} "
            f"({agreement['pct']:.1f}%) -- mismatches are likely source "
            f"mislabels or code-mixed documents, not bugs"
        )

    routed_purities = [p for p, f in zip(purities, folders) if f is not None]

    token_stats = tokens_by_lang = None
    if "post_tokens" in df.columns:
        routed_mask = routed_folder.notna()
        token_stats = token_summary(
            int(df["post_tokens"].sum()), int(df.loc[routed_mask, "post_tokens"].sum())
        )
        print(
            f"\ntokens: {token_stats['tokens_before']} -> {token_stats['tokens_after']} "
            f"(-{token_stats['tokens_dropped']}, -{token_stats['pct_dropped']:.2f}%)"
        )
        if "lang" in df.columns:
            tokens_by_lang = {
                lang: token_summary(
                    int(g["post_tokens"].sum()),
                    int(g.loc[routed_mask.loc[g.index], "post_tokens"].sum()),
                )
                for lang, g in df.groupby("lang")
            }

    save_stats(
        f"language_router_{TRACK}",
        {
            "input_docs": len(df),
            "purity_threshold": PURITY_THRESHOLD,
            "written_by_folder": dict(counts_written),
            "discarded": discarded,
            "mean_purity_of_routed_docs": (
                sum(routed_purities) / len(routed_purities) if routed_purities else None
            ),
            "agreement_with_source_lang": agreement,
            "tokens": token_stats,
            "tokens_by_language": tokens_by_lang,
        },
    )

    routed_df = df.loc[routed_folder.notna()].copy()
    routed_df["routed_lang_code"] = routed_folder.dropna().map(FOLDER_LANG_CODES)
    write_shards(
        routed_df,
        track=TRACK,
        stage="language_router",
        text_col=TEXT_COL,
        lang_col="routed_lang_code",
        source_url_col="source_url",
        license_class_col="license_class",
        cleaning_script="lang_route",
        cleaning_script_path=__file__,
        status="BLOCKED",
        token_col="post_tokens" if "post_tokens" in routed_df.columns else None,
    )

    delete_consumed_shards(TRACK, "minhash_lsh_dedup")


if __name__ == "__main__":
    main()
