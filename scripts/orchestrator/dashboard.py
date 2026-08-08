"""Phase 8 — Mission Dashboard.

Generate MISSION_STATUS.md showing the current mission, current phase,
completed / running / blocked tasks, estimated remaining time, health score,
and progress percentage. Deterministic; the numbers come from the mission
record and the routed plan.
"""

from __future__ import annotations

from pathlib import Path

from scripts.kernel.core import REPO_ROOT
from scripts.orchestrator.core import (
    MissionRecord,
    OrchestratedPlan,
    TaskStatus,
)

STATUS_PATH = REPO_ROOT / "docs/programs/MISSION_STATUS.md"

BLOCKED_PENALTY = 5.0
FAILURE_PENALTY = 10.0


def compute_progress(record: MissionRecord, plan: OrchestratedPlan) -> MissionRecord:
    """Derive progress %, counts, and health score from the plan."""
    total = len(plan.tasks)
    completed = sum(1 for t in plan.tasks if t.status == TaskStatus.COMPLETED.value)
    blocked = sum(1 for t in plan.tasks if t.status == TaskStatus.BLOCKED.value)
    failed = sum(1 for t in plan.tasks if t.status == TaskStatus.FAILED.value)

    record.assigned_tasks = total
    record.completed_tasks = completed
    record.blocked_tasks = blocked
    record.progress_percent = round(100.0 * completed / total, 1) if total else 0.0

    health = 100.0
    health -= blocked * BLOCKED_PENALTY
    health -= failed * FAILURE_PENALTY
    record.health_score = round(max(0.0, health), 1)
    return record


def remaining_minutes(plan: OrchestratedPlan) -> int:
    """Estimated remaining time from pending/running tasks."""
    total = 0
    for task in plan.tasks:
        if task.status in {TaskStatus.PENDING.value, TaskStatus.RUNNING.value, TaskStatus.BLOCKED.value}:
            total += task.estimated_minutes
    return total


def current_phase(plan: OrchestratedPlan) -> str:
    """Name of the phase containing the first non-completed task."""
    for task in plan.tasks:
        if task.status in {TaskStatus.PENDING.value, TaskStatus.RUNNING.value, TaskStatus.BLOCKED.value}:
            name = task.name
            start = name.find("[")
            end = name.find("]")
            if start != -1 and end != -1:
                return name[start + 1:end]
            return "General"
    return "Complete"


def render(record: MissionRecord, plan: OrchestratedPlan) -> str:
    """Render the mission dashboard markdown."""
    lines = [
        "# MISSION_STATUS.md",
        "",
        f"## {record.mission_id} — {record.mission_type} mission",
        "",
        f"**Objective:** {record.objective}",
        "",
        f"- Status: **{record.status}**",
        f"- Current phase: **{current_phase(plan)}**",
        f"- Progress: **{record.progress_percent}%**",
        f"- Health score: **{record.health_score:.1f}/100**",
        f"- Estimated remaining: **{remaining_minutes(plan)} minutes**",
        f"- Tasks: {record.completed_tasks}/{record.assigned_tasks} completed, "
        f"{record.blocked_tasks} blocked",
        "",
        "## Task Status",
        "",
        "| Task | Surface | Engine | Minutes | Status |",
        "|---|---|---|---|---|",
    ]
    for task in plan.tasks:
        lines.append(
            f"| {task.name} | {task.surface} | {task.engine or '—'} | "
            f"{task.estimated_minutes} | {task.status} |"
        )
    lines.append("")
    return "\n".join(lines)


def write_status(record: MissionRecord, plan: OrchestratedPlan, path: Path = STATUS_PATH) -> Path:
    """Persist the dashboard to MISSION_STATUS.md (or the given path)."""
    compute_progress(record, plan)
    path.write_text(render(record, plan), encoding="utf-8")
    return path
