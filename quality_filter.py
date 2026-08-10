"""
Quality filtering for cleaned Indic-language documents (Gopher/MassiveText-
style corpus-quality heuristics, adapted for Brahmic scripts).

Runs against one track at a time -- "indic" (build_corpus.py's curated
output) or "web" (build_web_corpus.py's raw/unverified output), selected by
an optional CLI arg (`python quality_filter.py web`; defaults to "indic").

Input: shards/<TRACK>/build_corpus/*.parquet, using the `cleaned` and
`lang` columns; those shards are deleted once read (see delete_consumed_shards).
Output: shards/<TRACK>/quality_filter/*.parquet, one column per metric plus
a boolean `keep` combining every threshold, and one provenance manifest
record per output shard. A console report shows per-rule and combined drop
counts plus the corpus's own percentile distribution for each metric, so
the fixed THRESHOLDS below can be sanity-checked against this corpus rather
than trusted blindly.

Word segmentation is whitespace-based. "Syllable" counts for readability use
an akshara (orthographic-syllable) approximation for Brahmic scripts, since
Flesch's syllable-counting assumption is English-specific and doesn't
transfer directly: an akshara boundary falls at (a) every dependent vowel
sign, or (b) every letter not immediately followed by a vowel sign or
virama (i.e. an independent vowel, or a consonant carrying its inherent
vowel). A consonant immediately before a virama or vowel sign folds into
that following akshara instead of counting on its own. Pure-Latin words
(numbers, loanwords) fall back to counting vowel-letter runs. This does not
model schwa deletion -- it's a corpus-filtering heuristic, not a
linguistic syllabifier.

Thresholds are Gopher/C4-derived where that literature applies (word count,
symbol-to-word ratio, top-n-gram repetition, mean word length); MLTD,
Flesch, difficulty ratio and term frequency don't have a standard
quality-filter cutoff in the literature for Indic text, so those values are
reasoned starting points -- check the printed percentiles before trusting
them on a different corpus.

Stdlib + pandas (already a pipeline dependency).
"""

from __future__ import annotations

import re
import sys
import unicodedata as ud
from collections import Counter

import pandas as pd

from indic_normalize import VIRAMAS
from pipeline_stats import save_stats, token_summary
from provenance import delete_consumed_shards, read_shards, write_shards

TRACK = sys.argv[1] if len(sys.argv) > 1 else "indic"  # "indic" or "web"
TEXT_COL = "cleaned"

WORD_RE = re.compile(r"\S+")
SENTENCE_SPLIT_RE = re.compile(r"[।॥.!?]+")
SYMBOL_RE = re.compile(r"[#*~^_+=<>|@$%&…]|\.\.\.")
LATIN_VOWEL_RUN_RE = re.compile(r"[aeiouy]+")

# --------------------------------------------------------------------------
# Thresholds -- see module docstring for provenance. Edit freely; the report
# printed at the bottom shows each metric's corpus percentiles so you can
# check where these cutoffs actually land before trusting them.
# --------------------------------------------------------------------------
THRESHOLDS = {
    "word_count_min": 20,               # Gopher uses >=50; loosened since
    "word_count_max": 100_000,          #   these are crawl passages, not full docs
    "mean_word_length_min": 1.5,        # sanity bounds -- Indic codepoint-per-word
    "mean_word_length_max": 20.0,       #   runs longer than English's [3,10]
    "symbol_to_word_ratio_max": 0.1,    # user-specified
    "top_2gram_ratio_max": 0.20,        # Gopher's published top-2-gram cutoff
    "mltd_min": 10.0,                   # very repetitive/degenerate text scores low
    "difficulty_ratio_max": 0.6,        # share of polysyllabic (akshara>=4) words
    "term_frequency_max": 0.15,         # no single word should be >15% of the doc
    "duplicate_line_ratio_max": 0.3,    # Gopher's duplicate-line-fraction cutoff
    "duplicate_paragraph_ratio_max": 0.3,   # Gopher's duplicate-paragraph cutoff
    "boilerplate_line_ratio_max": 0.3,      # see build_boilerplate_line_index()
}

# Source-type metadata from Sangraha (web/pdf/speech). "speech" is ASR
# transcript text -- typically no sentence punctuation, which breaks the
# sentence-count denominator in flesch_reading_ease() the same way
# script-specific score offsets did (see FLESCH_LO/HI below), so it's
# excluded by default rather than silently degrading that metric for a
# ~0.2% slice of the corpus. "pdf" is extraction text (can carry layout/OCR
# artifacts) but is common enough (~12%) to keep and just let the other
# metrics catch genuinely broken cases.
ALLOWED_TYPES = {"web", "pdf"}

