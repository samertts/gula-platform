"""Shared policy helpers for canonical NIAM sessions."""

from __future__ import annotations

import os
from datetime import datetime, timedelta

from app._compat import UTC

# The absolute timeout is persisted per session as ``expires_at``. Idle timeout
# is deliberately shorter and independently checked on every canonical request.
SESSION_IDLE_TIMEOUT_MINUTES = int(os.getenv("NIAM_SESSION_IDLE_TIMEOUT_MINUTES", "60"))
SESSION_IDLE_TIMEOUT = timedelta(minutes=SESSION_IDLE_TIMEOUT_MINUTES)


def session_is_expired(*, now: datetime, expires_at: datetime | None) -> bool:
    if expires_at is None:
        return True
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    return expires_at <= now


def session_is_idle(*, now: datetime, last_activity_at: datetime | None) -> bool:
    if last_activity_at is None:
        return True
    if last_activity_at.tzinfo is None:
        last_activity_at = last_activity_at.replace(tzinfo=UTC)
    return last_activity_at + SESSION_IDLE_TIMEOUT <= now


def session_is_usable(*, now: datetime, expires_at: datetime | None, last_activity_at: datetime | None) -> bool:
    return not session_is_expired(now=now, expires_at=expires_at) and not session_is_idle(
        now=now,
        last_activity_at=last_activity_at,
    )
