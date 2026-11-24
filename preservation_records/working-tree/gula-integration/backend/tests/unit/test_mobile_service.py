from __future__ import annotations

import os

os.environ.setdefault("ENV", "test")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production-" + "x" * 32)
os.environ.setdefault("ENCRYPTION_KEY", "6TJUTgJxBREYK9_yDy6VMXBw1HPwwxv1kiynV0WaAdw=")
os.environ.setdefault("NID_HMAC_KEY", "a" * 64)
os.environ.setdefault("REDIS_URL", "")

from datetime import datetime

import pytest
from app._compat import UTC
from app.database import Base
from app.models.lab import Lab
from app.models.lab_order import LabOrder
from app.models.lab_user import LabUser
from app.models.patient import Patient
from app.services import mobile_service
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
    lab = Lab(name="Mobile Lab", city="Baghdad", lab_type="private", is_active=True)
    db_session.add(lab)
    db_session.commit()
    db_session.refresh(lab)
    return lab


class TestRoleAr:
    def test_master_admin(self):
        assert mobile_service.role_ar("master_admin") == "مدير المنصة"

    def test_admin(self):
        assert mobile_service.role_ar("admin") == "مدير المختبر"

    def test_staff(self):
        assert mobile_service.role_ar("staff") == "موظف"

    def test_technician(self):
        assert mobile_service.role_ar("technician") == "تقني مختبر"

    def test_unknown_role_returns_raw(self):
        assert mobile_service.role_ar("unknown_role") == "unknown_role"

    def test_not_found_key(self):
        assert mobile_service.role_ar("nonexistent") == "nonexistent"


class TestGetPermissions:
    def test_staff_base_permissions(self):
        perms = mobile_service.get_permissions("staff")
        assert perms == ["view_patients", "view_results", "create_order"]

    def test_technician_permissions(self):
        perms = mobile_service.get_permissions("technician")
        assert "enter_results" in perms
        assert "view_samples" in perms
        assert "manage_users" not in perms

    def test_admin_permissions(self):
        perms = mobile_service.get_permissions("admin")
        assert "manage_users" in perms
        assert "manage_lab" in perms
        assert "view_audit_logs" in perms

    def test_master_admin_permissions(self):
        perms = mobile_service.get_permissions("master_admin")
        assert "manage_users" in perms
        assert "manage_lab" in perms
        assert "view_audit_logs" in perms

    def test_base_permissions_always_present(self):
        for role in ("staff", "technician", "admin", "master_admin"):
            perms = mobile_service.get_permissions(role)
            assert "view_patients" in perms
            assert "view_results" in perms
            assert "create_order" in perms

    def test_unknown_role_receives_base(self):
        perms = mobile_service.get_permissions("some_unknown_role")
        assert perms == ["view_patients", "view_results", "create_order"]


class TestGetMobileStats:
    def test_empty_stats(self, db_session, lab):
        stats = mobile_service.get_mobile_stats(lab.id, db_session)
        assert stats["total_patients"] == 0
        assert stats["total_orders"] == 0
        assert stats["orders_today"] == 0
        assert stats["orders_this_week"] == 0
        assert "timestamp" in stats

    def test_stats_with_data(self, db_session, lab):
        patient = Patient(
            lab_id=lab.id,
            full_name="Test Patient",
            phone="07700000000",
            gender="M",
        )
        db_session.add(patient)
        db_session.commit()

        order = LabOrder(lab_id=lab.id, patient_id=patient.id, status="pending")
        db_session.add(order)
        db_session.commit()

        stats = mobile_service.get_mobile_stats(lab.id, db_session)
        assert stats["total_patients"] == 1
        assert stats["total_orders"] == 1
        assert stats["orders_today"] == 1
        assert stats["orders_this_week"] == 1

    def test_lab_isolation(self, db_session, lab):
        other_lab = Lab(name="Other", city="Basra", lab_type="private", is_active=True)
        db_session.add(other_lab)
        db_session.commit()

        patient = Patient(
            lab_id=other_lab.id,
            full_name="Other Patient",
            phone="07709999999",
            gender="M",
        )
        db_session.add(patient)
        db_session.commit()

        order = LabOrder(lab_id=other_lab.id, patient_id=patient.id, status="pending")
        db_session.add(order)
        db_session.commit()

        stats = mobile_service.get_mobile_stats(lab.id, db_session)
        assert stats["total_patients"] == 0
        assert stats["total_orders"] == 0
