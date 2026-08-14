"""Tenant-isolation regression tests for the LIMS administrative surface."""

from __future__ import annotations

import pytest
from app.lims import models as lims_models
from app.lims.routes import (
    InstrumentCreateRequest,
    create_instrument,
    get_interoperability_capabilities,
    list_sections,
    list_workstations,
    order_fhir_bundle,
)
from app.models.audit_log import AuditLog
from app.models.lab_order import LabOrder
from app.models.patient import Patient
from fastapi import HTTPException


@pytest.fixture()
def lims_fixture(db, make_lab, make_lab_user):
    lab_a = make_lab("Lab A")
    lab_b = make_lab("Lab B")
    user_a = make_lab_user(lab_a.id, email="a@example.com")
    user_b = make_lab_user(lab_b.id, email="b@example.com")

    department_a = lims_models.Department(
        lab_id=lab_a.id,
        code="CHEM",
        name="Chemistry",
        name_ar="الكيمياء",
    )
    department_b = lims_models.Department(
        lab_id=lab_b.id,
        code="CHEM",
        name="Chemistry B",
        name_ar="الكيمياء ب",
    )
    db.add_all([department_a, department_b])
    db.flush()

    section_a = lims_models.Section(
        department_id=department_a.id,
        code="BENCH-1",
        name="Bench A",
        name_ar="منصة أ",
    )
    section_b = lims_models.Section(
        department_id=department_b.id,
        code="BENCH-1",
        name="Bench B",
        name_ar="منصة ب",
    )
    db.add_all([section_a, section_b])
    db.flush()

    workstation_a = lims_models.Workstation(
        section_id=section_a.id,
        code="WS-A",
        name="Workstation A",
    )
    workstation_b = lims_models.Workstation(
        section_id=section_b.id,
        code="WS-B",
        name="Workstation B",
    )
    db.add_all([workstation_a, workstation_b])
    db.flush()

    return {
        "lab_a": lab_a,
        "lab_b": lab_b,
        "user_a": user_a,
        "user_b": user_b,
        "department_a": department_a,
        "department_b": department_b,
        "section_a": section_a,
        "section_b": section_b,
        "workstation_a": workstation_a,
        "workstation_b": workstation_b,
    }


def test_interoperability_capabilities_are_explicit_and_tenant_scoped(lims_fixture):
    data = get_interoperability_capabilities(current_user=lims_fixture["user_a"])

    assert data["profile"] == "gula-lims-v1"
    assert data["tenant_scope"]["required"] is True
    assert data["tenant_scope"]["lab_id"] == lims_fixture["lab_a"].id
    assert data["fhir"]["version"] == "R4"
    assert set(data["fhir"]["resources"]) == {
        "Device",
        "DiagnosticReport",
        "Observation",
        "ServiceRequest",
        "Specimen",
        "Patient",
        "Parameters",
        "DocumentReference",
        "Bundle",
    }
    transactions = {item["id"]: item for item in data["ihe"]["transactions"]}
    assert set(transactions) == {"ITI-65", "ITI-67", "ITI-68", "ITI-83"}
    assert data["ihe"]["controls"]["organisation_bound_service_account"] is True
    assert data["ihe"]["controls"]["tenant_scoped_queries"] is True
    assert data["safety"]["tenant_isolation"] is True


def test_order_fhir_bundle_is_tenant_scoped_and_audited(db, lims_fixture):
    patient = Patient(
        lab_id=lims_fixture["lab_a"].id,
        full_name="Bundle Test Patient",
        phone="07700000000",
    )
    db.add(patient)
    db.flush()

    base_order = LabOrder(
        patient_id=patient.id,
        lab_id=lims_fixture["lab_a"].id,
        status="pending",
    )
    db.add(base_order)
    db.flush()

    lims_order = lims_models.Order(
        order_id=base_order.id,
        lab_id=lims_fixture["lab_a"].id,
        accession_number="ACC-BUNDLE-1",
    )
    db.add(lims_order)
    db.flush()

    specimen = lims_models.Specimen(
        lab_id=lims_fixture["lab_a"].id,
        order_id=base_order.id,
        barcode="SP-BUNDLE-1",
        specimen_type="blood",
    )
    db.add(specimen)
    db.flush()

    result = lims_models.Result(
        lab_id=lims_fixture["lab_a"].id,
        specimen_id=specimen.id,
        order_id=base_order.id,
        test_code="GLU",
        test_name="Glucose",
        value_numeric=95.0,
        unit="mg/dL",
    )
    db.add(result)
    db.flush()

    bundle = order_fhir_bundle(
        order_id=lims_order.id,
        current_user=lims_fixture["user_a"],
        db=db,
    )

    resources = [entry["resource"] for entry in bundle["entry"]]
    assert bundle["resourceType"] == "Bundle"
    assert all("subject" not in resource for resource in resources)
    assert bundle["type"] == "collection"
    assert [resource["resourceType"] for resource in resources] == [
        "ServiceRequest",
        "Specimen",
        "Observation",
    ]
    audit = db.query(AuditLog).filter(
        AuditLog.action == "export",
        AuditLog.resource_type == "lims_order_fhir_bundle",
        AuditLog.resource_id == lims_order.id,
        AuditLog.lab_id == lims_fixture["lab_a"].id,
    ).one()
    assert "Bundle Test Patient" not in (audit.details or "")
    assert "95.0" not in (audit.details or "")


def test_sections_are_filtered_by_current_lab(db, lims_fixture):
    data = list_sections(current_user=lims_fixture["user_a"], db=db)

    assert {section["id"] for section in data["sections"]} == {
        lims_fixture["section_a"].id
    }


def test_workstations_cannot_be_enumerated_through_another_lab_section(
    db, lims_fixture
):
    data = list_workstations(
        section_id=lims_fixture["section_b"].id,
        current_user=lims_fixture["user_a"],
        db=db,
    )

    assert data["workstations"] == []


def test_instrument_cannot_attach_to_another_lab_workstation(db, lims_fixture):
    manufacturer = lims_models.Manufacturer(code="ACME", name="Acme")
    db.add(manufacturer)
    db.flush()
    model = lims_models.InstrumentModel(
        manufacturer_id=manufacturer.id,
        model_code="AN-1",
        model_name="Analyzer 1",
    )
    db.add(model)
    db.flush()

    with pytest.raises(HTTPException) as exc_info:
        create_instrument(
            data=InstrumentCreateRequest(
                model_id=model.id,
                instrument_code="A-1",
                workstation_id=lims_fixture["workstation_b"].id,
            ),
            current_user=lims_fixture["user_a"],
            db=db,
        )

    assert exc_info.value.status_code == 404
    assert "Workstation" in str(exc_info.value.detail)
