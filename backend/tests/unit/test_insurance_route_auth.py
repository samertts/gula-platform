"""Insurance route authorization + audit regression tests (S2).

Covers GET /insurance/{insurance_id}:
  - Unauthenticated → 401
  - Authenticated but no patients:read (e.g. technician) → 403
  - patients:read holder (e.g. receptionist/doctor/master_admin) → 200
  - Every lookup is recorded in the immutable audit trail with actor + IP
"""

from __future__ import annotations

import os

os.environ.setdefault("ENV", "test")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production-" + "x" * 32)
os.environ.setdefault("ENCRYPTION_KEY", "6TJUTgJxBREYK9_yDy6VMXBw1HPwwxv1kiynV0WaAdw=")
os.environ.setdefault("NID_HMAC_KEY", "a" * 64)
os.environ.setdefault("REDIS_URL", "")
os.environ.setdefault("GULA_ADAPTER_MODE_INSURANCE", "stub")

import pytest
from app.database import Base, get_db
from app.models.audit_log import AuditLog
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


class TestInsuranceAuth:
    def test_unauthenticated_rejected(self, client):
        res = client.get("/insurance/ABC123")
        assert res.status_code == 401

    def test_technician_without_patients_read_rejected(self, client, db):
        lab = _create_lab(db)
        user = _create_user(db, lab.id, role="technician")
        db.commit()
        res = client.get("/insurance/ABC123", headers=_token(user.id, lab.id, "technician"))
        assert res.status_code == 403

    def test_receptionist_with_patients_read_allowed(self, client, db):
        lab = _create_lab(db)
        user = _create_user(db, lab.id, role="receptionist")
        db.commit()
        res = client.get("/insurance/ABC123", headers=_token(user.id, lab.id, "receptionist"))
        assert res.status_code == 200

    def test_doctor_allowed(self, client, db):
        lab = _create_lab(db)
        user = _create_user(db, lab.id, role="doctor")
        db.commit()
        res = client.get("/insurance/ABC123", headers=_token(user.id, lab.id, "doctor"))
        assert res.status_code == 200

    def test_invalid_insurance_id_400(self, client, db):
        lab = _create_lab(db)
        user = _create_user(db, lab.id, role="receptionist")
        db.commit()
        res = client.get(
            "/insurance/" + "X" * 51, headers=_token(user.id, lab.id, "receptionist")
        )
        assert res.status_code == 400

    def test_lookup_recorded_in_audit(self, client, db):
        lab = _create_lab(db)
        user = _create_user(db, lab.id, role="receptionist")
        db.commit()
        client.get("/insurance/ABC123", headers=_token(user.id, lab.id, "receptionist"))
        entry = (
            db.query(AuditLog)
            .filter(AuditLog.action == "insurance_lookup")
            .order_by(AuditLog.id.desc())
            .first()
        )
        assert entry is not None
        assert entry.user_id == user.id
        assert entry.resource_type == "insurance"
        assert "ABC123" in (entry.details or "")
