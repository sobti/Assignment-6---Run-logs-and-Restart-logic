"""
PII scrubber -- final in-place redaction pass over the routed corpus, and
the only stage allowed to mark a shard "OK" (training-ready) rather than
"BLOCKED" -- see provenance.py's module docstring.

Runs last, after language_router.py (indic/web tracks) and
build_code_corpus.py (code track), over routed/<track>/<language>/*.txt
directly (no parquet intermediate: those files already are the final
corpus). Each file is redacted in place; nothing is deleted (there's no
further stage to hand off to). Aggregate redaction counts go to
stats/pipeline_stats.json via pipeline_stats.save_stats(), and one
provenance manifest record per ~2,000-file shard goes to
provenance.MANIFEST_PATH via write_file_shards().

Scope: numeric/structured PII written in ASCII digits and Latin letters --
email, URL, IPv4, Indian PAN, Indian mobile numbers, Aadhaar numbers, and
credit-card numbers. This is the realistic scope for a Devanagari/Bengali/
Tamil/Telugu/English web+code corpus: these identifiers are conventionally
written in Western Arabic numerals and Latin letters even mid-sentence in
Brahmic script text, and natively so in the English/code shards, so
ASCII-only patterns catch the real cases without having to solve free-text
name/address extraction (which needs an NER model, not regexes, and isn't
attempted here).

Aadhaar (12 digits) and credit-card (13-19 digits) both show up as bare
digit runs, so a length-only regex would false-positive on any ordinary
12-16 digit number (order IDs, phone-book listings, etc). Both identifiers
carry a public checksum -- Aadhaar uses a Verhoeff check digit, cards use
Luhn -- so candidate digit runs are only redacted if they actually pass the
relevant checksum, which cuts false positives sharply versus a bare regex.
"""

from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path

from indic_normalize import count_tokens
from pipeline_stats import load_ledger, save_stats, token_summary
from provenance import write_file_shards

# Optional CLI arg restricts the scan to one track ("indic", "web", "code")
# so re-running after a single track changes (e.g. code) doesn't re-scan
# and re-log already-"OK" shards from the other two tracks.
TRACK_FILTER = sys.argv[1] if len(sys.argv) > 1 else None

ROUTED_DIR = Path("routed")

# Fixed language sets per prose track -- "web" has no English because
# Sangraha's raw/unverified split doesn't include one (see
# build_web_corpus.py). The code track's language set isn't fixed; it's
# discovered from whatever routed/code/ subfolders build_code_corpus.py
# actually wrote.
TRACK_LANGUAGES = {
    "indic": ("hindi", "bengali", "tamil", "telugu", "english"),
    "web": ("hindi", "bengali", "tamil", "telugu"),
}

FOLDER_LANG_CODES = {"hindi": "hi", "bengali": "bn", "tamil": "ta", "telugu": "te", "english": "en"}
FOLDER_SANGRAHA_CODES = {"hindi": "hin", "bengali": "ben", "tamil": "tam", "telugu": "tel", "english": "eng"}
SANGRAHA_SPLIT = {"indic": "verified", "web": "unverified"}
SANGRAHA_LICENSE = "CC-BY-4.0"

CODE_DATASET = "bigcode/the-stack-smol-xs"
CODE_LICENSE = "OTHER-PERMISSIVE"


def _source_url(track: str, lang_folder: str) -> str:
    if track == "code":
        return f"https://huggingface.co/datasets/{CODE_DATASET}/blob/main/data/{lang_folder}/data.json"
    split = SANGRAHA_SPLIT[track]
    code = FOLDER_SANGRAHA_CODES[lang_folder]
    return f"https://huggingface.co/datasets/ai4bharat/sangraha/blob/main/{split}/{code}/data-0.parquet"


def _license_class(track: str) -> str:
    return CODE_LICENSE if track == "code" else SANGRAHA_LICENSE


def _lang_label(track: str, lang_folder: str) -> str:
    return lang_folder if track == "code" else FOLDER_LANG_CODES[lang_folder]


