from __future__ import annotations

import os

os.environ.setdefault("ENV", "test")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production-" + "x" * 32)
os.environ.setdefault("ENCRYPTION_KEY", "6TJUTgJxBREYK9_yDy6VMXBw1HPwwxv1kiynV0WaAdw=")
os.environ.setdefault("NID_HMAC_KEY", "a" * 64)
os.environ.setdefault("REDIS_URL", "")

from datetime import datetime, timedelta

import pytest
from app._compat import UTC
from app.database import Base
from app.models.audit_log import AuditLog
from app.models.lab import Lab
from app.models.lab_order import LabOrder
from app.models.lab_result import LabResult
from app.models.lab_user import LabUser
from app.models.patient import Patient
from app.security.auth import hash_password
from app.services import admin_service
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
def master_lab(db_session):
    lab = Lab(name="Master Lab", city="Baghdad", lab_type="private", is_active=True)
    db_session.add(lab)
    db_session.commit()
    db_session.refresh(lab)
    return lab


@pytest.fixture
def master_admin(master_lab, db_session):
    u = LabUser(
        lab_id=master_lab.id,
        name="Master",
        email="master@test.com",
        password_hash="hash",
        role="master_admin",
        is_active=True,
    )
    db_session.add(u)
    db_session.commit()
    db_session.refresh(u)
    return u


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
        name="Admin",
        email="admin@lab.com",
        password_hash="hash",
        role="admin",
        is_active=True,
    )
    db_session.add(u)
    db_session.commit()
    db_session.refresh(u)
    return u


class TestUserDict:
    def test_all_fields(self):
        user = LabUser(
            id=1,
            name="Ali",
            email="ali@test.com",
            role="admin",
            lab_id=5,
            province_id=2,
            is_active=True,
            created_by=10,
        )
        d = admin_service.user_dict(user, "Test Lab")
        assert d["id"] == 1
        assert d["name"] == "Ali"
        assert d["email"] == "ali@test.com"
        assert d["role"] == "admin"
        assert d["lab_id"] == 5
        assert d["lab_name"] == "Test Lab"
        assert d["province_id"] == 2
        assert d["is_active"] is True
        assert d["created_by"] == 10

    def test_without_lab_name(self):
        user = LabUser(id=2, name="Staff", email="staff@test.com", role="staff", lab_id=5)
        d = admin_service.user_dict(user)
        assert d["lab_name"] is None

    def test_role_level(self):
        user = LabUser(id=3, name="Tech", email="tech@test.com", role="technician", lab_id=5)
        d = admin_service.user_dict(user)
        assert isinstance(d["role_level"], int)
        assert d["role_level"] > 0


class TestGetPlatformStats:
    def test_empty_stats(self, db_session):
        stats = admin_service.get_platform_stats(db_session)
        assert stats["total_labs"] == 0
        assert stats["total_users"] == 0
        assert stats["total_patients"] == 0
        assert stats["total_orders"] == 0
        assert stats["total_results"] == 0

    def test_stats_with_data(self, db_session, lab, admin_user):
        patient = Patient(lab_id=lab.id, full_name="P1", phone="07700000000", gender="M")
        db_session.add(patient)
        db_session.commit()

        order = LabOrder(lab_id=lab.id, patient_id=patient.id, status="pending")
        db_session.add(order)
        db_session.commit()

        result = LabResult(order_id=order.id, test_name="CBC", value="5.0", unit="x10^9/L")
        db_session.add(result)
        db_session.commit()

        stats = admin_service.get_platform_stats(db_session)
        assert stats["total_labs"] == 1
        assert stats["total_users"] == 1
        assert stats["total_patients"] == 1
        assert stats["total_orders"] == 1
        assert stats["total_results"] == 1

    def test_roles_breakdown(self, db_session, master_admin, admin_user):
        stats = admin_service.get_platform_stats(db_session)
        assert stats["roles_breakdown"]["master_admin"] >= 1
        assert stats["roles_breakdown"]["admin"] >= 1

    def test_active_labs(self, db_session, lab):
        stats = admin_service.get_platform_stats(db_session)
        assert stats["active_labs"] == 1
        assert stats["total_labs"] == 1


