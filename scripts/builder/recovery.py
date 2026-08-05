"""Phase 5 — Failure Recovery.

When any task fails:

    Never restart.
    Create checkpoint.
    Analyze failure.
    Retry.
    Resume.
    Continue.

Checkpoints are persisted under .ai/core/builder/state/checkpoints and are
loadable by mission id. Failures are classified (transient vs permanent) and
bounded retries are applied before resuming.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scripts.builder.core import (
    CHECKPOINT_DIR,
    Checkpoint,
    read_json,
    utcnow,
    write_json,
)

MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = (1, 2, 4)

TRANSIENT_MARKERS = ("timeout", "connection", "transient", "busy", "temporarily", "retry", "throttle")


class RecoveryError(Exception):
    """Raised for invalid recovery operations."""


@dataclass
class FailureAnalysis:
    """Classification of a single failure for the recovery path."""

    mission_id: str
    step: str
    classification: str  # transient | permanent | validation
    retries_left: int
    action: str  # retry | resume | abort
    detail: str = ""
    analyzed_at: str = field(default_factory=utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "mission_id": self.mission_id,
            "step": self.step,
            "classification": self.classification,
            "retries_left": self.retries_left,
            "action": self.action,
            "detail": self.detail,
            "analyzed_at": self.analyzed_at,
        }


def checkpoint_path(mission_id: str) -> Path:
    return CHECKPOINT_DIR / f"{mission_id}.json"


def create_checkpoint(mission_id: str, step: str, state: dict[str, Any] | None = None) -> Checkpoint:
    """Persist a checkpoint for a mission step."""
    checkpoint = Checkpoint(
        checkpoint_id=f"CHK-{uuid.uuid4().hex[:8].upper()}",
        mission_id=mission_id,
        step=step,
        state=state or {},
    )
    write_json(checkpoint_path(mission_id), checkpoint.to_dict())
    return checkpoint


def load_checkpoint(mission_id: str) -> Checkpoint | None:
    """Load the latest checkpoint for a mission (None when absent)."""
    data = read_json(checkpoint_path(mission_id))
    if not data:
        return None
    return Checkpoint(
        checkpoint_id=data.get("checkpoint_id", ""),
        mission_id=data.get("mission_id", mission_id),
        step=data.get("step", ""),
        state=data.get("state", {}),
        created_at=data.get("created_at", ""),
    )


def clear_checkpoint(mission_id: str) -> None:
    path = checkpoint_path(mission_id)
    if path.exists():
        path.unlink()


def list_checkpoints() -> list[Checkpoint]:
    """List every persisted checkpoint sorted by creation time."""
    checkpoints: list[Checkpoint] = []
    if not CHECKPOINT_DIR.exists():
        return checkpoints
    for path in CHECKPOINT_DIR.glob("*.json"):
        data = read_json(path)
        if data:
            checkpoints.append(Checkpoint(
                checkpoint_id=data.get("checkpoint_id", ""),
                mission_id=data.get("mission_id", ""),
                step=data.get("step", ""),
                state=data.get("state", {}),
                created_at=data.get("created_at", ""),
            ))
    return sorted(checkpoints, key=lambda c: c.created_at)


def classify_failure(exc: Exception | None, detail: str = "") -> str:
    """Classify a failure as transient, validation, or permanent."""
    message = f"{exc or ''} {detail}".lower()
    if any(marker in message for marker in TRANSIENT_MARKERS):
        return "transient"
    if any(word in message for word in ("invalid", "validation", "assert", "schema", "type error")):
        return "validation"
    return "permanent"


def analyze_failure(
    mission_id: str,
    step: str,
    exc: Exception | None,
    detail: str = "",
    retries_used: int = 0,
) -> FailureAnalysis:
    """Decide retry vs resume vs abort for a failed step."""
    classification = classify_failure(exc, detail)
    retries_left = max(0, MAX_RETRIES - retries_used)
    if classification == "permanent":
        action = "abort"
    elif classification == "validation":
        action = "resume"  # checkpoint exists; fix validation and continue
    else:
        action = "retry" if retries_left > 0 else "resume"
    return FailureAnalysis(
        mission_id=mission_id,
        step=step,
        classification=classification,
        retries_left=retries_left,
        action=action,
        detail=detail,
    )


def retry(
    fn: Any,
    *args: Any,
    retries: int = MAX_RETRIES,
    **kwargs: Any,
) -> Any:
    """Run fn with bounded retries (backoff via backoff_for())."""
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            return fn(*args, **kwargs)
        except Exception as exc:
            last_error = exc
            backoff_for(attempt + 1)
    if last_error is not None:
        raise last_error
    return None


def backoff_for(attempt: int) -> float:
    """Seconds to wait before retry N (1-based attempt)."""
    idx = min(attempt - 1, len(RETRY_BACKOFF_SECONDS) - 1)
    return RETRY_BACKOFF_SECONDS[idx]


def resume_step(mission_id: str) -> str | None:
    """The next step to run from a checkpoint (None when no checkpoint)."""
    checkpoint = load_checkpoint(mission_id)
    if checkpoint is None:
        return None
    from scripts.builder.planner import EXECUTION_ORDER

    if checkpoint.step not in EXECUTION_ORDER:
        return None
    index = EXECUTION_ORDER.index(checkpoint.step)
    if index + 1 >= len(EXECUTION_ORDER):
        return None
    return EXECUTION_ORDER[index + 1]


def _parse_time(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def checkpoint_age_seconds(checkpoint: Checkpoint) -> float:
    """Age of a checkpoint in seconds (0 for unparseable timestamps)."""
    parsed = _parse_time(checkpoint.created_at)
    if parsed is None:
        return 0.0
    try:
        return max(0.0, (datetime.now(UTC) - parsed).total_seconds())
    except OverflowError:
        return 0.0


def is_stale(checkpoint: Checkpoint, max_age_seconds: int = 3600) -> bool:
    """True when a checkpoint is older than the freshness window."""
    return checkpoint_age_seconds(checkpoint) > max_age_seconds
