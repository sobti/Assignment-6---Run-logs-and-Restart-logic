"""
Unicode normalization for Brahmic-script corpora.

Pipeline: strip format controls -> strip markup/URLs/emails -> collapse
elongation & punctuation runs -> collapse whitespace -> NFC -> force nukta
decomposition -> reorder nukta -> zero-width policy.

Why not just NFC
----------------
1. NFC decomposes the composition-exclusion nukta letters (U+0958-095F,
   U+09DC/DD/DF, U+0A33/0A36/0A59-0A5B/0A5E, U+0B5C/0B5D) and does not recompose
   them. Correct and stable.
2. But U+0929, U+0931, U+0934 are NOT exclusions, so NFC composes those. Plain
   NFC therefore leaves a mixed regime: some nukta letters atomic, some
   decomposed. nukta_policy="decompose_all" forces base + nukta everywhere.
3. Canonical reordering will not fix <ka, vowel-sign, nukta>. Indic vowel signs
   have ccc=0 and act as blockers, so that sequence survives NFC unchanged and
   stays byte-distinct from <ka, nukta, vowel-sign>. The virama case does get
   fixed (ccc 9 > 7), which is why this one tends to slip past testing.

Output is idempotent but deliberately NOT NFC-normalized when
nukta_policy="decompose_all" -- do not assert is_normalized("NFC", out)
downstream.

Normalization core is stdlib only. Token counting (count_tokens /
TokenCountReport) additionally needs tiktoken -- imported lazily so the rest
of the module still works without it installed.
"""

from __future__ import annotations

import re
import unicodedata as ud
from dataclasses import dataclass
from functools import lru_cache
from typing import Literal

UNIDATA_VERSION = ud.unidata_version  # pin/log this: tables are version-dependent

# --------------------------------------------------------------------------
# Character sets
# --------------------------------------------------------------------------

NUKTAS = frozenset("\u093C\u09BC\u0A3C\u0ABC\u0B3C\u0C3C\u0CBC")

VIRAMAS = frozenset(
    "\u094D\u09CD\u0A4D\u0ACD\u0B4D\u0BCD\u0C4D\u0CCD\u0D4D\u0DCA"
)

ZW = frozenset("\u200C\u200D")  # ZWNJ, ZWJ -- contrastive next to a virama

# Script-agnostic invisible junk from scraping. Safe to drop.
FORMAT_CONTROLS = frozenset(
    "\u200B\uFEFF\u00AD\u180E\u2060"                        # ZWSP, BOM, SHY, ...
    "\u200E\u200F\u202A\u202B\u202C\u202D\u202E"            # bidi marks
    "\u2066\u2067\u2068\u2069"                              # bidi isolates
)

_BRAHMIC_BLOCKS: tuple[tuple[int, int, str], ...] = (
    (0x0900, 0x097F, "Devanagari"),
    (0x0980, 0x09FF, "Bengali"),
    (0x0A00, 0x0A7F, "Gurmukhi"),
    (0x0A80, 0x0AFF, "Gujarati"),
    (0x0B00, 0x0B7F, "Odia"),
    (0x0B80, 0x0BFF, "Tamil"),
    (0x0C00, 0x0C7F, "Telugu"),
    (0x0C80, 0x0CFF, "Kannada"),
    (0x0D00, 0x0D7F, "Malayalam"),
    (0x0D80, 0x0DFF, "Sinhala"),
    (0x1CD0, 0x1CFF, "Devanagari"),   # Vedic Extensions
    (0xA8E0, 0xA8FF, "Devanagari"),   # Devanagari Extended
    (0x11B00, 0x11B5F, "Devanagari"), # Devanagari Extended-A
)


# --------------------------------------------------------------------------
# Derived tables (built from unicodedata, not hardcoded)
# --------------------------------------------------------------------------

@lru_cache(maxsize=1)
def _nukta_decomp_table() -> dict[int, str]:
    """Every codepoint whose canonical decomposition ends in a nukta.

    Picks up both the composition exclusions and U+0929/0931/0934, which NFC
    would otherwise recompose.
    """
    tbl: dict[int, str] = {}
    for lo, hi in ((0x0900, 0x0DFF), (0xA8E0, 0xA8FF)):
        for cp in range(lo, hi + 1):
            d = ud.normalize("NFD", chr(cp))
            if len(d) > 1 and d[-1] in NUKTAS:
                tbl[cp] = d
    return tbl


