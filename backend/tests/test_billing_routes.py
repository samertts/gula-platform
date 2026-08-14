from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from app.models.patient import Patient
from tests.conftest import auth_headers


def _patient(db, lab_id: int, name: str = "Synthetic Patient") -> Patient:
    patient = Patient(lab_id=lab_id, full_name=name, phone="0770000000")
    db.add(patient)
    db.flush()
    return patient


def test_invoice_creation_is_idempotent_and_lab_scoped(client, db, make_lab, make_lab_user):
    lab = make_lab("Billing Lab")
    user = make_lab_user(lab.id, role="admin")
    patient = _patient(db, lab.id)
    headers = {**auth_headers(user.id, lab.id, role="admin"), "Idempotency-Key": "bill-idem-001"}
    payload = {
        "patient_id": patient.id,
        "encounter_ref": "ENC-SYN-001",
        "lines": [{"service_code": "GULA-LAB-022", "description": "Synthetic lab panel", "quantity": 2, "unit_amount": "95.00"}],
        "covered_amount": "100.00",
    }

    first = client.post("/billing/invoices", json=payload, headers=headers)
    assert first.status_code == 201, first.text
    second = client.post("/billing/invoices", json=payload, headers=headers)
    assert second.status_code == 201, second.text
    assert first.json()["id"] == second.json()["id"]
    assert first.json()["gross_amount"] == "190.00"
    assert first.json()["patient_due"] == "90.00"

    listed = client.get("/billing/invoices", headers=auth_headers(user.id, lab.id, role="admin"))
    assert listed.status_code == 200
    assert len(listed.json()) == 1


def test_settlement_creates_local_payment_and_audit_event(client, db, make_lab, make_lab_user):
    lab = make_lab("Settlement Lab")
    user = make_lab_user(lab.id, role="admin")
    patient = _patient(db, lab.id)
    headers = auth_headers(user.id, lab.id, role="admin")
    created = client.post(
        "/billing/invoices",
        json={
            "patient_id": patient.id,
            "encounter_ref": "ENC-SYN-002",
            "lines": [{"service_code": "VISIT", "description": "Synthetic visit", "quantity": 1, "unit_amount": "180.00"}],
            "covered_amount": "0.00",
        },
        headers={**headers, "Idempotency-Key": "bill-idem-002"},
    )
    assert created.status_code == 201, created.text
    invoice_id = created.json()["id"]

    settled = client.post(f"/billing/invoices/{invoice_id}/simulate-settlement", headers=headers)
    assert settled.status_code == 200, settled.text
    assert settled.json()["status"] == "paid"
    assert settled.json()["payments"][0]["method"] == "synthetic_settlement"

    payments = client.get("/billing/payments", headers=headers)
    assert payments.status_code == 200
    assert len(payments.json()) == 1
    audit = client.get("/billing/audit-events", headers=headers)
    assert audit.status_code == 200
    assert {event["action"] for event in audit.json()} >= {"created", "synthetic_settlement_recorded"}


def test_coverage_local_verification_never_calls_external_gateway(client, db, make_lab, make_lab_user):
    lab = make_lab("Coverage Lab")
    user = make_lab_user(lab.id, role="admin")
    patient = _patient(db, lab.id, name="Synthetic Coverage Patient")
    headers = auth_headers(user.id, lab.id, role="admin")

    created = client.post(
        "/billing/coverages",
        json={
            "patient_id": patient.id,
            "payer": "Synthetic Care Fund",
            "plan": "Basic-A",
            "member_id": "MBR-SYN-001",
            "expires_on": (date.today() + timedelta(days=30)).isoformat(),
        },
        headers=headers,
    )
    assert created.status_code == 201, created.text
    coverage_id = created.json()["id"]
    assert created.json()["state"] == "needs_verification"

    verified = client.post(f"/billing/coverages/{coverage_id}/verify-local", headers=headers)
    assert verified.status_code == 200, verified.text
    assert verified.json()["state"] == "active"
    assert verified.json()["verification"] == "تمت المطابقة في سجل تجريبي محلي"


def test_cross_lab_invoice_access_is_denied_by_empty_scope(client, db, make_lab, make_lab_user):
    first_lab = make_lab("First Billing Lab")
    second_lab = make_lab("Second Billing Lab")
    first_user = make_lab_user(first_lab.id, role="admin")
    second_user = make_lab_user(second_lab.id, role="admin")
    patient = _patient(db, first_lab.id)

    created = client.post(
        "/billing/invoices",
        json={
            "patient_id": patient.id,
            "encounter_ref": "ENC-SYN-003",
            "lines": [{"service_code": "VISIT", "description": "Synthetic visit", "quantity": 1, "unit_amount": "50.00"}],
            "covered_amount": "0.00",
        },
        headers={**auth_headers(first_user.id, first_lab.id, role="admin"), "Idempotency-Key": "bill-idem-003"},
    )
    assert created.status_code == 201, created.text
    invoice_id = created.json()["id"]

    scoped = client.get(f"/billing/invoices/{invoice_id}", headers=auth_headers(second_user.id, second_lab.id, role="admin"))
    assert scoped.status_code == 404
    assert client.get("/billing/invoices", headers=auth_headers(second_user.id, second_lab.id, role="admin")).json() == []
