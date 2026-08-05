"""Phase 9 — Mission History.

Maintain the mission registry, timeline, decision log, execution history,
failure history, recovery history, and completion reports. Every mission is
persisted and searchable.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from scripts.orchestrator.core import (
    HISTORY_DIR,
    MISSION_DIR,
    MissionRecord,
    make_id,
    read_json,
    write_json,
)

REGISTRY_PATH = HISTORY_DIR / "registry.json"


def _mission_file(mission_id: str) -> Path:
    MISSION_DIR.mkdir(parents=True, exist_ok=True)
    return MISSION_DIR / f"{mission_id}.json"


def persist_record(record: MissionRecord) -> Path:
    """Write a mission record to its durable file."""
    return write_json(_mission_file(record.mission_id), record.to_dict())


def load_record(mission_id: str) -> MissionRecord:
    """Load a mission record (empty default when missing)."""
    data = read_json(_mission_file(mission_id))
    return MissionRecord(
        mission_id=mission_id,
        objective=data.get("objective", ""),
        mission_type=data.get("mission_type", ""),
        status=data.get("status", "received"),
        priority=data.get("priority", "medium"),
        complexity=data.get("complexity", "low"),
        risk=data.get("risk", "low"),
        plan_id=data.get("plan_id", ""),
        progress_percent=data.get("progress_percent", 0.0),
        health_score=data.get("health_score", 100.0),
        assigned_tasks=data.get("assigned_tasks", 0),
        completed_tasks=data.get("completed_tasks", 0),
        blocked_tasks=data.get("blocked_tasks", 0),
        timeline=data.get("timeline", []),
        decisions=data.get("decisions", []),
        failure_history=data.get("failure_history", []),
        recovery_history=data.get("recovery_history", []),
        created_at=data.get("created_at", ""),
        closed_at=data.get("closed_at", ""),
    )


def add_event(record: MissionRecord, event: str, detail: str = "") -> None:
    """Append a timeline event."""
    record.timeline.append({"event": event, "detail": detail, "event_id": make_id("EVT")})


def add_decision(record: MissionRecord, decision: str, rationale: str = "") -> None:
    """Record a decision in the decision log."""
    record.decisions.append({"decision": decision, "rationale": rationale})


def add_failure(record: MissionRecord, task_id: str, error: str, failure_class: str) -> None:
    """Record a failure event."""
    record.failure_history.append({
        "task_id": task_id,
        "error": error,
        "failure_class": failure_class,
        "failure_id": make_id("FLR"),
    })


def add_recovery(record: MissionRecord, task_id: str, action: str) -> None:
    """Record a recovery event."""
    record.recovery_history.append({
        "task_id": task_id,
        "action": action,
        "recovery_id": make_id("RCV"),
    })


def close_mission(record: MissionRecord, verdict: str = "completed") -> None:
    """Close a mission: status, closing event, and persist."""
    record.status = "closed" if verdict == "completed" else "failed"
    record.closed_at = datetime.now(UTC).isoformat()
    add_event(record, "mission closed", verdict)


def _registry() -> dict:
    return read_json(REGISTRY_PATH)


def register(mission_id: str, objective: str, mission_type: str, status: str) -> None:
    """Add or update a mission in the registry."""
    data = _registry()
    data.setdefault("missions", {})[mission_id] = {
        "objective": objective,
        "mission_type": mission_type,
        "status": status,
    }
    write_json(REGISTRY_PATH, data)


def list_missions() -> list[dict]:
    """List every registered mission, newest objective name first."""
    data = _registry().get("missions", {})
    return [
        {"mission_id": mid, **info}
        for mid, info in sorted(data.items(), key=lambda kv: kv[0])
    ]


def search_missions(query: str) -> list[dict]:
    """Search registered missions by objective substring (case-insensitive)."""
    query_lower = query.lower()
    return [
        m for m in list_missions()
        if query_lower in m.get("objective", "").lower()
    ]


def completion_report(record: MissionRecord) -> str:
    """Render a completion report for a mission."""
    lines = [
        f"# Mission Completion Report — {record.mission_id}",
        "",
        f"- Objective: {record.objective}",
        f"- Type: {record.mission_type}",
        f"- Status: {record.status}",
        f"- Progress: {record.progress_percent}%",
        f"- Health: {record.health_score:.1f}/100",
        f"- Tasks: {record.completed_tasks}/{record.assigned_tasks}",
        f"- Failures: {len(record.failure_history)}",
        f"- Recoveries: {len(record.recovery_history)}",
        f"- Decisions: {len(record.decisions)}",
        "",
        "## Timeline",
        "",
    ]
    for event in record.timeline:
        lines.append(f"- {event.get('event')}: {event.get('detail', '')}")
    lines.append("")
    return "\n".join(lines)
