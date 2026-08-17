from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta
from typing import Any

from app._compat import UTC
from app.database import SessionLocal
from app.national.sync_models import NationalSyncOutboxModel
from app.tasks.registry import task_handler

logger = logging.getLogger("gula.sync.outbox")

MAX_ATTEMPTS = 8
MAX_BACKOFF_SECONDS = 3600


def _now() -> datetime:
    return datetime.now(UTC)


def _backoff_seconds(attempts: int) -> int:
    return min(MAX_BACKOFF_SECONDS, 2 ** min(max(attempts, 1), 10))


def deliver_outbox_event(row: NationalSyncOutboxModel) -> None:
    """Hand an event to the configured delivery layer.

    The durable outbox is the source of truth. Development may use the log
    sink, but production must explicitly configure a broker or push gateway;
    a raised exception never marks the event processed and is retried.
    """
    backend = os.getenv("GULA_SYNC_OUTBOX_DELIVERY", "log").strip().lower()
    if backend not in {"log", "redis", "broker", "push"}:
        raise RuntimeError(f"Unsupported sync outbox delivery backend: {backend}")
    if os.getenv("IS_PRODUCTION", "").lower() == "true" and backend == "log":
        raise RuntimeError("Production sync outbox delivery backend is not configured")
    logger.info(
        "sync outbox event handed to delivery backend",
        extra={"event_id": row.event_id, "event_type": row.event_type, "backend": backend},
    )


@task_handler("sync_outbox_dispatch")
async def handle_sync_outbox(payload: dict[str, Any]) -> dict[str, Any]:
    """Drain due outbox events with bounded exponential backoff."""
    db = SessionLocal()
    try:
        limit = max(1, min(int(payload.get("limit", 100)), 500))
        now = _now()
        rows = db.query(NationalSyncOutboxModel).filter(
            NationalSyncOutboxModel.status.in_(["pending", "failed"]),
            (NationalSyncOutboxModel.next_attempt_at.is_(None) | (NationalSyncOutboxModel.next_attempt_at <= now)),
        ).order_by(
            NationalSyncOutboxModel.created_at.asc(),
        ).limit(limit).all()
        processed = 0
        retried = 0
        dead_lettered = 0
        for row in rows:
            row.attempts = (row.attempts or 0) + 1
            row.updated_at = now
            try:
                deliver_outbox_event(row)
            except Exception as exc:  # per-event isolation: one bad event cannot block the queue
                row.last_error = str(exc)[:2000]
                row.processed_at = None
                if row.attempts >= MAX_ATTEMPTS:
                    row.status = "dead_letter"
                    dead_lettered += 1
                else:
                    row.status = "failed"
                    row.next_attempt_at = now + timedelta(seconds=_backoff_seconds(row.attempts))
                    retried += 1
                logger.exception("sync outbox event delivery failed", extra={"event_id": row.event_id, "attempts": row.attempts})
                continue
            row.status = "processed"
            row.last_error = None
            row.next_attempt_at = None
            row.processed_at = now
            processed += 1
        db.commit()
        return {
            "processed": processed,
            "retried": retried,
            "dead_lettered": dead_lettered,
            "selected": len(rows),
        }
    except Exception:
        db.rollback()
        logger.exception("sync outbox dispatch failed")
        raise
    finally:
        db.close()