# Flesch Reading Ease is filtered per-language, not against one fixed range:
# the formula's constants (206.835/1.015/84.6) are English-calibrated, and
# each script's average akshara-per-word density shifts its whole score
# distribution by a different, roughly constant amount (Hindi docs here
# average ~-5, Tamil ~-85, for texts of comparable actual quality). A single
# global cutoff would flag far more Tamil/Telugu/Bengali documents than
# Hindi ones for reasons that have nothing to do with quality. Instead we
# keep each document within its own language's [FLESCH_LO, FLESCH_HI]
# percentile band, which treats "unusual for this script" consistently
# across languages.
FLESCH_LO, FLESCH_HI = 0.02, 0.98


# --------------------------------------------------------------------------
# Tokenization
# --------------------------------------------------------------------------

def words(text: str) -> list[str]:
    return WORD_RE.findall(text)


def sentences(text: str) -> list[str]:
    parts = [s for s in SENTENCE_SPLIT_RE.split(text) if s.strip()]
    return parts or [text]


# --------------------------------------------------------------------------
# Akshara (orthographic syllable) approximation -- see module docstring
# --------------------------------------------------------------------------

def _is_vowel_sign(ch: str) -> bool:
    if not ch or ud.category(ch) not in ("Mc", "Mn"):
        return False
    return "VOWEL SIGN" in ud.name(ch, "")


def akshara_count(word: str) -> int:
    if not word:
        return 0
    if not any(0x0900 <= ord(ch) <= 0x0DFF for ch in word):
        n = len(LATIN_VOWEL_RUN_RE.findall(word.lower()))
        return max(n, 1)

    n = 0
    for i, ch in enumerate(word):
        if _is_vowel_sign(ch):
            n += 1
            continue
        if ud.category(ch)[0] != "L":
            continue
        nxt = word[i + 1] if i + 1 < len(word) else ""
        if nxt in VIRAMAS or _is_vowel_sign(nxt):
            continue  # folds into the following/preceding akshara
        n += 1
    return max(n, 1)


# --------------------------------------------------------------------------
# Metrics
# --------------------------------------------------------------------------

def mean_word_length(tokens: list[str]) -> float:
    return sum(len(t) for t in tokens) / len(tokens) if tokens else 0.0


def symbol_to_word_ratio(text: str, word_count: int) -> float:
    if word_count == 0:
        return 0.0
    return len(SYMBOL_RE.findall(text)) / word_count


def top_ngram_ratio(tokens: list[str], n: int = 2) -> float:
    if len(tokens) < n:
        return 0.0
    grams = [tuple(tokens[i : i + n]) for i in range(len(tokens) - n + 1)]
    most_common_count = Counter(grams).most_common(1)[0][1]
    return (most_common_count * n) / len(tokens)


def max_term_frequency_ratio(tokens: list[str]) -> float:
    if not tokens:
        return 0.0
    return Counter(tokens).most_common(1)[0][1] / len(tokens)


def difficulty_ratio(tokens: list[str], syllable_threshold: int = 4) -> float:
    if not tokens:
        return 0.0
    difficult = sum(1 for t in tokens if akshara_count(t) >= syllable_threshold)
    return difficult / len(tokens)


def flesch_reading_ease(text: str, tokens: list[str]) -> float:
    if not tokens:
        return 0.0
    s = sentences(text)
    syllables = sum(akshara_count(t) for t in tokens)
    return 206.835 - 1.015 * (len(tokens) / len(s)) - 84.6 * (syllables / len(tokens))


def _nonblank_lines(text: str) -> list[str]:
    return [l.strip() for l in text.split("\n") if l.strip()]


def _paragraphs(text: str) -> list[str]:
    return [p.strip() for p in text.split("\n\n") if p.strip()]


def duplicate_line_ratio(text: str) -> float:
    """Fraction of a document's own lines that repeat another line in the
    same document -- catches repeated in-page nav/menu/footer blocks that
    top_ngram_ratio (word-level, no line structure) can't see."""
    lines = _nonblank_lines(text)
    if len(lines) < 2:
        return 0.0
    counts = Counter(lines)
    dup = sum(c for c in counts.values() if c > 1)
    return dup / len(lines)


