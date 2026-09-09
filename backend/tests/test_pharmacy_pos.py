from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Any

import pytest
from app.billing.models import BillingInvoice
from app.ehr.models.medication import MedicationDispense
from app.models.lab import Lab
from app.models.patient import Patient
from app.national import domain as _national_domain_models
from app.pharmacy.models import (
    DrugBatch,
    DrugCatalog,
    DrugSubstitutionRequest,
    DrugSubstitutionRule,
    PharmacySale,
    StockLevel,
)
from app.pharmacy.services import PharmacyService

# Importing these classes registers the cross-domain NationalBase tables before
# the shared test DDL and SQLAlchemy mapper configuration run.
NATIONAL_MODEL_REGISTRY = (_national_domain_models.Patient, _national_domain_models.Practitioner)

# pharmacy_stock_movements.performed_by is NOT NULL — an inventory change is
# always somebody's action, so these tests act as a real pharmacist.
PHARMACIST_ID = 4242


def _seed_pos(db: Any) -> tuple[Any, Any, Any, Any, Any]:
    lab = Lab(name="POS Test Lab", lab_type="pharmacy")
    db.add(lab)
    db.flush()
    patient = Patient(lab_id=lab.id, full_name="Synthetic Citizen", phone="0000000000")
    db.add(patient)
    db.flush()
    # The catalog is global: no lab_id. Field names follow the physical schema.
    drug = DrugCatalog(
        drug_code="SYN-PAR-500",
        drug_name="Synthetic Paracetamol",
        drug_name_ar="باراسيتامول اصطناعي",
        generic_name="Paracetamol",
        dosage_form="tablet",
        is_active=True,
        requires_prescription=False,
    )
    db.add(drug)
    db.flush()
    first_batch = DrugBatch(
        lab_id=lab.id,
        drug_id=drug.id,
        batch_number="BATCH-EXPIRING",
        expiry_date=date.today() + timedelta(days=30),
        quantity_received=2,
        quantity_remaining=2,
        unit_cost=Decimal("2.00"),
        selling_price=Decimal("5.00"),
        is_quarantined=False,
        received_date=datetime.now(UTC),
        status="active",
    )
    second_batch = DrugBatch(
        lab_id=lab.id,
        drug_id=drug.id,
        batch_number="BATCH-LATER",
        expiry_date=date.today() + timedelta(days=180),
        quantity_received=5,
        quantity_remaining=5,
        unit_cost=Decimal("2.50"),
        selling_price=Decimal("5.50"),
        is_quarantined=False,
        received_date=datetime.now(UTC),
        status="active",
    )
    db.add_all([first_batch, second_batch])
    db.flush()
    db.add_all([
        StockLevel(lab_id=lab.id, drug_id=drug.id, batch_id=first_batch.id, quantity_on_hand=2, quantity_reserved=0, quantity_available=2, unit="unit"),
        StockLevel(lab_id=lab.id, drug_id=drug.id, batch_id=second_batch.id, quantity_on_hand=5, quantity_reserved=0, quantity_available=5, unit="unit"),
    ])
    db.flush()
    return lab, patient, drug, first_batch, second_batch


def test_pos_sale_uses_fefo_and_writes_billing_and_dispense(db: Any) -> None:
    lab, patient, drug, first_batch, second_batch = _seed_pos(db)
    sale = PharmacyService(db, user_id=PHARMACIST_ID, lab_id=lab.id).create_pos_sale(
        {
            "patient_id": "SYNTHETIC-NATIONAL-PATIENT",
            "citizen_id": "SYNTHETIC-CITIZEN-001",
            "billing_patient_id": patient.id,
            "encounter_ref": "SYNTHETIC-POS-001",
            "idempotency_key": "pos-test-001",
            "lines": [{"drug_catalog_id": str(drug.drug_id), "quantity": 3}],
        },
        request_id="req-pos-test",
    )
    assert sale.sale_number.startswith("GULA-POS-")
    assert sale.total_amount == Decimal("15.50")
    assert sale.cost_amount == Decimal("6.50")
    assert sale.gross_profit == Decimal("9.00")
    assert sale.billing_invoice_id is not None
    assert db.query(BillingInvoice).filter(BillingInvoice.id == sale.billing_invoice_id).one().status == "paid"
    assert len(sale.lines) == 2
    assert sale.lines[0].lot_number == first_batch.batch_number
    assert sale.lines[0].quantity == 2
    assert sale.lines[1].lot_number == second_batch.batch_number
    assert sale.lines[1].quantity == 1
    assert db.query(MedicationDispense).filter(MedicationDispense.citizen_id == "SYNTHETIC-CITIZEN-001").count() == 2
    summary = PharmacyService(db, user_id=PHARMACIST_ID, lab_id=lab.id).get_pos_summary(30)
    assert summary["sale_count"] == 1
    assert summary["units_sold"] == 3
    assert summary["sales_total"] == "15.50"
    assert summary["gross_profit"] == "9.00"


