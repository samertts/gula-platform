"""MPI reliability primitives — serialization, version control and bounded retry.

Scope (MPI-only): every control in this module is PostgreSQL-native and needs
**no schema change, no Redis, no distributed lock and no new dependency**.

* The audit-chain lock is a single transaction-scoped advisory lock
  (``pg_advisory_xact_lock``). It is acquired at the outermost transaction level,
  before any SAVEPOINT and before the audit-tail read, and is released only by
  the caller's outer COMMIT/ROLLBACK. **Session-scoped locks are never used.**
* On non-PostgreSQL dialects (the SQLite test fixture) lock acquisition is a
  documented no-op: SQLite cannot prove PostgreSQL locking, and the real
  concurrency proof lives in the out-of-repository PostgreSQL harness.
* Version control uses one atomic ``UPDATE … SET version = version + 1
  … RETURNING version`` statement, with an optional optimistic version guard.
* Retry is bounded, classifies SQLSTATEs, never retries permanent integrity
  violations, never reuses a failed session, and reconciles an ambiguous commit
  through the caller-supplied idempotency lookup before any replay.

Nothing here owns a commit. The caller (HTTP endpoint or service) remains the
transaction owner.
"""

from __future__ import annotations

import contextlib
import hashlib
import time
from collections.abc import Callable
from typing import Any

from sqlalchemy import text, update
from sqlalchemy.orm import Session

# ── Transaction-scoped audit-chain lock ───────────────────────────────────────
# A versioned namespace makes the key stable across processes/workers and makes
# an intentional future key rotation an explicit, reviewable change. The key is
# public configuration — never a secret. The one-argument bigint overload of
# pg_advisory_xact_lock avoids collisions with two-int application namespaces.
AUDIT_LOCK_NAMESPACE = "gula:mpi:audit_chain:tail:v1"
AUDIT_LOCK_KEY: int = (
    int.from_bytes(hashlib.sha256(AUDIT_LOCK_NAMESPACE.encode("utf-8")).digest()[:8], "big")
    & 0x7FFF_FFFF_FFFF_FFFF
)


def acquire_audit_chain_lock(db: Session) -> bool:
    """Acquire the transaction-scoped audit-chain advisory lock.

    Returns ``True`` when a real PostgreSQL lock was acquired, ``False`` when
    the dialect cannot support advisory locks (SQLite test fixture). The lock
    is held by the *transaction*, not the session: it is released by the outer
    COMMIT/ROLLBACK and survives SAVEPOINT rollback, which is exactly why it
    must be acquired before ``begin_nested()``.
    """
    return _acquire_xact_lock(db, AUDIT_LOCK_KEY)


# AUD-02: canonical link writes are a separate append class from the MPI audit
# chain.  They get their OWN transaction-scoped advisory key so two concurrent
# link calls serialise on a check-then-insert that has no DB unique constraint
# yet (the UNIQUE(patient_id)/UNIQUE(citizen_id) migration is an owner-gated
# proposal -- see the AUD-02 Migration Proposal; no DDL is executed here).
CANONICAL_LINK_LOCK_NAMESPACE = "gula:canonical:link:v1"
CANONICAL_LINK_LOCK_KEY: int = (
    int.from_bytes(
        hashlib.sha256(CANONICAL_LINK_LOCK_NAMESPACE.encode("utf-8")).digest()[:8], "big"
    )
    & 0x7FFF_FFFF_FFFF_FFFF
)


def _acquire_xact_lock(db: Session, key: int) -> bool:
    bind = db.get_bind()
    if bind is None or bind.dialect.name != "postgresql":
        return False
    db.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": key})
    return True


def acquire_canonical_link_lock(db: Session) -> bool:
    """Serialise canonical link check-then-insert (AUD-02). PostgreSQL only."""
    return _acquire_xact_lock(db, CANONICAL_LINK_LOCK_KEY)


# ── Version control ───────────────────────────────────────────────────────────


class VersionConflictError(RuntimeError):
    """Raised when an optimistic version guard finds a stale version."""


def atomic_increment_version(
    db: Session,
    instance: Any,
    model: Any,
    *,
    expected: int | None = None,
) -> int:
    """Atomically increment ``instance.version`` and return the new value.

    ``SET version = version + 1`` is evaluated by PostgreSQL, so two concurrent
    transactions cannot lose an update. When ``expected`` is supplied an
    optimistic guard (``WHERE version = :expected``) is added; a stale writer
    gets ``VersionConflictError`` and no mutation. The ORM attribute is expired
    afterwards so no redundant write is emitted on the next flush.
    """
    column = model.version
    stmt = update(model).where(model.id == instance.id).values(version=column + 1)
    if expected is not None:
        stmt = stmt.where(column == expected)
    stmt = stmt.returning(column)
    new_version = db.execute(stmt).scalar_one_or_none()
    if new_version is None:
        raise VersionConflictError(
            f"version conflict on {model.__tablename__} row {instance.id}"
        )
    db.expire(instance, ["version"])
    return int(new_version)


