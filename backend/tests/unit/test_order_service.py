"""Unit tests for order_service — DTO serialization, sharing links, token logic."""

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
from app.models.lab_order import LabOrder
from app.models.lab_result import LabResult, hash_token
from app.models.patient import Patient
from app.services import order_service
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
def patient(db_session):
    p = Patient(full_name="Ali Ahmed", phone="+9647712345678", health_id="IQ-12345", lab_id=1)
    db_session.add(p)
    db_session.commit()
    db_session.refresh(p)
    return p


@pytest.fixture
def order(db_session, patient):
    o = LabOrder(patient_id=patient.id, doctor_name="Dr. Sana", status="completed", lab_id=1)
    db_session.add(o)
    db_session.commit()
    db_session.refresh(o)
    return o


def _result(order, token, value=5.2, flag="normal"):
    return LabResult(
        order_id=order.id,
        test_name="CBC",
        value=value,
        unit="x10^9/L",
        normal_range_low=4.0,
        normal_range_high=11.0,
        flag=flag,
        token=token,
        token_hash=hash_token(token),
    )


class TestResultDict:
    def test_to_dict_full(self):
        dto = order_service.ResultDict(
            id=1, test_name="CBC", value=5.2, value_text=None, unit="x10^9/L",
            normal_range_low=4.0, normal_range_high=11.0, flag="normal",
            result_token="tok", result_link="/r/tok", interpretation=None, created_at=None,
        )
        d = dto.to_dict()
        assert d["id"] == 1
        assert d["test_name"] == "CBC"
        assert d["value"] == 5.2
        assert d["unit"] == "x10^9/L"
        assert d["flag"] == "normal"
        assert d["result_token"] == "tok"
        assert d["result_link"] == "/r/tok"

    def test_to_dict_nullable(self):
        dto = order_service.ResultDict(
            id=2, test_name="Urea", value=None, value_text="negative", unit=None,
            normal_range_low=None, normal_range_high=None, flag="normal",
            result_token="", result_link="", interpretation=None, created_at=None,
        )
        d = dto.to_dict()
        assert d["value"] is None
        assert d["value_text"] == "negative"
        assert d["normal_range_low"] is None
        assert d["flag"] == "normal"


class TestOrderDict:
    def test_to_dict_without_results(self):
        dto = order_service.OrderDict(
            id=1, patient_id=1, patient_name="Ali", patient_phone="+9647",
            doctor_name="Dr. Sana", status="pending", is_critical=False, locked=False,
            validated_by=None, validated_at=None, created_at="2026-01-01T00:00:00+00:00",
            results=None,
        )
        d = dto.to_dict()
        assert "results" not in d
        assert "share_link" not in d
        assert d["patient_name"] == "Ali"

    def test_to_dict_with_results_no_share(self):
        dto = order_service.OrderDict(
            id=1, patient_id=1, patient_name="Ali", patient_phone=None,
            doctor_name=None, status="completed", is_critical=True, locked=True,
            validated_by=9, validated_at="2026-01-01T00:00:00+00:00",
            created_at=None, results=[],
        )
        d = dto.to_dict()
        assert d["results"] == []
        assert "share_link" not in d

    def test_to_dict_with_results_and_share(self):
        dto = order_service.OrderDict(
            id=1, patient_id=1, patient_name="Ali", patient_phone=None,
            doctor_name=None, status="completed", is_critical=False, locked=False,
            validated_by=None, validated_at=None, created_at=None,
            results=[{"id": 1}], share_link="/r/x", whatsapp_link="https://wa.me/?text=x",
        )
        d = dto.to_dict()
        assert d["share_link"] == "/r/x"
        assert d["whatsapp_link"].startswith("https://wa.me/")