def test_pos_sale_is_idempotent_and_does_not_double_decrement(db: Any) -> None:
    lab, patient, drug, _first_batch, _second_batch = _seed_pos(db)
    service = PharmacyService(db, user_id=PHARMACIST_ID, lab_id=lab.id)
    payload = {
        "patient_id": "SYNTHETIC-PATIENT-002",
        "billing_patient_id": patient.id,
        "idempotency_key": "pos-test-idempotent",
        "lines": [{"drug_catalog_id": str(drug.drug_id), "quantity": 1}],
    }
    first = service.create_pos_sale(payload)
    second = service.create_pos_sale(payload)
    assert first.id == second.id
    assert db.query(PharmacySale).filter(PharmacySale.lab_id == lab.id).count() == 1
    stock = db.query(StockLevel).filter(StockLevel.lab_id == lab.id, StockLevel.batch_id == first.lines[0].batch_id).one()
    assert stock.quantity_on_hand == 1


def test_approved_substitution_is_consumed_by_pos_and_audited(db: Any) -> None:
    lab, patient, original, _first_batch, _second_batch = _seed_pos(db)
    alternative = DrugCatalog(
        drug_code="SYN-ALT-500",
        drug_name="Synthetic Alternative",
        drug_name_ar="بديل اصطناعي",
        generic_name="Paracetamol",
        dosage_form="tablet",
        strength="500",
        unit="mg",
        is_active=True,
        requires_prescription=False,
    )
    db.add(alternative)
    db.flush()
    alt_batch = DrugBatch(
        lab_id=lab.id,
        drug_id=alternative.id,
        batch_number="ALT-BATCH-001",
        expiry_date=date.today() + timedelta(days=180),
        quantity_received=4,
        quantity_remaining=4,
        unit_cost=Decimal("3.00"),
        selling_price=Decimal("6.00"),
        is_quarantined=False,
        received_date=datetime.now(UTC),
        status="active",
    )
    db.add(alt_batch)
    db.flush()
    db.add(StockLevel(
        lab_id=lab.id,
        drug_id=alternative.id,
        batch_id=alt_batch.id,
        quantity_on_hand=4,
        quantity_reserved=0,
        quantity_available=4,
        unit="unit",
    ))
    rule = DrugSubstitutionRule(
        lab_id=lab.id,
        original_drug_catalog_id=original.id,
        alternative_drug_catalog_id=alternative.id,
        equivalence_type="generic",
        approval_level="pharmacist",
        requires_patient_consent=True,
        is_active=True,
        created_by=None,
        updated_by=None,
    )
    db.add(rule)
    db.flush()
    service = PharmacyService(db, user_id=PHARMACIST_ID, lab_id=lab.id)
    with pytest.raises(ValueError, match="patient or prescription context"):
        service.create_substitution_request({
            "rule_id": str(rule.substitution_rule_id),
            "quantity": 1,
            "patient_consent": True,
        })
    request = service.create_substitution_request({
        "rule_id": str(rule.substitution_rule_id),
        "patient_id": str(patient.id),
        "citizen_id": "SYNTHETIC-CITIZEN-SUB-001",
        "quantity": 1,
        "reason": "original medication unavailable",
        "patient_consent": True,
        "patient_notified": True,
    })
    assert request.status == "pending"
    assert request.quantity == 1
    service.approve_substitution(str(request.substitution_request_id))
    with pytest.raises(ValueError, match="sale quantity must match"):
        service.create_pos_sale({
            "patient_id": str(patient.id),
            "citizen_id": "SYNTHETIC-CITIZEN-SUB-001",
            "billing_patient_id": patient.id,
            "idempotency_key": "pos-substitution-quantity-mismatch",
            "lines": [{"substitution_request_id": str(request.substitution_request_id), "quantity": 2}],
        })
    sale = service.create_pos_sale({
        "patient_id": str(patient.id),
        "citizen_id": "SYNTHETIC-CITIZEN-SUB-001",
        "billing_patient_id": patient.id,
        "idempotency_key": "pos-substitution-001",
        "lines": [{"substitution_request_id": str(request.substitution_request_id), "quantity": 1}],
    })
    db.refresh(request)
    db.refresh(sale)
    assert request.status == "consumed"
    assert request.consumed_sale_id == sale.id
    # Compared as integers now. M3 converted PharmacySaleLine.drug_catalog_id
    # to the catalog's INTEGER key and gave it the foreign key PostgreSQL could
    # not hold while it was varchar(26) — P0-2-SUBBLOCKER-A Group A.
    assert sale.lines[0].drug_catalog_id == alternative.id
    # Sale-line metadata is returned to callers, so it carries public
    # identifiers rather than internal keys.
    assert sale.lines[0].metadata_["original_drug_catalog_id"] == str(original.drug_id)
    assert sale.lines[0].metadata_["alternative_drug_catalog_id"] == str(alternative.drug_id)
    assert db.query(StockLevel).filter(StockLevel.batch_id == alt_batch.id).one().quantity_on_hand == 3
    assert db.query(MedicationDispense).filter(
        MedicationDispense.citizen_id == "SYNTHETIC-CITIZEN-SUB-001",
        MedicationDispense.medication_code == alternative.drug_code,
    ).count() == 1
    assert db.query(DrugSubstitutionRequest).filter(DrugSubstitutionRequest.id == request.id).one().status == "consumed"
