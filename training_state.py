"""
Shared, resumable training state for the dummy training loop: a
deterministic round-robin data iterator over packed/<lane>/*.npz (so
"resume from step N" means literally continuing at microbatch N+1, never
skipping or repeating data), a dummy model with real (if trivial) weight/
optimizer state that actually evolves over steps, and RNG snapshotting.

Everything a genuine resume needs is captured in one trainer_state.json
per checkpoint:
  - global_step
  - model_state (weight, lr, momentum -- the dummy "model")
  - rng_state (python's random + numpy's RNG, captured even though the
    current dummy forward pass doesn't consume them, because a real
    resume must restore RNG state regardless of what today's dummy logic
    happens to use -- see DummyModel.forward_and_update)
  - dataloader_cursor (exact lane/shard/row position to resume from)
  - code_version (hashes tying the checkpoint to the exact script versions
    that produced it)

save_checkpoint.py uses this to start a run from scratch (step 0, fresh
cursor); resume_training.py (a separate script, as requested) uses it to
find the latest checkpoint and continue from exactly where it left off.
"""

from __future__ import annotations

import hashlib
import json
import random
import subprocess
from pathlib import Path

import numpy as np
import tiktoken

from provenance import script_hash
from tokenize_and_admit import ENCODING_NAME, tokenizer_hash as _tokenizer_hash

PACKED_DIR = Path("packed")
CHECKPOINT_DIR = Path("checkpoints")
TRAINING_LOG = Path("stats/training_log.jsonl")

LANE_ORDER = ["indic", "web", "code"]
MICROBATCH_SIZE = 4
SEQ_LEN = 2048


def git_branch() -> str:
    return subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True, check=True
    ).stdout.strip()


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


# --------------------------------------------------------------------------
# Dummy model with real (if trivial) evolving state
# --------------------------------------------------------------------------

class DummyModel:
    """Not a real model -- one scalar 'weight' updated by a toy momentum
    rule. Exists so there is real state that changes across steps and
    genuinely needs saving/restoring for a resume to be meaningful, rather
    than a resume that trivially has nothing to lose."""

    def __init__(self, weight: float = 0.0, lr: float = 0.01, momentum: float = 0.0, step: int = 0):
        self.weight = weight
        self.lr = lr
        self.momentum = momentum
        self.step = step

    def forward_and_update(self, batch: dict) -> tuple[float, float]:
        """Deterministic 'loss' seeded from the batch's real token bytes
        (not random) -- reruns of the same data at the same step reproduce
        the same numbers. Not a real forward pass; nothing is learned."""
        seed = int(hashlib.sha256(batch["token_id"].tobytes()).hexdigest()[:8], 16)
        noise = (seed % 1000) / 1000.0 * 0.3
        loss = max(0.5, 4.0 * (0.92 ** self.step) + noise)
        grad = loss * 0.1
        self.momentum = 0.9 * self.momentum + grad
        self.weight -= self.lr * self.momentum
        self.step += 1
        return loss, float(np.exp(loss))

    def state_dict(self) -> dict:
        return {"weight": self.weight, "lr": self.lr, "momentum": self.momentum, "step": self.step}

    @classmethod
    def from_state_dict(cls, d: dict) -> "DummyModel":
        return cls(weight=d["weight"], lr=d["lr"], momentum=d["momentum"], step=d["step"])


# --------------------------------------------------------------------------
# RNG snapshot -- captured for completeness even though today's dummy
# forward pass is fully deterministic and doesn't consume RNG draws. A
# real resume must restore RNG state regardless; a checkpoint format that
# only works because the current model happens not to need it isn't
# actually resumable.
# --------------------------------------------------------------------------

def snapshot_rng() -> dict:
    v, state, gauss = random.getstate()
    name, keys, pos, has_gauss, cached = np.random.get_state()
    return {
        "python_random": [v, list(state), gauss],
        "numpy_random": [name, keys.tolist(), int(pos), int(has_gauss), float(cached)],
    }


def restore_rng(snap: dict) -> None:
    v, state, gauss = snap["python_random"]
    random.setstate((v, tuple(state), gauss))
    name, keys, pos, has_gauss, cached = snap["numpy_random"]
    np.random.set_state((name, np.array(keys, dtype=np.uint32), pos, has_gauss, cached))


# --------------------------------------------------------------------------
# Checkpoint save / load
# --------------------------------------------------------------------------

def code_version() -> dict:
    enc = tiktoken.get_encoding(ENCODING_NAME)
    return {
        "tokenizer_version": f"{ENCODING_NAME}:{_tokenizer_hash(enc)}",
        "dataloader_version": "dataloader_" + script_hash("tokenize_and_admit.py")[:12],
        "training_state_version": "trainstate_" + script_hash("training_state.py")[:12],
    }


