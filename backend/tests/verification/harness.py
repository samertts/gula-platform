"""The canonical real-PostgreSQL verification harness.

Before this module, nine PostgreSQL-gated test files each rolled their own
bootstrap behind three different environment variable names
(``BLOOD_BANK_POSTGRES_URL``, ``BIOMED_POSTGRES_URL``, ``CC_POSTGRES_URL``),
seven of them calling ``create_engine`` twice apiece, and one of them importing
private helpers out of a sibling *test* module.  There was no shared fixture in
any ``conftest.py``.  That duplication is why real-PostgreSQL evidence stopped
at one domain: the cost of the tenth harness was the cost of the first.

This module is the shared one.  It deliberately does four things and no more:

* gates on a single canonical URL so a missing database skips rather than passes;
* builds sessions and an authenticated ``TestClient`` against the real app;
* reads back the *physical* truth — receipts, audit rows, column existence —
  with SQL rather than the ORM, because the ORM is sometimes the thing under
  suspicion;
* runs two actors against one row simultaneously on independent connections,
  which is the only way a concurrency claim can be earned.

It does not create tables.  A database handed to it must have been built by
migrations, so that ORM/migration drift is observable instead of papered over
by ``create_all``.
"""

from __future__ import annotations

import os
import threading
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

# One canonical name.  Domain-specific names are accepted as fallbacks only so
# that an operator who already exported one of the older three is not stranded.
_CANONICAL_ENV = "GULA_VERIFICATION_POSTGRES_URL"
_LEGACY_ENV = ("BLOOD_BANK_POSTGRES_URL", "CC_POSTGRES_URL", "BIOMED_POSTGRES_URL")


def postgres_url() -> str | None:
    """The verification database URL, or None when none is configured."""
    for name in (_CANONICAL_ENV, *_LEGACY_ENV):
        value = os.getenv(name)
        if value:
            return value
    return None


def requires_postgres() -> Any:
    """Skip marker for a module that cannot honestly run without PostgreSQL."""
    return pytest.mark.skipif(
        not postgres_url(),
        reason=f"{_CANONICAL_ENV} is not configured; a PostgreSQL claim must not be inferred",
    )


def session_factory(*, pool_size: int = 8) -> Any:
    """A sessionmaker bound to a fresh engine.

    ``expire_on_commit=False`` so a test can read attributes after commit, and
    ``max_overflow=0`` so a leaked connection surfaces as a timeout rather than
    as unbounded growth that hides the leak.
    """
    url = postgres_url()
    if not url:  # pragma: no cover - guarded by requires_postgres()
        raise RuntimeError("no verification PostgreSQL URL configured")
    engine = create_engine(url, future=True, pool_size=pool_size, max_overflow=0)
    return sessionmaker(bind=engine, expire_on_commit=False)


def dispose(Session: Any) -> None:
    """Release the engine behind a session factory."""
    Session.kw["bind"].dispose()


# ---------------------------------------------------------------------------
# Physical-schema probes.  These read the database, never the ORM's opinion of
# it, which is what makes ORM/migration drift visible.
# ---------------------------------------------------------------------------


def physical_tables(Session: Any) -> set[str]:
    """Table names the database actually has."""
    return set(inspect(Session.kw["bind"]).get_table_names())


def physical_columns(Session: Any, table: str) -> set[str]:
    """Column names the database actually has for ``table``.

    Raises if the table is absent, rather than returning an empty set.  An
    absent table and a table with no matching columns are different findings and
    conflating them would let 405 missing tables read as 405 clean ones.
    """
    return {c["name"] for c in inspect(Session.kw["bind"]).get_columns(table)}


def orm_columns(model: Any) -> set[str]:
    """Column names the ORM declares for ``model``."""
    return {c.name for c in model.__table__.columns}


def missing_physical_columns(Session: Any, model: Any) -> set[str]:
    """Columns the ORM writes that the migrated database does not have.

    A non-empty result means any write touching those attributes raises
    ``UndefinedColumn`` at runtime, while a SQLite ``create_all`` suite built
    from the same ORM would pass — which is precisely why this probe exists.
    """
    return orm_columns(model) - physical_columns(Session, model.__table__.name)


def mapped_classes_by_table(models: dict[str, list[Any]] | dict[str, Any]) -> dict[str, list[Any]]:
    """Normalise a table->model or table->models mapping to table->list."""
    return {t: (m if isinstance(m, list) else [m]) for t, m in models.items()}


