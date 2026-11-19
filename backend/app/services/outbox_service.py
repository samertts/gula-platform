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
import json
import logging
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app._compat import UTC
from app.core.events import events
from app.models.outbox import MAX_ATTEMPTS, OutboxEvent

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
    event = OutboxEvent(
        event_type=event_type,
        aggregate_type=aggregate_type,
        aggregate_id=aggregate_id,
        payload=json.dumps(payload, ensure_ascii=False),
        status="pending",
        attempts=0,
        created_at=datetime.now(UTC),
    )
    db.add(event)
    db.flush()  # get id immediately; still inside caller's transaction
    return event


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
        now = datetime.now(UTC)
        summary = {"processed": 0, "failed": 0, "skipped": 0}

        events_to_process = (
            db.query(OutboxEvent)
            .filter(
                OutboxEvent.status.in_(["pending", "failed"]),
                OutboxEvent.attempts < MAX_ATTEMPTS,
            )
            .order_by(OutboxEvent.created_at.asc())
            .limit(_BATCH_SIZE)
            .with_for_update(skip_locked=True)  # safe for multiple workers
            .all()
        )

        for event in events_to_process:
            event.status = "processing"
            event.attempts = (event.attempts or 0) + 1
            db.flush()

            try:
                payload = json.loads(event.payload)
                dispatched = events.emit(event.event_type, payload)

                event.status = "done"
                event.processed_at = now
                event.last_error = None

                logger.info(
                    "[OUTBOX] event_type=%s id=%d aggregate=%s/%s dispatched_to=%d handlers",
                    event.event_type,
                    event.id,
                    event.aggregate_type or "—",
                    event.aggregate_id or "—",
                    dispatched,
                )
                summary["processed"] += 1

            except Exception as exc:
                event.last_error = str(exc)[:500]
                if event.attempts >= MAX_ATTEMPTS:
                    event.status = "failed"
                    logger.error(
                        "[OUTBOX] PERMANENTLY FAILED event_type=%s id=%d after %d attempts: %s",
                        event.event_type,
                        event.id,
                        event.attempts,
                        exc,
                    )
                    summary["failed"] += 1
                else:
                    event.status = "failed"  # will be retried next cycle
                    logger.warning(
                        "[OUTBOX] attempt %d/%d failed event_type=%s id=%d: %s",
                        event.attempts,
                        MAX_ATTEMPTS,
                        event.event_type,
                        event.id,
                        exc,
                    )
                    summary["skipped"] += 1

            db.flush()

        db.commit()
        return summary

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
    from datetime import UTC, datetime, timedelta

    from sqlalchemy import text

    cutoff = datetime.now(UTC) - timedelta(days=days)
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
