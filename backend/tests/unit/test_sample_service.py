"""Unit tests for sample_service — direct service layer tests."""

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
from app.domain.exceptions import NotFoundError, ValidationError
from app.models.lab import Lab
from app.models.lab_order import LabOrder
from app.models.lab_user import LabUser
from app.models.patient import Patient
from app.models.sample import Sample
from app.security.auth import hash_password
from app.services import sample_service
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
        lab_id=lab.id, name="Admin", email="admin@lab.com",
        password_hash=hash_password("pw"), role="admin", is_active=True,
    )
    db_session.add(u)
    db_session.commit()
    db_session.refresh(u)
    return u


@pytest.fixture
def patient(lab, db_session):
    p = Patient(lab_id=lab.id, full_name="Test Patient", phone="0770000000")
    db_session.add(p)
    db_session.commit()
    db_session.refresh(p)
    return p


@pytest.fixture
def order(lab, patient, db_session):
    o = LabOrder(lab_id=lab.id, patient_id=patient.id, status="pending")
    db_session.add(o)
    db_session.commit()
    db_session.refresh(o)
    return o


@pytest.fixture
def sample(lab, order, db_session):
    s = Sample(order_id=order.id, sample_type="blood", status="collected")
    db_session.add(s)
    db_session.commit()
    db_session.refresh(s)
    return s


class TestCreateSample:
    def test_create_sample_success(self, db_session, lab, order, admin_user):
        result = sample_service.create_sample(
            db_session, lab.id, order.id, "blood",
            "Tech", "no notes", "fridge A", admin_user,
        )
        assert result["sample"]["sample_type"] == "blood"
        assert result["sample"]["order_id"] == order.id

    def test_create_sample_invalid_type(self, db_session, lab, order, admin_user):
        with pytest.raises(ValidationError):
            sample_service.create_sample(
                db_session, lab.id, order.id, "invalid_type",
                None, None, None, admin_user,
            )

    def test_create_sample_order_not_found(self, db_session, lab, admin_user):
        with pytest.raises(NotFoundError):
            sample_service.create_sample(
                db_session, lab.id, 99999, "blood",
                None, None, None, admin_user,
            )

    def test_create_sample_other_lab_order(self, db_session, lab, admin_user, patient):
        other_lab = Lab(name="Other Lab", city="Basra", lab_type="private", is_active=True)
        db_session.add(other_lab)
        db_session.commit()
        other_order = LabOrder(lab_id=other_lab.id, patient_id=patient.id, status="pending")
        db_session.add(other_order)
        db_session.commit()
        with pytest.raises(NotFoundError):
            sample_service.create_sample(
                db_session, lab.id, other_order.id, "blood",
                None, None, None, admin_user,
            )


class TestListSamples:
    def test_list_samples_by_lab(self, db_session, lab, order, sample, admin_user):
        result = sample_service.list_samples(db_session, lab.id)
        assert result["total"] >= 1
        assert result["samples"][0]["barcode"] == sample.barcode

    def test_list_samples_other_lab_excluded(self, db_session, lab, order, sample, admin_user):
        other_lab = Lab(name="Other", city="Basra", lab_type="private", is_active=True)
        db_session.add(other_lab)
        db_session.commit()
        result = sample_service.list_samples(db_session, other_lab.id)
        assert result["total"] == 0

    def test_list_samples_filter_by_status(self, db_session, lab, order, sample, admin_user):
        result = sample_service.list_samples(db_session, lab.id, status="collected")
        assert result["total"] >= 1
        result2 = sample_service.list_samples(db_session, lab.id, status="analyzed")
        assert result2["total"] == 0

    def test_list_samples_pagination(self, db_session, lab, order, admin_user):
        for _i in range(3):
            s = Sample(order_id=order.id, sample_type="blood", status="collected")
            db_session.add(s)
        db_session.commit()
        result = sample_service.list_samples(db_session, lab.id, skip=0, limit=2)
        assert len(result["samples"]) == 2
        assert result["total"] >= 3


class TestGetSample:
    def test_get_sample_by_barcode(self, db_session, lab, sample, admin_user):
        result = sample_service.get_sample(db_session, lab.id, sample.barcode)
        assert result["id"] == sample.id

    def test_get_sample_not_found(self, db_session, lab, admin_user):
        with pytest.raises(NotFoundError):
            sample_service.get_sample(db_session, lab.id, "NONEXISTENT")

    def test_get_sample_other_lab(self, db_session, lab, sample, admin_user):
        other_lab = Lab(name="Other", city="Basra", lab_type="private", is_active=True)
        db_session.add(other_lab)
        db_session.commit()
        with pytest.raises(NotFoundError):
            sample_service.get_sample(db_session, other_lab.id, sample.barcode)


class TestUpdateSample:
    def test_update_status(self, db_session, lab, sample, admin_user):
        result = sample_service.update_sample(
            db_session, lab.id, sample.barcode,
            status="analyzed", rejection_reason=None,
            notes=None, storage_location=None,
            current_user=admin_user,
        )
        assert result["sample"]["status"] == "analyzed"

    def test_update_rejection_requires_reason(self, db_session, lab, sample, admin_user):
        with pytest.raises(ValidationError):
            sample_service.update_sample(
                db_session, lab.id, sample.barcode,
                status="rejected", rejection_reason="",
                notes=None, storage_location=None,
                current_user=admin_user,
            )

    def test_update_sample_not_found(self, db_session, lab, admin_user):
        with pytest.raises(NotFoundError):
            sample_service.update_sample(
                db_session, lab.id, "NONEXISTENT",
                status="analyzed", rejection_reason=None,
                notes=None, storage_location=None,
                current_user=admin_user,
            )

    def test_update_other_lab_sample(self, db_session, lab, sample, admin_user):
        other_lab = Lab(name="Other", city="Basra", lab_type="private", is_active=True)
        db_session.add(other_lab)
        db_session.commit()
        with pytest.raises(NotFoundError):
            sample_service.update_sample(
                db_session, other_lab.id, sample.barcode,
                status="analyzed", rejection_reason=None,
                notes=None, storage_location=None,
                current_user=admin_user,
            )

    def test_update_notes(self, db_session, lab, sample, admin_user):
        result = sample_service.update_sample(
            db_session, lab.id, sample.barcode,
            status=None, rejection_reason=None,
            notes="Updated notes", storage_location="Fridge B",
            current_user=admin_user,
        )
        assert result["sample"]["notes"] == "Updated notes"
        assert result["sample"]["storage_location"] == "Fridge B"


class TestConstants:
    def test_valid_sample_types(self):
        assert "blood" in sample_service.VALID_SAMPLE_TYPES
        assert "urine" in sample_service.VALID_SAMPLE_TYPES
        assert "csf" in sample_service.VALID_SAMPLE_TYPES

    def test_valid_statuses(self):
        for s in ["collected", "received", "processing", "analyzed", "rejected"]:
            assert s in sample_service.VALID_STATUSES
