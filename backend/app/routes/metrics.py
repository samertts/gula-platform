"""Operational and Prometheus metrics endpoints.

GET /metrics        — JSON dashboard metrics (authenticated)
GET /metrics/prom   — Prometheus text format (Bearer token or no-auth in dev)

The JSON endpoint now uses SQL aggregate queries (no more Python-loop over all
orders) — constant-time regardless of data volume.
"""

import time
from datetime import date, datetime

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import PlainTextResponse
from sqlalchemy import case, func, text
from sqlalchemy.orm import Session

from app._compat import UTC

from ..config import IS_PRODUCTION
from ..database import get_db
from ..models.lab_order import LabOrder
from ..models.lab_user import LabUser
from ..security.dependencies import get_current_user

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

    Scope:
    - master_admin / ministry_admin / province_admin: platform-wide numbers
    - Everyone else: scoped to their lab_id
    """
    db_status, db_ms = _ping_db_detail()
    red_ok, red_ms = _ping_redis()

    is_wide = current_user.role in _WIDE_ROLES
    stats = _order_stats(db, lab_id=None if is_wide else current_user.lab_id)
    uptime_s = int(time.time() - _START)

    return {
        "uptime_s": uptime_s,
        "uptime_h": round(uptime_s / 3600, 2),
        "memory_mb": _rss_mb(),
        "db": {"status": db_status, "ok": db_status == "ok", "ping_ms": db_ms},
        "redis": {"ok": red_ok, "ping_ms": red_ms},
        "stats": stats,
        "scope": "platform" if is_wide else "lab",
        "timestamp": datetime.now(UTC).isoformat(),
    }


# ── Prometheus text-format exposition ─────────────────────────────────────────
# Scraped by Prometheus at GET /metrics/prom
# Protected by METRICS_BEARER_TOKEN env var when set (optional in dev).

_PROM_CONTENT_TYPE = "text/plain; version=0.0.4; charset=utf-8"


@router.get("/metrics/prom", include_in_schema=False)
def prometheus_metrics(request: Request, db: Session = Depends(get_db)):
    """Prometheus text-format exposition endpoint.

    Secured by Bearer token when METRICS_BEARER_TOKEN env var is set.
    Open (no auth) in development so Prometheus can scrape without credentials.
    """
    import os

    token = os.getenv("METRICS_BEARER_TOKEN", "")
    if token and IS_PRODUCTION:
        auth = request.headers.get("Authorization", "")
        if auth != f"Bearer {token}":
            return Response(status_code=401, content="Unauthorized")

    db_ok, db_ms = _ping_db(db)
    red_ok, red_ms = _ping_redis()
    rss = _rss_mb()
    uptime_s = int(time.time() - _START)

    # Platform-wide order stats (Prometheus sees the whole system)
    try:
        stats = _order_stats(db, lab_id=None)
    except Exception:
        stats = {}

    # Outbox queue backlog (undelivered async events)
    queue_backlog = 0
    try:
        from ..database import SessionLocal
        from ..models.outbox import OutboxEvent

        _db2 = SessionLocal()
        try:
            queue_backlog = (
                _db2.query(OutboxEvent).filter(OutboxEvent.processed_at.is_(None)).count()
            )
        finally:
            _db2.close()
    except Exception:
        pass

    lines = [
        "# HELP gula_up Platform is operational (1=up, 0=down)",
        "# TYPE gula_up gauge",
        "gula_up 1",
        "",
        "# HELP gula_uptime_seconds Process uptime in seconds",
        "# TYPE gula_uptime_seconds counter",
        f"gula_uptime_seconds {uptime_s}",
        "",
        "# HELP gula_memory_rss_mb Resident set size in MB",
        "# TYPE gula_memory_rss_mb gauge",
        f"gula_memory_rss_mb {rss}",
        "",
        "# HELP gula_db_up Database connectivity (1=ok, 0=down)",
        "# TYPE gula_db_up gauge",
        f"gula_db_up {1 if db_ok else 0}",
        "",
        "# HELP gula_db_latency_ms Last DB ping latency in milliseconds",
        "# TYPE gula_db_latency_ms gauge",
        f"gula_db_latency_ms {db_ms}",
        "",
        "# HELP gula_redis_up Redis connectivity (1=ok, 0=down)",
        "# TYPE gula_redis_up gauge",
        f"gula_redis_up {1 if red_ok else 0}",
        "",
        "# HELP gula_redis_latency_ms Last Redis ping latency in milliseconds",
        "# TYPE gula_redis_latency_ms gauge",
        f"gula_redis_latency_ms {red_ms}",
        "",
        "# HELP gula_orders_total Total lab orders ever created",
        "# TYPE gula_orders_total counter",
        f"gula_orders_total {stats.get('orders_total', 0)}",
        "",
        "# HELP gula_orders_pending Orders currently in pending state",
        "# TYPE gula_orders_pending gauge",
        f"gula_orders_pending {stats.get('pending', 0)}",
        "",
        "# HELP gula_active_requests Concurrent requests being processed",
        "# TYPE gula_active_requests gauge",
        "",
        "# HELP gula_queue_backlog Outbox events pending delivery",
        "# TYPE gula_queue_backlog gauge",
        f"gula_queue_backlog {queue_backlog}",
    ]

    try:
        from ..middleware import ConcurrencyLimitMiddleware

        lines.append(f"gula_active_requests {ConcurrencyLimitMiddleware._active}")
    except Exception:
        lines.append("gula_active_requests 0")

    # ── Per-error-type DB counters ────────────────────────────────────────────
    # Exposes cumulative counts so Prometheus can track error trends and trigger
    # differentiated alerts:
    #   auth_failed > 0 → CRITICAL (misconfiguration, never self-heals)
    #   refused > N     → WARNING  (postgres down or network issue)
    #   timeout > N     → WARNING  (DB overloaded)
    try:
        from ..database import get_db_error_counts

        ec = get_db_error_counts()
        lines += [
            "",
            "# HELP gula_db_refused_total Cumulative DB 'connection refused' errors",
            "# TYPE gula_db_refused_total counter",
            f"gula_db_refused_total {ec.get('refused', 0)}",
            "",
            "# HELP gula_db_auth_failed_total Cumulative DB authentication failures (wrong password / pg_hba.conf)",
            "# TYPE gula_db_auth_failed_total counter",
            f"gula_db_auth_failed_total {ec.get('auth_failed', 0)}",
            "",
            "# HELP gula_db_timeout_total Cumulative DB connection timeouts",
            "# TYPE gula_db_timeout_total counter",
            f"gula_db_timeout_total {ec.get('timeout', 0)}",
            "",
            "# HELP gula_db_error_total Cumulative DB unknown/other errors",
            "# TYPE gula_db_error_total counter",
            f"gula_db_error_total {ec.get('error', 0)}",
        ]
    except Exception:
        pass

    # ── Sliding Window DB rates (5-minute) ───────────────────────────────────
    # These gauges capture the *rate* of DB events in the last 5 minutes,
    # enabling ratio-based Prometheus alerts that ignore ancient history.
    try:
        from ..database import get_db_window_snapshot

        win = get_db_window_snapshot(window_s=300)
        total_events = max(win["ok"] + win["refused"] + win["timeout"], 1)
        lines += [
            "",
            "# HELP gula_db_refused_rate_5m DB 'refused' events per minute (5min window)",
            "# TYPE gula_db_refused_rate_5m gauge",
            f"gula_db_refused_rate_5m {win['refused_per_min']}",
            "",
            "# HELP gula_db_timeout_rate_5m DB timeout events per minute (5min window)",
            "# TYPE gula_db_timeout_rate_5m gauge",
            f"gula_db_timeout_rate_5m {win['timeout_per_min']}",
            "",
            "# HELP gula_db_error_ratio_5m Fraction of DB checks that failed in last 5min (0–1)",
            "# TYPE gula_db_error_ratio_5m gauge",
            f"gula_db_error_ratio_5m {round((win['refused'] + win['timeout']) / total_events, 4)}",
        ]
    except Exception:
        pass

    # ── Control Layer metrics ────────────────────────────────────────────────
    try:
        from ..core.policy_engine import policy_engine

        ps = policy_engine.stats()
        lines += [
            "",
            "# HELP gula_policy_block_total Total autonomous actions blocked by policy",
            "# TYPE gula_policy_block_total counter",
            f"gula_policy_block_total {ps['blocked_total']}",
            "",
            "# HELP gula_policy_allow_total Total autonomous actions permitted by policy",
            "# TYPE gula_policy_allow_total counter",
            f"gula_policy_allow_total {ps['allowed_total']}",
        ]
    except Exception:
        pass

    try:
        from ..core.auto_repair import auto_repair

        total_repairs = sum(v["triggered"] for v in auto_repair.stats().values())
        lines += [
            "",
            "# HELP gula_auto_repair_total Total autonomous repair actions triggered",
            "# TYPE gula_auto_repair_total counter",
            f"gula_auto_repair_total {total_repairs}",
        ]
    except Exception:
        pass

    try:
        from ..core.kill_switch import is_kill_switch_active
        from ..core.self_healing import health as _sh

        lines += [
            "",
            "# HELP gula_kill_switch_active Kill switch state (1=active, 0=inactive)",
            "# TYPE gula_kill_switch_active gauge",
            f"gula_kill_switch_active {1 if is_kill_switch_active() else 0}",
            "",
            "# HELP gula_degradation_level Current degradation level (0=NONE 1=L1 2=L2 3=L3)",
            "# TYPE gula_degradation_level gauge",
            f"gula_degradation_level {_sh.degradation_level.value}",
        ]
    except Exception:
        pass

    lines.append("")
    return PlainTextResponse("\n".join(lines) + "\n", media_type=_PROM_CONTENT_TYPE)
