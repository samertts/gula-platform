"""Phase 7 — Resource Manager.

Continuously monitor context size, repository size, execution time, files
read, files modified, and memory consumption. Recommend splitting work before
limits are exceeded so context is never exhausted. The Orchestrator consumes
this advisory to split a mission into narrower missions.
"""

from __future__ import annotations

import time
from pathlib import Path

from scripts.orchestrator.core import (
    REPO_ROOT,
    ResourceUsage,
)

# Hard limits (bytes / seconds / counts). Percentages are advisory thresholds.
CONTEXT_LIMIT_BYTES = 128 * 1024 * 1024          # 128 MB context proxy
REPO_LIMIT_BYTES = 2 * 1024 * 1024 * 1024        # 2 GB
EXECUTION_LIMIT_SECONDS = 30 * 60                # 30 minutes
FILE_READ_LIMIT = 500
FILE_MODIFIED_LIMIT = 100
MEMORY_LIMIT_BYTES = 4 * 1024 * 1024 * 1024      # 4 GB
WARN_RATIO = 0.8


def repo_size_bytes(repo: Path = REPO_ROOT) -> int:
    """Total size of tracked Python/config sources under the repo."""
    total = 0
    excluded = {".venv", "site-packages", "node_modules", "__pycache__", ".git", "dist", "build"}
    for path in repo.rglob("*"):
        if not path.is_file():
            continue
        if any(part in excluded for part in path.parts):
            continue
        try:
            total += path.stat().st_size
        except OSError:
            continue
    return total


def snapshot(
    mission_id: str,
    *,
    context_bytes: int = 0,
    files_read: int = 0,
    files_modified: int = 0,
    memory_bytes: int = 0,
    started_at: float | None = None,
) -> ResourceUsage:
    """Compute a resource snapshot and the split advisory."""
    execution_seconds = int(time.time() - started_at) if started_at else 0
    usage = ResourceUsage(
        mission_id=mission_id,
        context_bytes=context_bytes,
        repo_bytes=repo_size_bytes(),
        execution_seconds=execution_seconds,
        files_read=files_read,
        files_modified=files_modified,
        memory_bytes=memory_bytes or _process_memory_bytes(),
    )
    usage.split_recommended, usage.split_reason = _split_advisory(usage)
    return usage


def _process_memory_bytes() -> int:
    try:
        import resource as _r

        return _r.getrusage(_r.RUSAGE_SELF).ru_maxrss * 1024
    except Exception:
        return 0


def _split_advisory(usage: ResourceUsage) -> tuple[bool, str]:
    """Return (split, reason) when any metric crosses the warning ratio."""
    checks = (
        (usage.context_bytes, CONTEXT_LIMIT_BYTES, "context size"),
        (usage.repo_bytes, REPO_LIMIT_BYTES, "repository size"),
        (usage.execution_seconds, EXECUTION_LIMIT_SECONDS, "execution time"),
        (usage.files_read, FILE_READ_LIMIT, "files read"),
        (usage.files_modified, FILE_MODIFIED_LIMIT, "files modified"),
        (usage.memory_bytes, MEMORY_LIMIT_BYTES, "memory"),
    )
    for value, limit, label in checks:
        if limit > 0 and value >= limit * WARN_RATIO:
            return True, f"{label} at {value}/{limit} exceeds {int(WARN_RATIO*100)}% warning ratio"
    return False, ""


def merge_usage(mission_id: str, *usages: ResourceUsage) -> ResourceUsage:
    """Merge per-step usages into one cumulative snapshot."""
    combined = ResourceUsage(mission_id=mission_id)
    for u in usages:
        combined.context_bytes += u.context_bytes
        combined.execution_seconds += u.execution_seconds
        combined.files_read += u.files_read
        combined.files_modified += u.files_modified
        combined.memory_bytes = max(combined.memory_bytes, u.memory_bytes)
        combined.repo_bytes = u.repo_bytes or combined.repo_bytes
    combined.split_recommended, combined.split_reason = _split_advisory(combined)
    return combined


def auto_split_tasks(task_ids: list[str]) -> list[list[str]]:
    """Split a list of task ids into batches that fit the modified-files budget."""
    batches: list[list[str]] = []
    current: list[str] = []
    for task_id in task_ids:
        current.append(task_id)
        if len(current) >= FILE_MODIFIED_LIMIT:
            batches.append(current)
            current = []
    if current:
        batches.append(current)
    return batches or [[]]
