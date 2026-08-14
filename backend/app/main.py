"""GULA Platform — FastAPI application entry point.

Uses the application factory from factory.py for all runtime modes.
Middleware classes have been moved to middleware.py.
Health endpoints remain here for direct decorator registration.
Background task management moved to core/startup.py.
"""

from __future__ import annotations

import logging
import os
import time
from contextlib import suppress
from datetime import datetime

from fastapi.responses import JSONResponse

from app._compat import UTC

from .config import APP_NAME, APP_VERSION, IS_PRODUCTION, PLATFORM_NAME_AR
from .core.logging_config import configure_logging
from .database import check_db_connection, get_pool_status

configure_logging(is_production=IS_PRODUCTION, log_level="INFO")
logger = logging.getLogger("gula")

from .factory import create_app  # noqa: E402

# Create the application using the factory
app = create_app()


# ===== HEALTH & STATUS =====
@app.get("/health", tags=["system"])
def health():
    """Liveness probe — always returns 200 if the process is alive.
    Includes circuit breaker state and pool info for observability.
    """
    from .core.self_healing import health as sys_health
    from .core.startup_guard import system_ready

    # Liveness must not open a DB connection on every orchestrator probe.
    # Use /health/ready or /health/status for dependency validation.
    pool = get_pool_status()
    return {
        "status": "alive",
        "platform": APP_NAME,
        "platform_ar": PLATFORM_NAME_AR,
        "version": APP_VERSION,
        "environment": os.getenv("ENV", "production"),
        "system_ready": system_ready,
        "database": "not_checked",
        "database_detail": "liveness_probe; use /health/ready for dependency readiness",
        "degraded_mode": sys_health.degraded,
        "degradation_level": sys_health.degradation_level.name,
        "circuits": sys_health.to_dict()["circuits"],
        "pool": pool,
        "timestamp": datetime.now(UTC).isoformat(),
    }


@app.get("/health/ready", tags=["system"])
def readiness():
    """Hybrid readiness probe — startup completed AND services still alive.

    Returns 200 only when:
      1. Startup guard completed successfully (all steps passed), AND
      2. Database is currently reachable, AND
      3. Redis cache is currently reachable.

    If DB or Redis fail after startup, this probe turns 503 again — the
    Docker healthcheck will detect it and trigger a container restart.
    """
    from .core.startup_guard import is_system_ready

    ready, reason = is_system_ready()
    if not ready:
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "reason": reason},
        )
    return {"status": "ready"}


@app.get("/health/live", tags=["system"])
def liveness():
    """Kubernetes-style liveness probe - always returns 200 if process is alive."""
    return {"status": "alive", "version": APP_VERSION}


@app.get("/health/status", tags=["system"])
def health_status():
    """Full diagnostic status — shows exactly why the system is or isn't ready.
    Useful for debugging startup failures without needing server access.
    Always returns 200 — check 'ready' field for actual state.
    """
    from .core.self_healing import health as sys_health
    from .core.startup_guard import is_system_ready, system_ready

    # Individual component checks
    db_ok = False
    db_error = None
    try:
        db_ok = check_db_connection()
    except Exception:
        db_error = "database_check_failed"

    redis_ok = False
    redis_error = None
    try:
        from .security.redis_client import cache as _redis

        _redis.set("_status_probe", "1", ex=10)
        redis_ok = True
    except Exception:
        redis_error = "redis_check_failed"

    ready, reason = is_system_ready()
    pool = get_pool_status()
    sys_h = sys_health.to_dict()

    return {
        "ready": ready,
        "reason": reason,
        "system_ready_flag": system_ready,
        "database": {
            "connected": db_ok,
            "error": db_error,
            "pool": pool,
        },
        "redis": {
            "connected": redis_ok,
            "error": redis_error,
        },
        "circuits": sys_h.get("circuits", {}),
        "degraded_mode": sys_h.get("degraded", False),
        "version": APP_VERSION,
        "environment": os.getenv("ENV", "production"),
        "timestamp": datetime.now(UTC).isoformat(),
    }


