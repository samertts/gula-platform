"""Unit tests for order_service — order/result lifecycle, public links, patient history."""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta

os.environ.setdefault("ENV", "test")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production-" + "x" * 32)
os.environ.setdefault("ENCRYPTION_KEY", "6TJUTgJxBREYK9_yDy6VMXBw1HPwwxv1kiynV0WaAdw=")
os.environ.setdefault("NID_HMAC_KEY", "a" * 64)
os.environ.setdefault("REDIS_URL", "")

import pytest
from app.database import Base
from app.domain.exceptions import OrderStateError
from app.models.audit_log import AuditLog
from app.models.lab import Lab
from app.models.lab_order import LabOrder
from app.models.lab_result import LabResult, hash_token
from app.models.lab_user import LabUser
from app.models.patient import Patient
from app.security.auth import hash_password
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
        password_hash=hash_password("pw"),
        role="admin",
        is_active=True,
    )
    db_session.add(u)
    db_session.commit()
    db_session.refresh(u)
    return u


@pytest.fixture
def doctor_user(lab, db_session):
    u = LabUser(
        lab_id=lab.id,
        name="Doctor",
        email="doctor@lab.com",
        password_hash=hash_password("pw"),
        role="doctor",
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
        full_name="Test Patient",
        phone="0770000000",
        health_id="IQ1234567",
        gender="M",
    )
    db_session.add(p)
    db_session.commit()
    db_session.refresh(p)
    return p


def _make_result(
    db_session,
    order: LabOrder,
    test_name: str = "Hemoglobin",
    value: float = 14.0,
    low: float = 12.0,
    high: float = 17.0,
    flag: str = "normal",
) -> LabResult:
    token = "tok_" + os.urandom(8).hex()
    r = LabResult(
        order_id=order.id,
        test_name=test_name,
        value=value,
        unit="g/dL",
        normal_range_low=low,
        normal_range_high=high,
        flag=flag,
        token=token,
        token_hash=hash_token(token),
    )
    db_session.add(r)
    db_session.commit()
    db_session.refresh(r)
    return r


def _create_order(db_session, lab, user, patient, results=None, **kwargs) -> dict:
    results = results or [
        {
            "test_name": "Hemoglobin",
            "value": 14.0,
            "unit": "g/dL",
            "normal_range_low": 12.0,
            "normal_range_high": 17.0,
        },
    ]
    return order_service.create_order(
        db_session,
        lab_id=lab.id,
        user_id=user.id,
        user_role="admin",
        patient_id=patient.id,
        doctor_name="Dr. Ali",
        doctor_user_id=None,
        results_data=results,
        **kwargs,
    )


class TestSerialization:
    def test_result_to_dict_with_interpretation(self, db_session, lab, admin_user, patient):
        resp = _create_order(db_session, lab, admin_user, patient)
        order_id = resp["order"]["id"]
        order = db_session.get(LabOrder, order_id)
        d = order_service.result_to_dict(order.results[0])
        assert d["test_name"] == "Hemoglobin"
        assert d["value"] == 14.0
        assert d["result_link"].startswith("/r/")
        assert d["interpretation"] is not None

    def test_order_to_dict_detects_critical(self, db_session, lab, admin_user, patient):
        resp = _create_order(db_session, lab, admin_user, patient)
        order = db_session.get(LabOrder, resp["order"]["id"])
        order.results[0].flag = "H"
        d = order_service.order_to_dict(order)
        assert d["is_critical"] is True

    def test_order_to_dict_share_and_whatsapp(self, db_session, lab, admin_user, patient):
        resp = _create_order(db_session, lab, admin_user, patient)
        order = db_session.get(LabOrder, resp["order"]["id"])
        d = order_service.order_to_dict(order)
        assert d["share_link"].startswith("/r/")
        assert "wa.me" in d["whatsapp_link"]
        assert d["results"] and d["results"][0]["test_name"] == "Hemoglobin"

    def test_order_to_dict_without_results(self, db_session, lab, admin_user, patient):
        resp = _create_order(db_session, lab, admin_user, patient)
        order = db_session.get(LabOrder, resp["order"]["id"])
        d = order_service.order_to_dict(order, include_results=False)
        assert "results" not in d


