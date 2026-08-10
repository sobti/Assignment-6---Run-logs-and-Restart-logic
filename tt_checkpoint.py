"""
Checkpoint save/load for the real tiny_transformer.py model -- shared by
train_tiny_transformer.py (fresh runs) and restart.py (the resume
trigger), so both write/read the exact same format.

Split across three files per checkpoint, using the right tool for each:
  - model_state.pt / optimizer_state.pt: real torch.save() of
    model.state_dict()/optimizer.state_dict() -- the standard way to
    checkpoint a PyTorch model, not reinvented as JSON/npz.
  - trainer_state.json: everything else needed to resume exactly --
    global_step, RNG state (python + numpy + torch, snapshotted for
    completeness even though this model has no dropout/sampling to
    desync -- see training_state.py's identical rationale for the dummy
    model), the exact dataloader cursor (reusing training_state.py's
    TrainingSchedule/LaneCursor, which is framework-agnostic), the model
    config needed to reconstruct the architecture before loading weights,
    and sha256 hashes of the two .pt files for integrity checking.
  - checkpoint_manifest.json: the same human-auditable 15-field schema
    used by save_checkpoint.py's dummy-model checkpoints.
"""

from __future__ import annotations

import hashlib
import json
import random
import subprocess
from pathlib import Path

import numpy as np
import tiktoken
import torch

from provenance import script_hash
from tiny_transformer import TinyTransformer, TinyTransformerConfig
from tokenize_and_admit import ENCODING_NAME, tokenizer_hash as _tokenizer_hash
from training_state import TrainingSchedule

CHECKPOINT_DIR = Path("checkpoints_tt")
SEQ_LEN = 2048  # packed sequence length in packed/<lane>/*.npz (the model's context_len is a slice of this)


def git_branch() -> str:
    return subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True, check=True
    ).stdout.strip()


def snapshot_rng() -> dict:
    v, state, gauss = random.getstate()
    name, keys, pos, has_gauss, cached = np.random.get_state()
    return {
        "python_random": [v, list(state), gauss],
        "numpy_random": [name, keys.tolist(), int(pos), int(has_gauss), float(cached)],
        "torch_random": torch.get_rng_state().tolist(),
    }


def restore_rng(snap: dict) -> None:
    v, state, gauss = snap["python_random"]
    random.setstate((v, tuple(state), gauss))
    name, keys, pos, has_gauss, cached = snap["numpy_random"]
    np.random.set_state((name, np.array(keys, dtype=np.uint32), pos, has_gauss, cached))
    torch.set_rng_state(torch.tensor(snap["torch_random"], dtype=torch.uint8))


def code_version() -> dict:
    enc = tiktoken.get_encoding(ENCODING_NAME)
    return {
        "tokenizer_version": f"{ENCODING_NAME}:{_tokenizer_hash(enc)}",
        "dataloader_version": "dataloader_" + script_hash("tokenize_and_admit.py")[:12],
        "model_version": "model_" + script_hash("tiny_transformer.py")[:12],
        "checkpoint_version": "ckptcode_" + script_hash("tt_checkpoint.py")[:12],
    }


def _sha256_file(path: Path) -> str:
    return "sha256_" + hashlib.sha256(path.read_bytes()).hexdigest()[:12]


def save_full_checkpoint(
    model: TinyTransformer,
    optimizer: torch.optim.Optimizer,
    schedule: TrainingSchedule,
    run_id: str,
    global_step: int,
    last_mb: dict,
) -> Path:
    checkpoint_id = f"ckpt-tt-{run_id}-step{global_step:09d}"
    out_dir = CHECKPOINT_DIR / checkpoint_id
    out_dir.mkdir(parents=True, exist_ok=True)

    model_path = out_dir / "model_state.pt"
    optim_path = out_dir / "optimizer_state.pt"
    torch.save(model.state_dict(), model_path)
    torch.save(optimizer.state_dict(), optim_path)

    cv = code_version()
    trainer_state = {
        "run_id": run_id,
        "checkpoint_id": checkpoint_id,
        "global_step": global_step,
        "model_config": {
            "vocab_size": model.config.vocab_size,
            "d_model": model.config.d_model,
            "d_ff": model.config.d_ff,
            "n_layers": model.config.n_layers,
            "context_len": model.config.context_len,
        },
        "rng_state": snapshot_rng(),
        "dataloader_cursor": schedule.to_dict(),
        "code_version": cv,
        "branch_id": git_branch(),
        "model_state_file": {"path": model_path.name, "sha256": _sha256_file(model_path)},
        "optimizer_state_file": {"path": optim_path.name, "sha256": _sha256_file(optim_path)},
    }
    (out_dir / "trainer_state.json").write_text(json.dumps(trainer_state, indent=2))

    manifest = {
        "run_id": run_id,
        "branch_id": trainer_state["branch_id"],
        "global_step": global_step,
        "checkpoint_id": checkpoint_id,
        "rank": 0,
        "microbatch_id": f"mb-{last_mb['shard_id']}-rows{last_mb['rows'][0]}-{last_mb['rows'][-1]}",
        "packed_sample_ids": [f"{last_mb['shard_id']}:{r}" for r in last_mb["rows"]],
        "shard_ids": [last_mb["shard_id"]],
        "token_span_ids": [[0, model.config.context_len] for _ in last_mb["rows"]],
        "loss_mask_hash": "sha256_" + hashlib.sha256(
            last_mb["loss_mask"][:, : model.config.context_len].tobytes()
        ).hexdigest()[:12],
        "attention_and_position_policy": (
            f"causal single-head attention (torch scaled_dot_product_attention, "
            f"is_causal=True), absolute learned position embeddings over the first "
            f"{model.config.context_len} tokens of each packed sequence; no LayerNorm, "
            f"no multi-head split -- a minimal real architecture, not a production one"
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
    candidates = []
    for d in CHECKPOINT_DIR.glob("ckpt-tt-*"):
        state_path = d / "trainer_state.json"
        if state_path.exists():
            step = json.loads(state_path.read_text())["global_step"]
            candidates.append((step, d))
    if not candidates:
        return None
    return max(candidates, key=lambda c: c[0])[1]


def load_full_checkpoint(ckpt_dir: Path) -> tuple[TinyTransformer, torch.optim.Optimizer, TrainingSchedule, str, int]:
    state = json.loads((ckpt_dir / "trainer_state.json").read_text())

    for key, info in (("model_state_file", None), ("optimizer_state_file", None)):
        path = ckpt_dir / state[key]["path"]
        actual = _sha256_file(path)
        if actual != state[key]["sha256"]:
            raise ValueError(f"{key} integrity check failed: expected {state[key]['sha256']}, got {actual}")

    restore_rng(state["rng_state"])

    config = TinyTransformerConfig(**state["model_config"])
    model = TinyTransformer(config)
    model.load_state_dict(torch.load(ckpt_dir / state["model_state_file"]["path"], weights_only=True))

    optimizer = torch.optim.SGD(model.parameters())  # hyperparams overwritten by the loaded state below
    optimizer.load_state_dict(torch.load(ckpt_dir / state["optimizer_state_file"]["path"], weights_only=True))

    schedule = TrainingSchedule.from_dict(state["dataloader_cursor"])
    return model, optimizer, schedule, state["run_id"], state["global_step"]
