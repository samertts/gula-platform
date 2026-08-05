"""Unit tests for claims_service — insurance claim lifecycle with lab isolation.

Covers: create_claim (idempotency, lab/patient validation, total calc),
validate_claim (status/items/amount checks), submit_claim (status transition +
outbox emit), get_claim (lab isolation), _get_claim_or_raise.
"""

from __future__ import annotations

import os
from decimal import Decimal
from unittest.mock import patch

os.environ.setdefault("ENV", "test")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production-" + "x" * 32)
os.environ.setdefault("ENCRYPTION_KEY", "6TJUTgJxBREYK9_yDy6VMXBw1HPwwxv1kiynV0WaAdw=")
os.environ.setdefault("NID_HMAC_KEY", "a" * 64)
os.environ.setdefault("REDIS_URL", "")

import pytest
from app.database import Base
from app.models.claim import Claim, ClaimItem
from app.models.lab import Lab
from app.models.patient import Patient
from app.services import claims_service
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
    lab = Lab(name="Claims Lab", city="Baghdad", lab_type="private", is_active=True)
    db_session.add(lab)
    db_session.commit()
    db_session.refresh(lab)
    return lab


@pytest.fixture
def patient(lab, db_session):
    p = Patient(lab_id=lab.id, full_name="Claim Patient", phone="07701110000")
    db_session.add(p)
    db_session.commit()
    db_session.refresh(p)
    return p


ITEMS = [
    {"test_code": "CBC", "description": "Complete blood count",
     "quantity": 1, "unit_price": "5000", "amount": "5000"},
    {"test_code": "GLU", "description": "Glucose", "quantity": 2,
     "unit_price": "3000", "amount": "6000"},
]


# ─── create_claim ──────────────────────────────────────────────────────────────


def test_create_claim_creates_draft_with_total(db_session, lab, patient):
    claim = claims_service.create_claim(
        db_session, lab.id, patient.id, ITEMS,
    )
    db_session.refresh(claim)
    assert claim.status == "draft"
    assert claim.total_amount == Decimal("11000")
    assert claim.currency == "IQD"
    assert len(claim.items) == 2
    assert claim.items[0].test_code == "CBC"


def test_create_claim_sums_decimal_amounts(db_session, lab, patient):
    claim = claims_service.create_claim(
        db_session, lab.id, patient.id,
        [{"test_code": "A", "unit_price": "0.50", "amount": "0.50"},
         {"test_code": "B", "unit_price": "0.25", "amount": "0.25"}],
    )
    db_session.refresh(claim)
    assert claim.total_amount == Decimal("0.75")


def test_create_claim_idempotent_return(db_session, lab, patient):
    first = claims_service.create_claim(
        db_session, lab.id, patient.id, ITEMS, idempotency_key="key-123",
    )
    second = claims_service.create_claim(
        db_session, lab.id, patient.id, ITEMS, idempotency_key="key-123",
    )
    assert first.id == second.id
    count = db_session.query(Claim).count()
    assert count == 1


def test_create_claim_idempotency_scoped_per_lab(db_session, lab):
    other = Lab(name="Other", city="Basra", lab_type="public", is_active=True)
    db_session.add(other)
    db_session.commit()
    p1 = Patient(lab_id=lab.id, full_name="P1", phone="07701110001")
    p2 = Patient(lab_id=other.id, full_name="P2", phone="07701110002")
    db_session.add_all([p1, p2])
    db_session.commit()

    claims_service.create_claim(
        db_session, lab.id, p1.id, ITEMS, idempotency_key="shared-key",
    )
    second = claims_service.create_claim(
        db_session, other.id, p2.id, ITEMS, idempotency_key="shared-key",
    )
    assert second.id is not None
    assert second.lab_id == other.id


def test_create_claim_rejects_cross_lab_patient(db_session, lab, patient):
    other = Lab(name="Other", city="Basra", lab_type="public", is_active=True)
    db_session.add(other)
    db_session.commit()

    with pytest.raises(ValueError, match="not found"):
        claims_service.create_claim(db_session, other.id, patient.id, ITEMS)


def test_create_claim_missing_patient_raises(db_session, lab):
    with pytest.raises(ValueError, match="not found"):
        claims_service.create_claim(db_session, lab.id, 9999, ITEMS)


