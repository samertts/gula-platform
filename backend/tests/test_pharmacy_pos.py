from datetime import date, timedelta
from decimal import Decimal
from typing import Any

from app.billing.models import BillingInvoice
from app.ehr.models.medication import MedicationDispense
from app.models.lab import Lab
from app.models.patient import Patient
from app.national import domain as _national_domain_models
from app.pharmacy.models import DrugBatch, DrugCatalog, PharmacySale, StockLevel
from app.pharmacy.services import PharmacyService

# Importing these classes registers the cross-domain NationalBase tables before
# the shared test DDL and SQLAlchemy mapper configuration run.
NATIONAL_MODEL_REGISTRY = (_national_domain_models.Patient, _national_domain_models.Practitioner)


def _seed_pos(db: Any) -> tuple[Any, Any, Any, Any, Any]:
    lab = Lab(name="POS Test Lab", lab_type="pharmacy")
    db.add(lab)
    db.flush()
    patient = Patient(lab_id=lab.id, full_name="Synthetic Citizen", phone="0000000000")
    db.add(patient)
    db.flush()
    drug = DrugCatalog(
        lab_id=lab.id,
        code="SYN-PAR-500",
        name="Synthetic Paracetamol",
        name_ar="باراسيتامول اصطناعي",
        generic_name="Paracetamol",
        barcode_gs1="890000000001",
        is_active=True,
        requires_prescription=False,
    )
    db.add(drug)
    db.flush()
    first_batch = DrugBatch(
        lab_id=lab.id,
        drug_catalog_id=drug.id,
        batch_number="BATCH-EXPIRING",
        expiry_date=date.today() + timedelta(days=30),
        quantity_initial=2,
        quantity_remaining=2,
        cost_price=Decimal("2.00"),
        selling_price=Decimal("5.00"),
        is_quarantined=False,
    )
    second_batch = DrugBatch(
        lab_id=lab.id,
        drug_catalog_id=drug.id,
        batch_number="BATCH-LATER",
        expiry_date=date.today() + timedelta(days=180),
        quantity_initial=5,
        quantity_remaining=5,
        cost_price=Decimal("2.50"),
        selling_price=Decimal("5.50"),
        is_quarantined=False,
    )
    db.add_all([first_batch, second_batch])
    db.flush()
    db.add_all([
        StockLevel(lab_id=lab.id, drug_catalog_id=drug.id, batch_id=first_batch.id, quantity=2, reserved_quantity=0, available_quantity=2),
        StockLevel(lab_id=lab.id, drug_catalog_id=drug.id, batch_id=second_batch.id, quantity=5, reserved_quantity=0, available_quantity=5),
    ])
    db.flush()
    return lab, patient, drug, first_batch, second_batch


def test_pos_sale_uses_fefo_and_writes_billing_and_dispense(db: Any) -> None:
    lab, patient, drug, first_batch, second_batch = _seed_pos(db)
    sale = PharmacyService(db, user_id=None, lab_id=lab.id).create_pos_sale(
        {
            "patient_id": "SYNTHETIC-NATIONAL-PATIENT",
            "citizen_id": "SYNTHETIC-CITIZEN-001",
            "billing_patient_id": patient.id,
            "encounter_ref": "SYNTHETIC-POS-001",
            "idempotency_key": "pos-test-001",
            "lines": [{"drug_catalog_id": drug.id, "quantity": 3}],
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
    summary = PharmacyService(db, user_id=None, lab_id=lab.id).get_pos_summary(30)
    assert summary["sale_count"] == 1
    assert summary["units_sold"] == 3
    assert summary["sales_total"] == "15.50"
    assert summary["gross_profit"] == "9.00"


def test_pos_sale_is_idempotent_and_does_not_double_decrement(db: Any) -> None:
    lab, patient, drug, _first_batch, _second_batch = _seed_pos(db)
    service = PharmacyService(db, user_id=None, lab_id=lab.id)
    payload = {
        "patient_id": "SYNTHETIC-PATIENT-002",
        "billing_patient_id": patient.id,
        "idempotency_key": "pos-test-idempotent",
        "lines": [{"drug_catalog_id": drug.id, "quantity": 1}],
    }
    first = service.create_pos_sale(payload)
    second = service.create_pos_sale(payload)
    assert first.id == second.id
    assert db.query(PharmacySale).filter(PharmacySale.lab_id == lab.id).count() == 1
    stock = db.query(StockLevel).filter(StockLevel.lab_id == lab.id, StockLevel.batch_id == first.lines[0].batch_id).one()
    assert stock.quantity == 1