def _scan_targets() -> list[tuple[str, str, Path]]:
    """(track, lang_folder, dir) triples to scrub: routed/indic/<lang>/ and
    routed/web/<lang>/ for the fixed language sets above, plus every
    routed/code/<language>/ subfolder discovered dynamically since the
    code-language set isn't fixed here. Filtered to TRACK_FILTER if set, so
    the three tracks' shards never get scanned/logged together in one run
    unless explicitly requested."""
    targets = [
        (track, lang, ROUTED_DIR / track / lang)
        for track, langs in TRACK_LANGUAGES.items()
        for lang in langs
    ]
    code_dir = ROUTED_DIR / "code"
    if code_dir.is_dir():
        targets += [("code", d.name, d) for d in sorted(code_dir.iterdir()) if d.is_dir()]
    if TRACK_FILTER:
        targets = [t for t in targets if t[0] == TRACK_FILTER]
    return targets

URL_RE = re.compile(r"(?:https?://|www\.)\S+", re.IGNORECASE)
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
IP_RE = re.compile(
    r"\b(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)\b"
)
PAN_RE = re.compile(r"\b[A-Za-z]{5}[0-9]{4}[A-Za-z]\b")
PHONE_RE = re.compile(r"(?<!\d)(?:\+?91[-\s]?)?[6-9]\d{9}(?!\d)")
# Candidate window for checksum-validated Aadhaar/credit-card numbers --
# deliberately broad (digits plus internal spaces/dashes); anything that
# doesn't pass a checksum below is left untouched.
DIGIT_RUN_RE = re.compile(r"(?<!\d)\d[\d \-]{9,24}\d(?!\d)")


# --------------------------------------------------------------------------
# Checksums
# --------------------------------------------------------------------------

_VERHOEFF_D = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9], [1, 2, 3, 4, 0, 6, 7, 8, 9, 5],
    [2, 3, 4, 0, 1, 7, 8, 9, 5, 6], [3, 4, 0, 1, 2, 8, 9, 5, 6, 7],
    [4, 0, 1, 2, 3, 9, 5, 6, 7, 8], [5, 9, 8, 7, 6, 0, 4, 3, 2, 1],
    [6, 5, 9, 8, 7, 1, 0, 4, 3, 2], [7, 6, 5, 9, 8, 2, 1, 0, 4, 3],
    [8, 7, 6, 5, 9, 3, 2, 1, 0, 4], [9, 8, 7, 6, 5, 4, 3, 2, 1, 0],
]
_VERHOEFF_P = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9], [1, 5, 7, 6, 2, 8, 3, 0, 9, 4],
    [5, 8, 0, 3, 7, 9, 6, 1, 4, 2], [8, 9, 1, 6, 0, 4, 3, 5, 2, 7],
    [9, 4, 5, 3, 1, 2, 6, 8, 7, 0], [4, 2, 8, 6, 5, 7, 3, 9, 0, 1],
    [2, 7, 9, 3, 8, 0, 6, 4, 1, 5], [7, 0, 4, 6, 9, 1, 3, 2, 5, 8],
]


def verhoeff_valid(digits: str) -> bool:
    """Aadhaar's check-digit scheme."""
    c = 0
    for i, d in enumerate(reversed(digits)):
        c = _VERHOEFF_D[c][_VERHOEFF_P[i % 8][int(d)]]
    return c == 0


def luhn_valid(digits: str) -> bool:
    """Card-number check-digit scheme."""
    total = 0
    parity = len(digits) % 2
    for i, ch in enumerate(digits):
        d = int(ch)
        if i % 2 == parity:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def _classify_digit_run(raw: str) -> str | None:
    digits = re.sub(r"\D", "", raw)
    if len(digits) == 12 and verhoeff_valid(digits):
        return "AADHAAR"
    if 13 <= len(digits) <= 19 and luhn_valid(digits):
        return "CREDIT_CARD"
    return None