class TestCreateOrder:
    def test_create_order_success(self, db_session, lab, admin_user, patient):
        resp = _create_order(db_session, lab, admin_user, patient)
        assert "error" not in resp
        assert resp["order"]["status"] == "completed"
        assert resp["order"]["patient_name"] == "Test Patient"
        assert len(resp["result_links"]) == 1
        assert resp["critical_alerts"] is None
        order = db_session.get(LabOrder, resp["order"]["id"])
        assert order.results[0].flag == "normal"

    def test_create_order_high_flag(self, db_session, lab, admin_user, patient):
        results = [
            {
                "test_name": "Hemoglobin",
                "value": 19.0,
                "unit": "g/dL",
                "normal_range_low": 12.0,
                "normal_range_high": 17.0,
            },
        ]
        resp = _create_order(db_session, lab, admin_user, patient, results=results)
        order = db_session.get(LabOrder, resp["order"]["id"])
        assert order.results[0].flag == "H"

    def test_create_order_critical_alert(self, db_session, lab, admin_user, patient):
        results = [
            {
                "test_name": "Potassium",
                "value": 7.2,
                "unit": "mEq/L",
                "normal_range_low": 3.5,
                "normal_range_high": 5.0,
            },
        ]
        resp = _create_order(db_session, lab, admin_user, patient, results=results)
        assert resp["critical_alerts"] and resp["critical_alerts"][0]["test_name"] == "Potassium"

    def test_create_order_value_text_unknown_flag(self, db_session, lab, admin_user, patient):
        results = [{"test_name": "Morphology", "value_text": "Normal smear"}]
        resp = _create_order(db_session, lab, admin_user, patient, results=results)
        order = db_session.get(LabOrder, resp["order"]["id"])
        assert order.results[0].flag == "unknown"

    def test_create_order_patient_not_found(self, db_session, lab, admin_user):
        resp = order_service.create_order(
            db_session,
            lab_id=lab.id,
            user_id=admin_user.id,
            user_role="admin",
            patient_id=999,
            doctor_name=None,
            doctor_user_id=None,
            results_data=[],
        )
        assert resp["status_code"] == 404

    def test_create_order_invalid_doctor(self, db_session, lab, admin_user, patient):
        from app.models.lab_user import LabUser

        resp = order_service.create_order(
            db_session,
            lab_id=lab.id,
            user_id=admin_user.id,
            user_role="admin",
            patient_id=patient.id,
            doctor_name=None,
            doctor_user_id=99999,
            results_data=[],
        )
        assert resp["status_code"] == 400

    def test_create_order_idempotency(self, db_session, lab, admin_user, patient, monkeypatch):
        cache_store = {}
        fake_cache = type("FakeCache", (), {"get": lambda self, k: cache_store.get(k), "set": lambda self, k, v, ex: cache_store.__setitem__(k, v)})()
        monkeypatch.setattr(order_service, "_cache", fake_cache)
        first = _create_order(db_session, lab, admin_user, patient, idempotency_key="key-1")
        second = _create_order(db_session, lab, admin_user, patient, idempotency_key="key-1")
        assert first["order"]["id"] == second["order"]["id"]
        assert db_session.query(LabOrder).count() == 1

    def test_create_order_audit_logged(self, db_session, lab, admin_user, patient):
        _create_order(db_session, lab, admin_user, patient)
        assert db_session.query(AuditLog).filter_by(action="create", resource_type="lab_order").count() == 1


class TestGetAndListOrders:
    def test_get_order_by_id(self, db_session, lab, admin_user, patient):
        resp = _create_order(db_session, lab, admin_user, patient)
        d = order_service.get_order_by_id(db_session, resp["order"]["id"], lab.id, "admin", admin_user.id)
        assert d and d["id"] == resp["order"]["id"]

    def test_get_order_scoped_to_lab(self, db_session, lab, admin_user, patient):
        other_lab = Lab(name="Other Lab", city="Basra", lab_type="private", is_active=True)
        db_session.add(other_lab)
        db_session.commit()
        resp = _create_order(db_session, lab, admin_user, patient)
        d = order_service.get_order_by_id(db_session, resp["order"]["id"], other_lab.id, "admin", admin_user.id)
        assert d is None

    def test_doctor_only_own_orders(self, db_session, lab, doctor_user, admin_user, patient):
        resp = _create_order(db_session, lab, admin_user, patient)
        d = order_service.get_order_by_id(db_session, resp["order"]["id"], lab.id, "doctor", doctor_user.id)
        assert d is None

    def test_citizen_sees_no_orders(self, db_session, lab, admin_user, patient):
        _create_order(db_session, lab, admin_user, patient)
        listing = order_service.list_orders(db_session, lab.id, "citizen", 1)
        assert listing["total"] == 0

    def test_list_orders_search(self, db_session, lab, admin_user, patient):
        _create_order(db_session, lab, admin_user, patient)
        found = order_service.list_orders(db_session, lab.id, "admin", admin_user.id, search="Test")
        assert found["total"] == 1
        none = order_service.list_orders(db_session, lab.id, "admin", admin_user.id, search="Nobody")
        assert none["total"] == 0


