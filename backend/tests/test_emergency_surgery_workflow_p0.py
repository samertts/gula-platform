"""Regression tests for P0 emergency response and surgical resource workflows."""
from __future__ import annotations

from typing import Any

import pytest
from app.domain.exceptions import ConflictError
from app.ems.application.service import EMSService
from app.ems.exceptions import EMSWorkflowError, InvalidIncidentStateError
from app.ems.infrastructure.models import (
    AmbulanceCrewModel,
    AmbulanceModel,
    EmergencyIncidentModel,
    ePCRModel,
)
from app.hospital.models import Bed, BedAssignment, OperationTheater
from app.services.hospital_service import HospitalService


def _incident(db: Any, *, status: str = "pending") -> EmergencyIncidentModel:
    model = EmergencyIncidentModel(lab_id=1, status=status, category="medical", priority="bravo")
    db.add(model)
    db.flush()
    return model


def test_emergency_dispatch_requires_available_crew_and_changes_resources_atomically(db: Any) -> None:
    incident = _incident(db)
    ambulance = AmbulanceModel(
        lab_id=1,
        registration_number="EMS-P0-001",
        call_sign="P0-UNIT-1",
        status="available",
        vehicle_status="active",
    )
    crew = AmbulanceCrewModel(
        lab_id=1,
        full_name="P0 Emergency Clinician",
        is_active=True,
        is_available=True,
    )
    db.add_all([ambulance, crew])
    db.flush()
    service = EMSService(db)

    with pytest.raises(EMSWorkflowError, match="at least one"):
        service.dispatch_incident(
            incident.id,
            ambulance.id,
            crew_ids=[],
            incident_expected_version=incident.version,
            ambulance_expected_version=ambulance.version,
        )

    dispatch = service.dispatch_incident(
        incident.id,
        ambulance.id,
        crew_ids=[crew.id],
        incident_expected_version=incident.version,
        ambulance_expected_version=ambulance.version,
    )
    assert dispatch.incident_id == incident.id
    assert incident.status == "dispatched"
    assert ambulance.status == "en_route"
    assert crew.is_available is False
    assert incident.version == 2
    assert ambulance.version == 2


def test_emergency_triage_and_epcr_submission_reject_closed_or_incomplete_clinical_records(db: Any) -> None:
    closed = _incident(db, status="completed")
    service = EMSService(db)
    with pytest.raises(EMSWorkflowError, match="closed incident"):
        service.record_triage(
            {"incident_id": closed.id, "ambulatory": True, "respiratory_rate": 18},
            incident_expected_version=closed.version,
        )

    incident = _incident(db)
    triage = service.record_triage(
        {"incident_id": incident.id, "ambulatory": False, "respiratory_rate": 36},
        incident_expected_version=incident.version,
    )
    assert triage.category == "immediate"
    assert incident.version == 2

    epcr = ePCRModel(lab_id=1, incident_id=incident.id, status="draft")
    db.add(epcr)
    db.flush()
    with pytest.raises(EMSWorkflowError, match="chief complaint"):
        service.submit_epcr(epcr.id, expected_version=epcr.version)

    epcr.chief_complaint = "Chest pain"
    epcr.narrative = "Patient assessed and transported safely."
    epcr.destination_facility = "Baghdad General Hospital"
    epcr.submitting_crew_member = "crew-1"
    epcr.signatures = [{"signer": "crew-1", "timestamp": "2026-08-20T00:00:00Z"}]
    db.flush()
    submitted = service.submit_epcr(epcr.id, expected_version=epcr.version)
    assert submitted.status == "completed"
    assert epcr.version == 2


def test_operation_theater_requires_surgery_identifier_and_cleaning_before_reuse(db: Any) -> None:
    theater = OperationTheater(
        lab_id=1,
        hospital_id=1,
        code="OT-P0-1",
        name="P0 Theater",
        theater_type="general",
        status="available",
    )
    db.add(theater)
    db.flush()

    with pytest.raises(ConflictError, match="surgery identifier"):
        HospitalService.update_operation_theater_status(
            db,
            1,
            101,
            theater.id,
            actor_role="lab_admin",
            expected_version=theater.version,
            next_status="in_use",
        )

    with pytest.raises(ConflictError, match="safety checklist"):
        HospitalService.update_operation_theater_status(
            db,
            1,
            101,
            theater.id,
            actor_role="lab_admin",
            expected_version=theater.version,
            next_status="in_use",
            surgery_id=7001,
        )

    HospitalService.complete_surgical_safety_checklist(
        db,
        1,
        101,
        {
            "operation_theater_id": theater.id,
            "surgery_id": 7001,
            "patient_id": 77,
            "procedure_name": "Emergency laparotomy",
            "procedure_site": "abdomen",
            "planned_laterality": "midline",
            "patient_identity_confirmed": True,
            "procedure_confirmed": True,
            "site_marked": True,
            "consent_verified": True,
            "anesthesia_assessment_complete": True,
            "allergy_reviewed": True,
            "antibiotic_prophylaxis_confirmed": True,
            "blood_products_confirmed": True,
            "imaging_reviewed": True,
            "team_time_out_completed": True,
        },
        actor_role="lab_admin",
    )
    active = HospitalService.update_operation_theater_status(
        db,
        1,
        101,
        theater.id,
        actor_role="lab_admin",
        expected_version=theater.version,
        next_status="in_use",
        surgery_id=7001,
    )
    assert active.current_surgery_id == 7001
    assert active.status == "in_use"

    with pytest.raises(ConflictError, match="Illegal operation theater transition"):
        HospitalService.update_operation_theater_status(
            db,
            1,
            101,
            theater.id,
            actor_role="lab_admin",
            expected_version=active.version,
            next_status="available",
        )

    cleaning = HospitalService.update_operation_theater_status(
        db,
        1,
        101,
        theater.id,
        actor_role="lab_admin",
        expected_version=active.version,
        next_status="cleaning",
    )
    assert cleaning.current_surgery_id is None
    assert cleaning.status == "cleaning"


def test_bed_transfer_preserves_patient_and_closes_source_assignment(db: Any) -> None:
    source = Bed(lab_id=1, room_id=1, bed_number="P0-A", status="occupied", current_patient_id=77)
    target = Bed(lab_id=1, room_id=1, bed_number="P0-B", status="available")
    db.add_all([source, target])
    db.flush()
    source_assignment = BedAssignment(
        lab_id=1,
        created_by=101,
        bed_id=source.id,
        patient_id=77,
    )
    db.add(source_assignment)
    db.flush()

    moved = HospitalService.transfer_bed(
        db,
        1,
        101,
        source.id,
        target.id,
        actor_role="lab_admin",
        from_expected_version=source.version,
        to_expected_version=target.version,
        reason="Critical care escalation",
    )
    assert moved["patient_id"] == 77
    assert source.status == "cleaning"
    assert source.current_patient_id is None
    assert target.status == "occupied"
    assert target.current_patient_id == 77
    assert source_assignment.discharge_date is not None
