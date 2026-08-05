"""Phase 5 — Checkpoint Engine.

Every step saves progress: todo, status, checkpoint, current context, and
resume information. A mission can always be resumed from its latest
checkpoint without restarting. Never lose progress.
"""

from __future__ import annotations

from pathlib import Path

from scripts.orchestrator.core import (
    CHECKPOINT_DIR,
    Checkpoint,
    make_id,
    read_json,
    write_json,
)


def _mission_dir(mission_id: str) -> Path:
    path = CHECKPOINT_DIR / mission_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_checkpoint(
    mission_id: str,
    step: str,
    state: dict,
    *,
    checkpoint_id: str | None = None,
) -> Checkpoint:
    """Persist a durable checkpoint for the given mission/step."""
    checkpoint = Checkpoint(
        checkpoint_id=checkpoint_id or make_id("OCK"),
        mission_id=mission_id,
        step=step,
        state=state,
    )
    path = _mission_dir(mission_id) / f"{checkpoint.checkpoint_id}.json"
    write_json(path, checkpoint.to_dict())
    return checkpoint


def latest_checkpoint(mission_id: str) -> Checkpoint | None:
    """Return the most recently created checkpoint for a mission."""
    mission_dir = _mission_dir(mission_id)
    files = sorted(
        mission_dir.glob("*.json"),
        key=lambda p: (p.stat().st_mtime, p.name),
    )
    if not files:
        return None
    data = read_json(files[-1])
    return Checkpoint(
        checkpoint_id=data.get("checkpoint_id", ""),
        mission_id=data.get("mission_id", mission_id),
        step=data.get("step", ""),
        state=data.get("state", {}),
        created_at=data.get("created_at", ""),
    )


def resume_state(mission_id: str) -> dict:
    """Return the latest saved state (empty dict when none exists)."""
    checkpoint = latest_checkpoint(mission_id)
    return checkpoint.state if checkpoint else {}


def checkpoint_count(mission_id: str) -> int:
    mission_dir = _mission_dir(mission_id)
    return len(list(mission_dir.glob("*.json")))


def step_progress(mission_id: str, step: str) -> str | None:
    """Find the last checkpoint recorded for a step (resume point)."""
    checkpoint = latest_checkpoint(mission_id)
    if checkpoint and checkpoint.step == step:
        return checkpoint.checkpoint_id
    return None
