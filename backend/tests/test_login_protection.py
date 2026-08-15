from __future__ import annotations

from datetime import datetime, timedelta
from types import SimpleNamespace

from app._compat import UTC
from app.security.login_protection import (
    LOCKOUT_MINUTES,
    MAX_FAILED_LOGIN_ATTEMPTS,
    is_locked,
    register_failed_login,
    register_successful_login,
)


def test_failed_logins_lock_account_after_threshold():
    now = datetime.now(UTC)
    user = SimpleNamespace(failed_login_attempts=MAX_FAILED_LOGIN_ATTEMPTS - 1, locked_until=None)

    assert register_failed_login(user, now=now) is True
    assert user.failed_login_attempts == MAX_FAILED_LOGIN_ATTEMPTS
    assert is_locked(user, now=now)
    assert user.locked_until == now + timedelta(minutes=LOCKOUT_MINUTES)


def test_successful_login_clears_lockout_state():
    user = SimpleNamespace(failed_login_attempts=5, locked_until=datetime.now(UTC) + timedelta(minutes=5))

    register_successful_login(user)

    assert user.failed_login_attempts == 0
    assert user.locked_until is None


def test_expired_lockout_is_not_active():
    user = SimpleNamespace(failed_login_attempts=5, locked_until=datetime.now(UTC) - timedelta(seconds=1))

    assert is_locked(user) is False
