"""Shared pytest fixtures for the GULA Platform test suite.

Sets up an in-memory SQLite database, a FastAPI TestClient with the DB
dependency overridden, and lightweight factories for common models.
All fixtures are function-scoped so each test starts with a clean slate.
"""
from __future__ import annotations

import os
import sys

# ── Must come before any app import ──────────────────────────────────────────
os.environ.setdefault("ENV", "test")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production-" + "x" * 32)
os.environ.setdefault("ENCRYPTION_KEY", "6TJUTgJxBREYK9_yDy6VMXBw1HPwwxv1kiynV0WaAdw=")
os.environ.setdefault("NID_HMAC_KEY", "a" * 64)
os.environ.setdefault("REDIS_URL", "")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.database import Base, get_db
from app.security.auth import hash_password, create_token


# ── DB fixture ────────────────────────────────────────────────────────────────

@pytest.fixture()
def db_engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    # Import every model so Base.metadata knows about all tables
    import app.models.lab           # noqa: F401
    import app.models.lab_user      # noqa: F401
    import app.models.user          # noqa: F401
    import app.models.patient       # noqa: F401
    import app.models.lab_order     # noqa: F401
    import app.models.lab_result    # noqa: F401
    import app.models.audit_log     # noqa: F401
    import app.models.sample        # noqa: F401
    import app.models.quality_control  # noqa: F401
    import app.models.consent       # noqa: F401
    import app.models.outbox        # noqa: F401
    import app.models.subscription  # noqa: F401
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
def client(db):
    """TestClient with the real DB dependency replaced by the test DB session."""
    from app.main import app

    def _override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
    app.dependency_overrides.clear()


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