class TestListLabs:
    def test_admin_sees_own_lab(self, db_session, lab, admin_user):
        result = admin_service.list_labs(admin_user, db_session)
        assert result["total"] == 1
        assert result["labs"][0]["id"] == lab.id

    def test_master_admin_sees_all(self, db_session, master_admin, lab):
        lab2 = Lab(name="Lab 2", city="Basra", lab_type="private", is_active=True)
        db_session.add(lab2)
        db_session.commit()

        result = admin_service.list_labs(master_admin, db_session)
        assert result["total"] == 3

    def test_admin_isolated_from_other_lab(self, db_session, admin_user):
        other_lab = Lab(name="Other", city="Mosul", lab_type="public", is_active=True)
        db_session.add(other_lab)
        db_session.commit()

        result = admin_service.list_labs(admin_user, db_session)
        assert result["total"] == 1
        assert result["labs"][0]["name"] == "Test Lab"


class TestToggleLab:
    def test_toggle_deactivates(self, db_session, lab, admin_user):
        result = admin_service.toggle_lab(lab.id, admin_user, db_session)
        assert "deactivated" in result["message"]
        assert result["is_active"] is False

    def test_toggle_reactivates(self, db_session, lab, admin_user):
        lab.is_active = False
        db_session.commit()

        result = admin_service.toggle_lab(lab.id, admin_user, db_session)
        assert "activated" in result["message"]
        assert result["is_active"] is True

    def test_toggle_nonexistent_lab(self, db_session, admin_user):
        with pytest.raises(Exception) as exc:
            admin_service.toggle_lab(9999, admin_user, db_session)
        assert exc.value.status_code == 404


class TestActivateLab:
    def test_activate_pending_lab(self, db_session, master_admin):
        lab = Lab(name="Pending", city="Baghdad", lab_type="private", is_active=False)
        db_session.add(lab)
        db_session.commit()

        result = admin_service.activate_lab(lab.id, master_admin, db_session)
        assert result["is_active"] is True

    def test_activate_already_active(self, db_session, lab, master_admin):
        result = admin_service.activate_lab(lab.id, master_admin, db_session)
        assert result["is_active"] is True
        assert "already active" in result["message"]

    def test_activate_nonexistent(self, db_session, master_admin):
        with pytest.raises(Exception) as exc:
            admin_service.activate_lab(9999, master_admin, db_session)
        assert exc.value.status_code == 404


class TestCreateLab:
    def test_create_lab_success(self, db_session, master_admin):
        result = admin_service.create_lab(
            name="New Lab",
            city="Basra",
            phone="07700000000",
            admin_email="admin@newlab.com",
            admin_password="password123",
            admin_name="New Admin",
            province_id=None,
            actor=master_admin,
            db=db_session,
        )
        assert result["lab_id"] is not None
        assert result["admin_email"] == "admin@newlab.com"
        lab = db_session.query(Lab).filter(Lab.id == result["lab_id"]).first()
        assert lab is not None
        assert lab.name == "New Lab"

    def test_create_lab_short_password(self, db_session, master_admin):
        with pytest.raises(Exception) as exc:
            admin_service.create_lab(
                name="New Lab",
                city="Basra",
                phone="07700000000",
                admin_email="admin@newlab.com",
                admin_password="short",
                admin_name="New Admin",
                province_id=None,
                actor=master_admin,
                db=db_session,
            )
        assert exc.value.status_code == 400

    def test_create_lab_duplicate_email(self, db_session, master_admin):
        admin_service.create_lab(
            name="Lab 1", city="Baghdad", phone="07700000001",
            admin_email="existing@test.com", admin_password="password123",
            admin_name="Admin1", province_id=None, actor=master_admin, db=db_session,
        )
        with pytest.raises(Exception) as exc:
            admin_service.create_lab(
                name="Lab 2", city="Basra", phone="07700000002",
                admin_email="existing@test.com", admin_password="password123",
                admin_name="Admin2", province_id=None, actor=master_admin, db=db_session,
            )
        assert exc.value.status_code == 409