@lru_cache(maxsize=1)
def _indic_digit_table() -> dict[int, str]:
    """Indic digits -> ASCII. Opt-in and lossy: NFKC does not do this, and it
    destroys the script signal if you are using digits for language ID."""
    tbl: dict[int, str] = {}
    for lo, hi, _ in _BRAHMIC_BLOCKS:
        for cp in range(lo, hi + 1):
            ch = chr(cp)
            if ud.category(ch) == "Nd":
                tbl[cp] = str(ud.decimal(ch))
    return tbl


# --------------------------------------------------------------------------
# Script detection (routing helper -- normalization does not need it)
# --------------------------------------------------------------------------

def detect_brahmic_script(text: str) -> str | None:
    counts: dict[str, int] = {}
    for ch in text:
        cp = ord(ch)
        for lo, hi, name in _BRAHMIC_BLOCKS:
            if lo <= cp <= hi:
                counts[name] = counts.get(name, 0) + 1
                break
    if not counts:
        return None
    return max(counts, key=counts.get)


# --------------------------------------------------------------------------
# Individual steps
# --------------------------------------------------------------------------

def decompose_nukta(text: str) -> str:
    """Force base + nukta for every nukta letter, uniformly."""
    return text.translate(_nukta_decomp_table())


def fix_nukta_order(text: str) -> str:
    """Move nukta to the front of its combining-mark run.

    Canonical reordering cannot do this: <U+0915, U+093E, U+093C> survives
    NFC/NFD unchanged because U+093E has ccc=0 and blocks the swap.
    """
    if not any(ch in NUKTAS for ch in text):
        return text
    out: list[str] = []
    i, n = 0, len(text)
    while i < n:
        ch = text[i]
        out.append(ch)
        i += 1
        if ud.category(ch)[0] != "L":
            continue
        j = i
        while j < n and ud.category(text[j])[0] == "M":
            j += 1
        marks = text[i:j]
        if any(m in NUKTAS for m in marks):
            nuk = [m for m in marks if m in NUKTAS]
            rest = [m for m in marks if m not in NUKTAS]
            marks = "".join(nuk) + "".join(rest)
        out.append(marks)
        i = j
    return "".join(out)


def strip_zero_width(text: str, keep_virama_adjacent: bool = True) -> str:
    """Drop ZWNJ/ZWJ. When keep_virama_adjacent, preserve them next to a virama,
    where they are the difference between an explicit halant and a half-form."""
    if not any(ch in ZW for ch in text):
        return text
    out = []
    for idx, ch in enumerate(text):
        if ch in ZW:
            prev = text[idx - 1] if idx else ""
            nxt = text[idx + 1] if idx + 1 < len(text) else ""
            if keep_virama_adjacent and (prev in VIRAMAS or nxt in VIRAMAS):
                out.append(ch)
            continue
        out.append(ch)
    return "".join(out)


def strip_chars(text: str, charset) -> str:
    return "".join(ch for ch in text if ch not in charset)


# --------------------------------------------------------------------------
# Scraped-corpus cleaning (script-agnostic noise from raw web/social text)
# --------------------------------------------------------------------------

_URL_RE = re.compile(r"(?:https?://|www\.)\S+", re.IGNORECASE)
_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_HTML_TAG_RE = re.compile(r"<[^>]+>")
_HTML_ENTITY_RE = re.compile(r"&(?:#\d+|#x[0-9a-fA-F]+|[a-zA-Z]+);")
_PUNCT_RUN_RE = re.compile(r"([!?.,;:।॥])\1{1,}")
_WS_RUN_RE = re.compile(r"[ \t ]+")
_BLANK_LINE_RE = re.compile(r"\n{3,}")


def strip_urls(text: str) -> str:
    return _URL_RE.sub(" ", text)


def strip_emails(text: str) -> str:
    return _EMAIL_RE.sub(" ", text)


