"""Unit tests for lab_service — direct service layer tests."""

from __future__ import annotations

import os

os.environ.setdefault("ENV", "test")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production-" + "x" * 32)
os.environ.setdefault("ENCRYPTION_KEY", "6TJUTgJxBREYK9_yDy6VMXBw1HPwwxv1kiynV0WaAdw=")
os.environ.setdefault("NID_HMAC_KEY", "a" * 64)
os.environ.setdefault("REDIS_URL", "")

import pytest
from app.database import Base
from app.domain.exceptions import ConflictError, ForbiddenError, NotFoundError, ValidationError
from app.models.lab import Lab
from app.models.lab_user import LabUser
from app.security.auth import hash_password
from app.services import lab_service
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


@pytest.fixture(scope="function")
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(bind=engine)
    session = TestSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def lab(db_session):
    lab = Lab(name="Test Lab", city="Baghdad", lab_type="private", is_active=True)
    db_session.add(lab)
    db_session.commit()
    db_session.refresh(lab)
    return lab


@pytest.fixture
def admin_user(lab, db_session):
    u = LabUser(
        lab_id=lab.id,
        name="Admin User",
        email="admin@test.com",
        password_hash=hash_password("password123"),
        role="admin",
        is_active=True,
    )
    db_session.add(u)
    db_session.commit()
    db_session.refresh(u)
    return u


@pytest.fixture
def staff_user(lab, db_session):
    u = LabUser(
        lab_id=lab.id,
        name="Staff User",
        email="staff@test.com",
        password_hash=hash_password("password123"),
        role="staff",
        is_active=True,
    )
    db_session.add(u)
    db_session.commit()
    db_session.refresh(u)
    return u


class TestGetLab:
    def test_get_existing_lab(self, db_session, lab, admin_user):
        result = lab_service.get_lab(db_session, lab.id)
        assert result["name"] == "Test Lab"
        assert result["city"] == "Baghdad"
        assert result["lab_type"] == "private"
        assert "id" in result

    def test_get_nonexistent_lab_raises_not_found(self, db_session, admin_user):
        with pytest.raises(NotFoundError):
            lab_service.get_lab(db_session, 99999)

    def test_get_lab_includes_all_fields(self, db_session, lab, admin_user):
        result = lab_service.get_lab(db_session, lab.id)
        expected_fields = {
            "id",
            "name",
            "city",
            "address",
            "phone",
            "lab_type",
            "license_number",
            "director_name",
            "website",
            "is_active",
            "created_at",
        }
        assert set(result.keys()) == expected_fields


class TestUpdateLab:
    def test_admin_can_update_lab_name(self, db_session, lab, admin_user):
        result = lab_service.update_lab(db_session, lab.id, {"name": "Updated Lab"}, admin_user)
        assert result["name"] == "Updated Lab"

    def test_non_admin_cannot_update_lab(self, db_session, lab, staff_user):
        with pytest.raises(ForbiddenError):
            lab_service.update_lab(db_session, lab.id, {"name": "Hacked"}, staff_user)

    def test_update_unknown_lab_raises_not_found(self, db_session, admin_user):
        with pytest.raises(NotFoundError):
            lab_service.update_lab(db_session, 99999, {"name": "Ghost"}, admin_user)

    def test_only_allowed_fields_updated(self, db_session, lab, admin_user):
        lab_service.update_lab(
            db_session,
            lab.id,
            {"name": "New Name", "city": "New City", "lab_type": "government"},
            admin_user,
        )
        result = lab_service.get_lab(db_session, lab.id)
        assert result["name"] == "New Name"
        assert result["city"] == "New City"
        assert result["lab_type"] == "government"