def test_create_claim_single_item(db_session, lab, patient):
    claim = claims_service.create_claim(
        db_session, lab.id, patient.id,
        [{"test_code": "HBA1C", "unit_price": "7000", "amount": "7000"}],
    )
    db_session.refresh(claim)
    assert claim.total_amount == Decimal("7000")
    assert len(claim.items) == 1


# ─── validate_claim ────────────────────────────────────────────────────────────


def test_validate_claim_transitions_to_validated(db_session, lab, patient):
    claim = claims_service.create_claim(db_session, lab.id, patient.id, ITEMS)
    validated = claims_service.validate_claim(db_session, claim.id, lab.id)
    assert validated.status == "validated"


def test_validate_claim_wrong_status_raises(db_session, lab, patient):
    claim = claims_service.create_claim(db_session, lab.id, patient.id, ITEMS)
    claims_service.validate_claim(db_session, claim.id, lab.id)
    with pytest.raises(ValueError, match="expected 'draft'"):
        claims_service.validate_claim(db_session, claim.id, lab.id)


def test_validate_claim_no_items_raises(db_session, lab, patient):
    claim = Claim(
        lab_id=lab.id, patient_id=patient.id, status="draft", total_amount=Decimal("0"),
    )
    db_session.add(claim)
    db_session.commit()

    with pytest.raises(ValueError, match="no items"):
        claims_service.validate_claim(db_session, claim.id, lab.id)


def test_validate_claim_rejects_negative_amount(db_session, lab, patient):
    claim = Claim(
        lab_id=lab.id, patient_id=patient.id, status="draft", total_amount=Decimal("10"),
    )
    db_session.add(claim)
    db_session.flush()
    db_session.add(ClaimItem(
        claim_id=claim.id, test_code="X", quantity=1,
        unit_price=Decimal("10"), amount=Decimal("-5"),
    ))
    db_session.commit()

    with pytest.raises(ValueError, match="non-positive amount"):
        claims_service.validate_claim(db_session, claim.id, lab.id)


def test_validate_claim_rejects_negative_unit_price(db_session, lab, patient):
    claim = Claim(
        lab_id=lab.id, patient_id=patient.id, status="draft", total_amount=Decimal("10"),
    )
    db_session.add(claim)
    db_session.flush()
    db_session.add(ClaimItem(
        claim_id=claim.id, test_code="X", quantity=1,
        unit_price=Decimal("0"), amount=Decimal("10"),
    ))
    db_session.commit()

    with pytest.raises(ValueError, match="non-positive unit_price"):
        claims_service.validate_claim(db_session, claim.id, lab.id)


# ─── submit_claim ──────────────────────────────────────────────────────────────


def test_submit_claim_transitions_and_emits_outbox(db_session, lab, patient):
    claim = claims_service.create_claim(db_session, lab.id, patient.id, ITEMS)
    claims_service.validate_claim(db_session, claim.id, lab.id)

    with patch("app.services.claims_service.emit_to_outbox") as emit:
        submitted = claims_service.submit_claim(db_session, claim.id, lab.id)

    assert submitted.status == "submitted"
    assert submitted.submitted_at is not None
    emit.assert_called_once()
    payload = emit.call_args.kwargs["payload"]
    assert payload["claim_id"] == claim.id
    assert payload["lab_id"] == lab.id
    assert payload["total_amount"] == "11000.00"
    assert len(payload["items"]) == 2


def test_submit_claim_requires_validated(db_session, lab, patient):
    claim = claims_service.create_claim(db_session, lab.id, patient.id, ITEMS)
    with pytest.raises(ValueError, match="expected 'validated'"):
        claims_service.submit_claim(db_session, claim.id, lab.id)


# ─── get_claim / isolation ─────────────────────────────────────────────────────


def test_get_claim_returns_for_owning_lab(db_session, lab, patient):
    claim = claims_service.create_claim(db_session, lab.id, patient.id, ITEMS)
    assert claims_service.get_claim(db_session, claim.id, lab.id).id == claim.id


def test_get_claim_raises_for_other_lab(db_session, lab, patient):
    other = Lab(name="Other", city="Basra", lab_type="public", is_active=True)
    db_session.add(other)
    db_session.commit()
    claim = claims_service.create_claim(db_session, lab.id, patient.id, ITEMS)

    with pytest.raises(ValueError, match="not found"):
        claims_service.get_claim(db_session, claim.id, other.id)


def test_get_claim_missing_raises(db_session, lab):
    with pytest.raises(ValueError, match="not found"):
        claims_service.get_claim(db_session, 9999, lab.id)