def strip_html(text: str) -> str:
    """Drop tags and leftover named/numeric entities. Entities are dropped,
    not decoded -- no entity table lookup, so no dependency for it."""
    text = _HTML_TAG_RE.sub(" ", text)
    text = _HTML_ENTITY_RE.sub(" ", text)
    return text


def collapse_elongation(text: str, max_repeat: int = 2) -> str:
    """Collapse runs of the same letter/mark beyond max_repeat -- the Indic
    equivalent of 'sooo good' -> 'so good'. Script-agnostic: keys off
    Unicode category (L/M), not a hardcoded alphabet, so it applies equally
    to Tamil/Telugu/Bengali/Devanagari repeats."""
    out: list[str] = []
    run_ch = ""
    run_len = 0
    for ch in text:
        run_len = run_len + 1 if ch == run_ch else 1
        run_ch = ch
        if run_len <= max_repeat or ud.category(ch)[0] not in ("L", "M"):
            out.append(ch)
    return "".join(out)


def collapse_punct_runs(text: str) -> str:
    """'!!!' -> '!', '।।।' -> '।'. Limited to a fixed punctuation set so it
    never touches script characters."""
    return _PUNCT_RUN_RE.sub(r"\1", text)


def collapse_whitespace(text: str) -> str:
    """Collapse horizontal whitespace runs, cap blank-line runs, trim ends."""
    text = _WS_RUN_RE.sub(" ", text)
    text = _BLANK_LINE_RE.sub("\n\n", text)
    return text.strip()


def clean_text(
    text: str,
    *,
    strip_urls_emails: bool = True,
    strip_markup: bool = True,
    collapse_punct: bool = True,
    max_elongation: int | None = 2,
) -> str:
    """Scraped-corpus cleanup: URLs/emails/HTML, repeated punctuation,
    elongated characters, whitespace. Run before normalize_text() -- it
    operates on structure, not codepoint identity, so the ordering relative
    to Unicode normalization doesn't matter, but doing cleanup first keeps
    normalize_text()'s input closer to plain prose."""
    if not text:
        return text
    if strip_markup:
        text = strip_html(text)
    if strip_urls_emails:
        text = strip_urls(text)
        text = strip_emails(text)
    if collapse_punct:
        text = collapse_punct_runs(text)
    if max_elongation is not None:
        text = collapse_elongation(text, max_elongation)
    return collapse_whitespace(text)


# --------------------------------------------------------------------------
# Driver
# --------------------------------------------------------------------------

def normalize_text(
    text: str,
    *,
    nukta_policy: Literal["decompose_all", "nfc"] = "decompose_all",
    zw_policy: Literal["keep", "strip", "strip_unless_virama"] = "strip_unless_virama",
    strip_format: bool = True,
    fold_digits: bool = False,
) -> str:
    """Normalize one document. Order matters: compose, then re-decompose nukta,
    then reorder, then strip."""
    if not text:
        return text

    if strip_format:
        text = strip_chars(text, FORMAT_CONTROLS)

    if not ud.is_normalized("NFC", text):
        text = ud.normalize("NFC", text)

    if nukta_policy == "decompose_all":
        text = decompose_nukta(text)
    text = fix_nukta_order(text)

    if fold_digits:
        text = text.translate(_indic_digit_table())

    if zw_policy == "strip":
        text = strip_chars(text, ZW)
    elif zw_policy == "strip_unless_virama":
        text = strip_zero_width(text, keep_virama_adjacent=True)

    return text


def normalize_for_dedup(text: str) -> str:
    """Aggressive variant: hash key only. Keep normalize_text() output as the
    stored text."""
    text = normalize_text(text, zw_policy="strip", fold_digits=True)
    return " ".join(text.split())


def preprocess(
    text: str,
    *,
    clean: bool = True,
    nukta_policy: Literal["decompose_all", "nfc"] = "decompose_all",
    zw_policy: Literal["keep", "strip", "strip_unless_virama"] = "strip_unless_virama",
    strip_format: bool = True,
    fold_digits: bool = False,
    max_elongation: int | None = 2,
) -> str:
    """clean_text() -> normalize_text(). The full pipeline to run on a raw
    scraped document; normalize_text() alone assumes cleanup already ran."""
    if clean:
        text = clean_text(text, max_elongation=max_elongation)
    return normalize_text(
        text,
        nukta_policy=nukta_policy,
        zw_policy=zw_policy,
        strip_format=strip_format,
        fold_digits=fold_digits,
    )


