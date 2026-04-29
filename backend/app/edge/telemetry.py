"""Telemetry — record and query device resource snapshots.

The agent posts a telemetry sample on every heartbeat; we persist a row and
keep a rolling retention window (env: EDGE_TELEMETRY_RETENTION_DAYS).

Operators access aggregate stats via /edge/devices/{id}/telemetry — which
reads from this module's helpers, not raw queries. Keeps the SQL surface
small and tenant-isolation easier to audit.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..models.edge import EdgeTelemetry
from .config import EDGE_TELEMETRY_RETENTION_DAYS


def record(db: Session, *, lab_id: int, device_id: str, sample: dict[str, Any]) -> None:
    """Persist a telemetry sample. Caller commits.

    Unknown fields in `sample` are ignored — only known columns are written.
    """
    allowed = {
        "cpu_pct", "mem_mb", "mem_total_mb", "gpu_pct", "battery_pct",
        "on_battery", "idle_s", "net_up_kbps", "net_down_kbps",
        "loaded_models", "queue_depth", "agent_uptime_s",
        "task_completed_total", "task_failed_total",
    }
    cleaned = {k: v for k, v in sample.items() if k in allowed}
    row = EdgeTelemetry(
        lab_id=lab_id,
        device_id=device_id,
        ts=datetime.now(timezone.utc),
        **cleaned,
    )
    db.add(row)


def latest(db: Session, *, device_id: str, lab_id: int) -> Optional[EdgeTelemetry]:
    return (
        db.query(EdgeTelemetry)
          .filter(EdgeTelemetry.device_id == device_id,
                  EdgeTelemetry.lab_id == lab_id)
          .order_by(EdgeTelemetry.ts.desc())
          .first()
    )


def history(
    db: Session, *, device_id: str, lab_id: int, hours: int = 6, limit: int = 720,
) -> list[EdgeTelemetry]:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=max(1, min(hours, 720)))
    return (
        db.query(EdgeTelemetry)
          .filter(EdgeTelemetry.device_id == device_id,
                  EdgeTelemetry.lab_id == lab_id,
                  EdgeTelemetry.ts >= cutoff)
          .order_by(EdgeTelemetry.ts.desc())
          .limit(limit)
          .all()
    )


def fleet_summary(db: Session, *, lab_id: int) -> dict[str, Any]:
    """Aggregate snapshot — used by the operator dashboard."""
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=10)
    rows = (
        db.query(EdgeTelemetry)
          .filter(EdgeTelemetry.lab_id == lab_id,
                  EdgeTelemetry.ts >= cutoff)
          .all()
    )
    if not rows:
        return {"online_devices": 0, "avg_cpu_pct": 0.0, "avg_mem_mb": 0.0}

    seen_devices: set[str] = set()
    cpu_sum = mem_sum = 0.0
    cnt = 0
    completed_total = failed_total = 0
    for r in rows:
        seen_devices.add(r.device_id)
        if r.cpu_pct is not None:
            cpu_sum += r.cpu_pct
            cnt += 1
        if r.mem_mb is not None:
            mem_sum += r.mem_mb
        completed_total += r.task_completed_total or 0
        failed_total += r.task_failed_total or 0
    return {
        "online_devices": len(seen_devices),
        "avg_cpu_pct": round(cpu_sum / cnt, 2) if cnt else 0.0,
        "avg_mem_mb": round(mem_sum / max(1, len(rows)), 1),
        "tasks_completed_total": completed_total,
        "tasks_failed_total": failed_total,
        "samples": len(rows),
    }


def sweep_old(db: Session) -> int:
    """Delete telemetry rows older than the retention window. Caller commits.

    Returns the number of rows removed.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=EDGE_TELEMETRY_RETENTION_DAYS)
    deleted = (
        db.query(EdgeTelemetry)
          .filter(EdgeTelemetry.ts < cutoff)
          .delete(synchronize_session=False)
    )
    return int(deleted or 0)
