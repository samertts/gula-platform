"""Shared pytest fixtures for the GULA Platform test suite.

Sets up an in-memory SQLite database, a FastAPI TestClient with the DB
dependency overridden, and lightweight factories for common models.
All fixtures are function-scoped so each test starts with a clean slate.

The backend/ package is installed via `pip install -e backend/` (or through
the backend/pyproject.toml). No sys.path manipulation is needed.
"""
from __future__ import annotations

import os
import tempfile

# ── Must come before any app import ──────────────────────────────────────────
# Runtime isolation: tests run in a process that must NEVER spawn background
# tasks, must NEVER trigger maintenance loops, and must NEVER touch edge_*
# tables. These two env vars are read by app.config at import time and force
# the strict isolation profile.
os.environ["RUNTIME_MODE"] = "test"
os.environ["FEATURE_BACKGROUND_TASKS"] = "false"

os.environ.setdefault("ENV", "test")
# A developer shell or CI service may already expose a production-like URL.
# Tests intentionally use SQLite and must not import that external dialect while
# collecting fixtures, otherwise a MySQL/PostgreSQL driver can be required before
# the test isolation setup has even started.
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production-" + "x" * 32)
os.environ.setdefault("ENCRYPTION_KEY", "6TJUTgJxBREYK9_yDy6VMXBw1HPwwxv1kiynV0WaAdw=")
os.environ.setdefault("NID_HMAC_KEY", "a" * 64)
os.environ.setdefault("REDIS_URL", "")

import contextlib
import pathlib
import sys

# Ensure the repo root is on sys.path so that `shared` package is importable.
_repo_root = pathlib.Path(__file__).resolve().parent.parent.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

import pytest
from app.database import Base, get_db
from app.security.auth import create_token, hash_password
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# ── SQLite compatibility: JSONB → JSON ────────────────────────────────────────
# Several production models use PostgreSQL's JSONB type. SQLite does not support
# it, so we register a type compiler that renders JSONB as JSON (which SQLite
# stores as TEXT). This must be set up before any models are imported.
from sqlalchemy.types import JSON as _SQLiteJSON
from sqlalchemy.types import TypeDecorator


class _JSONB_as_JSON(TypeDecorator):
    """JSONB stored as JSON for SQLite."""
    impl = _SQLiteJSON
    cache_ok = True


from sqlalchemy import BigInteger
from sqlalchemy.ext.compiler import compiles


@compiles(JSONB, "sqlite")
def _compile_jsonb_sqlite(element, compiler, **kw):
    return compiler.visit_JSON(element, **kw)


@compiles(BigInteger, "sqlite")
def _compile_bigint_sqlite(element, compiler, **kw):
    return "INTEGER"


# ── Module-level model imports ─────────────────────────────────────────────
# These must be here (not inside a fixture) so that SQLAlchemy relationship
# resolution works even in tests that never request a DB fixture.  In
# particular CitizenLink.citizen = relationship("Citizen") requires class
# "Citizen" be registered on Base *before* any mapper configuration fires.
from app.services.mpi.models import Citizen, IdentityClaim

# ── Session-scoped engine & DDL (once per test run) ───────────────────────────
# Creating hundreds of tables on every test function is too slow (~80s per test).
# We use a session-scoped SQLite temp file and a per-test savepoint-based
# rollback to achieve both isolation and speed.

@pytest.fixture(scope="session")
def _session_engine():
    """Create engine + all tables once per test session."""
    _f = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    _db_path = _f.name
    _f.close()
    engine = create_engine(f"sqlite:///{_db_path}", connect_args={"check_same_thread": False})
    # Import ALL models via app.main — registers Base + NationalBase + all
    # other domain models on their respective metadata namespaces.  This
    # must happen BEFORE table creation so the combined DDL metadata can
    # resolve cross-metadata FK references (nursing→lab_users, EHR→national,
    # etc.).  Without this, ForeignKey("lab_users.id") in a NationalBase
    # table fails because lab_users lives in Base.metadata.
    import app.main
    from app.care_continuum.base import CareContinuumBase
    from app.citizen_platform.base import CitizenPlatformBase
    from app.clinical.base import ClinicalBase
    from app.ehr.base import EHRBase
    from app.financial.models import FinBase
    from app.governance.base import GovernanceBase
    from app.health_data.base import HealthDataBase
    from app.hospital.base import HospitalBase
    from app.national.base import NationalBase
    from app.national_data.base import DataPlatformBase
    from app.nhdw.base import NHDWBase
    from app.nursing.base import NursingBase
    from app.pharmacy.base import PharmacyBase
    from app.radiology.base import RadiologyBase
    from app.trust.base import TrustBase
    from sqlalchemy import MetaData as _CombinedMeta

    _all_metas = [
        Base.metadata, NationalBase.metadata, EHRBase.metadata,
        CareContinuumBase.metadata, CitizenPlatformBase.metadata,
        ClinicalBase.metadata, GovernanceBase.metadata,
        HealthDataBase.metadata, HospitalBase.metadata,
        DataPlatformBase.metadata, NHDWBase.metadata,
        NursingBase.metadata, PharmacyBase.metadata,
        RadiologyBase.metadata, TrustBase.metadata, FinBase.metadata,
    ]
    _ddl_meta = _CombinedMeta()
    for _meta in _all_metas:
        for _tname, _tbl in list(_meta.tables.items()):
            if _tname not in _ddl_meta.tables:
                _tbl.to_metadata(_ddl_meta)

    # Deduplicate indexes (column index=True + same Index in __table_args__)
    for _tbl in list(_ddl_meta.tables.values()):
        _seen_idx = {}
        for _idx in list(_tbl.indexes):
            if _idx.name in _seen_idx:
                _tbl.indexes.discard(_idx)
            else:
                _seen_idx[_idx.name] = _idx

    _ddl_meta.create_all(engine)
    yield engine
    _ddl_meta.drop_all(engine)
    engine.dispose()
    os.unlink(_db_path)


@pytest.fixture()
def _savepoint_conn(_session_engine):
    """Per-test connection with a savepoint that rolls back on teardown."""
    conn = _session_engine.connect()
    conn.begin()
    try:
        yield conn
    finally:
        conn.rollback()
        conn.close()


@pytest.fixture()
def db_engine(_savepoint_conn):
    """Expose the session-scoped engine (savepoint ensures isolation)."""
    return _savepoint_conn.engine


@pytest.fixture()
def db(db_engine, _savepoint_conn):
    """Per-test session that rolls back when the test finishes."""
    Session = sessionmaker(bind=_savepoint_conn)
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
    # run_startup_guard() detects RUNTIME_MODE=test and sets system_ready=True
    # immediately, so ReadinessMiddleware allows all requests through the
    # TestClient lifespan. No manual system_ready manipulation needed.
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

def auth_headers(user_id: int, lab_id: int | None, role: str = "admin") -> dict:
    """Generate a valid Bearer token header for a given user."""
    account_kind = "user" if role == "citizen" or lab_id is None else "lab"
    token = create_token({"user_id": user_id, "lab_id": lab_id, "role": role, "account_kind": account_kind})
    return {"Authorization": f"Bearer {token}"}
