"""
Shard-level provenance logging for the corpus pipeline.

Every cleaning stage (build/clean, quality filter, dedup, route, PII scrub)
writes its output as fixed-size row shards (SHARD_SIZE docs each) instead of
one monolithic file per stage, and logs one JSON record per shard to
MANIFEST_PATH in this exact schema:

    {
      "source_url": "...",
      "license_class": "...",
      "contributor_id": "...",
      "cleaning_script": "...",
      "cleaning_script_hash": "...",
      "ingest_timestamp": "...",
      "sha256": "...",
      "token_count": 0,
      "lang_distribution": {"hi": 82, "en": 18},
      "status": "OK" | "BLOCKED"
    }

(plus a "shard_id" field prepended for addressability -- not in the
original spec, but records are otherwise unidentifiable once appended to a
shared JSONL file.)

status is a training-readiness flag, not a per-stage success flag: every
stage before pii_scrub logs "BLOCKED" because the shard may still contain
PII and isn't cleared for training use yet. pii_scrub is the only stage
that logs "OK", and only for shards it actually scrubbed.

source_url is always the true, verifiable upstream location the shard's
data was downloaded from (an HF dataset blob URL in this pipeline) -- never
a placeholder or a URL for a source the data didn't actually come from.
Recording a fabricated source in a provenance log defeats the log's entire
purpose.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from indic_normalize import count_tokens

CONTRIBUTOR_ID = "era5-punit"
SHARD_SIZE = 2000
SHARDS_DIR = Path("shards")
MANIFEST_PATH = Path("submission_artifacts/manifests/shard_manifest.jsonl")


def script_hash(script_path: str) -> str:
    """sha256 of the cleaning script's own source, so a manifest record is
    tied to the exact code that produced it, not just a script name."""
    return hashlib.sha256(Path(script_path).read_bytes()).hexdigest()


def lang_distribution(labels) -> dict[str, int]:
    """Percentage breakdown (ints, rounded) of a shard's per-row language
    labels. Rounding can make small shards sum to 99 or 101 -- an honest
    reflection of integer rounding on a small denominator, not a bug."""
    counts = Counter(labels)
    total = sum(counts.values())
    if not total:
        return {}
    return {str(k): round(100 * v / total) for k, v in counts.most_common()}


def log_shard(
    *,
    shard_id: str,
    source_url: str,
    license_class: str,
    cleaning_script: str,
    cleaning_script_path: str,
    sha256: str,
    token_count: int,
    lang_distribution: dict[str, int],
    status: str,
) -> dict:
    assert status in ("OK", "BLOCKED"), status
    record = {
        "shard_id": shard_id,
        "source_url": source_url,
        "license_class": license_class,
        "contributor_id": CONTRIBUTOR_ID,
        "cleaning_script": cleaning_script,
        "cleaning_script_hash": script_hash(cleaning_script_path),
        "ingest_timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "sha256": sha256,
        "token_count": int(token_count),
        "lang_distribution": lang_distribution,
        "status": status,
    }
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    with MANIFEST_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record


def _collapse(series: pd.Series) -> str:
    """A shard's source_url/license_class column collapsed to one value, or
    every distinct value joined, if the shard's rows don't all share one
    (e.g. a shard straddling two upstream shard files)."""
    values = sorted(set(series.astype(str)))
    return values[0] if len(values) == 1 else "; ".join(values)


def write_shards(
    df: pd.DataFrame,
    *,
    track: str,
    stage: str,
    text_col: str,
    lang_col: str,
    source_url_col: str,
    license_class_col: str,
    cleaning_script: str,
    cleaning_script_path: str,
    status: str,
    token_col: str | None = None,
    shard_size: int = SHARD_SIZE,
) -> list[Path]:
    """Split df into shard_size-row chunks, write each as its own parquet
    file under shards/<track>/<stage>/, and log one manifest record per
    shard. Returns the written shard paths."""
    out_dir = SHARDS_DIR / track / stage
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for start in range(0, len(df), shard_size):
        chunk = df.iloc[start : start + shard_size].reset_index(drop=True)
        idx = start // shard_size
        shard_id = f"{track}-{stage}-{idx:04d}"
        path = out_dir / f"{shard_id}.parquet"
        chunk.to_parquet(path, index=False)
        data = path.read_bytes()
        token_count = (
            int(chunk[token_col].sum())
            if token_col and token_col in chunk.columns
            else sum(count_tokens(t) for t in chunk[text_col])
        )
        log_shard(
            shard_id=shard_id,
            source_url=_collapse(chunk[source_url_col]),
            license_class=_collapse(chunk[license_class_col]),
            cleaning_script=cleaning_script,
            cleaning_script_path=cleaning_script_path,
            sha256=hashlib.sha256(data).hexdigest(),
            token_count=token_count,
            lang_distribution=lang_distribution(chunk[lang_col]),
            status=status,
        )
        paths.append(path)
    return paths


def read_shards(track: str, stage: str) -> pd.DataFrame:
    paths = sorted((SHARDS_DIR / track / stage).glob("*.parquet"))
    if not paths:
        raise FileNotFoundError(f"no shards under {SHARDS_DIR / track / stage}")
    return pd.concat([pd.read_parquet(p) for p in paths], ignore_index=True)


def delete_consumed_shards(track: str, stage: str) -> None:
    """Mirrors pipeline_stats.delete_consumed: once the next stage has read
    a stage's shards, drop them so disk usage doesn't accumulate every
    intermediate copy of the corpus."""
    d = SHARDS_DIR / track / stage
    paths = list(d.glob("*.parquet"))
    if not paths:
        return
    size_mb = sum(p.stat().st_size for p in paths) / 1e6
    shutil.rmtree(d)
    print(f"[cleanup] deleted {len(paths)} consumed shard(s) under {d} ({size_mb:.0f} MB)")


def write_file_shards(
    entries: list[tuple[Path, int]],
    *,
    track: str,
    stage: str,
    lang_label: str,
    source_url: str,
    license_class: str,
    cleaning_script: str,
    cleaning_script_path: str,
    status: str,
    shard_size: int = SHARD_SIZE,
) -> None:
    """Same manifest logging as write_shards, but for stages (pii_scrub)
    that operate on a flat list of already-written text files rather than
    a DataFrame. entries are (path, token_count) pairs -- token_count is
    passed in rather than recomputed so files aren't re-read+re-tokenized
    just for the manifest."""
    ordered = sorted(entries, key=lambda e: e[0])
    for start in range(0, len(ordered), shard_size):
        chunk = ordered[start : start + shard_size]
        idx = start // shard_size
        shard_id = f"{track}-{stage}-{lang_label}-{idx:04d}"
        h = hashlib.sha256()
        token_count = 0
        for path, tc in chunk:
            h.update(path.read_bytes())
            token_count += tc
        log_shard(
            shard_id=shard_id,
            source_url=source_url,
            license_class=license_class,
            cleaning_script=cleaning_script,
            cleaning_script_path=cleaning_script_path,
            sha256=h.hexdigest(),
            token_count=token_count,
            lang_distribution={lang_label: 100},
            status=status,
        )