class TestListEmployees:
    def test_admin_can_list_employees(self, db_session, lab, admin_user, staff_user):
        result = lab_service.list_employees(db_session, lab.id, admin_user)
        assert len(result) >= 2

    def test_non_admin_cannot_list_employees(self, db_session, lab, staff_user):
        with pytest.raises(ForbiddenError):
            lab_service.list_employees(db_session, lab.id, staff_user)

    def test_returns_only_own_lab_employees(self, db_session, lab, admin_user, staff_user):
        other_lab = Lab(name="Other Lab", city="Basra", lab_type="private", is_active=True)
        db_session.add(other_lab)
        db_session.commit()
        other_user = LabUser(
            lab_id=other_lab.id,
            name="Other",
            email="other@test.com",
            password_hash=hash_password("pw"),
            role="staff",
            is_active=True,
        )
        db_session.add(other_user)
        db_session.commit()

        result = lab_service.list_employees(db_session, lab.id, admin_user)
        employee_ids = {e["id"] for e in result}
        assert admin_user.id in employee_ids
        assert staff_user.id in employee_ids
        assert other_user.id not in employee_ids


class TestCreateEmployee:
    def test_admin_can_create_employee(self, db_session, lab, admin_user):
        result = lab_service.create_employee(
            db_session, lab.id, "New Emp", "new@test.com", "password123", "staff", admin_user
        )
        assert result["id"] is not None

    def test_non_admin_cannot_create_employee(self, db_session, lab, staff_user):
        with pytest.raises(ForbiddenError):
            lab_service.create_employee(
                db_session, lab.id, "New", "new@test.com", "password123", "staff", staff_user
            )

    def test_duplicate_email_raises_conflict(self, db_session, lab, admin_user, staff_user):
        with pytest.raises(ConflictError):
            lab_service.create_employee(
                db_session, lab.id, "Dup", staff_user.email, "password123", "staff", admin_user
            )

    def test_short_password_raises_value_error(self, db_session, lab, admin_user):
        with pytest.raises(ValueError):
            lab_service.create_employee(
                db_session, lab.id, "New", "new@test.com", "123", "staff", admin_user
            )


class TestUpdateEmployee:
    def test_admin_can_deactivate_employee(self, db_session, lab, admin_user, staff_user):
        result = lab_service.update_employee(
            db_session, lab.id, staff_user.id, is_active=False, role=None, current_user=admin_user
        )
        assert "updated" in result["message"].lower()

    def test_cannot_deactivate_self(self, db_session, lab, admin_user):
        with pytest.raises(ValidationError):
            lab_service.update_employee(
                db_session,
                lab.id,
                admin_user.id,
                is_active=False,
                role=None,
                current_user=admin_user,
            )

    def test_nonexistent_employee_raises_not_found(self, db_session, lab, admin_user):
        with pytest.raises(NotFoundError):
            lab_service.update_employee(
                db_session, lab.id, 99999, is_active=False, role=None, current_user=admin_user
            )

    def test_non_admin_cannot_update_employee(self, db_session, lab, staff_user):
        with pytest.raises(ForbiddenError):
            lab_service.update_employee(
                db_session,
                lab.id,
                staff_user.id,
                is_active=False,
                role=None,
                current_user=staff_user,
            )


class TestAllowedConstants:
    def test_allowed_lab_types(self):
        assert "private" in lab_service.ALLOWED_LAB_TYPES
        assert "government" in lab_service.ALLOWED_LAB_TYPES
        assert "hospital" in lab_service.ALLOWED_LAB_TYPES
        assert "clinic" in lab_service.ALLOWED_LAB_TYPES
        assert len(lab_service.ALLOWED_LAB_TYPES) == 4

    def test_allowed_roles(self):
        assert "admin" in lab_service.ALLOWED_ROLES
        assert "staff" in lab_service.ALLOWED_ROLES
        assert "technician" in lab_service.ALLOWED_ROLES
        assert len(lab_service.ALLOWED_ROLES) == 3

    def test_master_admin_can_bypass_admin_check(self, db_session, lab, admin_user):
        admin_user.role = "master_admin"
        result = lab_service.list_employees(db_session, lab.id, admin_user)
        assert isinstance(result, list)
