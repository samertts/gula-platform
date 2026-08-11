"""AI admin route authorization regression tests (S1).

Covers /api/ai/operations and /api/ai/providers:
  - Unauthenticated → 401 (was open — provider inventory / Ollama probe leak)
  - Non-admin (hospital_admin) → 403
  - Authorized (master_admin, system:admin) → 200
  - Provider response carries only the declared contract fields (no base_url,
    no available_models, no cost) — S1 leak minimization
"""

from __future__ import annotations

import os

os.environ.setdefault("ENV", "test")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production-" + "x" * 32)
os.environ.setdefault("ENCRYPTION_KEY", "6TJUTgJxBREYK9_yDy6VMXBw1HPwwxv1kiynV0WaAdw=")
os.environ.setdefault("NID_HMAC_KEY", "a" * 64)
os.environ.setdefault("REDIS_URL", "")

import pytest
from app.database import Base, get_db
from app.models.lab import Lab
from app.models.lab_user import LabUser
from app.security.auth import create_token, hash_password
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


@pytest.fixture(scope="function")
def db_engine():
    import app.models.audit_log
    import app.models.claim
    import app.models.consent
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

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture()
def db(db_engine):
    Session = sessionmaker(bind=db_engine, autoflush=False)
    s = Session()
    try:
        yield s
    finally:
        s.close()


@pytest.fixture()
def client(db):
    from app.main import app

    def _override():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = _override
    try:
        with TestClient(app, raise_server_exceptions=False) as c:
            yield c
    finally:
        app.dependency_overrides.clear()


def _create_lab(db, name: str = "Test Lab", active: bool = True) -> Lab:
    lab = Lab(name=name, is_active=active)
    db.add(lab)
    db.flush()
    return lab


def _create_user(
    db, lab_id: int, role: str = "admin", email: str | None = None, active: bool = True
) -> LabUser:
    import uuid

    em = email or f"user-{uuid.uuid4().hex[:8]}@lab.com"
    user = LabUser(
        lab_id=lab_id,
        name="Test User",
        email=em,
        password_hash=hash_password("Test1234"),
        role=role,
        is_active=active,
    )
    db.add(user)
    db.flush()
    return user


def _token(user_id: int, lab_id: int, role: str = "admin") -> dict:
    token = create_token({"user_id": user_id, "lab_id": lab_id, "role": role})
    return {"Authorization": f"Bearer {token}"}


class TestAIOperationsAuth:
    def test_unauthenticated_rejected(self, client):
        res = client.get("/api/ai/operations")
        assert res.status_code == 401

    def test_user_without_permission_rejected(self, client, db):
        lab = _create_lab(db)
        user = _create_user(db, lab.id, role="hospital_admin")
        db.commit()
        res = client.get("/api/ai/operations", headers=_token(user.id, lab.id, "hospital_admin"))
        assert res.status_code == 403

    def test_authorized_user_allowed(self, client, db):
        lab = _create_lab(db)
        user = _create_user(db, lab.id, role="master_admin")
        db.commit()
        res = client.get("/api/ai/operations", headers=_token(user.id, lab.id, "master_admin"))
        assert res.status_code == 200
        body = res.json()
        assert "whitelisted_operations" in body


class TestAIProvidersAuth:
    def test_unauthenticated_rejected(self, client):
        res = client.get("/api/ai/providers")
        assert res.status_code == 401

    def test_user_without_permission_rejected(self, client, db):
        lab = _create_lab(db)
        user = _create_user(db, lab.id, role="hospital_admin")
        db.commit()
        res = client.get("/api/ai/providers", headers=_token(user.id, lab.id, "hospital_admin"))
        assert res.status_code == 403

    def test_authorized_user_allowed(self, client, db):
        lab = _create_lab(db)
        user = _create_user(db, lab.id, role="master_admin")
        db.commit()
        res = client.get("/api/ai/providers", headers=_token(user.id, lab.id, "master_admin"))
        assert res.status_code == 200
        body = res.json()
        assert "providers" in body
        assert "active_provider" in body
        assert "fallback_chain" in body

    def test_provider_response_contains_no_internal_leaks(self, client, db):
        lab = _create_lab(db)
        user = _create_user(db, lab.id, role="master_admin")
        db.commit()
        body = client.get(
            "/api/ai/providers", headers=_token(user.id, lab.id, "master_admin")
        ).json()
        for provider in body["providers"]:
            assert "base_url" not in provider
            assert "available_models" not in provider
            assert "cost" not in provider
            assert "source" not in provider
            assert set(provider.keys()) <= {"name", "type", "configured", "reachable", "model"}
