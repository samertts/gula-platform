"""P0-D regression tests — password change/reset revokes active sessions.

Synthetic fixtures only. Pins two defects:
  * ``change_password`` called ``bump_perm_version(db, id)`` (wrong signature),
    which raised TypeError after the password hash was already written;
  * ``reset_password`` never revoked existing tokens at all.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta

import app.routes.password_reset as password_reset
import pytest
from app._compat import UTC
from app.security.redis_client import SecurityStoreUnavailable
from app.security.session import (
    bump_perm_version,
    get_perm_version,
    perm_ver_key,
    warm_perm_version,
)


class _FakeUser:
    def __init__(self):
        self.id = 77
        self.email = "synthetic@example.invalid"
        self.role = "admin"
        self.password_hash = "old-hash"
        self.perm_version = 3
        self.reset_token = "reset-hash"
        self.reset_token_expires = datetime.now(UTC) + timedelta(hours=1)


class _FakeQuery:
    def __init__(self, user):
        self._user = user

    def filter(self, *_args, **_kwargs):
        return self

    def all(self):
        return [self._user] if self._user.reset_token else []


class _FakeDb:
    def __init__(self, user):
        self._user = user
        self.commit_count = 0

    def query(self, *_args):
        return _FakeQuery(self._user)

    def commit(self):
        self.commit_count += 1


@pytest.fixture()
def bump_spy(monkeypatch):
    calls = []

    def _spy(user, db, **kwargs):
        calls.append((user, db, kwargs))

    monkeypatch.setattr("app.security.session.bump_perm_version", _spy)
    monkeypatch.setattr(password_reset, "hash_password", lambda _pw: "new-hash")
    # AUD-F17/P-15: reset_password's audit write is now fail-closed (no silent
    # contextlib.suppress). These tests exercise session revocation with a fake
    # DB, so stub the canonical writer as the other collaborators are stubbed.
    monkeypatch.setattr(password_reset, "log_action", lambda *args, **kwargs: None)
    return calls


def test_change_password_uses_correct_bump_signature(bump_spy):
    user = _FakeUser()
    db = _FakeDb(user)
    monkeypatch = pytest.MonkeyPatch()
    try:
        monkeypatch.setattr(
            "shared.auth.passwords.verify_password",
            lambda _plain, _hashed: True,
        )
        asyncio.run(
            password_reset.change_password(
                password_reset.ChangePasswordRequest(
                    current_password="old-password",
                    new_password="NewPass123!",
                ),
                db=db,
                current_user=user,
            ),
        )
    finally:
        monkeypatch.undo()

    assert len(bump_spy) == 1
    called_user, called_db, kwargs = bump_spy[0]
    assert called_user is user
    assert called_db is db
    assert kwargs == {"reason": "password_change"}
    assert user.password_hash == "new-hash"
    assert db.commit_count == 1


def test_reset_password_revokes_sessions_and_clears_token(bump_spy, monkeypatch):
    user = _FakeUser()
    db = _FakeDb(user)
    monkeypatch.setattr(
        "shared.auth.passwords.verify_password",
        lambda _plain, _hashed: True,
    )
    asyncio.run(
        password_reset.reset_password(
            password_reset.ResetPasswordRequest(
                token="synthetic-token",
                new_password="NewPass123!",
            ),
            db=db,
        ),
    )

    assert len(bump_spy) == 1
    called_user, called_db, kwargs = bump_spy[0]
    assert called_user is user
    assert called_db is db
    assert kwargs == {"reason": "password_reset"}
    assert user.password_hash == "new-hash"
    assert user.reset_token is None
    assert user.reset_token_expires is None
    assert db.commit_count == 1


def test_reset_password_invalid_token_does_not_revoke(bump_spy, monkeypatch):
    user = _FakeUser()
    db = _FakeDb(user)
    monkeypatch.setattr(
        "shared.auth.passwords.verify_password",
        lambda _plain, _hashed: False,
    )
    with pytest.raises(Exception) as exc:
        asyncio.run(
            password_reset.reset_password(
                password_reset.ResetPasswordRequest(
                    token="wrong-token",
                    new_password="NewPass123!",
                ),
                db=db,
            ),
        )
    assert getattr(exc.value, "status_code", None) == 400
    assert bump_spy == []
    assert db.commit_count == 0


# ─────────────────────────────────────────────────────────────────────────────
# P0-D3 — session-store fail-closed regression tests (synthetic fixtures only)
# ─────────────────────────────────────────────────────────────────────────────

class _FakeStore:
    """In-memory stand-in for the shared security store, with fault injection."""

    def __init__(self, values=None, *, get_exc=None, set_exc=None):
        self.values = dict(values or {})
        self.get_exc = get_exc
        self.set_exc = set_exc
        self.writes = []

    def get(self, key):
        if self.get_exc is not None:
            raise self.get_exc
        return self.values.get(key)

    def set(self, key, value, ex=None):
        if self.set_exc is not None:
            raise self.set_exc
        self.writes.append((key, value, ex))
        self.values[key] = str(value)


class _BumpUser:
    """Minimal legacy-shaped user: numeric id, perm_version, email (lab kind)."""

    def __init__(self, version=3, user_id=77):
        self.id = user_id
        self.email = "synthetic@example.invalid"
        self.perm_version = version


@pytest.fixture()
def session_store(monkeypatch):
    """Patch the store factory used by session.py; return a helper to install stores."""

    def _install(store=None, *, unavailable=False):
        if unavailable:

            def _raise(_operation):
                raise SecurityStoreUnavailable("synthetic shared-store outage")

            monkeypatch.setattr("app.security.session.security_store", _raise)
            return None
        store = store or _FakeStore()
        monkeypatch.setattr("app.security.session.security_store", lambda _op: store)
        return store

    return _install


def test_unavailable_store_falls_back_to_authoritative_db(session_store):
    """Redis unavailable in production → use DB version; never accept unknown state."""
    session_store(unavailable=True)
    assert get_perm_version(77, 4, "lab") == 4


def test_store_timeout_falls_back_to_authoritative_db(session_store):
    """A store timeout (transport error) is treated as a cache miss, not a pass."""
    store = _FakeStore(get_exc=TimeoutError("synthetic timeout"))
    session_store(store)
    assert get_perm_version(77, 5, "lab") == 5


def test_missing_entry_uses_db_version(session_store):
    store = _FakeStore()
    session_store(store)
    assert get_perm_version(77, 6, "lab") == 6


@pytest.mark.parametrize("bad", ["", "abc", "-1", "0", "3.7", True, object()])
def test_malformed_cached_value_ignored(session_store, bad):
    """Malformed/malicious cache values must never decide session validity."""
    store = _FakeStore({perm_ver_key(77, "lab"): bad})
    session_store(store)
    assert get_perm_version(77, 4, "lab") == 4


def test_stale_cache_cannot_keep_revoked_session_alive(session_store):
    """A stale cached version lower than the DB version must NOT preserve access."""
    store = _FakeStore({perm_ver_key(77, "lab"): 3})  # old, pre-revocation
    session_store(store)
    assert get_perm_version(77, 5, "lab") == 5  # revocation honoured


def test_fresher_cache_is_honoured_defensively(session_store):
    """A cached version ahead of DB (replica lag on DB) stays on the safe side."""
    store = _FakeStore({perm_ver_key(77, "lab"): 7})
    session_store(store)
    assert get_perm_version(77, 5, "lab") == 7


def test_bump_publishes_new_version_and_bumps_db(session_store, monkeypatch):
    monkeypatch.setattr("app.security.session.log_action", lambda *_a, **_k: None)
    store = session_store(_FakeStore())
    user = _BumpUser(version=3)
    new = bump_perm_version(user, object(), reason="password_reset")
    assert new == 4
    assert user.perm_version == 4
    assert (perm_ver_key(77, "lab"), 4, 86400 * 31) in store.writes


def test_bump_with_failed_store_still_bumps_db(session_store, monkeypatch):
    """A store write failure must not abort the authoritative DB revocation."""
    monkeypatch.setattr("app.security.session.log_action", lambda *_a, **_k: None)
    store = _FakeStore(set_exc=TimeoutError("synthetic write timeout"))
    session_store(store)
    user = _BumpUser(version=3)
    new = bump_perm_version(user, object(), reason="role_change")
    assert new == 4
    assert user.perm_version == 4  # DB bump survives the store outage


def test_password_reset_then_old_session_reuse_rejected(session_store, monkeypatch):
    """After a reset bumps perm_version, an old token (perm_ver=3) is unusable.

    Also covers the stale-cache case: even if the store still holds the old
    value, the fresh DB version is authoritative and the old token is rejected.
    """
    monkeypatch.setattr("app.security.session.log_action", lambda *_a, **_k: None)
    store = session_store(_FakeStore())
    user = _BumpUser(version=3)

    bump_perm_version(user, object(), reason="password_reset")  # DB now 4
    store.values[perm_ver_key(77, "lab")] = 3  # simulate a stale cache entry

    old_token_perm_ver = 3
    authoritative = get_perm_version(user.id, user.perm_version, "lab")
    assert authoritative == 4
    assert old_token_perm_ver != authoritative  # -> 401 "Permissions updated"


def test_normal_authentication_version_match(session_store):
    """A current token with a matching version authenticates normally."""
    store = _FakeStore({perm_ver_key(77, "lab"): 3})
    session_store(store)
    assert get_perm_version(77, 3, "lab") == 3  # token perm_ver=3 matches


def test_normal_logout_marks_token_blacklisted(monkeypatch):
    """Successful logout blacklists the JTI; a later check sees it revoked."""
    store = _FakeStore()
    monkeypatch.setattr(
        "app.security.redis_client.security_store", lambda _op: store,
    )
    from app.security.auth import blacklist_token, is_token_blacklisted

    assert is_token_blacklisted("jti-synthetic") is False
    blacklist_token("jti-synthetic", 3600)
    assert is_token_blacklisted("jti-synthetic") is True


def test_blacklist_check_unavailable_fails_closed(monkeypatch):
    """If revocation state can't be read, the check raises (→ HTTP 503)."""
    def _raise(_op):
        raise SecurityStoreUnavailable("synthetic outage")

    monkeypatch.setattr("app.security.redis_client.security_store", _raise)
    from app.security.auth import is_token_blacklisted

    with pytest.raises(SecurityStoreUnavailable):
        is_token_blacklisted("jti-synthetic")


def test_warm_perm_version_seeds_store_and_tolerates_outage(session_store):
    """Warm writes the current version when available and is harmless when not."""
    store = session_store(_FakeStore())
    warm_perm_version(_BumpUser(version=4))
    assert (perm_ver_key(77, "lab"), 4, 86400 * 31) in store.writes

    session_store(unavailable=True)
    warm_perm_version(_BumpUser(version=4))  # must not raise

