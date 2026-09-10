from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Any

import pytest
from app.billing.models import BillingInvoice
from app.models.lab import Lab
from app.models.patient import Patient
from app.national import domain as _national_domain_models
from app.pharmacy.models import (
    DispenseRecord,
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
    # NR-034: the dispense lands in the canonical Pharmacy table. It used to be
    # written to ehr_medication_dispenses, which no migration creates — the test
    # schema is built by create_all() from ORM metadata, so it existed here and
    # nowhere else, and this assertion passed while production could not commit.
    dispenses = db.query(DispenseRecord).filter(DispenseRecord.lab_id == lab.id).all()
    assert len(dispenses) == 2
    assert {d.drug_id for d in dispenses} == {drug.id}
    assert {d.patient_id for d in dispenses} == {patient.id}, (
        "the dispense must reference the local patients.id its foreign key accepts"
    )
    assert {d.batch_id for d in dispenses} == {first_batch.id, second_batch.id}
    assert sum(d.quantity_dispensed for d in dispenses) == 3
    assert all(d.dispensed_by == PHARMACIST_ID for d in dispenses)
    assert all(d.is_verified is False for d in dispenses), (
        "a counter sale has no independent verifier and must not claim one"
    )
    assert {line.medication_dispense_id for line in sale.lines} == {str(d.id) for d in dispenses}
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
    assert db.query(DispenseRecord).filter(
        DispenseRecord.lab_id == lab.id,
        DispenseRecord.drug_id == alternative.id,
    ).count() == 1
    assert db.query(DrugSubstitutionRequest).filter(DrugSubstitutionRequest.id == request.id).one().status == "consumed"


# ── NR-034 (MED-001): the canonical dispense owner ────────────────────────────


def test_a_sale_without_patient_context_writes_no_dispense(db: Any) -> None:
    """The case that always worked, pinned so the fix did not change it.

    An anonymous counter sale is not dispensing to a known patient, so it
    produces no dispense record — before this change and after it.
    """
    lab, patient, drug, _first, _second = _seed_pos(db)
    sale = PharmacyService(db, user_id=PHARMACIST_ID, lab_id=lab.id).create_pos_sale({
        "billing_patient_id": patient.id,
        "idempotency_key": "pos-no-patient-context",
        "lines": [{"drug_catalog_id": str(drug.drug_id), "quantity": 1}],
    })
    assert sale.sale_number.startswith("GULA-POS-")
    assert db.query(DispenseRecord).filter(DispenseRecord.lab_id == lab.id).count() == 0
    assert all(line.medication_dispense_id is None for line in sale.lines)


def test_a_sale_with_only_a_citizen_id_still_records_the_dispense(db: Any) -> None:
    """citizen_id alone must be enough — it was one of the two triggers."""
    lab, patient, drug, _first, _second = _seed_pos(db)
    sale = PharmacyService(db, user_id=PHARMACIST_ID, lab_id=lab.id).create_pos_sale({
        "citizen_id": "SYNTHETIC-CITIZEN-ONLY",
        "billing_patient_id": patient.id,
        "idempotency_key": "pos-citizen-only",
        "lines": [{"drug_catalog_id": str(drug.drug_id), "quantity": 1}],
    })
    record = db.query(DispenseRecord).filter(DispenseRecord.lab_id == lab.id).one()
    assert record.patient_id == patient.id
    assert sale.lines[0].medication_dispense_id == str(record.id)
    # The canonical identifiers stay on the sale, which is what owns them.
    assert sale.citizen_id == "SYNTHETIC-CITIZEN-ONLY"


def test_the_dispense_is_scoped_to_the_selling_laboratory(db: Any) -> None:
    """Tenant isolation: one laboratory's sale must not produce another's record."""
    lab_a, patient_a, drug, _f, _s = _seed_pos(db)
    lab_b = Lab(name="Other POS Lab", lab_type="pharmacy")
    db.add(lab_b)
    db.flush()

    PharmacyService(db, user_id=PHARMACIST_ID, lab_id=lab_a.id).create_pos_sale({
        "patient_id": "SYNTHETIC-TENANT-PROBE",
        "billing_patient_id": patient_a.id,
        "idempotency_key": "pos-tenant-a",
        "lines": [{"drug_catalog_id": str(drug.drug_id), "quantity": 1}],
    })

    assert db.query(DispenseRecord).filter(DispenseRecord.lab_id == lab_a.id).count() == 1
    assert db.query(DispenseRecord).filter(DispenseRecord.lab_id == lab_b.id).count() == 0


def test_a_failed_sale_leaves_no_dispense_and_no_stock_change(db: Any) -> None:
    """One atomic unit: a line that cannot be allocated rolls the whole sale back."""
    lab, patient, drug, _first, _second = _seed_pos(db)
    before = {
        row.batch_id: row.quantity_on_hand
        for row in db.query(StockLevel).filter(StockLevel.lab_id == lab.id).all()
    }
    service = PharmacyService(db, user_id=PHARMACIST_ID, lab_id=lab.id)

    # A nested savepoint, so only the failed sale is undone. A plain rollback
    # would discard the seed with it and prove nothing.
    savepoint = db.begin_nested()
    with pytest.raises(ValueError, match="insufficient non-expired stock"):
        service.create_pos_sale({
            "patient_id": "SYNTHETIC-ROLLBACK-PROBE",
            "billing_patient_id": patient.id,
            "idempotency_key": "pos-rollback",
            # more than the seven units the two batches hold
            "lines": [{"drug_catalog_id": str(drug.drug_id), "quantity": 99}],
        })
    savepoint.rollback()
    db.expire_all()

    assert db.query(DispenseRecord).filter(DispenseRecord.lab_id == lab.id).count() == 0
    assert db.query(PharmacySale).filter(PharmacySale.lab_id == lab.id).count() == 0
    after = {
        row.batch_id: row.quantity_on_hand
        for row in db.query(StockLevel).filter(StockLevel.lab_id == lab.id).all()
    }
    assert after == before, "a failed sale must not move stock"


def test_the_pos_path_no_longer_depends_on_an_unbuilt_ehr_table(db: Any) -> None:
    """The defect itself, asserted at the source.

    ehr_medication_dispenses exists in this test database only because the
    schema is built by create_all() from ORM metadata; no migration creates it,
    so in production the INSERT could not commit. Pharmacy must not reach for
    that model at all.
    """
    import pathlib

    from app.pharmacy import services as pharmacy_services

    source = pathlib.Path(pharmacy_services.__file__).read_text(encoding="utf-8")
    assert "from app.ehr.models.medication import" not in source, (
        "Pharmacy imports an EHR medication model again; NR-034 has regressed"
    )
    assert "MedicationDispense(" not in source, (
        "the POS path constructs an EHR dispense again; NR-034 has regressed"
    )