class TestValidateOrder:
    def test_validate_requires_admin_or_doctor(self, db_session, lab, admin_user, patient):
        tech = LabUser(
            lab_id=lab.id,
            name="Tech",
            email="tech@lab.com",
            password_hash=hash_password("pw"),
            role="technician",
            is_active=True,
        )
        db_session.add(tech)
        db_session.commit()
        resp = _create_order(db_session, lab, admin_user, patient)
        result = order_service.validate_order(db_session, resp["order"]["id"], lab.id, "technician", tech.id)
        assert result["status_code"] == 403

    def test_validate_not_found(self, db_session, lab, admin_user):
        result = order_service.validate_order(db_session, 999, lab.id, "admin", admin_user.id)
        assert result["status_code"] == 404

    def test_validate_no_results(self, db_session, lab, admin_user, patient):
        order = LabOrder(lab_id=lab.id, patient_id=patient.id, status="pending")
        db_session.add(order)
        db_session.commit()
        result = order_service.validate_order(db_session, order.id, lab.id, "admin", admin_user.id)
        assert result["status_code"] == 400

    def test_validate_success(self, db_session, lab, admin_user, patient):
        resp = _create_order(db_session, lab, admin_user, patient)
        order_id = resp["order"]["id"]
        d = order_service.validate_order(db_session, order_id, lab.id, "admin", admin_user.id)
        assert d["status"] == "validated"
        assert d["locked"] is True
        assert d["validated_by"] == admin_user.id

    def test_validate_twice_conflict(self, db_session, lab, admin_user, patient):
        resp = _create_order(db_session, lab, admin_user, patient)
        order_id = resp["order"]["id"]
        order_service.validate_order(db_session, order_id, lab.id, "admin", admin_user.id)
        with pytest.raises(OrderStateError):
            order_service.validate_order(db_session, order_id, lab.id, "admin", admin_user.id)


class TestCancelOrder:
    def test_cancel_success(self, db_session, lab, admin_user, patient):
        resp = _create_order(db_session, lab, admin_user, patient)
        result = order_service.cancel_order(db_session, resp["order"]["id"], lab.id, "admin", admin_user.id)
        assert result["message"] == "Order cancelled"
        order = db_session.get(LabOrder, resp["order"]["id"])
        assert order.status == "cancelled"

    def test_cancel_not_found(self, db_session, lab, admin_user):
        result = order_service.cancel_order(db_session, 999, lab.id, "admin", admin_user.id)
        assert result["status_code"] == 404

    def test_cancel_validated_order_raises(self, db_session, lab, admin_user, patient):
        resp = _create_order(db_session, lab, admin_user, patient)
        order_id = resp["order"]["id"]
        order_service.validate_order(db_session, order_id, lab.id, "admin", admin_user.id)
        with pytest.raises(OrderStateError):
            order_service.cancel_order(db_session, order_id, lab.id, "admin", admin_user.id)


class TestPublicResult:
    def test_public_result_not_found(self, db_session):
        result = order_service.get_public_result(db_session, "bad-token")
        assert result["status_code"] == 404

    def test_public_result_success(self, db_session, lab, admin_user, patient):
        resp = _create_order(db_session, lab, admin_user, patient)
        token = resp["result_links"][0]["link"].split("/")[-1]
        result = order_service.get_public_result(db_session, token)
        assert "error" not in result
        assert result["patient"]["name"] == "Test Patient"
        assert result["lab"]["name"] == "Test Lab"
        assert result["results"][0]["test_name"] == "Hemoglobin"
        assert result["disclaimer_ar"]

    def test_public_result_expired(self, db_session, lab, admin_user, patient):
        resp = _create_order(db_session, lab, admin_user, patient)
        order = db_session.get(LabOrder, resp["order"]["id"])
        order.results[0].expires_at = datetime.now(UTC) - timedelta(days=1)
        db_session.commit()
        token = resp["result_links"][0]["link"].split("/")[-1]
        result = order_service.get_public_result(db_session, token)
        assert result["status_code"] == 410


