"""NIAM-only async database boundary.

Every NIAM async route/service in ``app/identity/`` is written against
``sqlalchemy.ext.asyncio.AsyncSession`` (``await session.execute(...)``,
``await session.flush()``), but the shared ``Depends(get_db)`` dependency
(``app/database.py``) actually yields a plain synchronous
``sqlalchemy.orm.Session`` from a sync ``create_engine`` -- ``await``-ing
its ``execute()`` result raises
``TypeError: object ChunkedIteratorResult can't be used in 'await' expression``
before authentication ever completes (see docs/qa/NIAM_LIVE_PATH_PROOF.md).

This module is the smallest fix for that mismatch: a second, NIAM-scoped
async engine/session bound to the SAME ``DATABASE_URL``/database as the
existing sync engine (just a different driver -- ``psycopg`` v3, already
an installed dependency per ``requirements.txt``, used in its async mode).
It does not touch ``app/database.py``'s ``get_db()`` or its semantics, and
does not change any non-NIAM route. Only the specific NIAM routes/services
proven (Phase 10.6) to need a real async session are switched to
``get_niam_db`` -- see the two call sites in ``federation/routes.py`` and
``trust/routes.py``, plus the shared ``get_current_niam_actor`` dependency
in ``api/workspaces.py``. Every other NIAM route keeps ``Depends(get_db)``
unchanged.

A second connection pool is unavoidable here: the sync and async engines
use different DBAPI drivers (psycopg2 vs. psycopg3-async) and cannot share
one. Kept deliberately small since only a few routes use it today --
recheck CLAUDE.md's pool-budget formula if these defaults are ever raised.
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import DATABASE_URL

_NIAM_POOL_SIZE = max(1, int(os.getenv("NIAM_ASYNC_DB_POOL_SIZE", "2")))
_NIAM_MAX_OVERFLOW = max(0, int(os.getenv("NIAM_ASYNC_DB_MAX_OVERFLOW", "3")))
_NIAM_POOL_TIMEOUT = int(os.getenv("NIAM_ASYNC_DB_POOL_TIMEOUT", "10"))
_NIAM_POOL_RECYCLE = int(os.getenv("NIAM_ASYNC_DB_POOL_RECYCLE", "1800"))

_niam_async_engine = None
_niam_async_session_factory: async_sessionmaker[AsyncSession] | None = None


def _niam_async_url() -> str:
    """Derives the async-driver URL from the existing sync DATABASE_URL.

    Fails closed (raises) rather than silently falling back to a sync
    session or a different database -- a non-PostgreSQL DATABASE_URL means
    this boundary's precondition (a real async-capable driver for the
    actual production database) does not hold, and that must surface as an
    error, not a silent downgrade.
    """
    if DATABASE_URL.startswith("postgresql+psycopg://"):
        return DATABASE_URL
    if DATABASE_URL.startswith("postgresql+psycopg2://"):
        return "postgresql+psycopg://" + DATABASE_URL.split("://", 1)[1]
    if DATABASE_URL.startswith("postgresql://"):
        return "postgresql+psycopg://" + DATABASE_URL.split("://", 1)[1]
    raise RuntimeError(
        "NIAM async DB boundary requires a PostgreSQL DATABASE_URL "
        "(postgresql:// or postgresql+psycopg://); "
        f"got an incompatible scheme in {DATABASE_URL.split('://', 1)[0]!r}."
    )


def _niam_session_factory() -> async_sessionmaker[AsyncSession]:
    """Lazily builds the NIAM async engine on first real use.

    Lazy on purpose: constructing this at import time would run
    ``create_async_engine`` against whatever ``DATABASE_URL`` happens to be
    set during module import (e.g. the test suite's forced
    ``sqlite:///:memory:``), which has no async driver installed here and
    would break app import/collection for every test, not just NIAM's.
    Tests never reach this function for real -- ``tests/conftest.py``
    overrides ``get_niam_db`` exactly as it already overrides ``get_db``.
    """
    global _niam_async_engine, _niam_async_session_factory
    if _niam_async_session_factory is None:
        url = _niam_async_url()
        _niam_async_engine = create_async_engine(
            url,
            pool_pre_ping=True,
            pool_size=_NIAM_POOL_SIZE,
            max_overflow=_NIAM_MAX_OVERFLOW,
            pool_timeout=_NIAM_POOL_TIMEOUT,
            pool_recycle=_NIAM_POOL_RECYCLE,
            connect_args={"connect_timeout": 5},
        )
        _niam_async_session_factory = async_sessionmaker(
            bind=_niam_async_engine,
            autoflush=False,
            expire_on_commit=False,
        )
    return _niam_async_session_factory


async def get_niam_db():
    """NIAM's async counterpart to ``app.database.get_db``.

    Same lifecycle contract as the sync dependency it mirrors: one session
    per request, rollback on exception, always closed -- no commit is
    issued here on the success path either, matching ``get_db()``'s exact
    (non-committing) transaction semantics rather than silently changing
    them.
    """
    session = _niam_session_factory()()
    try:
        yield session
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


@asynccontextmanager
async def open_niam_session():
    """Same session/rollback/close contract as ``get_niam_db``, for
    non-request callers that have no FastAPI dependency injection to rely
    on (e.g. a startup-time seeding step). No route uses this -- it exists
    only for process-lifecycle code that needs a real NIAM async session
    before or outside any HTTP request.
    """
    session = _niam_session_factory()()
    try:
        yield session
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()
