"""Shared pytest fixtures for the GULA Platform test suite.

Sets up an in-memory SQLite database, a FastAPI TestClient with the DB
dependency overridden, and lightweight factories for common models.
All fixtures are function-scoped so each test starts with a clean slate.
"""
from __future__ import annotations

import os
import sys

# ── Must come before any app import ──────────────────────────────────────────
# Runtime isolation: tests run in a process that must NEVER spawn background
# tasks, must NEVER trigger maintenance loops, and must NEVER touch edge_*
# tables. These two env vars are read by app.config at import time and force
# the strict isolation profile.
os.environ["RUNTIME_MODE"] = "test"
os.environ["FEATURE_BACKGROUND_TASKS"] = "false"

os.environ.setdefault("ENV", "test")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production-" + "x" * 32)
os.environ.setdefault("ENCRYPTION_KEY", "6TJUTgJxBREYK9_yDy6VMXBw1HPwwxv1kiynV0WaAdw=")
os.environ.setdefault("NID_HMAC_KEY", "a" * 64)
os.environ.setdefault("REDIS_URL", "")

_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_REPO_ROOT = os.path.dirname(_BACKEND_DIR)
sys.path.insert(0, _BACKEND_DIR)
sys.path.insert(0, _REPO_ROOT)

import contextlib

import pytest
from app.database import Base, get_db
from app.security.auth import create_token, hash_password
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# ── DB fixture ────────────────────────────────────────────────────────────────

@pytest.fixture()
def db_engine():
    # StaticPool: all connections share the same in-memory database so that
    # create_all() and subsequent session checkouts see the same tables.
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    # Import every model so Base.metadata knows about all tables
    import app.models.audit_log
    import app.models.claim
    import app.models.consent
    import app.models.edge
    import app.models.lab
    import app.models.lab_order
    import app.models.lab_result
    import app.models.lab_user
    import app.models.outbox
    import app.models.patient
    import app.models.quality_control
    import app.models.sample
    import app.models.subscription
    import app.models.user
    from app.services.mpi.models import Citizen, IdentityClaim
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture()
def db(db_engine):
    Session = sessionmaker(bind=db_engine, autoflush=False)
    session = Session()
    try:
        yield session
    finally:
        session.close()


# ── FastAPI TestClient ────────────────────────────────────────────────────────

@pytest.fixture()
def client(db, db_engine, monkeypatch):
    """TestClient with the real DB dependency replaced by the test DB session.

    Three layers of override are needed because production code touches the
    database in three different ways:
      1. ``Depends(get_db)`` in route handlers           → dependency_overrides
      2. ``SessionLocal()`` called directly in services  → monkeypatched
      3. ``engine`` referenced by health/metrics paths   → monkeypatched
    Without all three, a test could silently hit the real (or CI) database
    even though `get_db` was overridden, breaking isolation.
    """
    import app.core.startup_guard as _guard
    import app.database as _database
    from app.kernel.integration import boot_kernel, init_kernel, stop_kernel
    from app.main import app
    from sqlalchemy.orm import sessionmaker

    def _override_get_db():
        try:
            yield db
        finally:
            pass

    test_session_factory = sessionmaker(bind=db_engine, autoflush=False)
    monkeypatch.setattr(_database, "SessionLocal", test_session_factory, raising=True)
    monkeypatch.setattr(_database, "engine", db_engine, raising=True)

    app.dependency_overrides[get_db] = _override_get_db
    # The backend-test CI job doesn't run `alembic upgrade head`, so
    # run_startup_guard() would fail (no alembic_version table) keeping
    # system_ready=False. ReadinessMiddleware then returns 503 for every request.
    # run_startup_guard() has `if system_ready: return` at the top, so setting
    # it True here causes startup validation to be skipped entirely in tests.
    _guard.system_ready = True
    import asyncio
    init_kernel()
    asyncio.run(boot_kernel())
    try:
        with TestClient(app, raise_server_exceptions=True) as c:
            yield c
    finally:
        _guard.system_ready = False
        app.dependency_overrides.clear()
        asyncio.run(stop_kernel())


# ── Test isolation: clear cross-test global state ────────────────────────────

@pytest.fixture(autouse=True)
def _reset_global_caches():
    """Clear cache state (rate limits, perm_version, JWT blacklist) between tests.

    SQLite in-memory DBs reset on every test, so user/lab IDs are re-used; if
    cache state from a prior test (e.g. perm_ver=2 for user_id=1) leaks into
    the next, unrelated tests fail with 401 ("Permissions updated"). Handles
    both the in-memory _MemoryStore (local dev) and the real Redis backend
    used in CI.
    """
    from app.security.redis_client import cache

    def _clear():
        if hasattr(cache, "_data"):
            cache._data.clear()
        client = getattr(cache, "_client", None)
        if client is not None:
            with contextlib.suppress(Exception):
                client.flushdb()

    _clear()
    yield
    _clear()


# ── Model factories ───────────────────────────────────────────────────────────

@pytest.fixture()
def make_lab(db):
    """Return a factory: make_lab(name="Acme Lab") → persisted Lab."""
    from app.models.lab import Lab

    _counter = [0]

    def _factory(name: str | None = None, is_active: bool = True, **kwargs):
        _counter[0] += 1
        lab = Lab(
            name=name or f"Test Lab {_counter[0]}",
            license_number=kwargs.get("license_number", f"LIC-{_counter[0]:04d}"),
            lab_type=kwargs.get("lab_type", "private"),
            city=kwargs.get("city", "Baghdad"),
            is_active=is_active,
        )
        db.add(lab)
        db.flush()
        return lab

    return _factory


@pytest.fixture()
def make_lab_user(db):
    """Return a factory: make_lab_user(lab_id=1, role='admin') → persisted LabUser."""
    from app.models.lab_user import LabUser

    _counter = [0]

    def _factory(lab_id: int, role: str = "admin", is_active: bool = True, **kwargs):
        _counter[0] += 1
        email = kwargs.get("email", f"user{_counter[0]}@test.com")
        user = LabUser(
            lab_id=lab_id,
            name=kwargs.get("name", f"Test User {_counter[0]}"),
            email=email,
            password_hash=hash_password(kwargs.get("password", "Testpass1")),
            role=role,
            is_active=is_active,
        )
        db.add(user)
        db.flush()
        return user

    return _factory


@pytest.fixture()
def make_subscription(db):
    """Return a factory: make_subscription(lab_id=1, tier='growth') → LabSubscription."""
    from app.models.subscription import LabSubscription

    def _factory(lab_id: int, tier: str = "starter",
                 deployment_mode: str = "single", security_level: str = "standard"):
        sub = LabSubscription(
            lab_id=lab_id,
            tier=tier,
            deployment_mode=deployment_mode,
            security_level=security_level,
            is_active=True,
        )
        db.add(sub)
        db.flush()
        return sub

    return _factory


# ── Auth helpers ──────────────────────────────────────────────────────────────

def auth_headers(user_id: int, lab_id: int, role: str = "admin") -> dict:
    """Generate a valid Bearer token header for a given user."""
    token = create_token({"user_id": user_id, "lab_id": lab_id, "role": role})
    return {"Authorization": f"Bearer {token}"}