class TestDownloadPdf:
    def test_download_not_found(self, db_session):
        result = order_service.download_result_pdf(db_session, "bad-token")
        assert result["status_code"] == 404

    def test_download_success(self, db_session, lab, admin_user, patient, monkeypatch):
        monkeypatch.setattr(order_service, "generate_result_pdf", lambda data, url: b"%PDF-1.4-test")
        resp = _create_order(db_session, lab, admin_user, patient)
        token = resp["result_links"][0]["link"].split("/")[-1]
        result = order_service.download_result_pdf(db_session, token)
        assert result["pdf_bytes"] == b"%PDF-1.4-test"
        assert result["filename"] == "GULA_Report_Test_Patient.pdf"

    def test_download_pdf_failure_500(self, db_session, lab, admin_user, patient, monkeypatch):
        def boom(data, url):
            raise RuntimeError("pdf engine down")

        monkeypatch.setattr(order_service, "generate_result_pdf", boom)
        resp = _create_order(db_session, lab, admin_user, patient)
        token = resp["result_links"][0]["link"].split("/")[-1]
        result = order_service.download_result_pdf(db_session, token)
        assert result["status_code"] == 500


class TestPatientHistory:
    def test_history_by_id(self, db_session, lab, admin_user, patient):
        _create_order(db_session, lab, admin_user, patient)
        history = order_service.get_patient_history_by_id(db_session, patient.id, lab.id)
        assert history and history["total_orders"] == 1
        assert "Hemoglobin" in history["trends"]
        assert history["results"][0]["test_name"] == "Hemoglobin"

    def test_history_by_id_wrong_lab(self, db_session, lab, admin_user, patient):
        other_lab = Lab(name="Other Lab", city="Mosul", lab_type="private", is_active=True)
        db_session.add(other_lab)
        db_session.commit()
        _create_order(db_session, lab, admin_user, patient)
        assert order_service.get_patient_history_by_id(db_session, patient.id, other_lab.id) is None

    def test_history_by_phone_name_too_short(self, db_session, lab, admin_user, patient):
        result = order_service.get_patient_history_by_phone(db_session, patient.phone, name="Ali")
        assert result["status_code"] == 400

    def test_history_by_phone_not_found(self, db_session, patient):
        result = order_service.get_patient_history_by_phone(db_session, "0799999999", name="Test Patient")
        assert result["status_code"] == 404

    def test_history_by_phone_name_mismatch(self, db_session, lab, admin_user, patient):
        result = order_service.get_patient_history_by_phone(db_session, patient.phone, name="Wrong Person")
        assert result["status_code"] == 403

    def test_history_by_phone_success(self, db_session, lab, admin_user, patient):
        _create_order(db_session, lab, admin_user, patient)
        result = order_service.get_patient_history_by_phone(db_session, patient.phone, name="test patient")
        assert "error" not in result
        assert result["patient_name"] == "Test Patient"
        assert result["history"][0]["test_name"] == "Hemoglobin"


class TestSharingLinks:
    def test_phone_07_prefix_converted_to_964(self):
        links = order_service._build_sharing_links("0770000000", "Test Patient", [{"link": "/r/tok"}])
        assert links["whatsapp_link"].startswith("https://wa.me/964770000000")

    def test_no_phone_no_links(self):
        links = order_service._build_sharing_links(None, "Test Patient", [{"link": "/r/tok"}])
        assert links["whatsapp_link"] is None
        assert links["sms_link"] is None


class TestTokenGeneration:
    def test_unique_tokens(self, db_session, lab, admin_user, patient):
        _create_order(db_session, lab, admin_user, patient)
        token_a, hash_a = order_service._generate_unique_token(db_session)
        token_b, hash_b = order_service._generate_unique_token(db_session)
        assert token_a != token_b
        assert hash_a != hash_b
