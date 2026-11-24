"""Operational and Prometheus metrics endpoints.

GET /metrics        — JSON dashboard metrics (authenticated)
GET /metrics/prom   — Prometheus text format (Bearer token or no-auth in dev)

The JSON endpoint now uses SQL aggregate queries (no more Python-loop over all
orders) — constant-time regardless of data volume.
"""

import time
from datetime import date

from fastapi import APIRouter, Depends, Request
from sqlalchemy import case, func, text
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.lab_order import LabOrder
from ..models.lab_user import LabUser
from ..security.dependencies import get_current_user
from ..services.metrics_service import build_prometheus_response, get_json_metrics

router = APIRouter(tags=["metrics"])

# Module-level start time for uptime calculation (imported by main.py /health/deep)
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


def _ping_db_detail() -> tuple[str, float]:
    """Return (status, latency_ms) using the detailed connection check.
    status: 'ok' | 'refused' | 'auth_failed' | 'timeout' | 'error'
    """
    from ..database import check_db_connection_detail

    t0 = time.perf_counter()
    status, _ = check_db_connection_detail()
    ms = round((time.perf_counter() - t0) * 1000, 1)
    return status, (ms if status == "ok" else -1.0)


def _ping_redis() -> tuple[bool, float]:
    try:
        from ..security.redis_client import cache

        t0 = time.perf_counter()
        cache.ping()
        return True, round((time.perf_counter() - t0) * 1000, 1)
    except Exception:
        return False, -1.0


def _order_stats(db: Session, lab_id: int | None) -> dict:
    """Single SQL query replaces Python-loop aggregation — O(1) instead of O(N)."""
    today = date.today()

    q = db.query(
        func.count(LabOrder.id).label("total"),
        func.count(case((func.date(LabOrder.created_at) == today, LabOrder.id))).label("today"),
        func.count(case((LabOrder.status == "validated", LabOrder.id))).label("validated_total"),
        func.count(
            case(
                (
                    (LabOrder.status == "validated") & (func.date(LabOrder.validated_at) == today),
                    LabOrder.id,
                ),
            ),
        ).label("validated_today"),
        func.count(case((LabOrder.status == "pending", LabOrder.id))).label("pending"),
    )
    if lab_id is not None:
        q = q.filter(LabOrder.lab_id == lab_id)
    row = q.one()
    return {
        "orders_total": row.total,
        "orders_today": row.today,
        "validated_total": row.validated_total,
        "validated_today": row.validated_today,
        "pending": row.pending,
    }


@router.get("/metrics")
def get_metrics(
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    """Return operational metrics for the monitoring dashboard.

    Delegates to `app.services.metrics_service.get_json_metrics`. Scope:
    - master_admin / ministry_admin / province_admin: platform-wide numbers
    - Everyone else: scoped to their lab_id
    """
    is_wide = current_user.role in _WIDE_ROLES
    return get_json_metrics(db, lab_id=current_user.lab_id, is_wide=is_wide)


# ── Prometheus text-format exposition ─────────────────────────────────────────
# Scraped by Prometheus at GET /metrics/prom
# Protected by METRICS_BEARER_TOKEN env var when set (optional in dev).

_PROM_CONTENT_TYPE = "text/plain; version=0.0.4; charset=utf-8"


@router.get("/metrics/prom", include_in_schema=False)
def prometheus_metrics(request: Request, db: Session = Depends(get_db)):
    """Prometheus text-format exposition.

    All rendering, including the production fail-closed scrape policy and SLO
    metrics, is owned by `services.metrics_service.build_prometheus_response`.
    This route is a thin adapter so there is exactly one live renderer.
    """
    return build_prometheus_response(request, db)