# --------------------------------------------------------------------------
# Scrub
# --------------------------------------------------------------------------

def scrub_text(text: str) -> tuple[str, Counter]:
    counts: Counter[str] = Counter()

    def make_sub(label: str):
        def repl(m: re.Match) -> str:
            counts[label] += 1
            return f"[{label}]"
        return repl

    # URL/email first so their embedded digits aren't re-matched by later
    # numeric patterns.
    text = URL_RE.sub(make_sub("URL"), text)
    text = EMAIL_RE.sub(make_sub("EMAIL"), text)
    text = IP_RE.sub(make_sub("IP"), text)
    text = PAN_RE.sub(make_sub("PAN"), text)
    text = PHONE_RE.sub(make_sub("PHONE"), text)

    def digit_repl(m: re.Match) -> str:
        label = _classify_digit_run(m.group())
        if label is None:
            return m.group()
        counts[label] += 1
        return f"[{label}]"

    text = DIGIT_RUN_RE.sub(digit_repl, text)
    return text, counts


def main() -> None:
    total_counts: Counter[str] = Counter()
    by_target: dict[str, Counter[str]] = {}
    files_touched = 0
    files_scanned = 0

    # Kept per-track (not merged) because print_pipeline_token_waterfall()
    # treats each track's pii_scrub total as the direct continuation of
    # that same track's language_router total -- merging tracks together
    # would make the step percentages meaningless.
    track_tokens_before: dict[str, int] = {}
    track_tokens_after: dict[str, int] = {}
    tokens_by_target: dict[str, dict] = {}

    for track, lang, lang_dir in _scan_targets():
        if not lang_dir.exists():
            continue
        label = f"{track}/{lang}"
        lang_counts: Counter[str] = Counter()
        entries: list[tuple[Path, int]] = []
        lang_tokens_before = 0
        lang_tokens_after = 0
        for path in sorted(lang_dir.glob("*.txt")):
            files_scanned += 1
            original = path.read_text(encoding="utf-8")
            tb = count_tokens(original)
            scrubbed, counts = scrub_text(original)
            if counts:
                path.write_text(scrubbed, encoding="utf-8")
                files_touched += 1
                lang_counts.update(counts)
                total_counts.update(counts)
                ta = count_tokens(scrubbed)
            else:
                ta = tb
            lang_tokens_before += tb
            lang_tokens_after += ta
            entries.append((path, ta))
        by_target[label] = lang_counts
        tokens_by_target[label] = token_summary(lang_tokens_before, lang_tokens_after)
        track_tokens_before[track] = track_tokens_before.get(track, 0) + lang_tokens_before
        track_tokens_after[track] = track_tokens_after.get(track, 0) + lang_tokens_after

        if entries:
            write_file_shards(
                entries,
                track=track,
                stage="pii_scrub",
                lang_label=_lang_label(track, lang),
                source_url=_source_url(track, lang),
                license_class=_license_class(track),
                cleaning_script="PII",
                cleaning_script_path=__file__,
                status="OK",
            )

    print(f"scanned {files_scanned} files, redacted PII in {files_touched} of them")
    print("\n--- redactions by type ---")
    for label, n in total_counts.most_common():
        print(f"  {label:14s} {n}")
    print("\n--- redactions by track/language ---")
    for label, counts in by_target.items():
        print(f"  {label:14s} {dict(counts)}")

    tokens_by_track = {
        track: token_summary(track_tokens_before[track], track_tokens_after[track])
        for track in track_tokens_before
    }
    print("\n--- tokens by track ---")
    for track, stats in tokens_by_track.items():
        print(
            f"  {track:6s} {stats['tokens_before']} -> {stats['tokens_after']} "
            f"(-{stats['tokens_dropped']}, -{stats['pct_dropped']:.2f}%)"
        )

    save_stats(
        "pii_scrub",
        {
            "files_scanned": files_scanned,
            "files_redacted": files_touched,
            "redactions_by_type": dict(total_counts),
            "redactions_by_target": {k: dict(v) for k, v in by_target.items()},
            "tokens_by_track": tokens_by_track,
            "tokens_by_target": tokens_by_target,
        },
    )

    for track in tokens_by_track:
        print_pipeline_token_waterfall(track)