# --------------------------------------------------------------------------
# Token counting (pre/post pipeline) -- needs tiktoken, imported lazily
# --------------------------------------------------------------------------

_ENCODING_CACHE: dict[str, object] = {}


def _get_encoding(encoding: str):
    try:
        import tiktoken
    except ImportError as e:
        raise ImportError(
            "Token counting needs tiktoken: pip install tiktoken"
        ) from e
    enc = _ENCODING_CACHE.get(encoding)
    if enc is None:
        enc = _ENCODING_CACHE[encoding] = tiktoken.get_encoding(encoding)
    return enc


def count_tokens(text: str, encoding: str = "o200k_base") -> int:
    """Subword token count under a real LLM tokenizer (default: the GPT-4o /
    GPT-5 family encoding). Use cl100k_base to match GPT-3.5/4 instead."""
    return len(_get_encoding(encoding).encode(text))


@dataclass(frozen=True)
class TokenCountReport:
    encoding: str
    pre_chars: int
    post_chars: int
    pre_tokens: int
    post_tokens: int

    @property
    def token_delta(self) -> int:
        return self.post_tokens - self.pre_tokens

    @property
    def token_pct_change(self) -> float:
        return 100.0 * self.token_delta / self.pre_tokens if self.pre_tokens else 0.0

    def __str__(self) -> str:
        sign = "+" if self.token_delta >= 0 else ""
        return (
            f"[{self.encoding}] {self.pre_chars} chars/{self.pre_tokens} tok -> "
            f"{self.post_chars} chars/{self.post_tokens} tok "
            f"({sign}{self.token_delta}, {sign}{self.token_pct_change:.1f}%)"
        )


def token_count_report(
    raw_text: str, cleaned_text: str, *, encoding: str = "o200k_base"
) -> TokenCountReport:
    """Pre/post token counts across a cleaning+normalization pass, so you can
    see whether it actually helps tokenizer fragmentation rather than just
    assuming it does."""
    enc = _get_encoding(encoding)
    return TokenCountReport(
        encoding=encoding,
        pre_chars=len(raw_text),
        post_chars=len(cleaned_text),
        pre_tokens=len(enc.encode(raw_text)),
        post_tokens=len(enc.encode(cleaned_text)),
    )


# --------------------------------------------------------------------------
# Self-test
# --------------------------------------------------------------------------

