from __future__ import annotations

from app.lims import models as lims_models
from fastapi import HTTPException

from app.models.integration_inbox import IntegrationInboxEvent
from app.models.lab_order import LabOrder
from app.models.patient import Patient
from app.national.api.routes.interop import (
    mhd_provide_document,
    mhd_read_document,
    mhd_search_documents,
    pix_query,
)


def test_pixm_query_returns_only_local_identifiers(db, make_lab, make_lab_user):
    lab_a = make_lab("PIXm A")
    lab_b = make_lab("PIXm B")
    user_a = make_lab_user(lab_a.id, email="pixm-a@example.com")
    patient_a = Patient(
        lab_id=lab_a.id,
        health_id="IQ-LOCAL-001",
        full_name="Synthetic Patient A",
        phone="07700000001",
    )
    patient_b = Patient(
        lab_id=lab_b.id,
        health_id="IQ-LOCAL-002",
        full_name="Synthetic Patient B",
        phone="07700000002",
    )
    db.add_all([patient_a, patient_b])
    db.flush()

    result = pix_query(
        sourceIdentifier=f"urn:gula:health-id|{patient_a.health_id}",
        targetSystem=None,
        targetIdentifier=None,
        actor=user_a,
        db=db,
    )

    values = {item["valueIdentifier"]["value"] for item in result["parameter"]}
    assert "IQ-LOCAL-001" in values
    assert "IQ-LOCAL-002" not in values

    blocked = pix_query(
        sourceIdentifier="urn:iq:national-id|raw-sensitive-value",
        targetSystem=None,
        targetIdentifier=None,
        actor=user_a,
        db=db,
    )
    assert blocked["parameter"] == []


def test_mhd_iti65_is_idempotent_and_stays_in_review_inbox(db, make_lab, make_lab_user):
    lab = make_lab("MHD Source")
    user = make_lab_user(lab.id, email="mhd-source@example.com")
    payload = {
        "resourceType": "Bundle",
        "id": "bundle-synthetic-001",
        "type": "document",
        "entry": [
            {"resource": {"resourceType": "Composition", "id": "composition-1"}},
            {"resource": {"resourceType": "DiagnosticReport", "id": "report-1"}},
        ],
    }

    first = mhd_provide_document(
        payload=payload,
        idempotency_key="mhd-idem-001",
        source_system="synthetic-hospital",
        actor=user,
        db=db,
    )
    second = mhd_provide_document(
        payload=payload,
        idempotency_key="mhd-idem-001",
        source_system="synthetic-hospital",
        actor=user,
        db=db,
    )

    assert first["status"] == "accepted"
    assert second["status"] == "already_accepted"
    event = db.query(IntegrationInboxEvent).filter(
        IntegrationInboxEvent.idempotency_key == "mhd-idem-001",
    ).one()
    assert event.status == "pending_review"
    assert event.tenant_id == str(lab.id)


def test_mhd_idempotency_is_scoped_to_recipient_lab(db, make_lab, make_lab_user):
    lab_a = make_lab("MHD Idempotency A")
    lab_b = make_lab("MHD Idempotency B")
    user_a = make_lab_user(lab_a.id, email="mhd-idem-a@example.com")
    user_b = make_lab_user(lab_b.id, email="mhd-idem-b@example.com")
    payload = {"resourceType": "Bundle", "id": "shared-bundle", "type": "document", "entry": []}

    first = mhd_provide_document(payload, "shared-key", "hospital-a", user_a, db)
    second = mhd_provide_document(payload, "shared-key", "hospital-a", user_b, db)

    assert first["status"] == "accepted"
    assert second["status"] == "accepted"
    assert first["eventId"] != second["eventId"]
    assert db.query(IntegrationInboxEvent).filter(IntegrationInboxEvent.idempotency_key == "shared-key").count() == 2


def test_mhd_document_reference_search_is_lab_scoped_and_final_only(
    db, make_lab, make_lab_user
):
    lab_a = make_lab("MHD A")
    lab_b = make_lab("MHD B")
    user_a = make_lab_user(lab_a.id, email="mhd-a@example.com")
    patient_a = Patient(lab_id=lab_a.id, full_name="MHD Patient A", phone="07700000003")
    patient_b = Patient(lab_id=lab_b.id, full_name="MHD Patient B", phone="07700000004")
    db.add_all([patient_a, patient_b])
    db.flush()

    order_a = LabOrder(patient_id=patient_a.id, lab_id=lab_a.id, status="completed")
    order_b = LabOrder(patient_id=patient_b.id, lab_id=lab_b.id, status="completed")
    db.add_all([order_a, order_b])
    db.flush()
    report_a = lims_models.LabReport(
        lab_id=lab_a.id,
        order_id=order_a.id,
        report_number="MHD-A-001",
        status="final",
        title="Synthetic final report",
    )
    report_b = lims_models.LabReport(
        lab_id=lab_b.id,
        order_id=order_b.id,
        report_number="MHD-B-001",
        status="final",
        title="Other lab report",
    )
    db.add_all([report_a, report_b])
    db.flush()

    result = mhd_search_documents(
        patient=None,
        subject=None,
        status_filter=None,
        actor=user_a,
        db=db,
    )
    ids = {entry["resource"]["id"] for entry in result["entry"]}
    assert f"gula-report-{report_a.id}" in ids
    assert f"gula-report-{report_b.id}" not in ids
    assert result["total"] == 1

    read_by_clinical_id = mhd_read_document(
        report_id=f"gula-report-{report_a.id}",
        actor=user_a,
        db=db,
    )
    assert read_by_clinical_id["id"] == f"gula-report-{report_a.id}"
    assert read_by_clinical_id["subject"]["reference"] == f"Patient/{patient_a.id}"

    read_by_numeric_id = mhd_read_document(
        report_id=str(report_a.id),
        actor=user_a,
        db=db,
    )
    assert read_by_numeric_id["id"] == f"gula-report-{report_a.id}"

    try:
        mhd_read_document(report_id=str(report_b.id), actor=user_a, db=db)
    except HTTPException as exc:
        assert exc.status_code == 404
    else:
        raise AssertionError("cross-lab MHD read must be denied")
