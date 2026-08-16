"""Command 05 async database runtime contract tests."""

from __future__ import annotations

import pytest
from app.database_async import _async_database_url, get_async_db
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine


def test_async_database_url_translation_is_explicit():
    assert _async_database_url("sqlite:///tmp/gula.db") == "sqlite+aiosqlite:///tmp/gula.db"
    assert _async_database_url("postgresql://user:pass@db/gula") == "postgresql+asyncpg://user:pass@db/gula"
    assert _async_database_url("postgresql+psycopg2://user:pass@db/gula") == "postgresql+asyncpg://user:pass@db/gula"
    with pytest.raises(RuntimeError):
        _async_database_url("mysql://user:pass@db/gula")


@pytest.mark.asyncio
async def test_postgres_async_engine_can_be_constructed_without_network_io():
    engine = create_async_engine(_async_database_url("postgresql://user:pass@db/gula"))
    await engine.dispose()


@pytest.mark.asyncio
async def test_async_dependency_commits_after_successful_request():
    async for db in get_async_db():
        result = await db.execute(text("SELECT 1"))
        assert result.scalar_one() == 1


@pytest.mark.asyncio
async def test_async_dependency_rolls_back_on_request_exception():
    generator = get_async_db()
    db = await anext(generator)
    await db.execute(text("SELECT 1"))
    with pytest.raises(RuntimeError, match="request failed"):
        await generator.athrow(RuntimeError("request failed"))