if __name__ == "__main__":
    cases = [
        ("\u0958", "\u0915\u093C"),                    # Devanagari qa, precomposed
        ("\u095F", "\u092F\u093C"),                    # ya with nukta
        ("\u09DC", "\u09A1\u09BC"),                    # Bengali rra
        ("\u09DF", "\u09AF\u09BC"),                    # Bengali yya
        ("\u0A59", "\u0A16\u0A3C"),                    # Gurmukhi khha
        ("\u0A36", "\u0A38\u0A3C"),                    # Gurmukhi shashsha
        ("\u0B5C", "\u0B21\u0B3C"),                    # Odia ddda
        ("\u0929", "\u0928\u093C"),                    # NOT an exclusion: NFC recomposes
        ("\u0931", "\u0930\u093C"),
        ("\u0915\u093E\u093C", "\u0915\u093C\u093E"),  # nukta after vowel sign
        ("\u0915\u094D\u093C", "\u0915\u093C\u094D"),  # nukta after virama
    ]
    ok = True
    for a, b in cases:
        na, nb = normalize_text(a), normalize_text(b)
        good = na == nb
        ok &= good
        print(f"{'ok ' if good else 'FAIL'} {a!a} -> {na!a}   |   {b!a} -> {nb!a}")

    sample = "\u0958\u0915\u093E\u093C\u200C \u0915\u094D\u200D\u0937 \u0967\u0968"
    once = normalize_text(sample)
    assert once == normalize_text(once), "not idempotent"
    print("idempotent: ok")
    print("virama ZWJ kept:", "\u200D" in once)
    print("dedup key:", repr(normalize_for_dedup(sample)))
    print("detected script:", detect_brahmic_script(sample))
    print("unicodedata version:", UNIDATA_VERSION)

    # ---------------------------------------------------------------------
    # Noisy scraped-style samples: Hindi, Bengali, Tamil, Telugu.
    # Each has HTML tags, a URL, irregular whitespace, punctuation runs,
    # and elongated letters -- clean_text() should strip/collapse all of it.
    # ---------------------------------------------------------------------
    noisy_samples = {
        "Hindi": (
            "<p>\u092F\u0939 \u092A\u094D\u0930\u094B\u0921\u0915\u094D\u091F \u092C\u0939\u0941\u0924   \u092C\u0922\u093C\u093F\u092F\u093E \u0939\u0948!!!   \u0926\u0947\u0916\u093F\u090F https://example.com/offer "
            "\u0914\u0930 \u0905\u092D\u0940 \u0916\u0930\u0940\u0926\u0947\u0902\u0964\u0964\u0964   \u0938\u0938\u0938\u0938\u0938\u094D\u0924\u093E \u0939\u0948\u0964\u0964</p>"
        ),
        "Bengali": (
            "<p>\u098F\u0987 \u099C\u09BF\u09A8\u09BF\u09B8\u099F\u09BE   \u09A6\u09BE\u09B0\u09C1\u09A3 !!!   \u09A6\u09C7\u0996\u09C1\u09A8 www.example.com/offer   "
            "\u0986\u099C\u0987 \u0995\u09BF\u09A8\u09C1\u09A8\u0964\u0964\u0964   \u0996\u09C1\u09AC\u09AC\u09AC\u09AC\u0987 \u09B8\u09B8\u09CD\u09A4\u09BE\u0964\u0964</p>"
        ),
        "Tamil": (
            "<p>\u0B87\u0BA4\u0BC1   \u0BAE\u0BBF\u0B95\u0BB5\u0BC1\u0BAE\u0BCD \u0BA8\u0BB2\u0BCD\u0BB2\u0BA4\u0BC1!!!   \u0BAA\u0BBE\u0BB0\u0BC1\u0B99\u0BCD\u0B95\u0BB3\u0BCD https://example.com/tamil   "
            "\u0B87\u0BAA\u0BCD\u0BAA\u0BCB\u0BA4\u0BC7 \u0BB5\u0BBE\u0B99\u0BCD\u0B95\u0BC1\u0B99\u0BCD\u0B95\u0BB3\u0BCD\u0964\u0964\u0964   \u0BB0\u0BCA\u0BCA\u0BCA\u0BCA\u0BAE\u0BCD\u0BAA \u0BAE\u0BB2\u0BBF\u0BB5\u0BC1.....</p>"
        ),
        "Telugu": (
            "<p>\u0C07\u0C26\u0C3F   \u0C1A\u0C3E\u0C32\u0C3E \u0C2C\u0C3E\u0C17\u0C41\u0C02\u0C26\u0C3F!!!   \u0C1A\u0C42\u0C21\u0C02\u0C21\u0C3F www.example.com/telugu   "
            "\u0C07\u0C2A\u0C4D\u0C2A\u0C41\u0C21\u0C47 \u0C15\u0C4A\u0C28\u0C02\u0C21\u0C3F\u0964\u0964\u0964   \u0C1A\u0C3E\u0C32\u0C3E\u0C3E\u0C3E\u0C3E \u0C1A\u0C35\u0C15.....</p>"
        ),
    }

    print("\n--- cleaning + token counts ---")
    for lang, raw in noisy_samples.items():
        cleaned = preprocess(raw)
        print(f"\n{lang}")
        print("  raw:    ", raw)
        print("  cleaned:", cleaned)
        try:
            report = token_count_report(raw, cleaned)
            print("  tokens: ", report)
        except ImportError as e:
            print("  tokens:  skipped ({})".format(e))

    raise SystemExit(0 if ok else 1)
