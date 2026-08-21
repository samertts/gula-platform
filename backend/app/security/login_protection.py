"""Account-level brute-force protection for both citizen and lab accounts."""

from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Any

from app._compat import UTC

MAX_FAILED_LOGIN_ATTEMPTS = int(os.getenv("MAX_FAILED_LOGIN_ATTEMPTS", "5"))
LOCKOUT_MINUTES = int(os.getenv("LOGIN_LOCKOUT_MINUTES", "15"))


def is_locked(user: Any, now: datetime | None = None) -> bool:
    locked_until = getattr(user, "locked_until", None)
    if not isinstance(locked_until, datetime):
        return False
    current = now or datetime.now(UTC)
    return locked_until > current


def register_failed_login(user: Any, now: datetime | None = None) -> bool:
    """Increment failures and return whether the account is now locked."""
    current = now or datetime.now(UTC)
    attempts = int(getattr(user, "failed_login_attempts", 0) or 0) + 1
    user.failed_login_attempts = attempts
    if attempts >= MAX_FAILED_LOGIN_ATTEMPTS:
        user.locked_until = current + timedelta(minutes=LOCKOUT_MINUTES)
        return True
    return False


def register_successful_login(user: Any) -> None:
    """Clear the account lockout state after a valid, unlocked login."""
    user.failed_login_attempts = 0
    user.locked_until = None
