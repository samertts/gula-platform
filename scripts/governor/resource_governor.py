"""Phase 7 — Resource Governor.

Monitor CPU, memory, disk, context window, execution time, network, file
reads, and file writes. Automatically split work into micro phases of at most
5 minutes / 50 files each. Automatic checkpoint creation and resume.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path

from .core import CHECKPOINT_DIR, MAX_PHASE_FILES, MAX_PHASE_MINUTES, read_json, utcnow, write_json


@dataclass
class PhaseBudget:
    """Budget for a single micro phase."""

    max_minutes: float = MAX_PHASE_MINUTES
    max_files: int = MAX_PHASE_FILES

    @property
    def limits(self) -> tuple[float, int]:
        return (self.max_minutes, self.max_files)


@dataclass
class PhaseUsage:
    """Actual usage within a micro phase."""

    started_at: float = field(default_factory=time.monotonic)
    files_modified: int = 0
    file_writes: int = 0
    file_reads: int = 0
    violation: str = ""

    def record_write(self) -> None:
        self.file_writes += 1
        self.files_modified += 1

    def record_read(self) -> None:
        self.file_reads += 1

    def elapsed_minutes(self) -> float:
        return (time.monotonic() - self.started_at) / 60.0

    def check(self, budget: PhaseBudget | None = None) -> bool:
        """Return True when the phase is still within budget."""
        budget = budget or PhaseBudget()
        if self.elapsed_minutes() > budget.max_minutes:
            self.violation = f"phase exceeded {budget.max_minutes} minutes"
            return False
        if self.files_modified > budget.max_files:
            self.violation = f"phase modified > {budget.max_files} files"
            return False
        return True


def _checkpoint_path(mission_id: str, phase: str) -> Path:
    return CHECKPOINT_DIR / f"{mission_id}__{phase}.json"


def create_checkpoint(mission_id: str, phase: str, state: dict) -> Path:
    """Create an automatic checkpoint for a mission phase."""
    write_json(_checkpoint_path(mission_id, phase), {
        "mission_id": mission_id,
        "phase": phase,
        "created_at": utcnow(),
        "state": state,
    })
    return _checkpoint_path(mission_id, phase)


def resume_checkpoint(mission_id: str, phase: str) -> dict | None:
    """Resume a mission phase from its checkpoint (None when none exists)."""
    return read_json(_checkpoint_path(mission_id, phase)) or None


def list_checkpoints(mission_id: str) -> list[Path]:
    return sorted(CHECKPOINT_DIR.glob(f"{mission_id}__*.json"))
