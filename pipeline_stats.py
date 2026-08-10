"""
Shared stats ledger for the corpus pipeline.

Each stage writes its own summary numbers here instead of a full data
snapshot -- the pipeline deletes each stage's input parquet once the next
stage has consumed it (disk stays small), so this JSON file is the only
persistent record of what happened at each step.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

STATS_PATH = Path("stats/pipeline_stats.json")


def _to_jsonable(obj):
    """Recursively coerce numpy/pandas scalars into plain JSON-safe types."""
    if isinstance(obj, dict):
        return {str(k): _to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [_to_jsonable(v) for v in obj]
    if hasattr(obj, "item"):  # numpy scalar
        return obj.item()
    return obj


def load_ledger() -> dict:
    if STATS_PATH.exists():
        return json.loads(STATS_PATH.read_text())
    return {}


def save_stats(stage: str, stats: dict) -> None:
    STATS_PATH.parent.mkdir(exist_ok=True)
    ledger = load_ledger()
    ledger[stage] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        **_to_jsonable(stats),
    }
    STATS_PATH.write_text(json.dumps(ledger, indent=2, ensure_ascii=False))
    print(f"[stats] wrote stage '{stage}' to {STATS_PATH}")


def token_summary(before: int, after: int) -> dict:
    """before/after token counts for one stage, plus the drop and its %."""
    dropped = before - after
    pct_dropped = 100.0 * dropped / before if before else 0.0
    return {
        "tokens_before": int(before),
        "tokens_after": int(after),
        "tokens_dropped": int(dropped),
        "pct_dropped": pct_dropped,
    }


def delete_consumed(path: str) -> None:
    p = Path(path)
    if p.exists():
        size_mb = p.stat().st_size / 1e6
        p.unlink()
        print(f"[cleanup] deleted consumed intermediate {path} ({size_mb:.0f} MB)")
