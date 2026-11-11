"""Registration route integration tests.

Covers (POST /register — lab registration):
  - Happy path: valid data → 201 + pending_approval status
  - Duplicate email → 409
  - Short password → 400
  - Letters-only password → 400
  - Digits-only password → 400
  - Invalid email format → 422
  - Invalid lab_type → 422
  - Lab starts INACTIVE (requires admin approval)
  - Audit log entry created on successful registration

Covers (POST /register/staff — lab admin adds staff):
  - Happy path: admin adds technician → 201
  - Non-admin cannot add staff → 403
  - Duplicate email → 409
  - Invalid role → 422

Covers (POST /register/doctor — doctor self-registration):
  - Happy path → 201 + pending_verification
  - Duplicate email → 409
  - Duplicate license → 409
  - Missing license → 422
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
from app.models.audit_log import AuditLog
from app.models.lab import Lab
from app.models.lab_user import LabUser
from app.orm_topology import own_tables
from app.security.auth import create_token, hash_password
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def approved_onboarding_in_test(monkeypatch):
    """Exercise the pending-approval registration path without opening production."""
    import app.routes.register as register_routes

    monkeypatch.setattr(register_routes, "PUBLIC_SELF_REGISTRATION_ENABLED", True)


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
    Base.metadata.create_all(engine, tables=own_tables(Base))
    yield engine
    Base.metadata.drop_all(engine, tables=own_tables(Base))
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


def _admin_token(user_id: int, lab_id: int) -> dict:
    token = create_token({"user_id": user_id, "lab_id": lab_id, "role": "admin"})
    return {"Authorization": f"Bearer {token}"}


# ── POST /register (lab registration) ────────────────────────────────────────

class TestLabRegistration:
    _VALID = {
        "lab_name": "Mesopotamia Medical Lab",
        "admin_name": "Ahmed Hassan",
        "email": "ahmed@meso.lab",
        "password": "SecurePassword123!",
        "city": "Baghdad",
        "lab_type": "private",
    }

    def test_happy_path_returns_201(self, client):
        res = client.post("/register", json=self._VALID)
        assert res.status_code == 201

    def test_response_contains_lab_id_and_pending_status(self, client):
        res = client.post("/register", json=self._VALID)
        body = res.json()
        assert "lab_id" in body
        assert body["status"] == "pending_approval"

    def test_response_contains_arabic_message(self, client):
        res = client.post("/register", json=self._VALID)
        assert "message_ar" in res.json()

    def test_lab_created_as_inactive(self, client, db):
        client.post("/register", json=self._VALID)
        lab = db.query(Lab).filter(Lab.name == "Mesopotamia Medical Lab").first()
        assert lab is not None
        assert lab.is_active is False

    def test_admin_user_created_as_inactive(self, client, db):
        client.post("/register", json=self._VALID)
        user = db.query(LabUser).filter(LabUser.email == "ahmed@meso.lab").first()
        assert user is not None
        assert user.is_active is False

    def test_audit_log_entry_created(self, client, db):
        client.post("/register", json=self._VALID)
        log = db.query(AuditLog).filter(AuditLog.action == "register").first()
        assert log is not None

    def test_duplicate_email_returns_409(self, client):
        client.post("/register", json=self._VALID)
        res = client.post("/register", json={**self._VALID, "lab_name": "Other Lab"})
        assert res.status_code == 409

    def test_password_too_short_returns_400(self, client):
        res = client.post("/register", json={**self._VALID, "password": "Ab1"})
        assert res.status_code == 400

    def test_letters_only_password_returns_400(self, client):
        res = client.post("/register", json={**self._VALID, "password": "abcdefghij"})
        assert res.status_code == 400

    def test_digits_only_password_returns_400(self, client):
        res = client.post("/register", json={**self._VALID, "password": "12345678"})
        assert res.status_code == 400

    def test_invalid_email_returns_422(self, client):
        res = client.post("/register", json={**self._VALID, "email": "not-an-email"})
        assert res.status_code == 422

    def test_invalid_lab_type_returns_422(self, client):
        res = client.post("/register", json={**self._VALID, "lab_type": "space_station"})
        assert res.status_code == 422

    def test_lab_name_too_short_returns_422(self, client):
        res = client.post("/register", json={**self._VALID, "lab_name": "X"})
        assert res.status_code == 422

    def test_missing_required_fields_returns_422(self, client):
        res = client.post("/register", json={"lab_name": "Only Name"})
        assert res.status_code == 422

    def test_password_not_stored_in_plain_text(self, client, db):
        client.post("/register", json=self._VALID)
        user = db.query(LabUser).filter(LabUser.email == "ahmed@meso.lab").first()
        assert user.password_hash != "Secure123"
        assert len(user.password_hash) > 30


# ── POST /register/staff (staff addition by admin) ───────────────────────────

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
            lab_id=lab.id, name="Admin", email="admin@lab.com",
            password_hash=hash_password("AdminPassword123!"), role="admin", is_active=True,
        )
        db.add(admin)
        db.flush()
        db.commit()
        return lab, admin

    def test_admin_can_add_staff(self, client, db):
        lab, admin = self._setup_active_lab(db)
        res = client.post(
            "/register/staff",
            json=self._STAFF,
            headers=_admin_token(admin.id, lab.id),
        )
        assert res.status_code == 201

    def test_response_contains_user_id_and_role(self, client, db):
        lab, admin = self._setup_active_lab(db)
        res = client.post(
            "/register/staff",
            json=self._STAFF,
            headers=_admin_token(admin.id, lab.id),
        )
        body = res.json()
        assert "user_id" in body
        assert body["role"] == "technician"
        assert body["lab_id"] == lab.id

    def test_staff_assigned_to_same_lab_as_admin(self, client, db):
        lab, admin = self._setup_active_lab(db)
        client.post(
            "/register/staff",
            json=self._STAFF,
            headers=_admin_token(admin.id, lab.id),
        )
        staff = db.query(LabUser).filter(LabUser.email == "fatima@lab.com").first()
        assert staff is not None
        assert staff.lab_id == lab.id

    def test_non_admin_cannot_add_staff(self, client, db):
        lab, _ = self._setup_active_lab(db)
        tech = LabUser(
            lab_id=lab.id, name="Tech", email="tech@lab.com",
            password_hash=hash_password("TechPassword123!"), role="technician", is_active=True,
        )
        db.add(tech)
        db.flush()
        db.commit()
        token = create_token({"user_id": tech.id, "lab_id": lab.id, "role": "technician"})
        res = client.post(
            "/register/staff",
            json={**self._STAFF, "email": "new@lab.com"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 403

    def test_duplicate_staff_email_returns_409(self, client, db):
        lab, admin = self._setup_active_lab(db)
        headers = _admin_token(admin.id, lab.id)
        client.post("/register/staff", json=self._STAFF, headers=headers)
        res = client.post("/register/staff", json=self._STAFF, headers=headers)
        assert res.status_code == 409

    def test_invalid_role_returns_422(self, client, db):
        lab, admin = self._setup_active_lab(db)
        res = client.post(
            "/register/staff",
            json={**self._STAFF, "role": "dictator"},
            headers=_admin_token(admin.id, lab.id),
        )
        assert res.status_code == 422

    def test_unauthenticated_request_returns_401_or_403(self, client):
        res = client.post("/register/staff", json=self._STAFF)
        assert res.status_code in (401, 403)


# ── POST /register/doctor (doctor self-registration) ─────────────────────────

class TestDoctorRegistration:
    _DOCTOR = {
        "full_name": "Dr. Omar Khalid",
        "email": "omar@clinic.iq",
        "phone": "+9647701234567",
        "password": "DoctorPassword123!",
        "license_number": "IQ-MED-2024-001",
        "specialty": "Internal Medicine",
    }

    def test_happy_path_returns_201(self, client):
        res = client.post("/register/doctor", json=self._DOCTOR)
        assert res.status_code == 201

    def test_response_contains_pending_verification(self, client):
        res = client.post("/register/doctor", json=self._DOCTOR)
        body = res.json()
        assert body["status"] == "pending_verification"
        assert "user_id" in body

    def test_response_contains_arabic_message(self, client):
        res = client.post("/register/doctor", json=self._DOCTOR)
        assert "message_ar" in res.json()

    def test_duplicate_email_returns_409(self, client):
        client.post("/register/doctor", json=self._DOCTOR)
        res = client.post(
            "/register/doctor",
            json={**self._DOCTOR, "phone": "+9647709999999", "license_number": "IQ-MED-2024-002"},
        )
        assert res.status_code == 409

    def test_duplicate_license_returns_409(self, client):
        client.post("/register/doctor", json=self._DOCTOR)
        res = client.post(
            "/register/doctor",
            json={**self._DOCTOR, "email": "other@clinic.iq", "phone": "+9647708888888"},
        )
        assert res.status_code == 409

    def test_missing_license_number_returns_422(self, client):
        data = {k: v for k, v in self._DOCTOR.items() if k != "license_number"}
        res = client.post("/register/doctor", json=data)
        assert res.status_code == 422

    def test_invalid_phone_returns_422(self, client):
        res = client.post("/register/doctor", json={**self._DOCTOR, "phone": "not-a-phone"})
        assert res.status_code == 422

    def test_short_password_returns_400(self, client):
        res = client.post("/register/doctor", json={**self._DOCTOR, "password": "Ab1"})
        assert res.status_code == 400

    def test_password_not_stored_in_plain_text(self, client, db):
        from app.models.user import User
        client.post("/register/doctor", json=self._DOCTOR)
        doctor = db.query(User).filter(User.email == "omar@clinic.iq").first()
        assert doctor is not None
        assert doctor.password_hash != "Doctor123"
