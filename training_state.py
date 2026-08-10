"""
Shared, resumable data-loading state used by both TinyTransformer training
scripts (train_tiny_transformer.py / restart.py) and run_audit.py: a
deterministic round-robin iterator over packed/<lane>/*.npz, so "resume from
step N" means literally continuing at microbatch N+1, never skipping or
repeating data.

TrainingSchedule.to_dict()/from_dict() is exactly what tt_checkpoint.py
saves as trainer_state.json's dataloader_cursor and restores on resume --
the framework-agnostic piece of the checkpoint format.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

PACKED_DIR = Path("packed")

LANE_ORDER = ["indic", "web", "code"]
MICROBATCH_SIZE = 4
SEQ_LEN = 2048


def load_microbatch(lane: str, shard_id: str, rows: list[int]) -> dict:
    d = np.load(PACKED_DIR / lane / f"{shard_id}.npz")
    return {
        "lane": lane, "shard_id": shard_id, "rows": rows,
        "token_id": d["token_id"][rows], "loss_mask": d["loss_mask"][rows],
        "doc_id": d["doc_id"][rows],
    }


# --------------------------------------------------------------------------
# Deterministic, resumable data iteration
# --------------------------------------------------------------------------

class LaneCursor:
    """Position within one lane's packed shards: shard_idx indexes into the
    lane's sorted shard list, row_idx is the next row to read within that
    shard. A microbatch is never split across a shard boundary -- if fewer
    than MICROBATCH_SIZE rows remain in the current shard, the leftover
    rows are skipped and the cursor advances to the next shard. That's a
    real (if minor) tradeoff: a few rows at the tail of each shard never
    get sampled. Documented here rather than silently accepted."""

    def __init__(self, lane: str, shard_ids: list[str], shard_idx: int = 0, row_idx: int = 0):
        self.lane = lane
        self.shard_ids = shard_ids
        self.shard_idx = shard_idx
        self.row_idx = row_idx

    @classmethod
    def fresh(cls, lane: str) -> "LaneCursor":
        shard_ids = sorted(p.stem for p in (PACKED_DIR / lane).glob("*.npz"))
        return cls(lane, shard_ids)

    def to_dict(self) -> dict:
        return {"shard_ids": self.shard_ids, "shard_idx": self.shard_idx, "row_idx": self.row_idx}

    @classmethod
    def from_dict(cls, lane: str, d: dict) -> "LaneCursor":
        return cls(lane, d["shard_ids"], d["shard_idx"], d["row_idx"])

    @property
    def exhausted(self) -> bool:
        return self.shard_idx >= len(self.shard_ids)

    def next_microbatch(self, size: int = MICROBATCH_SIZE) -> dict | None:
        while not self.exhausted:
            shard_id = self.shard_ids[self.shard_idx]
            n_rows = np.load(PACKED_DIR / self.lane / f"{shard_id}.npz")["token_id"].shape[0]
            if self.row_idx + size > n_rows:
                self.shard_idx += 1
                self.row_idx = 0
                continue
            rows = list(range(self.row_idx, self.row_idx + size))
            self.row_idx += size
            return load_microbatch(self.lane, shard_id, rows)
        return None


class TrainingSchedule:
    """Round-robins microbatches across LANE_ORDER, skipping any lane
    that's exhausted, so the lane mix stays even over the course of
    training rather than draining one lane before touching the next."""

    def __init__(self, cursors: dict[str, LaneCursor], next_lane_pointer: int = 0):
        self.cursors = cursors
        self.next_lane_pointer = next_lane_pointer

    @classmethod
    def fresh(cls) -> "TrainingSchedule":
        return cls({lane: LaneCursor.fresh(lane) for lane in LANE_ORDER})

    def to_dict(self) -> dict:
        return {
            "next_lane_pointer": self.next_lane_pointer,
            "lane_cursors": {lane: c.to_dict() for lane, c in self.cursors.items()},
        }

    @classmethod
    def from_dict(cls, d: dict) -> "TrainingSchedule":
        cursors = {lane: LaneCursor.from_dict(lane, cd) for lane, cd in d["lane_cursors"].items()}
        return cls(cursors, d["next_lane_pointer"])

    def next_microbatch(self) -> dict | None:
        for _ in range(len(LANE_ORDER)):
            lane = LANE_ORDER[self.next_lane_pointer]
            self.next_lane_pointer = (self.next_lane_pointer + 1) % len(LANE_ORDER)
            mb = self.cursors[lane].next_microbatch()
            if mb is not None:
                return mb
        return None  # every lane exhausted
