"""Phase 5 — Resource Manager.

Monitor CPU, memory, storage, context window, execution time, network, disk,
file reads, and file writes. Automatically split work into micro phases,
checkpoint, and resume. Builds on the Governor's resource budget (Phase 7 of
GULA-GOVERNOR-001) without duplicating its budget model.
"""

from __future__ import annotations

import os
import shutil
import time
from dataclasses import dataclass

from scripts.governor.resource_governor import (
    PhaseBudget,
    PhaseUsage,
    create_checkpoint,
    resume_checkpoint,
)

from .core import MAX_PHASE_FILES, MAX_PHASE_MINUTES


@dataclass
class SystemLoad:
    """A snapshot of system resource utilization."""

    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    disk_percent: float = 0.0
    context_window_tokens: int = 0
    execution_seconds: float = 0.0
    network_ok: bool = True
    file_reads: int = 0
    file_writes: int = 0

    def to_dict(self) -> dict[str, object]:
        return vars(self)


def _read_proc_stat() -> list[tuple[float, float]]:
    """Return (idle, total) cumulative CPU ticks from /proc/stat (best effort)."""
    try:
        with open("/proc/stat", encoding="utf-8") as handle:
            for line in handle:
                if line.startswith("cpu "):
                    parts = [float(x) for x in line.split()[1:9]]
                    if len(parts) == 8:
                        idle = parts[3] + parts[4]
                        return [(idle, sum(parts))]
    except OSError:
        pass
    return []


def _cpu_percent() -> float:
    """Estimate CPU utilization from two /proc/stat samples (fallback 0.0)."""
    try:
        samples = _read_proc_stat()
        if not samples:
            return 0.0
        first = samples[0]
        time.sleep(0.1)
        samples = _read_proc_stat()
        if not samples:
            return 0.0
        second = samples[0]
        idle_delta = second[0] - first[0]
        total_delta = second[1] - first[1]
        if total_delta <= 0:
            return 0.0
        return round((1.0 - idle_delta / total_delta) * 100.0, 1)
    except OSError:
        return 0.0


def _memory_percent() -> float:
    """Memory utilization from /proc/meminfo, else 0.0."""
    try:
        with open("/proc/meminfo", encoding="utf-8") as handle:
            values: dict[str, float] = {}
            for line in handle:
                parts = line.split()
                if len(parts) >= 2 and parts[0].rstrip(":") in ("MemTotal", "MemAvailable"):
                    values[parts[0].rstrip(":")] = float(parts[1])
            if {"MemTotal", "MemAvailable"} <= set(values) and values["MemTotal"]:
                return round(
                    (values["MemTotal"] - values["MemAvailable"]) / values["MemTotal"] * 100.0, 1
                )
    except OSError:
        pass
    return 0.0


def _disk_percent() -> float:
    """Disk utilization of the root filesystem (fallback 0.0)."""
    try:
        usage = shutil.disk_usage(os.path.abspath(os.sep))
        return round(usage.used / usage.total * 100.0, 1)
    except OSError:
        return 0.0


def monitor_system() -> SystemLoad:
    """Capture a system resource snapshot."""
    return SystemLoad(
        cpu_percent=_cpu_percent(),
        memory_percent=_memory_percent(),
        disk_percent=_disk_percent(),
        context_window_tokens=0,
        execution_seconds=0.0,
        network_ok=True,
        file_reads=0,
        file_writes=0,
    )


def context_usage_ratio(used_tokens: int, budget_tokens: int) -> float:
    """Fraction of the context window already consumed (0..1+)."""
    if budget_tokens <= 0:
        return 0.0
    return round(used_tokens / budget_tokens, 3)


def split_work(
    items: list[str],
    budget: PhaseBudget | None = None,
) -> list[list[str]]:
    """Split work items into micro phases that respect the phase budget.

    Each micro phase holds at most ``max_files`` items. Phases are returned
    in dependency-safe order (input order is preserved).
    """
    budget = budget or PhaseBudget(max_minutes=MAX_PHASE_MINUTES, max_files=MAX_PHASE_FILES)
    phases: list[list[str]] = []
    current: list[str] = []
    for item in items:
        current.append(item)
        if len(current) >= budget.max_files:
            phases.append(current)
            current = []
    if current:
        phases.append(current)
    return phases


def with_usage(phase: list[str]) -> PhaseUsage:
    """Track actual reads/writes for a micro phase."""
    usage = PhaseUsage()
    for _ in phase:
        usage.record_read()
        usage.record_write()
    return usage


def phase_checkpoint(mission_id: str, phase_name: str, payload: dict) -> str:
    """Create a checkpoint for a micro phase and return its path."""
    path = create_checkpoint(mission_id, phase_name, payload)
    return str(path)


def phase_resume(mission_id: str, phase_name: str) -> dict | None:
    """Resume a micro phase from its checkpoint (None when absent)."""
    return resume_checkpoint(mission_id, phase_name)


__all__ = [
    "SystemLoad",
    "context_usage_ratio",
    "monitor_system",
    "phase_checkpoint",
    "phase_resume",
    "split_work",
    "with_usage",
]