class TestResultToDict:
    def test_interpretation_attached_when_value(self, db_session, order):
        r = _result(order, "tok-a")
        db_session.add(r)
        db_session.commit()
        d = order_service.result_to_dict(r)
        assert d["test_name"] == "CBC"
        assert d["value"] == 5.2
        assert d["result_token"] == "tok-a"
        assert d["result_link"] == "/r/tok-a"
        assert d["interpretation"] is not None

    def test_no_interpretation_when_text_only(self, db_session, order):
        r = _result(order, "tok-b", value=None)
        r.value_text = "negative"
        db_session.add(r)
        db_session.commit()
        d = order_service.result_to_dict(r)
        assert d["value"] is None
        assert d["interpretation"] is None


class TestOrderToDict:
    def test_critical_flag_detection(self, db_session, order, patient):
        r = _result(order, "tok-c", value=20.0, flag="critical")
        db_session.add(r)
        db_session.commit()
        d = order_service.order_to_dict(order)
        assert d["is_critical"] is True
        assert d["patient_name"] == "Ali Ahmed"
        assert d["status"] == "completed"
        assert len(d["results"]) == 1
        assert d["share_link"] == "/r/tok-c"

    def test_locked_detection(self, db_session, order):
        order.locked_at = None
        db_session.add(order)
        db_session.commit()
        d = order_service.order_to_dict(order, include_results=False)
        assert d["locked"] is False

    def test_whatsapp_link_contains_url(self, db_session, order):
        r = _result(order, "tok-d")
        db_session.add(r)
        db_session.commit()
        d = order_service.order_to_dict(order)
        assert "wa.me" in d["whatsapp_link"]
        assert "/r/tok-d" in d["whatsapp_link"]


class TestGenerateUniqueToken:
    def test_returns_token_and_hash(self, db_session):
        token, token_h = order_service._generate_unique_token(db_session)
        assert token
        assert token_h == hash_token(token)
        assert len(token) >= 32

    def test_avoids_collision(self, db_session, order):
        existing = _result(order, "tok-e")
        db_session.add(existing)
        db_session.commit()
        token, _ = order_service._generate_unique_token(db_session)
        assert token != "tok-e"


class TestBuildSharingLinks:
    def test_iraqi_phone_normalized_to_964(self):
        links = order_service._build_sharing_links(
            "07712345678", "Ali Ahmed", [{"link": "/r/abc"}],
        )
        assert links["whatsapp_link"].startswith("https://wa.me/9647712345678?text=")
        assert links["sms_link"].startswith("sms:07712345678?body=")

    def test_international_phone(self):
        links = order_service._build_sharing_links(
            "+1 555-0100", "Sam", [{"link": "/r/xyz"}],
        )
        assert links["whatsapp_link"].startswith("https://wa.me/15550100?text=")
        assert "Sam" in links["whatsapp_link"]

    def test_no_phone_no_links(self):
        links = order_service._build_sharing_links(None, "Ali", [{"link": "/r/abc"}])
        assert links["whatsapp_link"] is None
        assert links["sms_link"] is None

    def test_sms_body_contains_url(self):
        links = order_service._build_sharing_links("07712345678", "Ali", [{"link": "/r/abc"}])
        assert "/r/abc" in links["sms_link"]


class TestCheckCriticalAlerts:
    def test_no_value_no_alert(self):
        assert order_service._check_critical_alerts([{"test_name": "CBC", "value": None}]) == []

    def test_normal_value_no_alert(self):
        assert order_service._check_critical_alerts([{"test_name": "CBC", "value": 5.0}]) == []

    def test_abnormal_value_alerts(self):
        alerts = order_service._check_critical_alerts([{"test_name": "glucose", "value": 600.0}])
        assert alerts
        assert alerts[0]["test_name"] == "glucose"
        assert alerts[0]["value"] == 600.0
        assert alerts[0]["severity"] == "critical_high"

    def test_critical_low_alerts(self):
        alerts = order_service._check_critical_alerts([{"test_name": "Glucose", "value": 30.0}])
        assert alerts
        assert alerts[0]["severity"] == "critical_low"
        assert alerts[0]["threshold"] == 40.0
