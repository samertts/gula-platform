"""Async SQLAlchemy runtime for canonical NIAM routes.

The legacy application continues to use ``app.database.get_db``.  NIAM auth,
session, and workspace routes use this module so their async transaction
lifecycle is explicit and cannot silently receive a synchronous Session.
"""
from __future__ import annotations

import logging
import os
from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from .config import DATABASE_URL

logger = logging.getLogger("gula.database.async")


def _async_database_url(url: str) -> str:
    if url.startswith("sqlite:///"):
        return url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
    if url.startswith("postgresql+psycopg2://"):
        return url.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    raise RuntimeError("Unsupported DATABASE_URL for canonical async NIAM runtime")


ASYNC_DATABASE_URL = os.getenv("ASYNC_DATABASE_URL") or _async_database_url(DATABASE_URL)

_engine_kwargs: dict[str, object] = {
    "pool_pre_ping": True,
    "echo": False,
}
if ASYNC_DATABASE_URL.startswith("sqlite+"):
    _engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    _engine_kwargs.update(
        {
            "pool_size": max(2, int(os.getenv("DB_POOL_SIZE", "5"))),
            "max_overflow": max(0, int(os.getenv("DB_MAX_OVERFLOW", "10"))),
            "pool_timeout": int(os.getenv("DB_POOL_TIMEOUT", "10")),
            "pool_recycle": int(os.getenv("DB_POOL_RECYCLE", "1800")),
        },
    )

async_engine: AsyncEngine = create_async_engine(ASYNC_DATABASE_URL, **_engine_kwargs)
AsyncSessionLocal = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False, autoflush=False)


async def get_async_db() -> AsyncIterator[AsyncSession]:
    """Yield a NIAM session and commit only after a successful request.

    Route-level exceptions roll back automatically.  This keeps activity
    timestamps, session revocations, and workspace context changes durable while
    preserving the legacy sync database dependency for older routes.
    """
    async with AsyncSessionLocal() as db:
        try:
            yield db
        except Exception:
            await db.rollback()
            raise
        else:
            await db.commit()


async def dispose_async_engine() -> None:
    """Close the canonical async pool during controlled application shutdown."""
    await async_engine.dispose()