def save_full_checkpoint(model: DummyModel, schedule: TrainingSchedule, run_id: str, last_mb: dict) -> Path:
    """Writes everything needed to resume exactly at the next microbatch:
    trainer_state.json (model/optimizer/RNG/dataloader-cursor state) plus
    the human-auditable checkpoint_manifest.json (provenance-style fields
    describing the last microbatch actually processed)."""
    checkpoint_id = f"ckpt-{run_id}-step{model.step:09d}"
    out_dir = CHECKPOINT_DIR / checkpoint_id
    out_dir.mkdir(parents=True, exist_ok=True)

    trainer_state = {
        "run_id": run_id,
        "checkpoint_id": checkpoint_id,
        "global_step": model.step,
        "model_state": model.state_dict(),
        "rng_state": snapshot_rng(),
        "dataloader_cursor": schedule.to_dict(),
        "code_version": code_version(),
        "branch_id": git_branch(),
    }
    (out_dir / "trainer_state.json").write_text(json.dumps(trainer_state, indent=2))

    cv = trainer_state["code_version"]
    manifest = {
        "run_id": run_id,
        "branch_id": trainer_state["branch_id"],
        "global_step": model.step,
        "checkpoint_id": checkpoint_id,
        "rank": 0,
        "microbatch_id": f"mb-{last_mb['shard_id']}-rows{last_mb['rows'][0]}-{last_mb['rows'][-1]}",
        "packed_sample_ids": [f"{last_mb['shard_id']}:{r}" for r in last_mb["rows"]],
        "shard_ids": [last_mb["shard_id"]],
        "token_span_ids": [[0, SEQ_LEN] for _ in last_mb["rows"]],
        "loss_mask_hash": "sha256_" + hashlib.sha256(last_mb["loss_mask"].tobytes()).hexdigest()[:12],
        "attention_and_position_policy": (
            "causal, flat (non-reset) position_ids across packed documents; "
            "no explicit cross-document attention mask is emitted by this "
            "pipeline -- attention is NOT restricted at document boundaries "
            "within a packed sequence unless the training framework derives "
            "a block mask from doc_id itself"
        ),
        "mixture_lane": last_mb["lane"].capitalize(),
        "curriculum_stage": "stage_0_uniform",  # mock -- no curriculum engine implemented in this project
        "tokenizer_version": cv["tokenizer_version"],
        "dataloader_version": cv["dataloader_version"],
        "opus_decision_id": "opus-mix-v5-50w25i25c",  # mock -- ties to the 50/25/25 web/indic/code ratio (build_corpus.py)
    }
    (out_dir / "checkpoint_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    return out_dir


def find_latest_checkpoint() -> Path | None:
    """Latest by global_step parsed out of the checkpoint_id (not directory
    mtime, which is fragile across filesystems/copies)."""
    candidates = []
    for d in CHECKPOINT_DIR.glob("ckpt-*"):
        state_path = d / "trainer_state.json"
        if state_path.exists():
            step = json.loads(state_path.read_text())["global_step"]
            candidates.append((step, d))
    if not candidates:
        return None
    return max(candidates, key=lambda c: c[0])[1]


def load_full_checkpoint(ckpt_dir: Path) -> tuple[DummyModel, TrainingSchedule, str]:
    state = json.loads((ckpt_dir / "trainer_state.json").read_text())
    restore_rng(state["rng_state"])
    model = DummyModel.from_state_dict(state["model_state"])
    schedule = TrainingSchedule.from_dict(state["dataloader_cursor"])
    return model, schedule, state["run_id"]


def append_training_log(records: list[dict]) -> None:
    TRAINING_LOG.parent.mkdir(exist_ok=True)
    with TRAINING_LOG.open("a", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")


def run_steps(model: DummyModel, schedule: TrainingSchedule, n_steps: int, run_id: str) -> tuple[list[dict], dict | None]:
    records = []
    last_mb = None
    for _ in range(n_steps):
        mb = schedule.next_microbatch()
        if mb is None:
            print("  all lanes exhausted -- stopping early")
            break
        loss, perplexity = model.forward_and_update(mb)
        last_mb = mb
        record = {
            "run_id": run_id, "step": model.step, "lane": mb["lane"], "shard_id": mb["shard_id"], "rows": mb["rows"],
            "loss": round(loss, 4), "perplexity": round(perplexity, 4),
        }
        records.append(record)
        print(f"  step {model.step:4d}  lane={mb['lane']:6s}  shard={mb['shard_id']:20s}"
              f"  loss={loss:.4f}  perplexity={perplexity:.4f}")
    return records, last_mb
