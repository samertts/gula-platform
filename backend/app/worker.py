"""GULA Platform — Background Worker Entrypoint
================================================
Runs the maintenance loops (outbox dispatch, recovery probe, health watchdog,
adaptive concurrency, auto-repair) in a process separate from the FastAPI
API server.

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
    IS_WORKER_RUNTIME,
    RUNTIME_MODE,
    background_tasks_enabled,
)
from .core.logging_config import configure_logging
from .config import IS_PRODUCTION

configure_logging(is_production=IS_PRODUCTION, log_level="INFO")
logger = logging.getLogger("gula.worker")


async def _run_worker() -> None:
    """Spawn every maintenance loop and wait for shutdown."""
    # Lazy imports — these touch the DB engine and we want config validation
    # (RUNTIME_MODE check) to fail fast before we open any pools.
    from .services.outbox_service import OutboxWorker
    from .core.self_healing import RecoveryWorker
    from .core.auto_repair import auto_repair as _auto_repair
    from .database import restore_db_window_from_redis
    from .main import _health_alert_loop, _adaptive_concurrency_loop

    logger.info("GULA Worker %s starting (RUNTIME_MODE=%s)", APP_VERSION, RUNTIME_MODE)

    restore_db_window_from_redis()

    tasks: list[asyncio.Task] = [
        asyncio.create_task(OutboxWorker.background_loop(),  name="outbox"),
        asyncio.create_task(RecoveryWorker.background_loop(), name="recovery"),
        asyncio.create_task(_health_alert_loop(),             name="health-alert"),
        asyncio.create_task(_adaptive_concurrency_loop(),     name="adaptive-concurrency"),
        asyncio.create_task(_auto_repair.run(),               name="auto-repair"),
    ]
    logger.info("Worker spawned %d background loops: %s",
                len(tasks), [t.get_name() for t in tasks])

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


def main() -> None:
    if not IS_WORKER_RUNTIME:
        print(
            f"[GULA FATAL] app.worker requires RUNTIME_MODE=worker "
            f"(got {RUNTIME_MODE!r}). Refusing to start.",
            file=sys.stderr,
        )
        sys.exit(2)

    if not background_tasks_enabled():
        print(
            "[GULA FATAL] FEATURE_BACKGROUND_TASKS must be true to run the worker.",
            file=sys.stderr,
        )
        sys.exit(2)

    asyncio.run(_run_worker())


if __name__ == "__main__":
    main()
