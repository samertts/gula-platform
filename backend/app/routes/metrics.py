"""Lightweight operational metrics endpoint.

Returns system health numbers useful for a monitoring dashboard:
  - Process uptime and RSS memory (no psutil needed — reads /proc/self/status)
  - DB round-trip time
  - Redis round-trip time
  - Per-lab order counts (scoped: lab staff see their lab, admins see all)

All numbers are computed fresh on every request — no caching — so the
dashboard always reflects reality.  The endpoint is protected: callers
must be authenticated.
"""
import time
import os
from datetime import datetime, date, timezone
from sqlalchemy import text
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.lab_user import LabUser
from ..models.lab_order import LabOrder
from ..security.dependencies import get_current_user

router = APIRouter(tags=["metrics"])

# Module-level start time for uptime calculation
_START = time.time()

_WIDE_ROLES = {"master_admin", "ministry_admin", "province_admin"}


def _rss_mb() -> float:
    """RSS memory in MB without psutil — reads /proc/self/status on Linux."""
    try:
        with open("/proc/self/status") as fh:
            for line in fh:
                if line.startswith("VmRSS:"):
                    return round(int(line.split()[1]) / 1024, 1)
    except OSError:
        pass
    return 0.0


def _ping_db(db: Session) -> tuple[bool, float]:
    t0 = time.perf_counter()
    try:
        db.execute(text("SELECT 1"))
        return True, round((time.perf_counter() - t0) * 1000, 1)
    except Exception:
        return False, -1.0


def _ping_redis() -> tuple[bool, float]:
    try:
        from ..security.redis_client import cache
        t0 = time.perf_counter()
        cache.ping()
        return True, round((time.perf_counter() - t0) * 1000, 1)
    except Exception:
        return False, -1.0


@router.get("/metrics")
def get_metrics(
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    """Return operational metrics for the monitoring dashboard.

    Scope:
    - master_admin / ministry_admin / province_admin: platform-wide numbers
    - Everyone else: scoped to their lab_id
    """
    db_ok, db_ms   = _ping_db(db)
    red_ok, red_ms = _ping_redis()

    today_start = datetime.combine(date.today(), datetime.min.time())

    q = db.query(LabOrder)
    if current_user.role not in _WIDE_ROLES:
        q = q.filter(LabOrder.lab_id == current_user.lab_id)

    orders_total     = q.count()
    orders_today     = q.filter(LabOrder.created_at   >= today_start).count()
    validated_today  = q.filter(
        LabOrder.status == "validated",
        LabOrder.validated_at >= today_start,
    ).count()
    pending_count    = q.filter(LabOrder.status == "pending").count()

    uptime_s = int(time.time() - _START)

    return {
        "uptime_s":   uptime_s,
        "uptime_h":   round(uptime_s / 3600, 2),
        "memory_mb":  _rss_mb(),
        "db":         {"ok": db_ok,  "ping_ms": db_ms},
        "redis":      {"ok": red_ok, "ping_ms": red_ms},
        "stats": {
            "orders_total":    orders_total,
            "orders_today":    orders_today,
            "validated_today": validated_today,
            "pending":         pending_count,
        },
        "scope":      "platform" if current_user.role in _WIDE_ROLES else "lab",
        "timestamp":  datetime.now(timezone.utc).isoformat(),
    }