def drift_report(Session: Any, models: dict[str, Any]) -> dict[str, Any]:
    """Split every mapped model into: drifting, absent, or clean.

    The three outcomes are kept apart on purpose.  A mapped table with no
    physical table at all is a deployment-completeness problem; a physical table
    missing some of the columns the ORM writes is a runtime-failure problem; and
    conflating them would let the larger number hide the sharper one.
    """
    present = physical_tables(Session)
    by_table = mapped_classes_by_table(models)
    drift: dict[str, set[str]] = {}
    absent: list[str] = []
    for table, classes in by_table.items():
        if table not in present:
            absent.append(table)
            continue
        physical = physical_columns(Session, table)
        # A table counts as drifting when *any* of its owners declares a column
        # the database lacks.  Taking only the first owner would let a table with
        # two disagreeing owners read as clean depending on import order, which
        # is the failure mode rather than a detail of it.
        missing: set[str] = set()
        for cls in classes:
            missing |= orm_columns(cls) - physical
        if missing:
            drift[table] = missing
    return {
        "drift": drift,
        "absent": sorted(absent),
        "multi_owned": {t: [f"{c.__module__}.{c.__name__}" for c in cs] for t, cs in by_table.items() if len(cs) > 1},
        "clean": len(present & set(by_table)) - len(drift),
    }


# ---------------------------------------------------------------------------
# Actors and clients
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Actor:
    """A seeded authenticated caller.

    ``role`` decides authorization outcomes, so it is explicit at every call
    site rather than defaulted — a test that silently used the most privileged
    role would prove nothing about the authorization boundary.
    """

    user_id: int
    lab_id: int
    role: str


def client(Session: Any, actor: Actor | None) -> TestClient:
    """A TestClient against the real app, authenticated as ``actor``.

    ``actor=None`` leaves the real authentication dependency in place, which is
    how an unauthenticated rejection is proven rather than assumed.
    """
    from app.database import get_db
    from app.main import app
    from app.security.dependencies import get_current_user

    def db_override() -> Iterator[Any]:
        session = Session()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = db_override
    if actor is None:
        app.dependency_overrides.pop(get_current_user, None)
    else:
        app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
            id=actor.user_id,
            lab_id=actor.lab_id,
            role=actor.role,
            perm_version=1,
            is_active=True,
            is_verified=True,
        )
    return TestClient(app, raise_server_exceptions=False)


def clear_overrides() -> None:
    from app.main import app

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Evidence readers.  Raw SQL on purpose: the claim is about committed rows.
# ---------------------------------------------------------------------------


def receipts(Session: Any, *, lab_id: int, operation: str, key: str) -> list[dict[str, Any]]:
    """Durable idempotency claims for one operation and key, newest last."""
    sql = text(
        "SELECT id, actor_user_id, status, request_fingerprint, resource_id, completed_at "
        "FROM clinical_command_receipts "
        "WHERE lab_id = :lab_id AND operation = :operation AND idempotency_key = :key "
        "ORDER BY created_at, id"
    )
    with Session() as session:
        rows = session.execute(sql, {"lab_id": lab_id, "operation": operation, "key": key}).mappings()
        return [dict(r) for r in rows]


def audit_rows(Session: Any, *, lab_id: int, action: str) -> list[dict[str, Any]]:
    """Audit-log rows for one action, newest last."""
    sql = text(
        "SELECT id, user_id, user_role, action, resource_type, resource_id, details, chain_hash "
        "FROM audit_logs WHERE lab_id = :lab_id AND action = :action ORDER BY id"
    )
    with Session() as session:
        rows = session.execute(sql, {"lab_id": lab_id, "action": action}).mappings()
        return [dict(r) for r in rows]


def committed(Session: Any, sql: str, **params: Any) -> list[dict[str, Any]]:
    """Run a read in its own session so the answer is committed state only."""
    with Session() as session:
        return [dict(r) for r in session.execute(text(sql), params).mappings()]


# ---------------------------------------------------------------------------
# Concurrency.  Two actors, one row, released together.
# ---------------------------------------------------------------------------


def race(first: Callable[[], Any], second: Callable[[], Any], *, timeout: float = 30.0) -> tuple[Any, Any]:
    """Run two callables released from a barrier, each on its own thread.

    Each callable must build and use its own session and connection; sharing one
    would serialise the two actors inside SQLAlchemy and produce a sequential
    test wearing a concurrency test's clothes.  The barrier makes both threads
    arrive at the contended row together, so whichever ordering PostgreSQL picks
    is a real ordering rather than one the test chose.
    """
    barrier = threading.Barrier(2, timeout=timeout)
    results: dict[int, Any] = {}
    errors: dict[int, BaseException] = {}

    def run(index: int, fn: Callable[[], Any]) -> None:
        try:
            barrier.wait()
            results[index] = fn()
        except BaseException as exc:
            errors[index] = exc

    threads = [threading.Thread(target=run, args=(i, fn)) for i, fn in enumerate((first, second))]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=timeout)
        if t.is_alive():
            raise AssertionError("a racing actor did not finish; the contended row may be deadlocked")
    if errors:
        raise errors[min(errors)]
    return results[0], results[1]
