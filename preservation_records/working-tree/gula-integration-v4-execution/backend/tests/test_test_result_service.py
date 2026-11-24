from __future__ import annotations

import os

os.environ.setdefault("ENV", "test")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production-" + "x" * 32)
os.environ.setdefault("ENCRYPTION_KEY", "6TJUTgJxBREYK9_yDy6VMXBw1HPwwxv1kiynV0WaAdw=")
os.environ.setdefault("REDIS_URL", "")

from datetime import datetime

import pytest
from app._compat import UTC
from app.database import Base
from app.services.test_result_service import derive_status, result_dict, validate_payload
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


class FakeOrder:
    def __init__(self, status="pending", validated_by=None, validated_at=None):
        self.status = status
        self.validated_by = validated_by
        self.validated_at = validated_at
        self.patient = None
        self.samples = []


class FakePatient:
    def __init__(self, health_id="HD-001", full_name="Test Patient"):
        self.health_id = health_id
        self.full_name = full_name


class FakeTestType:
    def __init__(self, test_code="T001", test_name="Glucose", category="Chemistry", unit="mg/dL",
                 normal_range_low=70.0, normal_range_high=110.0):
        self.test_code = test_code
        self.test_name = test_name
        self.category = category
        self.unit = unit
        self.normal_range_low = normal_range_low
        self.normal_range_high = normal_range_high


class FakeResult:
    def __init__(self, order=None, test_name="Glucose", value=100.0, value_text=None,
                 unit="mg/dL", normal_range_low=70.0, normal_range_high=110.0,
                 flag="normal", token="abc123", test_type=None, order_id=1,
                 created_at=None):
        self.order = order
        self.test_name = test_name
        self.value = value
        self.value_text = value_text
        self.unit = unit
        self.normal_range_low = normal_range_low
        self.normal_range_high = normal_range_high
        self.flag = flag
        self.token = token
        self.test_type = test_type
        self.order_id = order_id
        self.created_at = created_at or datetime.now(UTC)
        self.id = 1


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    s = Session()
    try:
        yield s
    finally:
        s.close()


def test_derive_status_none():
    assert derive_status(None) == "pending"


def test_derive_status_validated():
    assert derive_status(FakeOrder(status="validated")) == "verified"


def test_derive_status_cancelled():
    assert derive_status(FakeOrder(status="cancelled")) == "cancelled"


def test_derive_status_pending():
    assert derive_status(FakeOrder(status="pending")) == "pending"


def test_derive_status_in_progress():
    assert derive_status(FakeOrder(status="in_progress")) == "pending"


def test_result_dict_with_patient():
    o = FakeOrder(status="validated", validated_by="Dr. Ali",
                  validated_at=datetime(2026, 7, 30, 12, 0, 0, tzinfo=UTC))
    p = FakePatient()
    o.patient = p
    tt = FakeTestType()
    r = FakeResult(order=o, test_type=tt, created_at=datetime(2026, 7, 29, 10, 0, 0, tzinfo=UTC))
    d = result_dict(r, patient=p)
    assert d["health_id"] == "HD-001"
    assert d["patient_name"] == "Test Patient"
    assert d["test_name"] == "Glucose"
    assert d["value"] == 100.0
    assert d["flag"] == "normal"
    assert not d["is_critical"]
    assert not d["is_abnormal"]
    assert d["status"] == "verified"
    assert d["verified_by"] == "Dr. Ali"
    assert d["test_code"] == "T001"
    assert d["category"] == "Chemistry"
    assert d["result_token"] == "abc123"


def test_result_dict_abnormal():
    d = result_dict(FakeResult(order=FakeOrder(), flag="H"))
    assert d["flag"] == "H"
    assert d["is_abnormal"]
    assert not d["is_critical"]


def test_result_dict_critical():
    d = result_dict(FakeResult(order=FakeOrder(), flag="critical"))
    assert d["flag"] == "critical"
    assert d["is_critical"]
    assert d["is_abnormal"]