# build_corpus.py's ledger stage is named "build_corpus" (not track-suffixed,
# since it only ever builds the "indic" track); build_web_corpus.py's is
# named "build_web_corpus" for the same reason. quality_filter.py,
# minhash_lsh_dedup.py and language_router.py are shared between tracks, so
# their ledger stages are suffixed with the track (see their save_stats calls).
_BUILD_STAGE = {"indic": "build_corpus", "web": "build_web_corpus"}


def print_pipeline_token_waterfall(track: str) -> None:
    """One track's full pipeline token funnel: raw text at build time ->
    final PII-scrubbed corpus, with each stage's drop -- answers "how much
    did each step cost, and what's left of the original token budget" for
    this track. Code isn't included: its pipeline is a single script, not
    a multi-stage funnel, so there's nothing to chart stage-by-stage."""
    ledger = load_ledger()
    build_stage = _BUILD_STAGE.get(track)
    required = [
        build_stage,
        f"quality_filter_{track}",
        f"minhash_lsh_dedup_{track}",
        f"language_router_{track}",
        "pii_scrub",
    ]
    if build_stage is None or not all(stage in ledger for stage in required):
        print(f"\n(skipping {track} token waterfall -- not all stages present in the ledger)")
        return
    if track not in ledger["pii_scrub"].get("tokens_by_track", {}):
        print(f"\n(skipping {track} token waterfall -- no pii_scrub tokens for this track)")
        return

    initial_raw = int(ledger[build_stage]["token_counts_by_language"]["TOTAL"]["pre_tokens"])
    after_cleaning = int(ledger[build_stage]["token_counts_by_language"]["TOTAL"]["post_tokens"])
    after_quality_filter = ledger[f"quality_filter_{track}"]["tokens"]["tokens_after"]
    after_dedup = ledger[f"minhash_lsh_dedup_{track}"]["tokens"]["tokens_after"]
    after_routing = ledger[f"language_router_{track}"]["tokens"]["tokens_after"]
    after_pii_scrub = ledger["pii_scrub"]["tokens_by_track"][track]["tokens_after"]

    stages = [
        (f"build_{track} (raw)", initial_raw),
        (f"build_{track} (cleaned)", after_cleaning),
        ("quality_filter", after_quality_filter),
        ("minhash_lsh_dedup", after_dedup),
        ("language_router", after_routing),
        ("pii_scrub (final)", after_pii_scrub),
    ]

    print(f"\n--- {track} token waterfall (raw -> final) ---")
    prev = None
    rows = []
    for name, tokens in stages:
        step_pct = 100.0 * (tokens - prev) / prev if prev else 0.0
        cum_pct = 100.0 * (tokens - initial_raw) / initial_raw if initial_raw else 0.0
        print(f"  {name:24s} {tokens:>10d} tokens  step {step_pct:+6.2f}%  cumulative {cum_pct:+6.2f}%")
        rows.append(
            {"stage": name, "tokens": tokens, "step_pct_change": step_pct, "cumulative_pct_change": cum_pct}
        )
        prev = tokens

    overall_pct = 100.0 * (after_pii_scrub - initial_raw) / initial_raw if initial_raw else 0.0
    print(
        f"\n{track} overall: {initial_raw} -> {after_pii_scrub} tokens "
        f"({overall_pct:+.2f}%, {initial_raw - after_pii_scrub} tokens dropped)"
    )

    save_stats(
        f"pipeline_summary_{track}",
        {
            "waterfall": rows,
            "initial_raw_tokens": initial_raw,
            "final_tokens": after_pii_scrub,
            "overall_pct_change": overall_pct,
            "overall_tokens_dropped": initial_raw - after_pii_scrub,
        },
    )


if __name__ == "__main__":
    main()