class TestCreateUser:
    def test_create_staff_user(self, db_session, lab, admin_user):
        result = admin_service.create_user(
            name="Staff1", email="staff@lab.com", password="pass1234",
            target_role="staff", lab_id=lab.id, province_id=None,
            national_id=None, actor=admin_user, db=db_session,
        )
        assert result["user"]["email"] == "staff@lab.com"
        assert result["user"]["role"] == "staff"

    def test_create_user_invalid_role(self, db_session, lab, admin_user):
        with pytest.raises(Exception) as exc:
            admin_service.create_user(
                name="X", email="x@test.com", password="pass1234",
                target_role="invalid_role", lab_id=lab.id, province_id=None,
                national_id=None, actor=admin_user, db=db_session,
            )
        assert exc.value.status_code == 400

    def test_create_user_short_password(self, db_session, lab, admin_user):
        with pytest.raises(Exception) as exc:
            admin_service.create_user(
                name="X", email="x@test.com", password="short",
                target_role="staff", lab_id=lab.id, province_id=None,
                national_id=None, actor=admin_user, db=db_session,
            )
        assert exc.value.status_code == 400

    def test_create_user_duplicate_email(self, db_session, lab, admin_user):
        admin_service.create_user(
            name="A", email="dup@test.com", password="pass1234",
            target_role="staff", lab_id=lab.id, province_id=None,
            national_id=None, actor=admin_user, db=db_session,
        )
        with pytest.raises(Exception) as exc:
            admin_service.create_user(
                name="B", email="dup@test.com", password="pass1234",
                target_role="staff", lab_id=lab.id, province_id=None,
                national_id=None, actor=admin_user, db=db_session,
            )
        assert exc.value.status_code == 409

    def test_create_user_nonexistent_lab(self, db_session, master_admin):
        with pytest.raises(Exception) as exc:
            admin_service.create_user(
                name="X", email="x@test.com", password="pass1234",
                target_role="staff", lab_id=9999, province_id=None,
                national_id=None, actor=master_admin, db=db_session,
            )
        assert exc.value.status_code == 404


class TestListUsers:
    def test_admin_lists_visible_users(self, db_session, lab, admin_user):
        staff = LabUser(
            lab_id=lab.id, name="Staff1", email="staff@lab.com",
            password_hash="hash", role="staff", is_active=True,
        )
        db_session.add(staff)
        db_session.commit()

        result = admin_service.list_users(admin_user, db_session)
        assert result["total"] >= 1
        emails = [u["email"] for u in result["users"]]
        assert "staff@lab.com" in emails

    def test_master_admin_sees_all(self, db_session, master_admin, admin_user):
        result = admin_service.list_users(master_admin, db_session)
        assert result["total"] >= 1

    def test_technician_has_no_visible_users(self, db_session, lab):
        tech = LabUser(
            lab_id=lab.id, name="Tech", email="tech@lab.com",
            password_hash="hash", role="technician", is_active=True,
        )
        db_session.add(tech)
        db_session.commit()

        result = admin_service.list_users(tech, db_session)
        assert result["total"] == 0


class TestToggleUser:
    def test_deactivate_user(self, db_session, lab, master_admin):
        target = LabUser(
            lab_id=lab.id, name="Target", email="target@lab.com",
            password_hash="hash", role="staff", is_active=True,
        )
        db_session.add(target)
        db_session.commit()

        result = admin_service.toggle_user(target.id, master_admin, db_session)
        assert "deactivated" in result["message"]
        assert db_session.query(LabUser).filter(LabUser.id == target.id).first().is_active is False

    def test_cannot_deactivate_self(self, db_session, master_admin):
        with pytest.raises(Exception) as exc:
            admin_service.toggle_user(master_admin.id, master_admin, db_session)
        assert exc.value.status_code == 403

    def test_toggle_nonexistent(self, db_session, master_admin):
        with pytest.raises(Exception) as exc:
            admin_service.toggle_user(9999, master_admin, db_session)
        assert exc.value.status_code == 404


