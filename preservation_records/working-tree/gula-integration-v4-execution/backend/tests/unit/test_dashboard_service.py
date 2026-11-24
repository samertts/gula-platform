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
from app.models.lab import Lab
from app.models.lab_order import LabOrder
from app.models.lab_result import LabResult
from app.models.lab_user import LabUser
from app.models.patient import Patient
from app.services import dashboard_service
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


@pytest.fixture
def patient(lab, db_session):
    p = Patient(
        lab_id=lab.id,
        full_name="Ali Ahmed",
        phone="07701234567",
        gender="M",
    )
    db_session.add(p)
    db_session.commit()
    db_session.refresh(p)
    return p


@pytest.fixture
def another_lab(db_session):
    lab = Lab(name="Other Lab", city="Basra", lab_type="private", is_active=True)
    db_session.add(lab)
    db_session.commit()
    db_session.refresh(lab)
    return lab


class TestArabicGreeting:
    def test_morning_5_to_12(self):
        assert dashboard_service.arabic_greeting(5) == "صباح الخير"
        assert dashboard_service.arabic_greeting(8) == "صباح الخير"
        assert dashboard_service.arabic_greeting(11) == "صباح الخير"

    def test_afternoon_12_to_17(self):
        assert dashboard_service.arabic_greeting(12) == "مساء الخير"
        assert dashboard_service.arabic_greeting(14) == "مساء الخير"
        assert dashboard_service.arabic_greeting(16) == "مساء الخير"

    def test_evening_17_to_21(self):
        assert dashboard_service.arabic_greeting(17) == "مساء النور"
        assert dashboard_service.arabic_greeting(19) == "مساء النور"
        assert dashboard_service.arabic_greeting(20) == "مساء النور"

    def test_night_21_to_5(self):
        assert dashboard_service.arabic_greeting(21) == "أهلاً"
        assert dashboard_service.arabic_greeting(0) == "أهلاً"
        assert dashboard_service.arabic_greeting(3) == "أهلاً"
        assert dashboard_service.arabic_greeting(4) == "أهلاً"

    def test_all_hours_in_range(self):
        seen = set()
        for h in range(24):
            seen.add(dashboard_service.arabic_greeting(h))
        assert seen == {"صباح الخير", "مساء الخير", "مساء النور", "أهلاً"}


class TestGetGreeting:
    def test_default_no_user(self):
        result = dashboard_service.get_greeting(None)
        assert result["greeting"] in {"صباح الخير", "مساء الخير", "مساء النور", "أهلاً"}
        assert result["user_name"] == "مستخدم"

    def test_with_user(self):
        class FakeUser:
            name = "Ali"

        result = dashboard_service.get_greeting(FakeUser())
        assert "Ali" in result["user_name"]
        assert result["user_name"] in result["message"]

    def test_user_without_name(self):
        class FakeUser:
            name = None

        result = dashboard_service.get_greeting(FakeUser())
        assert result["user_name"] == "مستخدم"


class TestGetDashboard:
    def test_returns_structure(self, db_session, admin_user):
        result = dashboard_service.get_dashboard(db_session, admin_user)
        assert isinstance(result, dict)
        assert "greeting" in result
        assert "patients" in result
        assert "orders" in result
        assert "tests" in result
        assert "critical" in result
        assert "today" in result
        assert "this_week" in result
        assert "abnormal_results" in result
        assert "recent_orders" in result
        assert "lab_name" in result

    def test_empty_dashboard(self, db_session, admin_user):
        result = dashboard_service.get_dashboard(db_session, admin_user)
        assert result["patients"] == 0
        assert result["orders"] == 0
        assert result["tests"] == 0
        assert result["critical"] == 0
        assert result["today"]["patients"] == 0
        assert result["today"]["orders"] == 0
        assert result["today"]["tests"] == 0
        assert result["abnormal_results"] == []
        assert result["recent_orders"] == []

    def test_counts_with_data(self, db_session, lab, admin_user, patient):
        order = LabOrder(lab_id=lab.id, patient_id=patient.id, status="completed")
        db_session.add(order)
        db_session.commit()
        db_session.refresh(order)

        result_obj = LabResult(
            order_id=order.id,
            test_name="CBC",
            value="5.0",
            unit="x10^9/L",
            flag="critical",
            created_at=datetime.now(UTC),
            token="tok-1",
        )
        db_session.add(result_obj)
        db_session.commit()

        result = dashboard_service.get_dashboard(db_session, admin_user)
        assert result["patients"] == 1
        assert result["orders"] == 1
        assert result["tests"] == 1
        assert result["critical"] == 1
        assert result["abnormal_results"] != []

    def test_lab_isolation(self, db_session, lab, admin_user, another_lab):
        other_patient = Patient(
            lab_id=another_lab.id,
            full_name="Other Patient",
            phone="07709999999",
            gender="M",
        )
        db_session.add(other_patient)
        db_session.commit()
        db_session.refresh(other_patient)

        order = LabOrder(lab_id=another_lab.id, patient_id=other_patient.id, status="completed")
        db_session.add(order)
        db_session.commit()

        result_obj = LabResult(
            order_id=order.id,
            test_name="CBC",
            value="5.0",
            unit="x10^9/L",
            flag="critical",
            created_at=datetime.now(UTC),
            token="tok-1",
        )
        db_session.add(result_obj)
        db_session.commit()

        result = dashboard_service.get_dashboard(db_session, admin_user)
        assert result["patients"] == 0
        assert result["orders"] == 0
        assert result["tests"] == 0
        assert result["critical"] == 0

    def test_abnormal_results_sorted(self, db_session, lab, admin_user, patient):
        order = LabOrder(lab_id=lab.id, patient_id=patient.id, status="completed")
        db_session.add(order)
        db_session.commit()

        for i in range(5):
            r = LabResult(
                order_id=order.id,
                test_name=f"Test-{i}",
                value=str(i),
                unit="unit",
                flag="H" if i % 2 == 0 else "L",
                created_at=datetime.now(UTC) - timedelta(hours=i),
                token=f"tok-{i}",
            )
            db_session.add(r)
        db_session.commit()

        result = dashboard_service.get_dashboard(db_session, admin_user)
        assert len(result["abnormal_results"]) == 5
        assert result["abnormal_results"][0]["test_name"] == "Test-0"

    def test_recent_orders_limit(self, db_session, lab, admin_user, patient):
        for i in range(10):
            o = LabOrder(lab_id=lab.id, patient_id=patient.id, status="pending")
            db_session.add(o)
        db_session.commit()

        result = dashboard_service.get_dashboard(db_session, admin_user)
        assert len(result["recent_orders"]) == 6

    def test_lab_name_in_result(self, db_session, lab, admin_user):
        result = dashboard_service.get_dashboard(db_session, admin_user)
        assert result["lab_name"] == "Test Lab"

    def test_greeting_includes_admin_name(self, db_session, admin_user):
        result = dashboard_service.get_dashboard(db_session, admin_user)
        assert "Admin" in result["greeting"]
