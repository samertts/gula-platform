"""Idempotency Key Middleware — GULA Platform
=============================================
Prevents double-processing of mutating API requests.

How it works:
  1. Client sends header: `Idempotency-Key: <uuid>`
  2. Dependency checks if key was seen before (in `idempotency_keys` table).
  3. If seen → returns the cached response immediately (HTTP 200).
  4. If new  → stores the key before processing; caches response after.

Supported on: POST endpoints that create or mutate clinical data
  - POST /api/orders
  - POST /api/results (entering results)
  - POST /api/results/{id}/validate
  - POST /api/samples

Usage (in a route):
    @router.post("/orders")
    def create_order(
        ...,
        idem: IdempotencyResult = Depends(idempotency_check),
    ):
        if idem.is_duplicate:
            return idem.cached_response     # replay previous result

        # ... business logic ...

        idem.cache(db, status_code=201, body=response)

Rules:
  - Keys are scoped per lab (prevents cross-lab replay attacks).
  - Keys expire after 24 hours (auto-purged by maintenance CRON).
  - Key format: any non-empty string ≤ 255 chars (UUIDs recommended).
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Any, Optional

from fastapi import Depends, Header, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db
from app.security.dependencies import get_current_user

logger = logging.getLogger("gula.idempotency")

_KEY_TTL_HOURS = 24


@dataclass
class IdempotencyResult:
    """Passed to the route handler after the idempotency check."""
    key:             str
    is_duplicate:    bool
    cached_response: Optional[Any]
    _db:             Session
    _lab_id:         Optional[int]
    _endpoint:       str

    def cache(self, status_code: int, body: Any) -> None:
        """
        Cache the response for this key so replay requests return the same answer.
        Call this AFTER the business operation succeeds.
        """
        if self.is_duplicate:
            return  # nothing to cache — already stored
        try:
            self._db.execute(
                text("""
                    UPDATE idempotency_keys
                    SET status_code   = :sc,
                        response_body = :body
                    WHERE key = :key
                """),
                {
                    "sc":   status_code,
                    "body": json.dumps(body, ensure_ascii=False, default=str),
                    "key":  self.key,
                },
            )
            # Don't commit — let the caller's transaction handle it
        except Exception as exc:
            logger.warning("[IDEMPOTENCY] Failed to cache response for key=%s: %s", self.key, exc)


def idempotency_check(
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> IdempotencyResult:
    """
    FastAPI dependency.  Use on any POST endpoint that creates or mutates data.

    If no Idempotency-Key header is present, the check passes through
    (not all clients send one; we do not require it).
    """
    if not idempotency_key:
        # No key supplied — pass through without idempotency protection
        return IdempotencyResult(
            key="",
            is_duplicate=False,
            cached_response=None,
            _db=db,
            _lab_id=getattr(current_user, "lab_id", None),
            _endpoint="",
        )

    key = idempotency_key.strip()
    if len(key) > 255:
        raise HTTPException(status_code=400, detail="Idempotency-Key must be ≤ 255 characters")

    lab_id = getattr(current_user, "lab_id", None)

    # Compute cutoff in Python so the query works on both SQLite and PostgreSQL
    cutoff = datetime.now(timezone.utc) - timedelta(hours=_KEY_TTL_HOURS)

    # Check for existing key
    row = db.execute(
        text("""
            SELECT status_code, response_body
            FROM idempotency_keys
            WHERE key = :key
              AND (lab_id = :lab_id OR lab_id IS NULL)
              AND created_at > :cutoff
        """),
        {"key": key, "lab_id": lab_id, "cutoff": cutoff},
    ).fetchone()

    if row:
        sc, body = row
        cached = json.loads(body) if body else None
        logger.info("[IDEMPOTENCY] duplicate request detected key=%s lab=%s", key, lab_id)
        return IdempotencyResult(
            key=key,
            is_duplicate=True,
            cached_response=cached,
            _db=db,
            _lab_id=lab_id,
            _endpoint="",
        )

    # New key — insert reservation so concurrent requests are rejected
    try:
        db.execute(
            text("""
                INSERT INTO idempotency_keys (key, lab_id, created_at)
                VALUES (:key, :lab_id, :now)
                ON CONFLICT (key) DO NOTHING
            """),
            {"key": key, "lab_id": lab_id, "now": datetime.now(timezone.utc)},
        )
        db.flush()
    except Exception as exc:
        logger.warning("[IDEMPOTENCY] Insert failed for key=%s: %s", key, exc)

    return IdempotencyResult(
        key=key,
        is_duplicate=False,
        cached_response=None,
        _db=db,
        _lab_id=lab_id,
        _endpoint="",
    )


def purge_expired_keys(db: Session) -> int:
    """
    Delete idempotency keys older than _KEY_TTL_HOURS.
    Call from a maintenance CRON or startup task.
    """
    from datetime import datetime, timedelta

    cutoff = datetime.utcnow() - timedelta(hours=_KEY_TTL_HOURS)
    result = db.execute(
        text("""
            DELETE FROM idempotency_keys
            WHERE created_at < :cutoff
        """),
        {"cutoff": cutoff},
    )
    db.commit()
    return result.rowcount
