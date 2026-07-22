"""GULA Platform — Background Worker Entrypoint
================================================
Runs the maintenance loops (outbox dispatch, recovery probe, health watchdog,
adaptive concurrency, auto-repair) AND the discrete task queue consumer in a
process separate from the FastAPI API server.

Runtime contract:
    RUNTIME_MODE=worker            (mandatory — refuses to start otherwise)
    FEATURE_BACKGROUND_TASKS=true  (mandatory — explicit opt-in)

Why a separate process?
    - The API process must stay focused on serving HTTP traffic. Background
      loops sharing the same event loop cause unpredictable tail latency.
    - A worker can be scaled, restarted, or paused independently of the API.
    - Process-level isolation makes the readiness/health checks for each
      role meaningful (an unhealthy worker doesn't mark the API unhealthy).

Run with::

    RUNTIME_MODE=worker FEATURE_BACKGROUND_TASKS=true python -m app.worker
"""

from __future__ import annotations

import asyncio
import logging
import signal
import sys

from .config import (
    APP_VERSION,
    IS_PRODUCTION,
    IS_WORKER_RUNTIME,
    RUNTIME_MODE,
    background_tasks_enabled,
)
from .core.logging_config import configure_logging

configure_logging(is_production=IS_PRODUCTION, log_level="INFO")
logger = logging.getLogger("gula.worker")

# ── Crash-isolated loop wrapper ───────────────────────────────────────────────

_RESTART_BASE_DELAY_S = 5.0
_RESTART_MAX_DELAY_S = 120.0


async def _resilient_loop(coro_factory, name: str) -> None:
    """Run a background coroutine and restart it on unexpected crashes.

    Each consecutive crash doubles the restart delay (exponential backoff)
    up to _RESTART_MAX_DELAY_S. A clean cancellation (asyncio.CancelledError)
    propagates immediately without restart.
    """
    delay = _RESTART_BASE_DELAY_S
    while True:
        try:
            logger.info("Loop [%s] starting", name)
            await coro_factory()
            # Coroutine returned normally — shouldn't happen for infinite loops.
            # Restart immediately rather than treating it as a crash.
            logger.warning("Loop [%s] exited normally — restarting", name)
            delay = _RESTART_BASE_DELAY_S
        except asyncio.CancelledError:
            logger.info("Loop [%s] cancelled", name)
            raise
        except Exception as exc:
            logger.error(
                "Loop [%s] crashed: %s — restarting in %.0fs", name, exc, delay, exc_info=True
            )
            await asyncio.sleep(delay)
            delay = min(delay * 2, _RESTART_MAX_DELAY_S)


# ── Main worker coroutine ─────────────────────────────────────────────────────


async def _run_worker() -> None:
    """Spawn every maintenance loop + task worker and wait for shutdown."""
    # Lazy imports — these touch the DB engine and we want config validation
    # (RUNTIME_MODE check) to fail fast before we open any pools.
    from .core.auto_repair import auto_repair as _auto_repair
    from .core.self_healing import RecoveryWorker
    from .core.startup import _adaptive_concurrency_loop, _health_alert_loop
    from .database import restore_db_window_from_redis
    from .services.outbox_service import OutboxWorker
    from .tasks.queue import task_queue
    from .tasks.worker import TaskWorker

    logger.info("GULA Worker %s starting (RUNTIME_MODE=%s)", APP_VERSION, RUNTIME_MODE)

    restore_db_window_from_redis()

    _task_worker = TaskWorker(task_queue)

    # Each maintenance loop is wrapped in _resilient_loop so a single crash
    # restarts only that loop, leaving all siblings running.
    tasks: list[asyncio.Task] = [
        asyncio.create_task(
            _resilient_loop(OutboxWorker.background_loop, "outbox"),
            name="outbox",
        ),
        asyncio.create_task(
            _resilient_loop(RecoveryWorker.background_loop, "recovery"),
            name="recovery",
        ),
        asyncio.create_task(
            _resilient_loop(_health_alert_loop, "health-alert"),
            name="health-alert",
        ),
        asyncio.create_task(
            _resilient_loop(_adaptive_concurrency_loop, "adaptive-concurrency"),
            name="adaptive-concurrency",
        ),
        asyncio.create_task(
            _resilient_loop(_auto_repair.run, "auto-repair"),
            name="auto-repair",
        ),
        # Discrete task queue consumer — runs until cancelled, crashes are
        # isolated to the failing task, not this loop.
        asyncio.create_task(
            _resilient_loop(_task_worker.run, "task-worker"),
            name="task-worker",
        ),
    ]
    logger.info("Worker spawned %d loops: %s", len(tasks), [t.get_name() for t in tasks])

    stop = asyncio.Event()

    def _signal_stop(*_):
        logger.info("Worker received shutdown signal — cancelling loops")
        stop.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _signal_stop)
        except NotImplementedError:
            # add_signal_handler isn't supported on Windows
            signal.signal(sig, _signal_stop)

    await stop.wait()

    for t in tasks:
        t.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)
    logger.info("Worker stopped cleanly")


# ── Entrypoint ────────────────────────────────────────────────────────────────


def main() -> None:
    if not IS_WORKER_RUNTIME:
        sys.exit(2)

    if not background_tasks_enabled():
        sys.exit(2)

    asyncio.run(_run_worker())


if __name__ == "__main__":
    main()