def duplicate_paragraph_ratio(text: str) -> float:
    paras = _paragraphs(text)
    if len(paras) < 2:
        return 0.0
    counts = Counter(paras)
    dup = sum(c for c in counts.values() if c > 1)
    return dup / len(paras)


def build_boilerplate_line_index(
    texts: pd.Series, min_doc_freq: int = 3, min_line_len: int = 8
) -> set[str]:
    """Lines (>=min_line_len chars, to skip trivial short lines) that appear
    in at least min_doc_freq *distinct* documents across the whole corpus --
    that's a site template/nav/copyright line, not organic repeated writing
    within one document (which duplicate_line_ratio already catches)."""
    doc_freq: Counter[str] = Counter()
    for text in texts:
        lines = {l for l in _nonblank_lines(text) if len(l) >= min_line_len}
        doc_freq.update(lines)
    return {line for line, freq in doc_freq.items() if freq >= min_doc_freq}


def boilerplate_line_ratio(text: str, boilerplate_lines: set[str]) -> float:
    lines = _nonblank_lines(text)
    if not lines:
        return 0.0
    hits = sum(1 for l in lines if l in boilerplate_lines)
    return hits / len(lines)


def mltd(tokens: list[str], ttr_threshold: float = 0.72) -> float:
    """Measure of Textual Lexical Diversity (McCarthy & Jarvis, 2010): the
    average number of words needed for the running type-token ratio to
    decay to ttr_threshold, averaged over a forward and a backward pass."""
    if len(tokens) < 2:
        return 0.0

    def score(seq: list[str]) -> float:
        factors = 0.0
        types: set[str] = set()
        count = 0
        for tok in seq:
            count += 1
            types.add(tok)
            if len(types) / count <= ttr_threshold:
                factors += 1
                types = set()
                count = 0
        if count > 0:
            ttr = len(types) / count
            factors += (1 - ttr) / (1 - ttr_threshold)
        return len(seq) / factors if factors else float(len(seq))

    return (score(tokens) + score(list(reversed(tokens)))) / 2


def compute_metrics(text: str) -> dict:
    tokens = words(text)
    word_count = len(tokens)
    return {
        "word_count": word_count,
        "mean_word_length": mean_word_length(tokens),
        "symbol_to_word_ratio": symbol_to_word_ratio(text, word_count),
        "top_2gram_ratio": top_ngram_ratio(tokens, 2),
        "mltd": mltd(tokens),
        "flesch_reading_ease": flesch_reading_ease(text, tokens),
        "difficulty_ratio": difficulty_ratio(tokens),
        "term_frequency_ratio": max_term_frequency_ratio(tokens),
        "duplicate_line_ratio": duplicate_line_ratio(text),
        "duplicate_paragraph_ratio": duplicate_paragraph_ratio(text),
    }


def flesch_mask(df: pd.DataFrame) -> pd.Series:
    """Keep documents within their own language's [FLESCH_LO, FLESCH_HI]
    percentile band -- see the FLESCH_LO/HI comment above THRESHOLDS."""
    lo = df.groupby("lang")["flesch_reading_ease"].transform("quantile", FLESCH_LO)
    hi = df.groupby("lang")["flesch_reading_ease"].transform("quantile", FLESCH_HI)
    return df["flesch_reading_ease"].between(lo, hi)


# --------------------------------------------------------------------------
# Driver
# --------------------------------------------------------------------------

