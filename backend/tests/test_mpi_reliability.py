"""MPI reliability primitive regressions — synthetic fixtures exclusively.

Pins MPI-01 (stable versioned advisory-lock key + SQLite no-op), MPI-03
(atomic version increment with optimistic guard) and MPI-07 (SQLSTATE
classification, bounded retry, no session reuse, reconcile-before-replay,
no replay of permanent errors).
"""

from __future__ import annotations

import pytest
from app.services.mpi.models import Citizen
from app.services.mpi.reliability import (
    AUDIT_LOCK_KEY,
    AUDIT_LOCK_NAMESPACE,
    PERMANENT_SQLSTATES,
    TRANSIENT_SQLSTATES,
    VersionConflictError,
    acquire_audit_chain_lock,
    atomic_increment_version,
    bounded_retry,
    is_permanent_db_error,
    is_transient_db_error,
    sqlstate_of,
)

# ── MPI-01: advisory lock identity ─────────────────────────────────────────


def test_audit_lock_key_is_stable_and_versioned():
    assert AUDIT_LOCK_NAMESPACE.endswith(":v1")
    assert isinstance(AUDIT_LOCK_KEY, int)
    assert 0 <= AUDIT_LOCK_KEY <= 0x7FFF_FFFF_FFFF_FFFF
    # Deterministic across processes: recompute from the public namespace.
    import hashlib

    expected = (
        int.from_bytes(hashlib.sha256(AUDIT_LOCK_NAMESPACE.encode("utf-8")).digest()[:8], "big")
        & 0x7FFF_FFFF_FFFF_FFFF
    )
    assert expected == AUDIT_LOCK_KEY


def test_audit_lock_is_noop_on_sqlite(db):
    # The SQLite test fixture cannot support PostgreSQL advisory locks; the
    # primitive must degrade to a documented no-op rather than emitting SQL.
    assert acquire_audit_chain_lock(db) is False


# ── MPI-03: atomic version increment ───────────────────────────────────────


def test_atomic_increment_increments_once(db):
    c = Citizen(
        citizen_ulid="01SYNTHRELIAB00000000000000"[:26],
        name_canonical="synthetic reliability",
        name_blocking_key="synreliab"[:20],
        status="active",
        version=1,
    )
    db.add(c)
    db.flush()
    new = atomic_increment_version(db, c, Citizen)
    assert new == 2
    db.expire_all()
    assert db.query(Citizen).filter(Citizen.id == c.id).one().version == 2


def test_atomic_increment_optimistic_guard_rejects_stale_version(db):
    c = Citizen(
        citizen_ulid="01SYNTHRELSTAL0000000000000"[:26],
        name_canonical="synthetic stale",
        name_blocking_key="synstale"[:20],
        status="active",
        version=5,
    )
    db.add(c)
    db.flush()
    with pytest.raises(VersionConflictError):
        atomic_increment_version(db, c, Citizen, expected=4)
    db.expire_all()
    # The stale writer performed no mutation.
    assert db.query(Citizen).filter(Citizen.id == c.id).one().version == 5


# ── MPI-07: SQLSTATE classification ────────────────────────────────────────


class _DbError(Exception):
    """Synthetic DB error exposing a SQLSTATE the way a DBAPI error does."""

    def __init__(self, state: str, message: str = "synthetic"):
        super().__init__(message)
        self.pgcode = state


@pytest.mark.parametrize("state", ["40001", "40P01", "55P03", "57014", "08006"])
def test_transient_sqlstates_are_classified(state):
    assert state in TRANSIENT_SQLSTATES
    exc = _DbError(state)
    assert sqlstate_of(exc) == state
    assert is_transient_db_error(exc) is True
    assert is_permanent_db_error(exc) is False


@pytest.mark.parametrize("state", ["23505", "23503", "23502", "23514", "42501"])
def test_permanent_sqlstates_are_never_transient(state):
    assert state in PERMANENT_SQLSTATES
    exc = _DbError(state)
    assert is_transient_db_error(exc) is False
    assert is_permanent_db_error(exc) is True


def test_unknown_error_is_not_retried():
    assert is_transient_db_error(RuntimeError("synthetic")) is False
    assert sqlstate_of(RuntimeError("synthetic")) is None


# ── MPI-07: bounded retry mechanics ────────────────────────────────────────


class _FakeSession:
    def __init__(self, *, fail_with: Exception | None = None):
        self.fail_with = fail_with
        self.committed = False
        self.rolled_back = False
        self.closed = False

    def commit(self):
        if self.fail_with is not None:
            raise self.fail_with
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def close(self):
        self.closed = True


def _transient():
    return _DbError("40001", "synthetic transient")


def test_retry_uses_fresh_session_and_succeeds():
    sessions = [_FakeSession(fail_with=_transient()), _FakeSession()]
    calls: list[int] = []

    def op(session):
        calls.append(1)
        return len(calls)

    made: list[_FakeSession] = []

    def factory():
        idx = len(made)
        session = sessions[idx] if idx < len(sessions) else _FakeSession()
        made.append(session)
        return session

    result = bounded_retry(factory, op, backoff_seconds=(0, 0))
    assert result == 2
    # First failed session rolled back and closed; never reused.
    assert sessions[0].rolled_back is True and sessions[0].closed is True
    assert sessions[0].committed is False
    assert sessions[1].committed is True


def test_retry_reconciles_ambiguous_commit_before_replay():
    sessions = [_FakeSession(fail_with=_transient())]
    calls: list[int] = []
    reconciled: list[int] = []

    def op(session):
        calls.append(1)
        return "written"

    def reconcile():
        reconciled.append(1)
        return "reconciled"

    result = bounded_retry(
        lambda: sessions[0], op, reconcile=reconcile, backoff_seconds=(0, 0)
    )
    assert result == "reconciled"
    assert len(calls) == 1  # no blind replay
    assert len(reconciled) == 1
    # Failed session is closed (locks released) before reconciliation reads.
    assert sessions[0].closed is True and sessions[0].rolled_back is True


def test_permanent_error_is_not_retried():
    sessions = [_FakeSession(fail_with=_DbError("23505"))]
    calls: list[int] = []

    def op(session):
        calls.append(1)

    with pytest.raises(_DbError):
        bounded_retry(lambda: sessions[0], op, backoff_seconds=(0, 0))
    assert len(calls) == 1


def test_retry_stops_at_max_attempts():
    sessions = [_FakeSession(fail_with=_transient()) for _ in range(3)]
    calls: list[int] = []

    def op(session):
        calls.append(1)

    made: list[_FakeSession] = []

    def factory():
        idx = len(made)
        session = sessions[idx] if idx < len(sessions) else _FakeSession()
        made.append(session)
        return session

    with pytest.raises(_DbError):
        bounded_retry(factory, op, max_attempts=3, backoff_seconds=(0, 0))
    assert len(calls) == 3
    assert all(s.closed for s in made)