def test_result_dict_no_order():
    d = result_dict(FakeResult(order=None))
    assert d["status"] == "pending"
    assert d["health_id"] is None
    assert d["patient_name"] is None


def test_result_dict_with_sample_barcode():
    o = FakeOrder()
    o.samples = [type("Sample", (), {"barcode": "BAR-001"})()]
    d = result_dict(FakeResult(order=o))
    assert d["sample_barcode"] == "BAR-001"


def test_result_dict_no_test_type():
    d = result_dict(FakeResult(order=FakeOrder(), test_type=None))
    assert d["test_code"] is None
    assert d["category"] is None


def test_validate_payload_unit_mismatch(db):
    from app.models.test_type import TestType
    tt = TestType(test_code="T001", test_name="Glucose", unit="mg/dL", category="Chemistry")
    db.add(tt)
    db.commit()
    warnings = validate_payload("Glucose", 100.0, "mmol/L", 70.0, 110.0, "T001", db)
    codes = [w["code"] for w in warnings]
    assert "unit_mismatch" in codes


def test_validate_payload_no_warnings(db):
    from app.models.test_type import TestType
    tt = TestType(test_code="T001", test_name="Glucose", unit="mg/dL", category="Chemistry")
    db.add(tt)
    db.commit()
    warnings = validate_payload("Glucose", 100.0, "mg/dL", 70.0, 110.0, "T001", db)
    assert warnings == []


def test_validate_payload_range_inverted(db):
    from app.models.test_type import TestType
    tt = TestType(test_code="T001", test_name="Glucose", unit="mg/dL", category="Chemistry")
    db.add(tt)
    db.commit()
    warnings = validate_payload("Glucose", 100.0, "mg/dL", 110.0, 70.0, "T001", db)
    codes = [w["code"] for w in warnings]
    assert "range_inverted" in codes


def test_validate_payload_negative_value(db):
    from app.models.test_type import TestType
    tt = TestType(test_code="T001", test_name="Glucose", unit="mg/dL", category="Chemistry")
    db.add(tt)
    db.commit()
    warnings = validate_payload("Glucose", -5.0, "mg/dL", 70.0, 110.0, "T001", db)
    codes = [w["code"] for w in warnings]
    assert "negative_value" in codes


def test_validate_payload_implausibly_high(db):
    from app.models.test_type import TestType
    tt = TestType(test_code="T001", test_name="Glucose", unit="mg/dL",
                  category="Chemistry", normal_range_low=70.0, normal_range_high=110.0)
    db.add(tt)
    db.commit()
    warnings = validate_payload("Glucose", 2000.0, "mg/dL", 70.0, 110.0, "T001", db)
    codes = [w["code"] for w in warnings]
    assert "implausibly_high" in codes


def test_validate_payload_implausibly_low(db):
    from app.models.test_type import TestType
    tt = TestType(test_code="T001", test_name="Glucose", unit="mg/dL",
                  category="Chemistry", normal_range_low=70.0, normal_range_high=110.0)
    db.add(tt)
    db.commit()
    warnings = validate_payload("Glucose", 1.0, "mg/dL", 70.0, 110.0, "T001", db)
    codes = [w["code"] for w in warnings]
    assert "implausibly_low" in codes


def test_validate_payload_unknown_test_no_code(db):
    warnings = validate_payload("UnknownTest", None, "U", None, None, None, db)
    codes = [w["code"] for w in warnings]
    assert "unknown_test" in codes


def test_validate_payload_no_test_code_fallback(db):
    from app.models.test_type import TestType
    tt = TestType(test_code="T001", test_name="Glucose", unit="mg/dL", category="Chemistry")
    db.add(tt)
    db.commit()
    warnings = validate_payload("Glucose", 100.0, "mg/dL", 70.0, 110.0, None, db)
    assert warnings == []
