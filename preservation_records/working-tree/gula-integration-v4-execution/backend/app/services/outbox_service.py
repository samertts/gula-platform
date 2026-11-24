"""Transactional Outbox Service — GULA Platform
================================================
Guarantees reliable event delivery even when the broker/notification service
is temporarily unavailable.

Pattern:
  1. Writer calls `emit_to_outbox()` INSIDE an existing DB transaction.
     The event is committed atomically with the business operation.
  2. `OutboxWorker.run_once()` is called periodically (startup lifespan task).
     It picks up pending events and dispatches them to the in-process EventBus.
  3. On success → status=done, processed_at=now
     On failure → attempts++, last_error=..., status=failed (if max reached)

At-least-once delivery guarantee:
  Even if the app crashes between the business commit and the worker dispatch,
  the event stays in 'pending' and will be picked up on the next worker cycle.

Usage:
    # Inside a route handler (same transaction as the business op)
    emit_to_outbox(db, event_type="order.validated",
                   aggregate_type="order", aggregate_id=order.id,
                   payload={"order_id": order.id, "lab_id": lab_id})

    # In app lifespan (main.py)
    asyncio.create_task(OutboxWorker.background_loop())
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from sqlalchemy.orm import Session

from app.core.events import events
from app.eventing.adapters import legacy_emit_to_outbox, legacy_run_once
from app.models.outbox import OutboxEvent

logger = logging.getLogger("gula.outbox")

_BATCH_SIZE = 50  # events per worker cycle
_POLL_SECS = 10  # seconds between worker polls


# ─── Writer (called inside business transaction) ──────────────────────────────


def emit_to_outbox(
    db: Session,
    event_type: str,
    payload: dict[str, Any],
    aggregate_type: str | None = None,
    aggregate_id: int | None = None,
) -> OutboxEvent:
    """Persist an outbox event in the same DB transaction as the business operation.

    DO NOT commit inside this function — let the caller's transaction handle it.
    This is what makes the Outbox Pattern work: if the outer transaction rolls
    back, the event is never saved either.
    """
    # V4 C09: delegation only. The historical signature, commit boundary and
    # payload serialization are preserved by the adapter and authoritative core.
    return legacy_emit_to_outbox(db, event_type, payload, aggregate_type, aggregate_id)


# ─── Worker ──────────────────────────────────────────────────────────────────


class OutboxWorker:
    """Background worker that processes pending outbox events.
    Dispatches to the in-process EventBus; any subscriber receives the payload.
    """

    @staticmethod
    def run_once(db: Session) -> dict[str, int]:
        """Process one batch of pending/retriable events.

        Returns a summary: {"processed": N, "failed": N, "skipped": N}
        """
        # V4 C09: no delivery logic here. Legacy callers intentionally keep the
        # historical zero-handler acknowledgement policy through the adapter;
        # canonical callers use NationalEventAuthority.drain(require_handler=True).
        # ``events`` is retained as the historical monkeypatch seam. The
        # compatibility adapter passes its emitter into the shared core.
        return legacy_run_once(db, dispatcher=events.emit)

    @staticmethod
    async def background_loop() -> None:
        """Asyncio task: poll outbox every _POLL_SECS seconds.
        Launched from FastAPI lifespan startup.

        Also runs automatic dead-event cleanup once every 24 hours so that
        permanently-failed events (MAX_ATTEMPTS exhausted) don't accumulate
        indefinitely in the database.
        """
        import time as _t

        from sqlalchemy import inspect as _inspect

        from app.database import SessionLocal, engine

        # Guard: verify the outbox_events table exists before entering the loop.
        # If alembic hasn't been applied the table won't exist and every cycle
        # would log a noisy ProgrammingError. Abort early with a clear message.
        try:
            if not _inspect(engine).has_table("outbox_events"):
                logger.error(
                    "[OUTBOX] outbox_events table does not exist — "
                    "alembic upgrade head must run before starting the outbox worker. "
                    "Worker will not start.",
                )
                return
        except Exception as exc:
            logger.error("[OUTBOX] Could not verify outbox_events table: %s — worker aborted", exc)
            return

        logger.info("[OUTBOX] Worker started (poll_interval=%ds)", _POLL_SECS)
        _last_purge = _t.monotonic()
        _purge_interval = 86_400  # 24 hours

        while True:
            await asyncio.sleep(_POLL_SECS)

            def _run_outbox_cycle(last_purge: float):
                db = SessionLocal()
                try:
                    summary = OutboxWorker.run_once(db)
                    purged = 0
                    if _t.monotonic() - last_purge >= _purge_interval:
                        purged = purge_old_events(db, days=30)
                    return summary, purged
                finally:
                    db.close()

            try:
                loop = asyncio.get_event_loop()
                summary, purged = await loop.run_in_executor(None, _run_outbox_cycle, _last_purge)

                if summary["processed"] or summary["failed"]:
                    logger.info("[OUTBOX] cycle summary: %s", summary)

                if purged:
                    logger.info("[OUTBOX] Auto-purged %d old events", purged)

                if purged or (summary["processed"] or summary["failed"]):
                    _last_purge = _t.monotonic()

            except Exception as exc:
                logger.error("[OUTBOX] Worker cycle error: %s", exc)


# ─── Cleanup helper (CRON / maintenance) ─────────────────────────────────────


def purge_old_events(db: Session, days: int = 30) -> int:
    """Delete done/failed outbox events older than `days` days.
    Safe to run periodically from a maintenance CRON job.
    Returns the number of rows deleted.
    """
    from datetime import datetime, timedelta

    from sqlalchemy import text

    cutoff = datetime.utcnow() - timedelta(days=days)
    result = db.execute(
        text("""
            DELETE FROM outbox_events
            WHERE status IN ('done', 'failed')
              AND created_at < :cutoff
        """),
        {"cutoff": cutoff},
    )
    db.commit()
    count = result.rowcount  # type: ignore[attr-defined]
    if count:
        logger.info("[OUTBOX] Purged %d old events (older than %d days)", count, days)
    return count
