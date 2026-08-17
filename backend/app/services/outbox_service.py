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
import hashlib
import json
import logging
import random
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from app.core.events import events
from app.models.outbox import MAX_ATTEMPTS, OutboxEvent

logger = logging.getLogger("gula.outbox")

_BATCH_SIZE = 50  # events per worker cycle
_POLL_SECS = 10  # seconds between worker polls
_LEASE_SECS = 120
_BASE_BACKOFF_SECS = 5
_MAX_BACKOFF_SECS = 900


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
    payload_json = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    event = OutboxEvent(
        event_type=event_type,
        lab_id=int(payload["lab_id"]) if str(payload.get("lab_id", "")).isdigit() else None,
        aggregate_type=aggregate_type,
        aggregate_id=aggregate_id,
        payload=payload_json,
        payload_hash=hashlib.sha256(payload_json.encode("utf-8")).hexdigest(),
        next_attempt_at=datetime.now(UTC),
        status="pending",
        attempts=0,
        created_at=datetime.now(UTC),
    )
    db.add(event)
    db.flush()  # get id immediately; still inside caller's transaction
    return event


def outbox_metrics(db: Session, event_type_prefix: str | None = None, lab_id: int | None = None) -> dict[str, Any]:
    """Return non-PII backlog metrics using database aggregates, not full-table loads."""
    from sqlalchemy import case, func

    query = db.query(OutboxEvent)
    if event_type_prefix:
        query = query.filter(OutboxEvent.event_type.like(f"{event_type_prefix}%"))
    if lab_id is not None:
        query = query.filter(OutboxEvent.lab_id == lab_id)
    aggregate = query.with_entities(
        func.count(OutboxEvent.id),
        func.sum(case((OutboxEvent.status == "pending", 1), else_=0)),
        func.sum(case(((OutboxEvent.status == "failed") & OutboxEvent.dead_letter_reason.is_(None), 1), else_=0)),
        func.sum(case((OutboxEvent.status == "processing", 1), else_=0)),
        func.sum(case((OutboxEvent.dead_letter_reason.is_not(None), 1), else_=0)),
        func.min(case((OutboxEvent.status.in_(["pending", "failed", "processing"]), OutboxEvent.created_at), else_=None)),
    ).one()
    total, pending, failed, processing, dead_letter, oldest_created = aggregate
    now = datetime.now(UTC)
    if oldest_created is None:
        oldest_age = 0
    else:
        normalized = oldest_created.replace(tzinfo=UTC) if oldest_created.tzinfo is None else oldest_created
        oldest_age = int(max(0.0, (now - normalized).total_seconds()))
    return {
        "total": int(total or 0),
        "pending": int(pending or 0),
        "failed": int(failed or 0),
        "processing": int(processing or 0),
        "dead_letter": int(dead_letter or 0),
        "oldest_pending_age_seconds": oldest_age,
    }


def replay_outbox_event(db: Session, event_id: int, replayed_by: str, lab_id: int | None = None) -> OutboxEvent:
    """Move one dead-letter event back to the queue without changing its payload."""
    event = db.query(OutboxEvent).filter(OutboxEvent.id == event_id).with_for_update().first()
    if not event or (lab_id is not None and event.lab_id != lab_id):
        raise LookupError("Outbox event not found")
    if event.status == "done":
        raise ValueError("Completed outbox events cannot be replayed")
    event.status = "pending"
    event.attempts = 0
    event.next_attempt_at = datetime.now(UTC)
    event.lease_until = None
    event.dead_letter_reason = None
    event.last_error = None
    event.replayed_by = str(replayed_by)[:160]
    db.commit()
    db.refresh(event)
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

        # Recover work claimed by a worker that died before completion.
        db.query(OutboxEvent).filter(
            OutboxEvent.status == "processing",
            OutboxEvent.lease_until.is_not(None),
            OutboxEvent.lease_until < now,
        ).update({"status": "failed", "last_error": "processing lease expired", "next_attempt_at": now}, synchronize_session=False)
        db.flush()

        events_to_process = (
            db.query(OutboxEvent)
            .filter(
                OutboxEvent.status.in_(["pending", "failed"]),
                OutboxEvent.attempts < MAX_ATTEMPTS,
                (OutboxEvent.next_attempt_at.is_(None) | (OutboxEvent.next_attempt_at <= now)),
            )
            .order_by(OutboxEvent.created_at.asc())
            .limit(_BATCH_SIZE)
            .with_for_update(skip_locked=True)  # safe for multiple workers
            .all()
        )

        for event in events_to_process:
            event.status = "processing"
            event.attempts = (event.attempts or 0) + 1
            event.lease_until = now + timedelta(seconds=_LEASE_SECS)
            db.flush()

            try:
                payload = json.loads(event.payload)
                dispatched = events.emit(event.event_type, payload)

                event.status = "done"
                event.processed_at = now
                event.lease_until = None
                event.next_attempt_at = None
                event.last_error = None
                event.dead_letter_reason = None

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
                event.lease_until = None
                if event.attempts >= MAX_ATTEMPTS:
                    event.status = "failed"
                    event.dead_letter_reason = str(exc)[:500]
                    logger.error(
                        "[OUTBOX] PERMANENTLY FAILED event_type=%s id=%d after %d attempts: %s",
                        event.event_type,
                        event.id,
                        event.attempts,
                        exc,
                    )
                    summary["failed"] += 1
                else:
                    event.status = "failed"  # will be retried after exponential backoff
                    delay = min(_MAX_BACKOFF_SECS, _BASE_BACKOFF_SECS * (2 ** max(0, event.attempts - 1)))
                    event.next_attempt_at = now + timedelta(seconds=delay + random.uniform(0, max(1, delay * 0.2)))
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
    from datetime import datetime, timedelta

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