class TestChangeUserRole:
    def test_master_admin_can_change_role(self, db_session, lab, master_admin):
        target = LabUser(
            lab_id=lab.id, name="Target", email="target@lab.com",
            password_hash="hash", role="staff", is_active=True,
        )
        db_session.add(target)
        db_session.commit()

        result = admin_service.change_user_role(
            target.id, "technician", None, master_admin, db_session
        )
        assert result["new_role"] == "technician"
        assert result["old_role"] == "staff"

    def test_cannot_change_own_role(self, db_session, lab, master_admin):
        with pytest.raises(Exception) as exc:
            admin_service.change_user_role(
                master_admin.id, "staff", None, master_admin, db_session
            )
        assert exc.value.status_code == 403

    def test_change_to_invalid_role(self, db_session, lab, master_admin):
        target = LabUser(
            lab_id=lab.id, name="T", email="t@test.com",
            password_hash="hash", role="staff", is_active=True,
        )
        db_session.add(target)
        db_session.commit()

        with pytest.raises(Exception) as exc:
            admin_service.change_user_role(
                target.id, "invalid_role", None, master_admin, db_session
            )
        assert exc.value.status_code == 400


class TestGetAuditLogs:
    def test_admin_sees_own_lab_logs(self, db_session, lab, admin_user):
        log = AuditLog(
            action="test_action", resource_type="test",
            user_id=admin_user.id, user_role=admin_user.role,
            details="Test log entry",
        )
        db_session.add(log)
        db_session.commit()

        result = admin_service.get_audit_logs(admin_user, db_session)
        assert result["total"] >= 1

    def test_empty_logs(self, db_session, lab, admin_user):
        result = admin_service.get_audit_logs(admin_user, db_session)
        assert result["total"] == 0

    def test_filter_by_action(self, db_session, lab, admin_user):
        log1 = AuditLog(
            action="create", resource_type="test",
            user_id=admin_user.id, user_role=admin_user.role,
            details="Create",
        )
        log2 = AuditLog(
            action="delete", resource_type="test",
            user_id=admin_user.id, user_role=admin_user.role,
            details="Delete",
        )
        db_session.add_all([log1, log2])
        db_session.commit()

        result = admin_service.get_audit_logs(admin_user, db_session, action="create")
        assert result["total"] == 1
        assert result["logs"][0]["action"] == "create"


class TestGetLabDetail:
    def test_lab_detail(self, db_session, lab, admin_user):
        result = admin_service.get_lab_detail(lab.id, admin_user, db_session)
        assert result["id"] == lab.id
        assert result["name"] == "Test Lab"
        assert result["admin_email"] == admin_user.email
        assert result["staff_count"] >= 1
        assert result["patient_count"] == 0

    def test_nonexistent_lab_detail(self, db_session, admin_user):
        with pytest.raises(Exception) as exc:
            admin_service.get_lab_detail(9999, admin_user, db_session)
        assert exc.value.status_code == 404


class TestListPendingLabs:
    def test_pending_labs_only(self, db_session, master_admin):
        active = Lab(name="Active", city="Baghdad", lab_type="private", is_active=True)
        pending = Lab(name="Pending", city="Basra", lab_type="private", is_active=False)
        db_session.add_all([active, pending])
        db_session.commit()

        result = admin_service.list_pending_labs(master_admin, db_session)
        assert result["total"] == 1
        assert result["pending_labs"][0]["name"] == "Pending"

    def test_pending_lab_includes_admin_info(self, db_session, master_admin):
        lab = Lab(name="New", city="Mosul", lab_type="private", is_active=False)
        db_session.add(lab)
        db_session.flush()

        lab_admin = LabUser(
            lab_id=lab.id, name="Lab Admin", email="labadmin@test.com",
            password_hash="hash", role="admin",
        )
        db_session.add(lab_admin)
        db_session.commit()

        result = admin_service.list_pending_labs(master_admin, db_session)
        assert result["pending_labs"][0]["admin_email"] == "labadmin@test.com"
