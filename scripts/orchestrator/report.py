"""Phase 10 — Implementation Report.

Generate ORCHESTRATOR_IMPLEMENTATION_REPORT.md summarizing the engine:
mission statistics, phase coverage, commands, and health of the registry.
Deterministic output backed by the mission history.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from scripts.kernel.core import REPO_ROOT
from scripts.orchestrator.core import (
    ENGINES,
    MISSION_DIR,
    SURFACE_ROUTING,
    read_json,
)

REPORT_PATH = REPO_ROOT / "ORCHESTRATOR_IMPLEMENTATION_REPORT.md"


def _missions_scan() -> list[dict]:
    """Read every persisted mission record."""
    records = []
    if MISSION_DIR.exists():
        for path in sorted(MISSION_DIR.glob("ORN-*.json")):
            records.append(read_json(path))
    return records


def mission_stats(records: list[dict] | None = None) -> dict:
    """Aggregate counts across all missions."""
    records = records if records is not None else _missions_scan()
    stats = {
        "total": len(records),
        "closed": 0,
        "failed": 0,
        "executing": 0,
        "by_type": {},
        "failures": 0,
        "recoveries": 0,
        "decisions": 0,
        "tasks_assigned": 0,
        "tasks_completed": 0,
    }
    for r in records:
        status = r.get("status", "received")
        if status in stats:
            stats[status] += 1
        mtype = r.get("mission_type", "unknown")
        stats["by_type"][mtype] = stats["by_type"].get(mtype, 0) + 1
        stats["failures"] += len(r.get("failure_history", []))
        stats["recoveries"] += len(r.get("recovery_history", []))
        stats["decisions"] += len(r.get("decisions", []))
        stats["tasks_assigned"] += r.get("assigned_tasks", 0)
        stats["tasks_completed"] += r.get("completed_tasks", 0)
    return stats


def render(records: list[dict] | None = None) -> str:
    """Render the implementation report markdown."""
    stats = mission_stats(records)
    now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# GULA Orchestrator Engine — Implementation Report",
        "",
        f"Generated: {now}",
        "",
        "## Engine Summary",
        "",
        "The Orchestrator is the executive brain of the GULA platform. It turns a",
        "single human objective into a managed workflow end-to-end:",
        "**classify → plan → route → schedule → execute → verify → deploy → learn → report**.",
        "It coordinates the Builder (execution), Reviewer (verification), and",
        "Deployer (delivery) engines without writing code or reviewing directly.",
        "",
        "## Phase Coverage",
        "",
        "| Phase | Module | Responsibility |",
        "|---|---|---|",
        "| 0 | `audit.py` | Detect available engines and surfaces |",
        "| 1 | `classifier.py` | Mission type, priority, complexity, risk |",
        "| 2 | `planner.py` | Budgeted micro-phase tasks |",
        "| 3 | `router.py` | Route tasks to engines/surfaces |",
        "| 4 | `dependencies.py` | Build DAG + critical path |",
        "| 5 | `checkpoint.py` | Durable save/resume per step |",
        "| 6 | `failure.py` | Failure classification + recovery |",
        "| 7 | `resources.py` | Context/repo/time/memory limits + auto-split |",
        "| 8 | `dashboard.py` | `MISSION_STATUS.md` live view |",
        "| 9 | `history.py` | Registry, timeline, decision/failure/recovery log |",
        "| 10 | `report.py` | This implementation report |",
        "",
        "## Engines in Scope",
        "",
        "| Engine | Exists | Capability |",
        "|---|---|---|",
    ]
    from .audit import detect

    detected = detect()
    for engine in ENGINES:
        exists = engine in detected
        lines.append(f"| {engine} | {'yes' if exists else 'no'} | {SURFACE_ROUTING.get(engine, '')} |")
    lines.append("")
    lines.append("## Mission Statistics")
    lines.append("")
    lines.append(f"- Total missions: **{stats['total']}**")
    lines.append(f"- Closed: {stats['closed']} | Failed: {stats['failed']} | Executing: {stats['executing']}")
    lines.append(f"- By type: {', '.join(f'{k}={v}' for k, v in sorted(stats['by_type'].items()))}")
    lines.append(f"- Tasks assigned/completed: {stats['tasks_completed']}/{stats['tasks_assigned']}")
    lines.append(f"- Failures: {stats['failures']} | Recoveries: {stats['recoveries']} | Decisions: {stats['decisions']}")
    lines.append("")
    return "\n".join(lines)


def write_report(path: Path = REPORT_PATH) -> Path:
    """Persist the implementation report."""
    path.write_text(render(), encoding="utf-8")
    return path
