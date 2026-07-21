"""Background task management and startup warmup.

Extracted from main.py to break the circular dependency between main.py and factory.py.
Factory imports startup logic from here; main.py imports create_app from factory.
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from datetime import datetime

from app._compat import UTC
from app.config import RUNTIME_MODE, background_tasks_enabled

logger = logging.getLogger("gula")

# ===== HEALTH ALERT WATCHDOG =====
async def _health_alert_loop():
    """Background coroutine: comprehensive health monitoring with thresholds.

    Checks every HEALTH_ALERT_interval_SECONDS (default 60s).
    When grade is RED, retries every 10s for fast recovery detection.
    Fires webhook on EVERY grade change (GREEN<->YELLOW<->RED) + periodic RED reminder.

    Thresholds:
      RED    -- DB down OR Redis down
      YELLOW -- DB slow (>200ms) OR Redis slow (>50ms) OR memory >600MB
               OR queue backlog >100 OR degraded mode
      GREEN  -- all clear

    Set ALERT_webhook_URL in .env (Telegram, Discord, Slack, or any HTTP POST sink).
    """
    _interval = int(os.getenv("HEALTH_ALERT_INTERVAL_SECONDS", "60"))
    _retry_fast = 10
    _remind_secs = 300
    _webhook = os.getenv("ALERT_WEBHOOK_URL", "")

    _prev_grade = "GREEN"
    _red_since = 0.0
    _last_alert = 0.0

    await asyncio.sleep(30)

    while True:
        try:
            from app.core.self_healing import health as _sh
            from app.database import check_db_connection as _db_check
            from app.security.redis_client import cache as _r

            loop = asyncio.get_event_loop()

            t0 = time.perf_counter()
            db_ok = await loop.run_in_executor(None, _db_check)
            db_ms = round((time.perf_counter() - t0) * 1000, 1)

            red_ok, red_ms = False, -1.0
            try:
                t0 = time.perf_counter()
                await loop.run_in_executor(None, _r.ping)
                red_ms = round((time.perf_counter() - t0) * 1000, 1)
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
                    from app.database import SessionLocal
                    from app.models.outbox import OutboxEvent

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

            now_mono = time.monotonic()
            if grade == "RED" and _prev_grade != "RED":
                _red_since = now_mono
            elif grade != "RED":
                _red_since = 0.0

            transition = grade != _prev_grade
            red_reminder = (
                grade == "RED" and (now_mono - _last_alert) >= _remind_secs and _red_since > 0
            )
            should_alert = (transition or red_reminder) and _webhook

            if should_alert:
                import httpx as _hx

                emoji = u"\U0001f534" if grade == "RED" else (u"\U0001f7e1" if grade == "YELLOW" else u"\u2705")
                red_dur = ""
                if grade == "RED" and _red_since > 0:
                    red_dur = f" ({int(now_mono - _red_since)}s in RED)"
                payload = {
                    "text": (
                        f"{emoji} *GULA Platform* -- `{_prev_grade}` -> `{grade}`{red_dur}\n"
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
                    logger.info("Health alert sent: %s -> %s issues=%s", _prev_grade, grade, issues)
                except Exception as _e:
                    logger.warning("Health alert webhook failed: %s", _e)

            _prev_grade = grade

        except Exception as exc:
            logger.debug("Health watchdog error: %s", exc)

        sleep_s = _retry_fast if _prev_grade == "RED" else _interval
        await asyncio.sleep(sleep_s)


# ===== ADAPTIVE CONCURRENCY =====
async def _adaptive_concurrency_loop():
    """Dynamically tighten the concurrency cap when the DB is under stress.

    Logic:
    - Poll DB latency every 30s.
    - 2 consecutive slow readings (>300ms): halve _max to shed non-critical load.
    - 3 consecutive fast readings (<150ms): restore original _max.
    """
    from app.database import check_db_connection as _db_check
    from app.middleware import ConcurrencyLimitMiddleware, _MAX_CONCURRENT

    _orig = _MAX_CONCURRENT
    _slow_streak = 0
    _fast_streak = 0
    _slow_ms = 300
    _fast_ms = 150
    _slow_trig = 2
    _fast_trig = 3
    _poll = 30

    await asyncio.sleep(45)

    while True:
        try:
            loop = asyncio.get_event_loop()
            t0 = time.perf_counter()
            await loop.run_in_executor(None, _db_check)
            db_ms = (time.perf_counter() - t0) * 1000

            if db_ms > _slow_ms:
                _slow_streak += 1
                _fast_streak = 0
            elif db_ms < _fast_ms:
                _fast_streak += 1
                _slow_streak = max(0, _slow_streak - 1)
            else:
                _slow_streak = max(0, _slow_streak - 1)
                _fast_streak = max(0, _fast_streak - 1)

            if _slow_streak >= _slow_trig:
                new_max = max(10, _orig // 2)
                if new_max != _orig:
                    logger.warning(
                        "Adaptive concurrency: DB slow %.0fms x%d -> cap %d->%d",
                        db_ms,
                        _slow_streak,
                        _orig,
                        new_max,
                    )
                    if ConcurrencyLimitMiddleware._instance is not None:
                        ConcurrencyLimitMiddleware._instance._max = new_max
                    _orig = new_max

            elif _fast_streak >= _fast_trig and _orig < _MAX_CONCURRENT:
                logger.info(
                    "Adaptive concurrency: DB recovered %.0fms x%d -> restore to %d",
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

        await asyncio.sleep(_poll)


# ===== BACKGROUND TASK TRACKING =====
_bg_tasks: set = set()


def _spawn(coro) -> asyncio.Task:
    """Create a tracked background task that is auto-cancelled on shutdown."""
    task = asyncio.create_task(coro)
    _bg_tasks.add(task)
    task.add_done_callback(_bg_tasks.discard)
    return task


async def start_background_workers():
    """Launch background workers -- only when this process is the worker runtime."""
    if not background_tasks_enabled():
        logger.info(
            "Background tasks disabled (RUNTIME_MODE=%s). "
            "Maintenance loops will NOT start in this process.",
            RUNTIME_MODE,
        )
        return

    from app.core.self_healing import RecoveryWorker
    from app.services.outbox_service import OutboxWorker

    _spawn(OutboxWorker.background_loop())
    logger.info("Outbox worker started")

    _spawn(RecoveryWorker.background_loop())
    logger.info("Recovery worker started")

    _spawn(_health_alert_loop())
    logger.info("Health alert watchdog started")

    _spawn(_adaptive_concurrency_loop())
    logger.info("Adaptive concurrency monitor started")

    from app.core.auto_repair import auto_repair as _auto_repair

    _spawn(_auto_repair.run())
    logger.info("Auto-repair engine started")

    if os.getenv("ENV") != "test":
        from app.edge.maintenance import edge_maintenance_loop

        _spawn(edge_maintenance_loop())
        logger.info("Edge maintenance loop started")

    from app.database import restore_db_window_from_redis

    restore_db_window_from_redis()
    logger.info("DB sliding window restored from Redis")


async def warmup():
    """Pre-load hot-path modules so first real request is fast."""
    t0 = time.perf_counter()
    try:
        from app.services.critical_alerts import check_critical
        from app.services.interpretation import get_flag, interpret_result

        check_critical("Potassium", 4.0)
        interpret_result("glucose", 85, 70, 100)
        get_flag(85, 70, 100, "Glucose")
        elapsed = (time.perf_counter() - t0) * 1000
        logger.info("Startup warmup complete in %.0fms", elapsed)
    except Exception as exc:
        logger.warning("Startup warmup skipped: %s", exc)
