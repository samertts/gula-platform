"""Registration policy and tenant-scoped staff-account tests."""
from __future__ import annotations

import os

os.environ.setdefault("ENV", "test")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production-" + "x" * 32)
os.environ.setdefault("ENCRYPTION_KEY", "6TJUTgJxBREYK9_yDy6VMXBw1HPwwxv1kiynV0WaAdA=")
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
    from app.services.mpi.models import Citizen, IdentityClaim

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
    session = Session()
    try:
        yield session
    finally:
        session.close()


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
        with TestClient(app, raise_server_exceptions=False) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


def _admin_token(user_id: int, lab_id: int) -> dict[str, str]:
    token = create_token(
        {"user_id": user_id, "lab_id": lab_id, "role": "admin", "account_kind": "lab"}
    )
    return {"Authorization": f"Bearer {token}"}


class TestPublicRegistrationDisabled:
    _LAB = {
        "lab_name": "Mesopotamia Medical Lab",
        "admin_name": "Ahmed Hassan",
        "email": "ahmed@meso.lab",
        "password": "SecurePassword123!",
        "city": "Baghdad",
        "lab_type": "private",
    }
    _CITIZEN = {
        "full_name": "Sara Hassan",
        "phone": "+9647701234567",
        "email": "sara@example.iq",
        "password": "SecurePassword123!",
    }
    _DOCTOR = {
        "full_name": "Dr. Omar Khalid",
        "email": "omar@clinic.iq",
        "phone": "+9647701234568",
        "password": "DoctorPassword123!",
        "license_number": "IQ-MED-2024-001",
        "specialty": "Internal Medicine",
    }

    @pytest.mark.parametrize(
        ("path", "payload"),
        [
            ("/register", _LAB),
            ("/register/citizen", _CITIZEN),
            ("/register/doctor", _DOCTOR),
        ],
    )
    def test_public_registration_is_account_request_only(self, client, db, path, payload):
        response = client.post(path, json=payload)
        assert response.status_code == 410
        body = response.json()
        assert body["detail"] == "Request failed."
        assert db.query(Lab).count() == 0
        assert db.query(LabUser).count() == 0

    def test_configuration_cannot_reenable_public_registration(self, client, monkeypatch):
        import app.routes.register as register_routes

        monkeypatch.setattr(register_routes, "PUBLIC_SELF_REGISTRATION_ENABLED", True, raising=False)
        response = client.post("/register/citizen", json=self._CITIZEN)
        assert response.status_code == 410


class TestStaffRegistration:
    _STAFF = {
        "name": "Fatima Zahra",
        "email": "fatima@lab.com",
        "password": "StaffPassword123!",
        "role": "technician",
    }

    def _setup_active_lab(self, db):
        lab = Lab(name="Active Lab", is_active=True)
        db.add(lab)
        db.flush()
        admin = LabUser(
            lab_id=lab.id,
            name="Admin",
            email="admin@lab.com",
            password_hash=hash_password("AdminPassword123!"),
            role="admin",
            is_active=True,
        )
        db.add(admin)
        db.flush()
        db.commit()
        return lab, admin

    def test_admin_can_add_staff_to_own_lab(self, client, db):
        lab, admin = self._setup_active_lab(db)
        response = client.post(
            "/register/staff",
            json=self._STAFF,
            headers=_admin_token(admin.id, lab.id),
        )
        assert response.status_code == 201
        body = response.json()
        assert body["lab_id"] == lab.id
        staff = db.query(LabUser).filter(LabUser.email == self._STAFF["email"]).one()
        assert staff.lab_id == lab.id

    def test_non_admin_cannot_add_staff(self, client, db):
        lab, _ = self._setup_active_lab(db)
        technician = LabUser(
            lab_id=lab.id,
            name="Tech",
            email="tech@lab.com",
            password_hash=hash_password("TechPassword123!"),
            role="technician",
            is_active=True,
        )
        db.add(technician)
        db.commit()
        token = create_token(
            {
                "user_id": technician.id,
                "lab_id": lab.id,
                "role": "technician",
                "account_kind": "lab",
            }
        )
        response = client.post(
            "/register/staff",
            json={**self._STAFF, "email": "new@lab.com"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403

    def test_duplicate_staff_email_returns_409(self, client, db):
        lab, admin = self._setup_active_lab(db)
        headers = _admin_token(admin.id, lab.id)
        assert client.post("/register/staff", json=self._STAFF, headers=headers).status_code == 201
        response = client.post("/register/staff", json=self._STAFF, headers=headers)
        assert response.status_code == 409

    def test_invalid_role_returns_422(self, client, db):
        lab, admin = self._setup_active_lab(db)
        response = client.post(
            "/register/staff",
            json={**self._STAFF, "role": "dictator"},
            headers=_admin_token(admin.id, lab.id),
        )
        assert response.status_code == 422

    def test_unauthenticated_request_returns_401_or_403(self, client):
        response = client.post("/register/staff", json=self._STAFF)
        assert response.status_code in (401, 403)