@app.get("/health/deep", tags=["system"])
def health_deep():
    """Deep diagnostic endpoint — comprehensive latency + queue + memory snapshot.
    Designed for monitoring dashboards and alerting (Prometheus, Grafana, etc.).

    Returns overall health grade:
      GREEN   — all components healthy, latencies normal
      YELLOW  — degraded performance, some components slow
      RED     — one or more critical components failing

    Always returns HTTP 200 — check 'grade' field for actual state.
    Accessible without authentication (all values are non-sensitive metrics).
    """
    import time as _t

    t_start = _t.perf_counter()

    # ── 1. Database latency ──────────────────────────────────────────────────
    db_ok, db_ms, db_err = False, -1.0, None
    try:
        from sqlalchemy import text as _text

        from .database import SessionLocal

        _db = SessionLocal()
        try:
            t0 = _t.perf_counter()
            _db.execute(_text("SELECT 1"))
            db_ms = round((_t.perf_counter() - t0) * 1000, 1)
            db_ok = True
        finally:
            _db.close()
    except Exception:
        db_err = "database_check_failed"

    # ── 2. Redis latency ─────────────────────────────────────────────────────
    red_ok, red_ms, red_err = False, -1.0, None
    try:
        from .security.redis_client import cache as _r

        t0 = _t.perf_counter()
        _r.ping()
        red_ms = round((_t.perf_counter() - t0) * 1000, 1)
        red_ok = True
    except Exception:
        red_err = "redis_check_failed"

    # ── 3. Queue backlog (OutboxEvent undelivered rows) ──────────────────────
    queue_backlog, queue_err = 0, None
    try:
        from .database import SessionLocal
        from .models.outbox import OutboxEvent

        _db2 = SessionLocal()
        try:
            queue_backlog = (
                _db2.query(OutboxEvent).filter(OutboxEvent.processed_at.is_(None)).count()
            )
        finally:
            _db2.close()
    except Exception:
        queue_err = "queue_check_failed"

    # ── 4. Memory RSS ────────────────────────────────────────────────────────
    rss_mb = 0.0
    try:
        with open("/proc/self/status") as _f:
            for line in _f:
                if line.startswith("VmRSS:"):
                    rss_mb = round(int(line.split()[1]) / 1024, 1)
                    break
    except OSError:
        pass

    # ── 5. Circuit breaker state ─────────────────────────────────────────────
    circuits = {}
    degraded = False
    try:
        from .core.self_healing import health as _sh

        sh = _sh.to_dict()
        circuits = sh.get("circuits", {})
        degraded = sh.get("degraded", False)
    except Exception:
        pass

    # ── 6. Uptime ────────────────────────────────────────────────────────────
    from .routes.metrics import _START as PROC_START

    uptime_s = int(_t.time() - PROC_START)

    # ── 7. Active concurrent requests (from ConcurrencyLimitMiddleware) ─────────
    active_requests = 0
    with suppress(Exception):
        from .middleware import ConcurrencyLimitMiddleware
        active_requests = ConcurrencyLimitMiddleware._active

    # ── 8. Determine health grade ─────────────────────────────────────────────
    issues = []
    if not db_ok:
        issues.append("database_down")
    elif db_ms > 200:
        issues.append("database_slow")
    if not red_ok:
        issues.append("redis_down")
    elif red_ms > 50:
        issues.append("redis_slow")
    if queue_backlog > 100:
        issues.append("queue_backlog_high")
    if rss_mb > 800:
        issues.append("memory_high")
    if degraded:
        issues.append("degraded_mode")
    if any("down" in i for i in issues):
        grade = "RED"
    elif issues:
        grade = "YELLOW"
    else:
        grade = "GREEN"

    total_ms = round((_t.perf_counter() - t_start) * 1000, 1)

    return {
        "grade": grade,
        "issues": issues,
        "components": {
            "database": {"ok": db_ok, "latency_ms": db_ms, "error": db_err},
            "redis": {"ok": red_ok, "latency_ms": red_ms, "error": red_err},
            "queue": {"backlog": queue_backlog, "error": queue_err},
        },
        "process": {
            "memory_rss_mb": rss_mb,
            "uptime_s": uptime_s,
            "uptime_h": round(uptime_s / 3600, 2),
            "active_requests": active_requests,
            "degraded_mode": degraded,
        },
        "circuits": circuits,
        "check_duration_ms": total_ms,
        "version": APP_VERSION,
        "timestamp": datetime.now(UTC).isoformat(),
        "auto_repair": (
            lambda: __import__("app.core.auto_repair", fromlist=["auto_repair"]).auto_repair.stats()
        )(),
    }


# ===== KERNEL HEALTH =====
@app.get("/health/kernel", tags=["system"])
async def kernel_health():
    """Kernel health and diagnostics.
    Returns the Kernel's internal state, component status, and uptime.
    Bypasses all middlewares so it is always reachable.
    """
    try:
        from .kernel.integration import get_kernel_health

        return await get_kernel_health()
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "kernel_initialized": False,
        }


# ===== PUBLIC ENDPOINTS =====
_test_types_cache: dict = {"data": None, "at": 0.0}


@app.get("/test-types", tags=["system"])
def list_test_types():
    """Returns all available test types and their reference ranges.
    Cached in-memory for 5 minutes to reduce database load.
    """
    cache = _test_types_cache
    if cache["data"] is not None and (time.time() - cache["at"]) < 300:
        return cache["data"]

    from .database import SessionLocal
    from .models import TestType

    db = SessionLocal()
    try:
        types = db.query(TestType).order_by(TestType.category, TestType.test_name).all()
        result = [
            {
                "id": t.id,
                "code": t.test_code,
                "name": t.test_name,
                "name_ar": t.test_name_ar,
                "category": t.category,
                "unit": t.unit,
                "normal_low": t.normal_range_low,
                "normal_high": t.normal_range_high,
            }
            for t in types
        ]
        cache["data"] = result
        cache["at"] = time.time()
        return result
    finally:
        db.close()