def main() -> None:
    df = read_shards(TRACK, "build_corpus")
    print(f"loaded {len(df)} rows from shards/{TRACK}/build_corpus/")

    metrics = df[TEXT_COL].map(compute_metrics).apply(pd.Series)
    df = pd.concat([df, metrics], axis=1)

    print("indexing cross-document boilerplate lines...")
    boilerplate_lines = build_boilerplate_line_index(df[TEXT_COL])
    df["boilerplate_line_ratio"] = df[TEXT_COL].map(
        lambda t: boilerplate_line_ratio(t, boilerplate_lines)
    )

    rule_masks = {
        "word_count": df["word_count"].between(
            THRESHOLDS["word_count_min"], THRESHOLDS["word_count_max"]
        ),
        "mean_word_length": df["mean_word_length"].between(
            THRESHOLDS["mean_word_length_min"], THRESHOLDS["mean_word_length_max"]
        ),
        "symbol_to_word_ratio": df["symbol_to_word_ratio"]
        <= THRESHOLDS["symbol_to_word_ratio_max"],
        "top_2gram_ratio": df["top_2gram_ratio"] <= THRESHOLDS["top_2gram_ratio_max"],
        "mltd": df["mltd"] >= THRESHOLDS["mltd_min"],
        "flesch_reading_ease": flesch_mask(df),
        "difficulty_ratio": df["difficulty_ratio"] <= THRESHOLDS["difficulty_ratio_max"],
        "term_frequency_ratio": df["term_frequency_ratio"]
        <= THRESHOLDS["term_frequency_max"],
        "duplicate_line_ratio": df["duplicate_line_ratio"]
        <= THRESHOLDS["duplicate_line_ratio_max"],
        "duplicate_paragraph_ratio": df["duplicate_paragraph_ratio"]
        <= THRESHOLDS["duplicate_paragraph_ratio_max"],
        "boilerplate_line_ratio": df["boilerplate_line_ratio"]
        <= THRESHOLDS["boilerplate_line_ratio_max"],
    }
    if "type" in df.columns:
        rule_masks["source_type"] = df["type"].isin(ALLOWED_TYPES)

    keep = pd.Series(True, index=df.index)
    print("\n--- per-rule drop counts ---")
    for name, mask in rule_masks.items():
        dropped = int((~mask).sum())
        print(f"  {name:24s} drops {dropped:6d} ({100 * dropped / len(df):.1f}%)")
        keep &= mask
    df["keep"] = keep

    print(f"\ncombined: keep {int(keep.sum())} / {len(df)} ({100 * keep.sum() / len(df):.1f}%)")
    print("\nby language:")
    print(df.groupby("lang")["keep"].agg(kept="sum", total="count"))

    token_stats = token_summary(int(df["post_tokens"].sum()), int(df.loc[keep, "post_tokens"].sum()))
    tokens_by_lang = {
        lang: token_summary(int(g["post_tokens"].sum()), int(g.loc[g["keep"], "post_tokens"].sum()))
        for lang, g in df.groupby("lang")
    }
    print(
        f"\ntokens: {token_stats['tokens_before']} -> {token_stats['tokens_after']} "
        f"(-{token_stats['tokens_dropped']}, -{token_stats['pct_dropped']:.2f}%)"
    )

    print("\n--- metric percentiles (full corpus, for threshold sanity-checking) ---")
    metric_cols = [c for c in rule_masks if c != "source_type"]
    with pd.option_context("display.width", 120):
        percentiles = df[metric_cols].describe(percentiles=[0.05, 0.25, 0.5, 0.75, 0.95]).T
        print(percentiles)

    type_stats = None
    if "type" in df.columns:
        type_stats = {
            t: {"kept": int(g["keep"].sum()), "total": int(len(g))}
            for t, g in df.groupby("type")
        }
        print("\nby source type:")
        print(pd.DataFrame(type_stats).T)

    drop_counts = {name: int((~mask).sum()) for name, mask in rule_masks.items()}
    by_lang = df.groupby("lang")["keep"].agg(kept="sum", total="count")
    save_stats(
        f"quality_filter_{TRACK}",
        {
            "input_rows": len(df),
            "kept_rows": int(keep.sum()),
            "drop_counts_by_rule": drop_counts,
            "by_language": {
                lang: {"kept": int(row.kept), "total": int(row.total)}
                for lang, row in by_lang.iterrows()
            },
            "by_source_type": type_stats,
            "tokens": token_stats,
            "tokens_by_language": tokens_by_lang,
            "thresholds": THRESHOLDS | {"flesch_lo_pct": FLESCH_LO, "flesch_hi_pct": FLESCH_HI},
            "allowed_types": sorted(ALLOWED_TYPES),
            "metric_percentiles": percentiles.to_dict(orient="index"),
            "boilerplate_lines_found": len(boilerplate_lines),
        },
    )

    # Only the rows that pass every rule are useful downstream; the rest are
    # already fully captured in drop_counts_by_rule above.
    df = df[df["keep"]].reset_index(drop=True)
    write_shards(
        df,
        track=TRACK,
        stage="quality_filter",
        text_col=TEXT_COL,
        lang_col="lang_code",
        source_url_col="source_url",
        license_class_col="license_class",
        cleaning_script="quality_filter",
        cleaning_script_path=__file__,
        status="BLOCKED",
        token_col="post_tokens",
    )
    print(f"\nsaved {len(df)} kept rows as shards under shards/{TRACK}/quality_filter/")

    delete_consumed_shards(TRACK, "build_corpus")


if __name__ == "__main__":
    main()
