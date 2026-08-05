"""Regression tests for PROGRAM-04 E2E findings.

PROD-BUG-001: patients.health_id was varchar(20) but the generator emits
              GULA-{16 hex} = 21 chars → patient creation failed on Postgres.
PROD-BUG-002: patients/canonical_patients/citizens.gender were varchar(1)
              but the API contract stores 'male'/'female' (and MPI 'MALE').
PROD-BUG-003: TestResultCreate.health_id Pydantic max_length=20 rejected
              valid 21-char health_ids.

All three were fixed by widening columns to (32/10) and schema bounds.
These tests pin the contract so any regression is caught.
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
from app.database import Base
from app.models.lab_user import LabUser
from app.models.patient import Patient
from app.routes.test_results import TestResultCreate
from app.models.mpi import Citizen
from app.services.patient_service import create_patient
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool


@pytest.fixture(scope="function")
def db() -> Session:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def admin(db: Session) -> LabUser:
    user = LabUser(
        name="Admin",
        email=f"a{id(db)}@test.local",
        role="admin",
        lab_id=1,
        password_hash="x" * 60,
    )
    db.add(user)
    db.commit()
    return user


class TestHealthIdWidth:
    """PROD-BUG-001: 21-char health_id must round-trip through the model."""

    def test_generator_produces_21_chars(self) -> None:
        import re
        import secrets

        hid = f"GULA-{secrets.token_hex(8).upper()}"
        assert len(hid) == 21

    def test_column_widened_to_32(self) -> None:
        col = Patient.__table__.c.health_id
        assert col.type.length == 32, f"expected String(32), got {col.type.length}"

    def test_21_char_health_id_persists(self, db: Session) -> None:
        hid = "GULA-A0BC16D0DC48032D"
        patient = Patient(
            lab_id=1,
            full_name="Width Test",
            phone="07700000000",
            gender="male",
            health_id=hid,
        )
        db.add(patient)
        db.commit()
        db.refresh(patient)
        assert patient.health_id == hid
        assert len(patient.health_id) == 21


class TestGenderWidth:
    """PROD-BUG-002: full gender strings must persist."""

    def test_patients_gender_column_widened(self) -> None:
        assert Patient.__table__.c.gender.type.length == 10

    def test_male_persists(self, db: Session) -> None:
        p = Patient(lab_id=1, full_name="G1", phone="07700000001", gender="male")
        db.add(p)
        db.commit()
        db.refresh(p)
        assert p.gender == "male"

    def test_female_persists(self, db: Session) -> None:
        p = Patient(lab_id=1, full_name="G2", phone="07700000002", gender="female")
        db.add(p)
        db.commit()
        db.refresh(p)
        assert p.gender == "female"

    def test_citizen_gender_column_widened(self) -> None:
        assert Citizen.__table__.c.gender.type.length == 10

    def test_citizen_male_persists(self, db: Session) -> None:
        c = Citizen(
            citizen_ulid="01KZTEST123456789012345678",
            nid_verified=False,
            gender="MALE",
            name_canonical="test citizen",
            name_blocking_key="test",
            status="active",
            version=1,
        )
        db.add(c)
        db.commit()
        db.refresh(c)
        assert c.gender == "MALE"


class TestResultCreateHealthIdBound:
    """PROD-BUG-003: 21-char health_id accepted by the API schema."""

    def test_21_char_health_id_valid(self) -> None:
        req = TestResultCreate(
            health_id="GULA-A0BC16D0DC48032D",
            test_name="Hemoglobin",
            value=13.5,
        )
        assert req.health_id == "GULA-A0BC16D0DC48032D"

    def test_32_char_health_id_valid(self) -> None:
        req = TestResultCreate(
            health_id="GULA-" + "A" * 27,
            test_name="Hemoglobin",
            value=13.5,
        )
        assert len(req.health_id) == 32

    def test_over_32_rejected(self) -> None:
        with pytest.raises(ValidationError):
            TestResultCreate(
                health_id="GULA-" + "A" * 40,
                test_name="Hemoglobin",
                value=13.5,
            )


class TestCreatePatientContract:
    """End-to-end creation path used by the P4 E2E probe."""

    def test_create_patient_returns_21_char_health_id(self, db: Session, admin: LabUser) -> None:
        result = create_patient(
            db=db,
            lab_id=1,
            user_id=admin.id,
            user_role=admin.role,
            full_name="E2E Contract",
            phone="07701234567",
            gender="male",
            national_id="1234567890123",
            force_create=True,
        )
        if isinstance(result, dict) and result.get("error"):
            pytest.fail(f"create failed: {result}")
        patient = result.get("patient")
        assert patient is not None
        assert patient["health_id"] is not None
        assert len(patient["health_id"]) == 21
        assert patient["gender"] == "male"