# ── SQLSTATE classification ──────────────────────────────────────────────────

# Explicit allowlist. Anything not listed here is NOT retried.
TRANSIENT_SQLSTATES = frozenset(
    {
        "40001",  # serialization_failure
        "40P01",  # deadlock_detected
        "55P03",  # lock_not_available
        "57014",  # query_canceled (reconcile before replay)
        "08000", "08001", "08003", "08004", "08006", "08007", "08S01",  # connection
        "57P01", "57P02", "57P03",  # admin shutdown / crash / cannot connect now
    }
)

# Explicit denylist of permanent integrity/data errors (never retried).
PERMANENT_SQLSTATES = frozenset(
    {
        "23505",  # unique_violation — handled as idempotent replay at the claim key
        "23503",  # foreign_key_violation
        "23502",  # not_null_violation
        "23514",  # check_violation
        "23515",  # exclusion_violation
        "22000", "22001", "22003", "22007", "22008",  # data exceptions
        "42501",  # insufficient_privilege
    }
)


def sqlstate_of(exc: BaseException) -> str | None:
    """Find a PostgreSQL SQLSTATE in an exception or its chained causes."""
    seen: set[int] = set()
    current: BaseException | None = exc
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        pgcode = getattr(current, "pgcode", None)
        if pgcode:
            return str(pgcode)
        sqlstate = getattr(current, "sqlstate", None)
        if sqlstate:
            return str(sqlstate)
        original = getattr(current, "orig", None)
        if original is not None and isinstance(original, BaseException):
            current = original
            continue
        current = current.__cause__ or current.__context__
    return None


def is_transient_db_error(exc: BaseException) -> bool:
    """True only for explicitly classified transient database errors."""
    state = sqlstate_of(exc)
    return state in TRANSIENT_SQLSTATES if state is not None else False


def is_permanent_db_error(exc: BaseException) -> bool:
    """True for explicitly classified permanent integrity/data errors."""
    state = sqlstate_of(exc)
    return state in PERMANENT_SQLSTATES if state is not None else False


# ── Bounded retry with ambiguous-commit reconciliation ───────────────────────

def bounded_retry[T](
    session_factory: Callable[[], Session],
    operation: Callable[[Session], T],
    *,
    reconcile: Callable[[], T | None] | None = None,
    max_attempts: int = 3,
    backoff_seconds: tuple[float, ...] = (0.025, 0.05),
) -> T:
    """Run ``operation`` in fresh transactions with bounded, classified retry.

    ``operation`` receives one session, performs the whole transaction body and
    returns **plain captured values** (never ORM objects — the session is
    committed and closed by this helper, and ``expire_on_commit=True`` would
    otherwise turn response building into post-commit SELECTs).

    On failure the session is rolled back and closed. A transient SQLSTATE is
    retried at most ``max_attempts`` times with the configured backoff; every
    other exception (including permanent integrity violations and validation
    errors) propagates immediately. Before any replay, ``reconcile`` is called
    on a fresh session so an in-doubt commit is resolved by the idempotency
    lookup — never by a blind replay.
    """
    if max_attempts < 1:
        raise ValueError("max_attempts must be >= 1")

    for attempt in range(max_attempts):
        session = session_factory()
        try:
            result = operation(session)
            session.commit()
            return result
        except Exception as exc:
            # A broken connection may reject rollback; either way the session
            # is closed in `finally` and never reused for a replay.
            with contextlib.suppress(Exception):
                session.rollback()
            if not is_transient_db_error(exc) or attempt + 1 >= max_attempts:
                raise
            # `finally` below closes the failed session before we continue, so
            # any in-doubt locks are released before reconciliation reads.
        finally:
            session.close()

        # Ambiguous commit: reconcile before any replay. If the attempt actually
        # committed, return its original result without writing anything again.
        if reconcile is not None:
            prior = reconcile()
            if prior is not None:
                return prior
        if attempt < len(backoff_seconds):
            time.sleep(backoff_seconds[attempt])

    raise RuntimeError("unreachable: bounded_retry exhausted its loop")  # pragma: no cover


__all__ = [
    "AUDIT_LOCK_KEY",
    "AUDIT_LOCK_NAMESPACE",
    "CANONICAL_LINK_LOCK_KEY",
    "CANONICAL_LINK_LOCK_NAMESPACE",
    "PERMANENT_SQLSTATES",
    "TRANSIENT_SQLSTATES",
    "VersionConflictError",
    "acquire_audit_chain_lock",
    "acquire_canonical_link_lock",
    "atomic_increment_version",
    "bounded_retry",
    "is_permanent_db_error",
    "is_transient_db_error",
    "sqlstate_of",
]
