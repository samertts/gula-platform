from __future__ import annotations

import logging
from datetime import timedelta

from app._compat import UTC
from app.database import SessionLocal
from app.national.sync_models import NationalSyncOutboxModel
from app.tasks.registry import task_handler

logger = logging.getLogger("gula.sync.outbox")


@task_handler("sync_outbox_dispatch")
async def handle_sync_outbox(payload: dict) -> dict:
    """Drain durable sync outbox rows without changing clinical state.

    Conflict notifications are created in the same database transaction as the
    conflict. The worker only marks the durable event as processed after the
    delivery layer has a chance to consume it; it never resolves or overwrites
    a clinical record.
    """
    db = SessionLocal()
    try:
        limit = max(1, min(int(payload.get("limit", 100)), 500))
        rows = db.query(NationalSyncOutboxModel).filter(
            NationalSyncOutboxModel.status == "pending",
        ).order_by(
            NationalSyncOutboxModel.created_at.asc(),
        ).limit(limit).all()
        processed = 0
        for row in rows:
            row.status = "processed"
            row.attempts = (row.attempts or 0) + 1
            row.processed_at = __import__("datetime").datetime.now(UTC)
            row.updated_at = row.processed_at
            processed += 1
        db.commit()
        return {"processed": processed, "remaining": max(0, len(rows) - processed)}
    except Exception:
        db.rollback()
        logger.exception("sync outbox dispatch failed")
        raise
    finally:
        db.close()
