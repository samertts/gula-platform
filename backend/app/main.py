"""GULA Platform — FastAPI application entry point.

Uses the application factory from factory.py for all runtime modes.
Middleware classes have been moved to middleware.py.
Health endpoints remain here for direct decorator registration.
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from contextlib import suppress
from datetime import datetime

from app._compat import UTC

from fastapi import Request
from fastapi.responses import JSONResponse

from .config import APP_NAME, APP_VERSION, IS_PRODUCTION, PLATFORM_NAME_AR, RUNTIME_MODE, background_tasks_enabled
from .core.logging_config import configure_logging
from .database import check_db_connection, engine, get_pool_status

configure_logging(is_production=IS_PRODUCTION, log_level="INFO")
logger = logging.getLogger("gula")

from .factory import create_app  # noqa: E402


# Create the application using the factory
app = create_app()

# ===== HEALTH ALERT WATCHDOG =====
async def _health_alert_loop():
    """Background coroutine: comprehensive health monitoring with thresholds.

    Checks every HEALTH_ALERT_interval_SECONDS (default 60s).
    When grade is RED, retries every 10s for fast recovery detection.
    Fires webhook on EVERY grade change (GREEN↔YELLOW↔RED) + periodic RED reminder.

    Thresholds:
      RED    — DB down OR Redis down
      YELLOW — DB slow (>200ms) OR Redis slow (>50ms) OR memory >600MB
               OR queue backlog >100 OR degraded mode
      GREEN  — all clear

    Set ALERT_webhook_URL in .env (Telegram, Discord, Slack, or any HTTP POST sink).
    """
    import asyncio as _aio
    import os
    import time as _t

    _interval = int(os.getenv("HEALTH_ALERT_INTERVAL_SECONDS", "60"))
    _retry_fast = 10  # seconds between checks when in RED state
    _remind_secs = 300  # re-alert every 5 min if still RED
    _webhook = os.getenv("ALERT_WEBHOOK_URL", "")

    _prev_grade = "GREEN"
    _red_since = 0.0  # monotonic timestamp when RED started
    _last_alert = 0.0  # monotonic timestamp of last webhook send

    await _aio.sleep(30)  # Let startup complete before first check

    while True:
        try:
            from .core.self_healing import health as _sh
            from .database import check_db_connection as _db_check
            from .security.redis_client import cache as _r

            # ── Component checks (run blocking ops in executor) ──────────
            loop = _aio.get_event_loop()

            t0 = _t.perf_counter()
            db_ok = await loop.run_in_executor(None, _db_check)
            db_ms = round((_t.perf_counter() - t0) * 1000, 1)

            red_ok, red_ms = False, -1.0
            try:
                t0 = _t.perf_counter()
                await loop.run_in_executor(None, _r.ping)
                red_ms = round((_t.perf_counter() - t0) * 1000, 1)
                red_ok = True
            except Exception:
                pass

            def _read_rss() -> float:
                try:
                    with open("/proc/self/status") as _f:
                        for line in _f:
                            if line.startswith("VmRSS:"):
                                return round(int(line.split()[1]) / 1024, 1)
                except OSError:
                    pass
                return 0.0

            rss_mb = await loop.run_in_executor(None, _read_rss)

            sh_dict = _sh.to_dict()
            degraded = sh_dict.get("degraded", False)

            def _get_queue_backlog() -> int:
                try:
                    from .database import SessionLocal
                    from .models.outbox import OutboxEvent

                    _db2 = SessionLocal()
                    try:
                        return (
                            _db2.query(OutboxEvent)
                            .filter(OutboxEvent.processed_at.is_(None))
                            .count()
                        )
                    finally:
                        _db2.close()
                except Exception:
                    return 0

            queue_backlog = await loop.run_in_executor(None, _get_queue_backlog)

            # ── Grade determination ───────────────────────────────────────
            issues = []
            if not db_ok:
                issues.append("database_down")
            if not red_ok:
                issues.append("redis_down")
            if db_ok and db_ms > 200:
                issues.append(f"database_slow_{db_ms}ms")
            if red_ok and red_ms > 50:
                issues.append(f"redis_slow_{red_ms}ms")
            if rss_mb > 600:
                issues.append(f"memory_high_{rss_mb}MB")
            if queue_backlog > 100:
                issues.append(f"queue_backlog_{queue_backlog}")
            if degraded:
                issues.append("degraded_mode")

            critical = [i for i in issues if "down" in i]
            grade = "RED" if critical else ("YELLOW" if issues else "GREEN")

            # ── Track RED duration ────────────────────────────────────────
            now_mono = _t.monotonic()
            if grade == "RED" and _prev_grade != "RED":
                _red_since = now_mono
            elif grade != "RED":
                _red_since = 0.0

            # ── Alert logic: transition OR periodic RED reminder ──────────
            transition = grade != _prev_grade
            red_reminder = (
                grade == "RED" and (now_mono - _last_alert) >= _remind_secs and _red_since > 0
            )
            should_alert = (transition or red_reminder) and _webhook

            if should_alert:
                from datetime import datetime

                import httpx as _hx

                emoji = "🔴" if grade == "RED" else ("🟡" if grade == "YELLOW" else "✅")
                red_dur = ""
                if grade == "RED" and _red_since > 0:
                    red_dur = f" ({int(now_mono - _red_since)}s in RED)"
                payload = {
                    "text": (
                        f"{emoji} *GULA Platform* — `{_prev_grade}` → `{grade}`{red_dur}\n"
                        f"Issues: {', '.join(issues) or 'none'}\n"
                        f"DB: {db_ms}ms  Redis: {red_ms}ms  "
                        f"Mem: {rss_mb}MB  Queue: {queue_backlog}\n"
                        f"{datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S')} UTC"
                    ),
                    "grade": grade,
                    "prev_grade": _prev_grade,
                    "issues": issues,
                    "metrics": {
                        "db_ms": db_ms,
                        "redis_ms": red_ms,
                        "memory_mb": rss_mb,
                        "queue_backlog": queue_backlog,
                    },
                }
                try:
                    async with _hx.AsyncClient(timeout=10) as _c:
                        await _c.post(_webhook, json=payload)
                    _last_alert = now_mono
                    logger.info("Health alert sent: %s → %s issues=%s", _prev_grade, grade, issues)
                except Exception as _e:
                    logger.warning("Health alert webhook failed: %s", _e)

            _prev_grade = grade

        except Exception as exc:
            logger.debug("Health watchdog error: %s", exc)

        # Faster retry when system is degraded, normal interval when healthy
        sleep_s = _retry_fast if _prev_grade == "RED" else _interval
        await _aio.sleep(sleep_s)


# ===== ADAPTIVE CONCURRENCY =====
async def _adaptive_concurrency_loop():
    """Dynamically tighten the concurrency cap when the DB is under stress.

    Logic:
    - Poll DB latency every 30s.
    - 2 consecutive slow readings (>300ms): halve _max to shed non-critical load.
    - 3 consecutive fast readings (<150ms): restore original _max.

    Prevents a slow DB from cascading into a full request pile-up:
    fewer in-flight requests → shorter queue → DB recovers faster.
    """
    import asyncio as _aio
    import time as _t

    from .database import check_db_connection as _db_check
    from .middleware import ConcurrencyLimitMiddleware, _MAX_CONCURRENT

    _orig = _MAX_CONCURRENT
    _slow_streak = 0
    _fast_streak = 0
    _slow_ms = 300
    _fast_ms = 150
    _slow_trig = 2
    _fast_trig = 3
    _poll = 30

    await _aio.sleep(45)  # let startup complete

    while True:
        try:
            loop = _aio.get_event_loop()
            t0 = _t.perf_counter()
            await loop.run_in_executor(None, _db_check)
            db_ms = (_t.perf_counter() - t0) * 1000

            if db_ms > _slow_ms:
                _slow_streak += 1
                _fast_streak = 0
            elif db_ms < _fast_ms:
                _fast_streak += 1
                _slow_streak = max(0, _slow_streak - 1)
            else:
                _slow_streak = max(0, _slow_streak - 1)
                _fast_streak = max(0, _fast_streak - 1)

            # Tighten when DB is consistently slow
            if _slow_streak >= _slow_trig:
                new_max = max(10, _orig // 2)
                if new_max != _orig:
                    logger.warning(
                        "Adaptive concurrency: DB slow %.0fms ×%d → cap %d→%d",
                        db_ms,
                        _slow_streak,
                        _orig,
                        new_max,
                    )
                    if ConcurrencyLimitMiddleware._instance is not None:
                        ConcurrencyLimitMiddleware._instance._max = new_max
                    _orig = new_max

            # Restore when DB recovers
            elif _fast_streak >= _fast_trig and _orig < _MAX_CONCURRENT:
                logger.info(
                    "Adaptive concurrency: DB recovered %.0fms ×%d → restore to %d",
                    db_ms,
                    _fast_streak,
                    _MAX_CONCURRENT,
                )
                if ConcurrencyLimitMiddleware._instance is not None:
                    ConcurrencyLimitMiddleware._instance._max = _MAX_CONCURRENT
                _orig = _MAX_CONCURRENT
                _fast_streak = 0

        except Exception as exc:
            logger.debug("Adaptive concurrency check error: %s", exc)

        await _aio.sleep(_poll)


# ===== STARTUP WARMUP =====

# Tracks all background tasks so shutdown can cancel them cleanly.
_bg_tasks: set = set()


def _spawn(coro) -> "asyncio.Task":
    """Create a tracked background task that is auto-cancelled on shutdown."""
    task = asyncio.create_task(coro)
    _bg_tasks.add(task)
    task.add_done_callback(_bg_tasks.discard)
    return task


async def start_background_workers():
    """Launch background workers — only when this process is the worker runtime.

    Runtime isolation rules (see config.background_tasks_enabled):
      - API runtime         → never launches maintenance loops
      - Worker runtime      → launches all loops
      - Test / CLI runtime  → never launches anything

    The double-gate (FEATURE_BACKGROUND_TASKS + RUNTIME_MODE=worker) ensures
    a misconfigured env var alone can't promote an API process into a worker.
    """
    if not background_tasks_enabled():
        logger.info(
            "Background tasks disabled (RUNTIME_MODE=%s). "
            "Maintenance loops will NOT start in this process.",
            RUNTIME_MODE,
        )
        return

    from .core.self_healing import RecoveryWorker
    from .services.outbox_service import OutboxWorker

    _spawn(OutboxWorker.background_loop())
    logger.info("Outbox worker started")

    _spawn(RecoveryWorker.background_loop())
    logger.info("Recovery worker started")

    _spawn(_health_alert_loop())
    logger.info("Health alert watchdog started")

    _spawn(_adaptive_concurrency_loop())
    logger.info("Adaptive concurrency monitor started")

    from .core.auto_repair import auto_repair as _auto_repair

    _spawn(_auto_repair.run())
    logger.info("Auto-repair engine started")

    # Edge AI maintenance — reaps stale tasks, marks offline devices, prunes telemetry.
    # Skipped under ENV=test so the loop's SessionLocal() calls (which target the
    # production engine, not the test fixture session) can't touch a Postgres DB
    # whose edge_* tables aren't created by the test fixture.
    if os.getenv("ENV") != "test":
        from .edge.maintenance import edge_maintenance_loop

        _spawn(edge_maintenance_loop())
        logger.info("Edge maintenance loop started")

    # ── Restore sliding window from Redis (DB error history survives restarts) ─
    from .database import restore_db_window_from_redis

    restore_db_window_from_redis()
    logger.info("DB sliding window restored from Redis")


async def warmup():
    """Pre-load hot-path modules so first real request is fast."""
    import time as _t

    t0 = _t.perf_counter()
    try:
        # Resolve deferred import inside get_flag → check_critical
        from .routes.critical_alerts import check_critical
        from .services.interpretation import get_flag, interpret_result

        # Warm function caches
        check_critical("Potassium", 4.0)
        interpret_result("glucose", 85, 70, 100)
        get_flag(85, 70, 100, "Glucose")
        elapsed = (_t.perf_counter() - t0) * 1000
        logger.info("Startup warmup complete in %.0fms", elapsed)
    except Exception as exc:
        logger.warning("Startup warmup skipped: %s", exc)


# ===== HEALTH & STATUS =====
@app.get("/health", tags=["system"])
def health():
    """
    Liveness probe — always returns 200 if the process is alive.
    Includes circuit breaker state and pool info for observability.
    """
    from .core.self_healing import health as sys_health
    from .core.startup_guard import system_ready
    from .database import check_db_connection_detail

    db_status, db_detail = check_db_connection_detail()
    pool = get_pool_status()
    return {
        "status": "healthy" if db_status == "ok" else "degraded",
        "platform": APP_NAME,
        "platform_ar": PLATFORM_NAME_AR,
        "version": APP_VERSION,
        "environment": os.getenv("ENV", "production"),
        "system_ready": system_ready,
        "database": db_status,  # "ok" | "refused" | "auth_failed" | "timeout" | "error"
        "database_detail": db_detail,  # human-readable reason for failures
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
    """
    Full diagnostic status — shows exactly why the system is or isn't ready.
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
    except Exception as e:
        db_error = str(e)

    redis_ok = False
    redis_error = None
    try:
        from .security.redis_client import cache as _redis

        _redis.set("_status_probe", "1", ex=10)
        redis_ok = True
    except Exception as e:
        redis_error = str(e)

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
    """
    Deep diagnostic endpoint — comprehensive latency + queue + memory snapshot.
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
    except Exception as e:
        db_err = str(e)[:120]

    # ── 2. Redis latency ─────────────────────────────────────────────────────
    red_ok, red_ms, red_err = False, -1.0, None
    try:
        from .security.redis_client import cache as _r

        t0 = _t.perf_counter()
        _r.ping()
        red_ms = round((_t.perf_counter() - t0) * 1000, 1)
        red_ok = True
    except Exception as e:
        red_err = str(e)[:80]

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
    except Exception as e:
        queue_err = str(e)[:80]

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
    """
    Kernel health and diagnostics.
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
    """
    Returns all available test types and their reference ranges.
    Cached in-memory for 5 minutes to reduce database load.
    """
    import time

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
