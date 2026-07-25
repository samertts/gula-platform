"""Runtime isolation tests.

Verify that the test runtime stays clean:
  * No maintenance loops (asyncio tasks) start during a test.
  * No additional threads are spawned beyond the pytest baseline.
  * Edge tables (``edge_*``) cannot be queried from a non-worker process.
  * The runtime config flags resolve to the strict-isolation profile.
"""

from __future__ import annotations

import asyncio
import threading

import app.config as gula_config
import pytest
from app.core.runtime_guard import (
    RuntimeIsolationError,
    assert_worker_runtime,
    is_edge_table,
)

# ── 1. Config flags resolve to test/strict profile ───────────────────────────


def test_runtime_mode_is_test():
    assert gula_config.RUNTIME_MODE == "test"
    assert gula_config.IS_TEST_RUNTIME is True
    assert gula_config.IS_WORKER_RUNTIME is False
    assert gula_config.IS_API_RUNTIME is False


def test_background_tasks_force_disabled_in_tests():
    assert gula_config.FEATURE_BACKGROUND_TASKS is False
    assert gula_config.background_tasks_enabled() is False


# ── 2. Edge table predicate + guard ──────────────────────────────────────────


@pytest.mark.parametrize(
    "name,expected",
    [
        ("edge_outbox", True),
        ("edge_signals", True),
        ("EDGE_REPLICA", True),
        ("lab_orders", False),
        ("patients", False),
        ("ledger_edge", False),  # only prefix counts
    ],
)
def test_is_edge_table(name, expected):
    assert is_edge_table(name) is expected


def test_assert_worker_runtime_blocks_api_tests():
    with pytest.raises(RuntimeIsolationError):
        assert_worker_runtime("attempted edge_* operation")


# ── 3. No background tasks spawn when the FastAPI app boots ──────────────────


def test_app_startup_does_not_launch_background_loops(client):
    """Boot the API via TestClient and verify zero loops were spawned."""
    from app.main import _bg_tasks

    # The TestClient context manager already triggered all startup events.
    response = client.get("/health/live")
    assert response.status_code == 200
    assert _bg_tasks == set(), (
        f"Test runtime spawned background tasks: {[t.get_name() for t in _bg_tasks]}"
    )


# ── 4. No new threads beyond the pytest baseline ─────────────────────────────


def test_no_unexpected_threads_after_startup(client):
    """The test process must not launch worker threads from app startup."""
    # Allowed: main thread, asyncio + pytest internals. We don't enumerate
    # the exact whitelist (it varies by python/pytest version) — instead we
    # assert no thread name matches the worker patterns we control.
    forbidden_substrings = (
        "outbox",
        "recovery",
        "auto_repair",
        "auto-repair",
        "health-alert",
        "adaptive-concurrency",
    )
    offenders = [
        t.name
        for t in threading.enumerate()
        if any(s in t.name.lower() for s in forbidden_substrings)
    ]
    assert offenders == [], f"Forbidden worker threads alive: {offenders}"


# ── 5. Edge access guard rejects raw SQL ─────────────────────────────────────


def test_edge_access_guard_blocks_raw_sql():
    """Any statement referencing edge_* must be rejected from the test runtime."""
    from app.core.runtime_guard import install_edge_access_guard
    from sqlalchemy import create_engine, text
    from sqlalchemy.pool import StaticPool

    # Use a private engine so that installing the guard here does not pollute
    # the shared db_engine fixture and cause RuntimeIsolationError during
    # Base.metadata.drop_all() in fixture teardown (PRAGMA table_info triggers
    # the guard on any edge_* table name).
    guard_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    install_edge_access_guard(guard_engine)

    with pytest.raises(RuntimeIsolationError), guard_engine.connect() as conn:
        conn.execute(text("SELECT 1 FROM edge_signals LIMIT 1"))

    guard_engine.dispose()


# ── 6. asyncio.all_tasks stays empty after request handling ──────────────────


def test_no_asyncio_tasks_after_request(client):
    """Confirm no leftover tasks from a request-response cycle."""
    response = client.get("/health")
    assert response.status_code == 200

    try:
        loop = asyncio.get_event_loop()
        leftover = [t for t in asyncio.all_tasks(loop) if not t.done()]
    except RuntimeError:
        leftover = []
    assert leftover == [], (
        f"Pending asyncio tasks after request: {[t.get_name() for t in leftover]}"
    )
