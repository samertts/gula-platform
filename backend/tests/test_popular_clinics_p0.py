from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.domain.exceptions import ConflictError
from app.factory import import_all_models
from app.financial.models import FinBase
from app.models.lab import Lab
from app.models.lab_user import LabUser
from app.models.patient import Patient
from app.models.popular_clinic import PopularClinic
from app.services.popular_clinics import PopularClinicService
from app.database import Base


import_all_models()


@pytest.fixture()
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    FinBase.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False)()
    try:
        yield session
    finally:
        session.close()
        FinBase.metadata.drop_all(engine)
        Base.metadata.drop_all(engine)
        engine.dispose()


def seed(db):
    lab = Lab(name="P0 Lab", lab_type="government", is_active=True)
    db.add(lab)
    db.flush()
    actor = LabUser(
        lab_id=lab.id,
        name="P0 Operator",
        email="p0-operator@example.gov",
        password_hash="test-only",
        role="lab_admin",
        is_active=True,
    )
    patient = Patient(lab_id=lab.id, full_name="P0 Patient", phone="0711111111", health_id="P0-001")
    db.add_all([actor, patient])
    db.flush()
    service = PopularClinicService(db)
    clinic = service.create_clinic(
        lab_id=lab.id,
        province_id=1,
        administrative_unit_code="P0-UNIT",
        name="P0 Clinic",
    )
    service.create_service(
        clinic,
        service_code="CHRONIC_DISPENSE",
        name="Monthly chronic medication quota",
        category="chronic",
        price_cash=Decimal("3250.00"),
        price_electronic=Decimal("3000.00"),
    )
    db.flush()
    return service, lab, actor, patient, clinic


def test_monthly_dispensing_is_atomic_and_one_per_month(db):
    service, _lab, actor, patient, clinic = seed(db)
    profile = service.create_profile(
        clinic,
        actor,
        patient_id=patient.id,
        attending_doctor_id=actor.id,
        conditions=["hypertension"],
        enrolled_at=date(2026, 8, 1),
    )
    plan = service.create_treatment_plan(
        clinic,
        actor,
        patient_profile_id=profile.id,
        medication_name="Amlodipine",
        quantity=30,
        dosage="10mg once daily",
        valid_from=date(2026, 8, 1),
    )
    service.dispense(
        clinic,
        actor,
        patient_id=patient.id,
        treatment_plan_id=plan.id,
        dispense_year=2026,
        dispense_month=8,
        medication_name="Amlodipine",
        quantity=30,
        dosage="10mg once daily",
    )
    with pytest.raises(ConflictError, match="only one medication quota"):
        service.dispense(
            clinic,
            actor,
            patient_id=patient.id,
            treatment_plan_id=plan.id,
            dispense_year=2026,
            dispense_month=8,
            medication_name="Amlodipine",
            quantity=30,
            dosage="10mg once daily",
        )


def test_ticket_prices_and_cash_electronic_capture_are_separated(db):
    service, lab, actor, patient, clinic = seed(db)
    cash_ticket = service.issue_ticket(
        clinic,
        actor,
        patient_id=patient.id,
        service_code="CHRONIC_DISPENSE",
        payment_method="cash",
    )
    electronic_ticket = service.issue_ticket(
        clinic,
        actor,
        patient_id=patient.id,
        service_code="CHRONIC_DISPENSE",
        payment_method="electronic",
    )
    assert cash_ticket.amount == Decimal("3250.00")
    assert electronic_ticket.amount == Decimal("3000.00")

    from app.payments.service import PaymentService

    shift = PaymentService(db).open_cash_shift(
        institution_id=lab.id,
        cashier_user_id=actor.id,
        terminal_reference="P0-TERM",
        opening_float=Decimal("0.00"),
    )
    service.capture_cash(clinic, actor, cash_ticket.id, shift.id, "P0-CASH-001")
    service.confirm_electronic(clinic, actor, electronic_ticket.id, "gula_internal", "P0-ELEC-001")
    report = service.daily_report(clinic, date.today())

    assert cash_ticket.status == "paid"
    assert electronic_ticket.status == "paid"
    assert report["cash_total"] == Decimal("3250.00")
    assert report["electronic_total"] == Decimal("3000.00")


def test_popular_clinic_rbac_separates_cashier_and_clinical_permissions():
    from shared.rbac.permissions import has_permission_str

    assert has_permission_str("cashier", "popular_clinics:payment:capture")
    assert not has_permission_str("cashier", "popular_clinics:clinical:write")
    assert has_permission_str("doctor", "popular_clinics:prescription:write")
    assert not has_permission_str("doctor", "popular_clinics:payment:capture")
    assert has_permission_str("lab_staff", "popular_clinics:dispense:record")
    assert not has_permission_str("lab_staff", "popular_clinics:prescription:write")
    assert has_permission_str("receptionist", "popular_clinics:ticket:issue")
    assert not has_permission_str("receptionist", "popular_clinics:payment:capture")
