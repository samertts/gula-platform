from __future__ import annotations

from datetime import date, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.ehr.enums import (
    AlcoholStatus,
    AllergySeverity,
    AllergyStatus,
    CarePlanStatus,
    ClinicalNoteType,
    DiagnosisType,
    DisabilityType,
    MedicationAdministrationStatus,
    MedicationOrderStatus,
    ProblemStatus,
    RiskLevel,
    SmokingStatus,
)

from ..database import get_db
from ..models.lab_user import LabUser
from ..security.dependencies import get_current_user
from ..services import ehr_service

router = APIRouter(prefix="/ehr", tags=["ehr"])


# ── Helper ───────────────────────────────────────────────────────────────


def _get_patient(db: Session, patient_id: str, lab_id: int):
    return ehr_service.get_national_patient_or_404(db, patient_id, lab_id)


# ═══════════════════════════════════════════════════════════════════════════
# Clinical Notes
# ═══════════════════════════════════════════════════════════════════════════


class ClinicalNoteCreate(BaseModel):
    patient_id: str
    citizen_id: str | None = None
    encounter_id: str | None = None
    practitioner_id: str | None = None
    author_id: str | None = None
    note_type: ClinicalNoteType
    title: str = Field(..., min_length=1, max_length=300)
    title_ar: str | None = None
    content: str
    content_format: str = "html"
    is_final: bool = False
    facility_id: str | None = None
    department_id: str | None = None
    tags: dict[str, Any] | None = None
    metadata_: dict[str, Any] | None = None


class ClinicalNoteUpdate(BaseModel):
    title: str | None = None
    title_ar: str | None = None
    content: str | None = None
    content_format: str | None = None
    is_final: bool | None = None
    is_signed: bool | None = None
    signed_by: str | None = None
    tags: dict[str, Any] | None = None
    metadata_: dict[str, Any] | None = None


@router.post("/clinical-notes", summary="Create a clinical note")
def create_clinical_note(
    body: ClinicalNoteCreate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_patient(db, body.patient_id, current_user.lab_id)
    record = ehr_service.create_clinical_note(db, body.model_dump(exclude_none=True))
    db.commit()
    return record.to_dict()


@router.get("/clinical-notes/{note_id}", summary="Get a clinical note")
def get_clinical_note(
    note_id: str,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = ehr_service.get_clinical_note(db, note_id)
    if not record:
        raise HTTPException(status_code=404, detail="Clinical note not found")
    _get_patient(db, record.patient_id, current_user.lab_id)
    return record.to_dict()


@router.put("/clinical-notes/{note_id}", summary="Update a clinical note")
def update_clinical_note(
    note_id: str,
    body: ClinicalNoteUpdate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = ehr_service.get_clinical_note(db, note_id)
    if not record:
        raise HTTPException(status_code=404, detail="Clinical note not found")
    _get_patient(db, record.patient_id, current_user.lab_id)
    updated = ehr_service.update_clinical_note(
        db,
        note_id,
        body.model_dump(exclude_none=True),
    )
    db.commit()
    return updated.to_dict()


@router.delete("/clinical-notes/{note_id}", summary="Soft-delete a clinical note")
def delete_clinical_note(
    note_id: str,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = ehr_service.get_clinical_note(db, note_id)
    if not record:
        raise HTTPException(status_code=404, detail="Clinical note not found")
    _get_patient(db, record.patient_id, current_user.lab_id)
    ehr_service.soft_delete_clinical_note(db, note_id)
    db.commit()
    return {"detail": "Clinical note deleted"}


@router.get(
    "/patients/{patient_id}/clinical-notes",
    summary="List clinical notes for a patient",
)
def list_patient_clinical_notes(
    patient_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_patient(db, patient_id, current_user.lab_id)
    records = ehr_service.list_clinical_notes_by_patient(db, patient_id, skip, limit)
    return [r.to_dict() for r in records]


@router.get(
    "/encounters/{encounter_id}/clinical-notes",
    summary="List clinical notes for an encounter",
)
def list_encounter_clinical_notes(
    encounter_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    records = ehr_service.list_clinical_notes_by_encounter(db, encounter_id, skip, limit)
    return [r.to_dict() for r in records]


# ═══════════════════════════════════════════════════════════════════════════
# Allergies
# ═══════════════════════════════════════════════════════════════════════════


class AllergyCreate(BaseModel):
    patient_id: str
    citizen_id: str | None = None
    encounter_id: str | None = None
    practitioner_id: str | None = None
    allergy_type: str | None = None
    category: str | None = None
    criticality: str | None = None
    code: str | None = None
    code_system: str | None = None
    code_display: str
    code_display_ar: str | None = None
    severity: AllergySeverity | None = None
    status: AllergyStatus = AllergyStatus.ACTIVE
    verification_status: str | None = None
    reaction: str | None = None
    reaction_details: dict[str, Any] | None = None
    onset_date: date | None = None
    notes: str | None = None
    metadata_: dict[str, Any] | None = None


class AllergyUpdate(BaseModel):
    code_display: str | None = None
    code_display_ar: str | None = None
    severity: AllergySeverity | None = None
    status: AllergyStatus | None = None
    reaction: str | None = None
    reaction_details: dict[str, Any] | None = None
    notes: str | None = None


@router.post("/allergies", summary="Create an allergy record")
def create_allergy(
    body: AllergyCreate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_patient(db, body.patient_id, current_user.lab_id)
    record = ehr_service.create_allergy(db, body.model_dump(exclude_none=True))
    db.commit()
    return record.to_dict()


@router.get("/allergies/{allergy_id}", summary="Get an allergy record")
def get_allergy(
    allergy_id: str,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = ehr_service.get_allergy(db, allergy_id)
    if not record:
        raise HTTPException(status_code=404, detail="Allergy not found")
    _get_patient(db, record.patient_id, current_user.lab_id)
    return record.to_dict()


@router.put("/allergies/{allergy_id}", summary="Update an allergy record")
def update_allergy(
    allergy_id: str,
    body: AllergyUpdate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = ehr_service.get_allergy(db, allergy_id)
    if not record:
        raise HTTPException(status_code=404, detail="Allergy not found")
    _get_patient(db, record.patient_id, current_user.lab_id)
    updated = ehr_service.update_allergy(db, allergy_id, body.model_dump(exclude_none=True))
    db.commit()
    return updated.to_dict()


@router.delete("/allergies/{allergy_id}", summary="Soft-delete an allergy record")
def delete_allergy(
    allergy_id: str,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = ehr_service.get_allergy(db, allergy_id)
    if not record:
        raise HTTPException(status_code=404, detail="Allergy not found")
    _get_patient(db, record.patient_id, current_user.lab_id)
    ehr_service.soft_delete_allergy(db, allergy_id)
    db.commit()
    return {"detail": "Allergy record deleted"}


@router.get(
    "/patients/{patient_id}/allergies",
    summary="List allergies for a patient",
)
def list_patient_allergies(
    patient_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_patient(db, patient_id, current_user.lab_id)
    records = ehr_service.list_allergies_by_patient(db, patient_id, skip, limit)
    return [r.to_dict() for r in records]


# ═══════════════════════════════════════════════════════════════════════════
# Medication Statements
# ═══════════════════════════════════════════════════════════════════════════


class MedStatementCreate(BaseModel):
    patient_id: str
    citizen_id: str | None = None
    encounter_id: str | None = None
    practitioner_id: str | None = None
    medication_code: str | None = None
    medication_code_system: str | None = None
    medication_name: str
    medication_name_ar: str | None = None
    medication_brand: str | None = None
    medication_form: str | None = None
    strength_value: str | None = None
    strength_unit: str | None = None
    dosage_text: str | None = None
    route: str | None = None
    frequency: str | None = None
    timing: dict[str, Any] | None = None
    status: str = "active"
    category: str | None = None
    date_started: date | None = None
    date_ended: date | None = None
    reason_code: str | None = None
    reason_description: str | None = None
    note: str | None = None
    metadata_: dict[str, Any] | None = None


@router.post("/medication-statements", summary="Create a medication statement")
def create_medication_statement(
    body: MedStatementCreate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_patient(db, body.patient_id, current_user.lab_id)
    record = ehr_service.create_medication_statement(db, body.model_dump(exclude_none=True))
    db.commit()
    return record.to_dict()


@router.get(
    "/medication-statements/{statement_id}",
    summary="Get a medication statement",
)
def get_medication_statement(
    statement_id: str,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = ehr_service.get_medication_statement(db, statement_id)
    if not record:
        raise HTTPException(status_code=404, detail="Medication statement not found")
    _get_patient(db, record.patient_id, current_user.lab_id)
    return record.to_dict()


@router.put(
    "/medication-statements/{statement_id}",
    summary="Update a medication statement",
)
def update_medication_statement(
    statement_id: str,
    body: MedStatementCreate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = ehr_service.get_medication_statement(db, statement_id)
    if not record:
        raise HTTPException(status_code=404, detail="Medication statement not found")
    _get_patient(db, record.patient_id, current_user.lab_id)
    updated = ehr_service.update_medication_statement(
        db,
        statement_id,
        body.model_dump(exclude_none=True),
    )
    db.commit()
    return updated.to_dict()


@router.delete(
    "/medication-statements/{statement_id}",
    summary="Soft-delete a medication statement",
)
def delete_medication_statement(
    statement_id: str,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = ehr_service.get_medication_statement(db, statement_id)
    if not record:
        raise HTTPException(status_code=404, detail="Medication statement not found")
    _get_patient(db, record.patient_id, current_user.lab_id)
    ehr_service.soft_delete_medication_statement(db, statement_id)
    db.commit()
    return {"detail": "Medication statement deleted"}


@router.get(
    "/patients/{patient_id}/medication-statements",
    summary="List medication statements for a patient",
)
def list_patient_medication_statements(
    patient_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_patient(db, patient_id, current_user.lab_id)
    records = ehr_service.list_medication_statements_by_patient(db, patient_id, skip, limit)
    return [r.to_dict() for r in records]


# ═══════════════════════════════════════════════════════════════════════════
# Medication Requests
# ═══════════════════════════════════════════════════════════════════════════


class MedRequestCreate(BaseModel):
    patient_id: str
    citizen_id: str | None = None
    encounter_id: str | None = None
    prescriber_id: str | None = None
    medication_code: str | None = None
    medication_code_system: str | None = None
    medication_name: str
    medication_name_ar: str | None = None
    medication_brand: str | None = None
    medication_form: str | None = None
    status: MedicationOrderStatus = MedicationOrderStatus.DRAFT
    intent: str = "order"
    priority: str = "routine"
    category: str | None = None
    dosage_instruction: str | None = None
    dosage_instructions: dict[str, Any] | None = None
    route: str | None = None
    frequency: str | None = None
    quantity: int | None = None
    quantity_unit: str | None = None
    refills: int = 0
    duration_days: int | None = None
    reason_code: str | None = None
    reason_description: str | None = None
    clinical_indication: str | None = None
    valid_from: date | None = None
    valid_to: date | None = None
    dispense_interval_days: int | None = None
    substitution_allowed: bool = True
    note: str | None = None
    metadata_: dict[str, Any] | None = None


@router.post("/medication-requests", summary="Create a medication request")
def create_medication_request(
    body: MedRequestCreate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_patient(db, body.patient_id, current_user.lab_id)
    record = ehr_service.create_medication_request(db, body.model_dump(exclude_none=True))
    db.commit()
    return record.to_dict()


@router.get(
    "/medication-requests/{request_id}",
    summary="Get a medication request",
)
def get_medication_request(
    request_id: str,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = ehr_service.get_medication_request(db, request_id)
    if not record:
        raise HTTPException(status_code=404, detail="Medication request not found")
    _get_patient(db, record.patient_id, current_user.lab_id)
    return record.to_dict()


@router.put(
    "/medication-requests/{request_id}",
    summary="Update a medication request",
)
def update_medication_request(
    request_id: str,
    body: MedRequestCreate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = ehr_service.get_medication_request(db, request_id)
    if not record:
        raise HTTPException(status_code=404, detail="Medication request not found")
    _get_patient(db, record.patient_id, current_user.lab_id)
    updated = ehr_service.update_medication_request(
        db,
        request_id,
        body.model_dump(exclude_none=True),
    )
    db.commit()
    return updated.to_dict()


@router.delete(
    "/medication-requests/{request_id}",
    summary="Soft-delete a medication request",
)
def delete_medication_request(
    request_id: str,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = ehr_service.get_medication_request(db, request_id)
    if not record:
        raise HTTPException(status_code=404, detail="Medication request not found")
    _get_patient(db, record.patient_id, current_user.lab_id)
    ehr_service.soft_delete_medication_request(db, request_id)
    db.commit()
    return {"detail": "Medication request deleted"}


@router.get(
    "/patients/{patient_id}/medication-requests",
    summary="List medication requests for a patient",
)
def list_patient_medication_requests(
    patient_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_patient(db, patient_id, current_user.lab_id)
    records = ehr_service.list_medication_requests_by_patient(db, patient_id, skip, limit)
    return [r.to_dict() for r in records]


# ═══════════════════════════════════════════════════════════════════════════
# Medication Dispenses
# ═══════════════════════════════════════════════════════════════════════════


class MedDispenseCreate(BaseModel):
    medication_request_id: str | None = None
    patient_id: str
    citizen_id: str | None = None
    dispenser_id: str | None = None
    medication_code: str | None = None
    medication_code_system: str | None = None
    medication_name: str
    medication_name_ar: str | None = None
    medication_brand: str | None = None
    medication_form: str | None = None
    status: str = "prepared"
    category: str | None = None
    quantity: int
    quantity_unit: str | None = None
    days_supply: int | None = None
    dosage_instruction: str | None = None
    route: str | None = None
    frequency: str | None = None
    prepared_by: str | None = None
    verified_by: str | None = None
    lot_number: str | None = None
    expiry_date: date | None = None
    note: str | None = None
    metadata_: dict[str, Any] | None = None


@router.post("/medication-dispenses", summary="Create a medication dispense")
def create_medication_dispense(
    body: MedDispenseCreate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_patient(db, body.patient_id, current_user.lab_id)
    record = ehr_service.create_medication_dispense(db, body.model_dump(exclude_none=True))
    db.commit()
    return record.to_dict()


@router.get(
    "/medication-dispenses/{dispense_id}",
    summary="Get a medication dispense",
)
def get_medication_dispense(
    dispense_id: str,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = ehr_service.get_medication_dispense(db, dispense_id)
    if not record:
        raise HTTPException(status_code=404, detail="Medication dispense not found")
    _get_patient(db, record.patient_id, current_user.lab_id)
    return record.to_dict()


@router.put(
    "/medication-dispenses/{dispense_id}",
    summary="Update a medication dispense",
)
def update_medication_dispense(
    dispense_id: str,
    body: MedDispenseCreate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = ehr_service.get_medication_dispense(db, dispense_id)
    if not record:
        raise HTTPException(status_code=404, detail="Medication dispense not found")
    _get_patient(db, record.patient_id, current_user.lab_id)
    updated = ehr_service.update_medication_dispense(
        db,
        dispense_id,
        body.model_dump(exclude_none=True),
    )
    db.commit()
    return updated.to_dict()


@router.delete(
    "/medication-dispenses/{dispense_id}",
    summary="Soft-delete a medication dispense",
)
def delete_medication_dispense(
    dispense_id: str,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = ehr_service.get_medication_dispense(db, dispense_id)
    if not record:
        raise HTTPException(status_code=404, detail="Medication dispense not found")
    _get_patient(db, record.patient_id, current_user.lab_id)
    ehr_service.soft_delete_medication_dispense(db, dispense_id)
    db.commit()
    return {"detail": "Medication dispense deleted"}


@router.get(
    "/patients/{patient_id}/medication-dispenses",
    summary="List medication dispenses for a patient",
)
def list_patient_medication_dispenses(
    patient_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_patient(db, patient_id, current_user.lab_id)
    records = ehr_service.list_medication_dispenses_by_patient(db, patient_id, skip, limit)
    return [r.to_dict() for r in records]


# ═══════════════════════════════════════════════════════════════════════════
# Medication Administrations
# ═══════════════════════════════════════════════════════════════════════════


class MedAdminCreate(BaseModel):
    medication_request_id: str | None = None
    patient_id: str
    citizen_id: str | None = None
    encounter_id: str | None = None
    administrator_id: str | None = None
    medication_code: str | None = None
    medication_code_system: str | None = None
    medication_name: str
    medication_name_ar: str | None = None
    status: MedicationAdministrationStatus = MedicationAdministrationStatus.COMPLETED
    category: str | None = None
    dose_value: str | None = None
    dose_unit: str | None = None
    route: str | None = None
    site: str | None = None
    method: str | None = None
    administration_time: datetime
    reason_not_given: str | None = None
    note: str | None = None
    metadata_: dict[str, Any] | None = None


@router.post(
    "/medication-administrations",
    summary="Create a medication administration",
)
def create_medication_administration(
    body: MedAdminCreate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_patient(db, body.patient_id, current_user.lab_id)
    record = ehr_service.create_medication_administration(
        db,
        body.model_dump(exclude_none=True),
    )
    db.commit()
    return record.to_dict()


@router.get(
    "/medication-administrations/{admin_id}",
    summary="Get a medication administration",
)
def get_medication_administration(
    admin_id: str,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = ehr_service.get_medication_administration(db, admin_id)
    if not record:
        raise HTTPException(status_code=404, detail="Medication administration not found")
    _get_patient(db, record.patient_id, current_user.lab_id)
    return record.to_dict()


@router.put(
    "/medication-administrations/{admin_id}",
    summary="Update a medication administration",
)
def update_medication_administration(
    admin_id: str,
    body: MedAdminCreate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = ehr_service.get_medication_administration(db, admin_id)
    if not record:
        raise HTTPException(status_code=404, detail="Medication administration not found")
    _get_patient(db, record.patient_id, current_user.lab_id)
    updated = ehr_service.update_medication_administration(
        db,
        admin_id,
        body.model_dump(exclude_none=True),
    )
    db.commit()
    return updated.to_dict()


@router.delete(
    "/medication-administrations/{admin_id}",
    summary="Soft-delete a medication administration",
)
def delete_medication_administration(
    admin_id: str,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = ehr_service.get_medication_administration(db, admin_id)
    if not record:
        raise HTTPException(status_code=404, detail="Medication administration not found")
    _get_patient(db, record.patient_id, current_user.lab_id)
    ehr_service.soft_delete_medication_administration(db, admin_id)
    db.commit()
    return {"detail": "Medication administration deleted"}


@router.get(
    "/patients/{patient_id}/medication-administrations",
    summary="List medication administrations for a patient",
)
def list_patient_medication_administrations(
    patient_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_patient(db, patient_id, current_user.lab_id)
    records = ehr_service.list_medication_administrations_by_patient(
        db,
        patient_id,
        skip,
        limit,
    )
    return [r.to_dict() for r in records]


# ═══════════════════════════════════════════════════════════════════════════
# Care Plans
# ═══════════════════════════════════════════════════════════════════════════


class CarePlanCreate(BaseModel):
    patient_id: str
    citizen_id: str | None = None
    encounter_id: str | None = None
    practitioner_id: str | None = None
    status: CarePlanStatus = CarePlanStatus.DRAFT
    intent: str = "plan"
    title: str
    title_ar: str | None = None
    description: str | None = None
    period_start: date | None = None
    period_end: date | None = None
    category: str | None = None
    contributor: dict[str, Any] | None = None
    supporting_info: dict[str, Any] | None = None
    notes: str | None = None
    metadata_: dict[str, Any] | None = None


class CarePlanUpdate(BaseModel):
    status: CarePlanStatus | None = None
    title: str | None = None
    title_ar: str | None = None
    description: str | None = None
    period_start: date | None = None
    period_end: date | None = None
    notes: str | None = None


@router.post("/care-plans", summary="Create a care plan")
def create_care_plan(
    body: CarePlanCreate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_patient(db, body.patient_id, current_user.lab_id)
    record = ehr_service.create_care_plan(db, body.model_dump(exclude_none=True))
    db.commit()
    return record.to_dict()


@router.get("/care-plans/{plan_id}", summary="Get a care plan with goals and activities")
def get_care_plan(
    plan_id: str,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = ehr_service.get_care_plan(db, plan_id)
    if not record:
        raise HTTPException(status_code=404, detail="Care plan not found")
    _get_patient(db, record.patient_id, current_user.lab_id)
    result = record.to_dict()
    goals = ehr_service.get_care_plan_goals(db, plan_id)
    result["goals"] = [g.to_dict() for g in goals]
    for g in result["goals"]:
        g["activities"] = [
            a.to_dict() for a in ehr_service.get_care_plan_activities(db, goal_id=g["id"])
        ]
    return result


@router.put("/care-plans/{plan_id}", summary="Update a care plan")
def update_care_plan(
    plan_id: str,
    body: CarePlanUpdate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = ehr_service.get_care_plan(db, plan_id)
    if not record:
        raise HTTPException(status_code=404, detail="Care plan not found")
    _get_patient(db, record.patient_id, current_user.lab_id)
    updated = ehr_service.update_care_plan(db, plan_id, body.model_dump(exclude_none=True))
    db.commit()
    result = updated.to_dict()
    goals = ehr_service.get_care_plan_goals(db, plan_id)
    result["goals"] = [g.to_dict() for g in goals]
    for g in result["goals"]:
        g["activities"] = [
            a.to_dict() for a in ehr_service.get_care_plan_activities(db, goal_id=g["id"])
        ]
    return result


@router.delete("/care-plans/{plan_id}", summary="Soft-delete a care plan")
def delete_care_plan(
    plan_id: str,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = ehr_service.get_care_plan(db, plan_id)
    if not record:
        raise HTTPException(status_code=404, detail="Care plan not found")
    _get_patient(db, record.patient_id, current_user.lab_id)
    ehr_service.soft_delete_care_plan(db, plan_id)
    db.commit()
    return {"detail": "Care plan deleted"}


@router.get(
    "/patients/{patient_id}/care-plans",
    summary="List care plans for a patient",
)
def list_patient_care_plans(
    patient_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_patient(db, patient_id, current_user.lab_id)
    records = ehr_service.list_care_plans_by_patient(db, patient_id, skip, limit)
    result = []
    for cp in records:
        d = cp.to_dict()
        goals = ehr_service.get_care_plan_goals(db, cp.id)
        d["goals"] = [g.to_dict() for g in goals]
        for g in d["goals"]:
            g["activities"] = [
                a.to_dict() for a in ehr_service.get_care_plan_activities(db, goal_id=g["id"])
            ]
        result.append(d)
    return result


# ── Care Plan Goals ───────────────────────────────────────────────────────


class CarePlanGoalCreate(BaseModel):
    care_plan_id: str
    description: str
    description_ar: str | None = None
    status: str = "in_progress"
    priority: int = 0
    target_date: date | None = None
    measured_by: str | None = None
    notes: str | None = None
    metadata_: dict[str, Any] | None = None


@router.post("/care-plans/{plan_id}/goals", summary="Add a goal to a care plan")
def create_care_plan_goal(
    plan_id: str,
    body: CarePlanGoalCreate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cp = ehr_service.get_care_plan(db, plan_id)
    if not cp:
        raise HTTPException(status_code=404, detail="Care plan not found")
    _get_patient(db, cp.patient_id, current_user.lab_id)
    data = body.model_dump(exclude_none=True)
    data["care_plan_id"] = plan_id
    record = ehr_service.create_care_plan_goal(db, data)
    db.commit()
    return record.to_dict()


@router.put(
    "/care-plan-goals/{goal_id}",
    summary="Update a care plan goal",
)
def update_care_plan_goal(
    goal_id: str,
    body: CarePlanGoalCreate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    goal = ehr_service.get_care_plan_goal(db, goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail="Care plan goal not found")
    cp = ehr_service.get_care_plan(db, goal.care_plan_id)
    if cp:
        _get_patient(db, cp.patient_id, current_user.lab_id)
    updated = ehr_service.update_care_plan_goal(
        db,
        goal_id,
        body.model_dump(exclude_none=True),
    )
    db.commit()
    return updated.to_dict()


@router.delete(
    "/care-plan-goals/{goal_id}",
    summary="Soft-delete a care plan goal",
)
def delete_care_plan_goal(
    goal_id: str,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    goal = ehr_service.get_care_plan_goal(db, goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail="Care plan goal not found")
    cp = ehr_service.get_care_plan(db, goal.care_plan_id)
    if cp:
        _get_patient(db, cp.patient_id, current_user.lab_id)
    ehr_service.soft_delete_care_plan_goal(db, goal_id)
    db.commit()
    return {"detail": "Care plan goal deleted"}


# ── Care Plan Activities ──────────────────────────────────────────────────


class CarePlanActivityCreate(BaseModel):
    care_plan_id: str | None = None
    goal_id: str | None = None
    activity_code: str | None = None
    activity_code_system: str | None = None
    description: str
    description_ar: str | None = None
    status: str = "not_started"
    scheduled_start: date | None = None
    scheduled_end: date | None = None
    performer: str | None = None
    performer_id: str | None = None
    location: str | None = None
    outcome: str | None = None
    progress_notes: str | None = None
    notes: str | None = None
    metadata_: dict[str, Any] | None = None


@router.post(
    "/care-plans/{plan_id}/activities",
    summary="Add an activity to a care plan",
)
def create_care_plan_activity(
    plan_id: str,
    body: CarePlanActivityCreate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cp = ehr_service.get_care_plan(db, plan_id)
    if not cp:
        raise HTTPException(status_code=404, detail="Care plan not found")
    _get_patient(db, cp.patient_id, current_user.lab_id)
    data = body.model_dump(exclude_none=True)
    data["care_plan_id"] = plan_id
    record = ehr_service.create_care_plan_activity(db, data)
    db.commit()
    return record.to_dict()


@router.put(
    "/care-plan-activities/{activity_id}",
    summary="Update a care plan activity",
)
def update_care_plan_activity(
    activity_id: str,
    body: CarePlanActivityCreate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    activity = ehr_service.get_care_plan_activity(db, activity_id)
    if not activity:
        raise HTTPException(status_code=404, detail="Care plan activity not found")
    cp = ehr_service.get_care_plan(db, activity.care_plan_id)
    if cp:
        _get_patient(db, cp.patient_id, current_user.lab_id)
    updated = ehr_service.update_care_plan_activity(
        db,
        activity_id,
        body.model_dump(exclude_none=True),
    )
    db.commit()
    return updated.to_dict()


@router.delete(
    "/care-plan-activities/{activity_id}",
    summary="Soft-delete a care plan activity",
)
def delete_care_plan_activity(
    activity_id: str,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    activity = ehr_service.get_care_plan_activity(db, activity_id)
    if not activity:
        raise HTTPException(status_code=404, detail="Care plan activity not found")
    cp = ehr_service.get_care_plan(db, activity.care_plan_id)
    if cp:
        _get_patient(db, cp.patient_id, current_user.lab_id)
    ehr_service.soft_delete_care_plan_activity(db, activity_id)
    db.commit()
    return {"detail": "Care plan activity deleted"}


# ═══════════════════════════════════════════════════════════════════════════
# Problem List
# ═══════════════════════════════════════════════════════════════════════════


class ProblemListItemCreate(BaseModel):
    patient_id: str
    citizen_id: str | None = None
    encounter_id: str | None = None
    status: ProblemStatus = ProblemStatus.ACTIVE
    code: str | None = None
    code_system: str | None = None
    display: str
    display_ar: str | None = None
    clinical_status: str | None = None
    verification_status: str | None = None
    category: str | None = None
    severity: str | None = None
    onset_date: date | None = None
    resolution_date: date | None = None
    body_site: str | None = None
    notes: str | None = None
    metadata_: dict[str, Any] | None = None


class ProblemListItemUpdate(BaseModel):
    status: ProblemStatus | None = None
    display: str | None = None
    display_ar: str | None = None
    clinical_status: str | None = None
    severity: str | None = None
    resolution_date: date | None = None
    notes: str | None = None


@router.post("/problem-list", summary="Add a problem list item")
def create_problem_list_item(
    body: ProblemListItemCreate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_patient(db, body.patient_id, current_user.lab_id)
    record = ehr_service.create_problem_list_item(db, body.model_dump(exclude_none=True))
    db.commit()
    return record.to_dict()


@router.get(
    "/problem-list/{item_id}",
    summary="Get a problem list item",
)
def get_problem_list_item(
    item_id: str,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = ehr_service.get_problem_list_item(db, item_id)
    if not record:
        raise HTTPException(status_code=404, detail="Problem list item not found")
    _get_patient(db, record.patient_id, current_user.lab_id)
    return record.to_dict()


@router.put(
    "/problem-list/{item_id}",
    summary="Update a problem list item",
)
def update_problem_list_item(
    item_id: str,
    body: ProblemListItemUpdate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = ehr_service.get_problem_list_item(db, item_id)
    if not record:
        raise HTTPException(status_code=404, detail="Problem list item not found")
    _get_patient(db, record.patient_id, current_user.lab_id)
    updated = ehr_service.update_problem_list_item(
        db,
        item_id,
        body.model_dump(exclude_none=True),
    )
    db.commit()
    return updated.to_dict()


@router.delete(
    "/problem-list/{item_id}",
    summary="Soft-delete a problem list item",
)
def delete_problem_list_item(
    item_id: str,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = ehr_service.get_problem_list_item(db, item_id)
    if not record:
        raise HTTPException(status_code=404, detail="Problem list item not found")
    _get_patient(db, record.patient_id, current_user.lab_id)
    ehr_service.soft_delete_problem_list_item(db, item_id)
    db.commit()
    return {"detail": "Problem list item deleted"}


@router.get(
    "/patients/{patient_id}/problem-list",
    summary="List problem list items for a patient",
)
def list_patient_problem_list(
    patient_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_patient(db, patient_id, current_user.lab_id)
    records = ehr_service.list_problem_list_items_by_patient(db, patient_id, skip, limit)
    return [r.to_dict() for r in records]


# ═══════════════════════════════════════════════════════════════════════════
# Conditions
# ═══════════════════════════════════════════════════════════════════════════


class ConditionCreate(BaseModel):
    patient_id: str
    citizen_id: str | None = None
    encounter_id: str | None = None
    practitioner_id: str | None = None
    clinical_status: str = "active"
    verification_status: str | None = None
    category: str | None = None
    severity: str | None = None
    code: str | None = None
    code_system: str | None = None
    code_display: str
    code_display_ar: str | None = None
    icd10_code: str | None = None
    icd10_description: str | None = None
    body_site: str | None = None
    laterality: str | None = None
    onset_date: date | None = None
    abatement_date: date | None = None
    notes: str | None = None
    metadata_: dict[str, Any] | None = None


class ConditionUpdate(BaseModel):
    clinical_status: str | None = None
    severity: str | None = None
    code_display: str | None = None
    icd10_code: str | None = None
    icd10_description: str | None = None
    abatement_date: date | None = None
    notes: str | None = None


@router.post("/conditions", summary="Create a condition record")
def create_condition(
    body: ConditionCreate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_patient(db, body.patient_id, current_user.lab_id)
    record = ehr_service.create_condition(db, body.model_dump(exclude_none=True))
    db.commit()
    return record.to_dict()


@router.get(
    "/conditions/{condition_id}",
    summary="Get a condition record",
)
def get_condition(
    condition_id: str,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = ehr_service.get_condition(db, condition_id)
    if not record:
        raise HTTPException(status_code=404, detail="Condition not found")
    _get_patient(db, record.patient_id, current_user.lab_id)
    return record.to_dict()


@router.put(
    "/conditions/{condition_id}",
    summary="Update a condition record",
)
def update_condition(
    condition_id: str,
    body: ConditionUpdate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = ehr_service.get_condition(db, condition_id)
    if not record:
        raise HTTPException(status_code=404, detail="Condition not found")
    _get_patient(db, record.patient_id, current_user.lab_id)
    updated = ehr_service.update_condition(db, condition_id, body.model_dump(exclude_none=True))
    db.commit()
    return updated.to_dict()


@router.delete(
    "/conditions/{condition_id}",
    summary="Soft-delete a condition record",
)
def delete_condition(
    condition_id: str,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = ehr_service.get_condition(db, condition_id)
    if not record:
        raise HTTPException(status_code=404, detail="Condition not found")
    _get_patient(db, record.patient_id, current_user.lab_id)
    ehr_service.soft_delete_condition(db, condition_id)
    db.commit()
    return {"detail": "Condition deleted"}


@router.get(
    "/patients/{patient_id}/conditions",
    summary="List conditions for a patient",
)
def list_patient_conditions(
    patient_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_patient(db, patient_id, current_user.lab_id)
    records = ehr_service.list_conditions_by_patient(db, patient_id, skip, limit)
    return [r.to_dict() for r in records]


# ═══════════════════════════════════════════════════════════════════════════
# Diagnoses
# ═══════════════════════════════════════════════════════════════════════════


class DiagnosisCreate(BaseModel):
    patient_id: str
    citizen_id: str | None = None
    encounter_id: str | None = None
    practitioner_id: str | None = None
    diagnosis_type: DiagnosisType = DiagnosisType.PRIMARY
    rank: int = 0
    icd10_code: str | None = None
    icd10_description: str | None = None
    snomed_code: str | None = None
    snomed_description: str | None = None
    diagnosis_text: str
    diagnosis_text_ar: str | None = None
    diagnosis_date: date | None = None
    resolution_date: date | None = None
    is_active: bool = True
    is_chronic: bool = False
    certainty: str | None = None
    notes: str | None = None
    metadata_: dict[str, Any] | None = None


class DiagnosisUpdate(BaseModel):
    diagnosis_type: DiagnosisType | None = None
    icd10_code: str | None = None
    icd10_description: str | None = None
    diagnosis_text: str | None = None
    diagnosis_text_ar: str | None = None
    resolution_date: date | None = None
    is_active: bool | None = None
    notes: str | None = None


@router.post("/diagnoses", summary="Create a diagnosis record")
def create_diagnosis(
    body: DiagnosisCreate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_patient(db, body.patient_id, current_user.lab_id)
    record = ehr_service.create_diagnosis(db, body.model_dump(exclude_none=True))
    db.commit()
    return record.to_dict()


@router.get(
    "/diagnoses/{diagnosis_id}",
    summary="Get a diagnosis record",
)
def get_diagnosis(
    diagnosis_id: str,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = ehr_service.get_diagnosis(db, diagnosis_id)
    if not record:
        raise HTTPException(status_code=404, detail="Diagnosis not found")
    _get_patient(db, record.patient_id, current_user.lab_id)
    return record.to_dict()


@router.put(
    "/diagnoses/{diagnosis_id}",
    summary="Update a diagnosis record",
)
def update_diagnosis(
    diagnosis_id: str,
    body: DiagnosisUpdate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = ehr_service.get_diagnosis(db, diagnosis_id)
    if not record:
        raise HTTPException(status_code=404, detail="Diagnosis not found")
    _get_patient(db, record.patient_id, current_user.lab_id)
    updated = ehr_service.update_diagnosis(db, diagnosis_id, body.model_dump(exclude_none=True))
    db.commit()
    return updated.to_dict()


@router.delete(
    "/diagnoses/{diagnosis_id}",
    summary="Soft-delete a diagnosis record",
)
def delete_diagnosis(
    diagnosis_id: str,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = ehr_service.get_diagnosis(db, diagnosis_id)
    if not record:
        raise HTTPException(status_code=404, detail="Diagnosis not found")
    _get_patient(db, record.patient_id, current_user.lab_id)
    ehr_service.soft_delete_diagnosis(db, diagnosis_id)
    db.commit()
    return {"detail": "Diagnosis deleted"}


@router.get(
    "/patients/{patient_id}/diagnoses",
    summary="List diagnoses for a patient",
)
def list_patient_diagnoses(
    patient_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_patient(db, patient_id, current_user.lab_id)
    records = ehr_service.list_diagnoses_by_patient(db, patient_id, skip, limit)
    return [r.to_dict() for r in records]


# ═══════════════════════════════════════════════════════════════════════════
# Family History
# ═══════════════════════════════════════════════════════════════════════════


class FamilyHistoryCreate(BaseModel):
    patient_id: str
    citizen_id: str | None = None
    practitioner_id: str | None = None
    relationship: str
    relationship_detail: str | None = None
    relative_name: str | None = None
    relative_citizen_id: str | None = None
    condition_code: str | None = None
    condition_code_system: str | None = None
    condition_display: str
    condition_display_ar: str | None = None
    icd10_code: str | None = None
    icd10_description: str | None = None
    age_at_onset: int | None = None
    onset_age_years: int | None = None
    is_deceased_due_to: bool = False
    notes: str | None = None


class FamilyHistoryUpdate(BaseModel):
    relationship: str | None = None
    relative_name: str | None = None
    condition_display: str | None = None
    icd10_code: str | None = None
    notes: str | None = None


@router.post("/family-history", summary="Create a family history record")
def create_family_history(
    body: FamilyHistoryCreate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_patient(db, body.patient_id, current_user.lab_id)
    record = ehr_service.create_family_history_record(db, body.model_dump(exclude_none=True))
    db.commit()
    return record.to_dict()


@router.get(
    "/family-history/{record_id}",
    summary="Get a family history record",
)
def get_family_history(
    record_id: str,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = ehr_service.get_family_history_record(db, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Family history record not found")
    _get_patient(db, record.patient_id, current_user.lab_id)
    return record.to_dict()


@router.put(
    "/family-history/{record_id}",
    summary="Update a family history record",
)
def update_family_history(
    record_id: str,
    body: FamilyHistoryUpdate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = ehr_service.get_family_history_record(db, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Family history record not found")
    _get_patient(db, record.patient_id, current_user.lab_id)
    updated = ehr_service.update_family_history_record(
        db,
        record_id,
        body.model_dump(exclude_none=True),
    )
    db.commit()
    return updated.to_dict()


@router.delete(
    "/family-history/{record_id}",
    summary="Soft-delete a family history record",
)
def delete_family_history(
    record_id: str,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = ehr_service.get_family_history_record(db, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Family history record not found")
    _get_patient(db, record.patient_id, current_user.lab_id)
    ehr_service.soft_delete_family_history_record(db, record_id)
    db.commit()
    return {"detail": "Family history record deleted"}


@router.get(
    "/patients/{patient_id}/family-history",
    summary="List family history for a patient",
)
def list_patient_family_history(
    patient_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_patient(db, patient_id, current_user.lab_id)
    records = ehr_service.list_family_history_by_patient(db, patient_id, skip, limit)
    return [r.to_dict() for r in records]


# ═══════════════════════════════════════════════════════════════════════════
# Social History
# ═══════════════════════════════════════════════════════════════════════════


class SocialHistoryCreate(BaseModel):
    patient_id: str
    citizen_id: str | None = None
    encounter_id: str | None = None
    practitioner_id: str | None = None
    smoking_status: SmokingStatus | None = None
    smoking_pack_years: int | None = None
    smoking_quit_date: date | None = None
    smoking_start_age: int | None = None
    smoking_frequency: str | None = None
    alcohol_status: AlcoholStatus | None = None
    alcohol_frequency: str | None = None
    alcohol_quit_date: date | None = None
    alcohol_start_age: int | None = None
    occupation: str | None = None
    occupation_history: dict[str, Any] | None = None
    occupational_hazards: str | None = None
    disability_type: DisabilityType | None = None
    disability_detail: str | None = None
    disability_since: date | None = None
    exercise_frequency: str | None = None
    diet_notes: str | None = None
    lifestyle_factors: dict[str, Any] | None = None
    notes: str | None = None
    metadata_: dict[str, Any] | None = None


class SocialHistoryUpdate(BaseModel):
    smoking_status: SmokingStatus | None = None
    smoking_pack_years: int | None = None
    alcohol_status: AlcoholStatus | None = None
    occupation: str | None = None
    disability_type: DisabilityType | None = None
    exercise_frequency: str | None = None
    diet_notes: str | None = None
    notes: str | None = None


@router.post("/social-history", summary="Create a social history record")
def create_social_history(
    body: SocialHistoryCreate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_patient(db, body.patient_id, current_user.lab_id)
    record = ehr_service.create_social_history_record(db, body.model_dump(exclude_none=True))
    db.commit()
    return record.to_dict()


@router.get(
    "/social-history/{record_id}",
    summary="Get a social history record",
)
def get_social_history(
    record_id: str,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = ehr_service.get_social_history_record(db, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Social history record not found")
    _get_patient(db, record.patient_id, current_user.lab_id)
    return record.to_dict()


@router.put(
    "/social-history/{record_id}",
    summary="Update a social history record",
)
def update_social_history(
    record_id: str,
    body: SocialHistoryUpdate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = ehr_service.get_social_history_record(db, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Social history record not found")
    _get_patient(db, record.patient_id, current_user.lab_id)
    updated = ehr_service.update_social_history_record(
        db,
        record_id,
        body.model_dump(exclude_none=True),
    )
    db.commit()
    return updated.to_dict()


@router.delete(
    "/social-history/{record_id}",
    summary="Soft-delete a social history record",
)
def delete_social_history(
    record_id: str,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = ehr_service.get_social_history_record(db, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Social history record not found")
    _get_patient(db, record.patient_id, current_user.lab_id)
    ehr_service.soft_delete_social_history_record(db, record_id)
    db.commit()
    return {"detail": "Social history record deleted"}


@router.get(
    "/patients/{patient_id}/social-history",
    summary="List social history for a patient",
)
def list_patient_social_history(
    patient_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_patient(db, patient_id, current_user.lab_id)
    records = ehr_service.list_social_history_by_patient(db, patient_id, skip, limit)
    return [r.to_dict() for r in records]


# ═══════════════════════════════════════════════════════════════════════════
# Risk Factors
# ═══════════════════════════════════════════════════════════════════════════


class RiskFactorCreate(BaseModel):
    patient_id: str
    citizen_id: str | None = None
    encounter_id: str | None = None
    practitioner_id: str | None = None
    risk_type: str
    risk_level: RiskLevel | None = None
    score_name: str | None = None
    score_value: float | None = None
    score_maximum: float | None = None
    score_version: str | None = None
    factors: dict[str, Any] | None = None
    recommendations: str | None = None
    assessment_date: datetime
    next_assessment_date: date | None = None
    is_high_risk: bool = False
    notes: str | None = None
    metadata_: dict[str, Any] | None = None


class RiskFactorUpdate(BaseModel):
    risk_level: RiskLevel | None = None
    score_value: float | None = None
    score_maximum: float | None = None
    factors: dict[str, Any] | None = None
    recommendations: str | None = None
    next_assessment_date: date | None = None
    is_high_risk: bool | None = None
    notes: str | None = None


@router.post("/risk-factors", summary="Create a risk factor record")
def create_risk_factor(
    body: RiskFactorCreate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_patient(db, body.patient_id, current_user.lab_id)
    record = ehr_service.create_risk_factor_record(db, body.model_dump(exclude_none=True))
    db.commit()
    return record.to_dict()


@router.get(
    "/risk-factors/{record_id}",
    summary="Get a risk factor record",
)
def get_risk_factor(
    record_id: str,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = ehr_service.get_risk_factor_record(db, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Risk factor record not found")
    _get_patient(db, record.patient_id, current_user.lab_id)
    return record.to_dict()


@router.put(
    "/risk-factors/{record_id}",
    summary="Update a risk factor record",
)
def update_risk_factor(
    record_id: str,
    body: RiskFactorUpdate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = ehr_service.get_risk_factor_record(db, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Risk factor record not found")
    _get_patient(db, record.patient_id, current_user.lab_id)
    updated = ehr_service.update_risk_factor_record(
        db,
        record_id,
        body.model_dump(exclude_none=True),
    )
    db.commit()
    return updated.to_dict()


@router.delete(
    "/risk-factors/{record_id}",
    summary="Soft-delete a risk factor record",
)
def delete_risk_factor(
    record_id: str,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = ehr_service.get_risk_factor_record(db, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Risk factor record not found")
    _get_patient(db, record.patient_id, current_user.lab_id)
    ehr_service.soft_delete_risk_factor_record(db, record_id)
    db.commit()
    return {"detail": "Risk factor record deleted"}


@router.get(
    "/patients/{patient_id}/risk-factors",
    summary="List risk factors for a patient",
)
def list_patient_risk_factors(
    patient_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_patient(db, patient_id, current_user.lab_id)
    records = ehr_service.list_risk_factors_by_patient(db, patient_id, skip, limit)
    return [r.to_dict() for r in records]


# ═══════════════════════════════════════════════════════════════════════════
# Immunizations
# ═══════════════════════════════════════════════════════════════════════════


class ImmunizationCreate(BaseModel):
    patient_id: str
    citizen_id: str | None = None
    encounter_id: str | None = None
    practitioner_id: str | None = None
    administrator_id: str | None = None
    vaccine_code: str
    vaccine_code_system: str | None = None
    vaccine_name: str
    vaccine_name_ar: str | None = None
    administration_date: datetime
    manufacturer: str | None = None
    lot_number: str | None = None
    expiry_date: date | None = None
    dose_number: int | None = None
    dose_series: str | None = None
    total_doses: int | None = None
    route: str | None = None
    site: str | None = None
    dose_quantity: str | None = None
    dose_unit: str | None = None
    is_completed: bool = True
    status: str = "completed"
    reason_not_given: str | None = None
    adverse_event: str | None = None
    adverse_event_reported: bool = False
    facility_id: str | None = None
    notes: str | None = None
    metadata_: dict[str, Any] | None = None


class ImmunizationUpdate(BaseModel):
    vaccine_name: str | None = None
    lot_number: str | None = None
    dose_number: int | None = None
    is_completed: bool | None = None
    status: str | None = None
    adverse_event: str | None = None
    notes: str | None = None


@router.post("/immunizations", summary="Create an immunization record")
def create_immunization(
    body: ImmunizationCreate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_patient(db, body.patient_id, current_user.lab_id)
    record = ehr_service.create_immunization_record(db, body.model_dump(exclude_none=True))
    db.commit()
    return record.to_dict()


@router.get(
    "/immunizations/{record_id}",
    summary="Get an immunization record",
)
def get_immunization(
    record_id: str,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = ehr_service.get_immunization_record(db, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Immunization record not found")
    _get_patient(db, record.patient_id, current_user.lab_id)
    return record.to_dict()


@router.put(
    "/immunizations/{record_id}",
    summary="Update an immunization record",
)
def update_immunization(
    record_id: str,
    body: ImmunizationUpdate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = ehr_service.get_immunization_record(db, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Immunization record not found")
    _get_patient(db, record.patient_id, current_user.lab_id)
    updated = ehr_service.update_immunization_record(
        db,
        record_id,
        body.model_dump(exclude_none=True),
    )
    db.commit()
    return updated.to_dict()


@router.delete(
    "/immunizations/{record_id}",
    summary="Soft-delete an immunization record",
)
def delete_immunization(
    record_id: str,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = ehr_service.get_immunization_record(db, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Immunization record not found")
    _get_patient(db, record.patient_id, current_user.lab_id)
    ehr_service.soft_delete_immunization_record(db, record_id)
    db.commit()
    return {"detail": "Immunization record deleted"}


@router.get(
    "/patients/{patient_id}/immunizations",
    summary="List immunizations for a patient",
)
def list_patient_immunizations(
    patient_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_patient(db, patient_id, current_user.lab_id)
    records = ehr_service.list_immunizations_by_patient(db, patient_id, skip, limit)
    return [r.to_dict() for r in records]


# ═══════════════════════════════════════════════════════════════════════════
# Clinical Attachments
# ═══════════════════════════════════════════════════════════════════════════


class AttachmentCreate(BaseModel):
    patient_id: str
    citizen_id: str | None = None
    encounter_id: str | None = None
    practitioner_id: str | None = None
    uploaded_by: str | None = None
    source_type: str
    source_id: str
    file_name: str
    file_type: str
    file_size_bytes: int | None = None
    storage_path: str | None = None
    storage_bucket: str | None = None
    content_hash: str | None = None
    mime_type: str | None = None
    caption: str | None = None
    caption_ar: str | None = None
    description: str | None = None
    is_watermarked: bool = False
    is_encrypted: bool = False
    is_confidential: bool = False
    is_archived: bool = False
    category: str | None = None
    sort_order: int = 0
    facility_id: str | None = None


class AttachmentUpdate(BaseModel):
    caption: str | None = None
    caption_ar: str | None = None
    description: str | None = None
    is_confidential: bool | None = None
    is_archived: bool | None = None
    category: str | None = None
    sort_order: int | None = None


@router.post("/attachments", summary="Create a clinical attachment record")
def create_attachment(
    body: AttachmentCreate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_patient(db, body.patient_id, current_user.lab_id)
    record = ehr_service.create_clinical_attachment(db, body.model_dump(exclude_none=True))
    db.commit()
    return record.to_dict()


@router.get(
    "/attachments/{attachment_id}",
    summary="Get a clinical attachment record",
)
def get_attachment(
    attachment_id: str,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = ehr_service.get_clinical_attachment(db, attachment_id)
    if not record:
        raise HTTPException(status_code=404, detail="Attachment not found")
    _get_patient(db, record.patient_id, current_user.lab_id)
    return record.to_dict()


@router.put(
    "/attachments/{attachment_id}",
    summary="Update a clinical attachment record",
)
def update_attachment(
    attachment_id: str,
    body: AttachmentUpdate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = ehr_service.get_clinical_attachment(db, attachment_id)
    if not record:
        raise HTTPException(status_code=404, detail="Attachment not found")
    _get_patient(db, record.patient_id, current_user.lab_id)
    updated = ehr_service.update_clinical_attachment(
        db,
        attachment_id,
        body.model_dump(exclude_none=True),
    )
    db.commit()
    return updated.to_dict()


@router.delete(
    "/attachments/{attachment_id}",
    summary="Soft-delete a clinical attachment record",
)
def delete_attachment(
    attachment_id: str,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = ehr_service.get_clinical_attachment(db, attachment_id)
    if not record:
        raise HTTPException(status_code=404, detail="Attachment not found")
    _get_patient(db, record.patient_id, current_user.lab_id)
    ehr_service.soft_delete_clinical_attachment(db, attachment_id)
    db.commit()
    return {"detail": "Attachment deleted"}


@router.get(
    "/patients/{patient_id}/attachments",
    summary="List attachments for a patient",
)
def list_patient_attachments(
    patient_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_patient(db, patient_id, current_user.lab_id)
    records = ehr_service.list_attachments_by_patient(db, patient_id, skip, limit)
    return [r.to_dict() for r in records]


# ═══════════════════════════════════════════════════════════════════════════
# Patient Timeline
# ═══════════════════════════════════════════════════════════════════════════


@router.get(
    "/patients/{patient_id}/timeline",
    summary="Get patient's unified clinical timeline",
)
def get_patient_timeline(
    patient_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    event_type: str | None = Query(None),
    live: bool = Query(False, description="If true, aggregates from all EHR tables in real-time"),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_patient(db, patient_id, current_user.lab_id)
    if live:
        events = ehr_service.build_live_timeline(db, patient_id, max_per_type=limit)
        return events[skip : skip + limit]
    records = ehr_service.get_patient_timeline(db, patient_id, skip, limit, event_type)
    return [r.to_dict() for r in records]


# ═══════════════════════════════════════════════════════════════════════════
# Legacy Backward-Compatible Endpoints
# ═══════════════════════════════════════════════════════════════════════════


@router.get("/patient/{patient_id}")
def get_patient_ehr(
    patient_id: str,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_patient(db, patient_id, current_user.lab_id)
    timeline = ehr_service.build_live_timeline(db, patient_id, max_per_type=5)
    return {
        "patient_id": patient_id,
        "timeline": timeline,
    }


@router.get("/patient/{patient_id}/summary")
def get_patient_summary(
    patient_id: str,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_patient(db, patient_id, current_user.lab_id)
    allergies = ehr_service.list_allergies_by_patient(db, patient_id, limit=5)
    conditions = ehr_service.list_conditions_by_patient(db, patient_id, limit=5)
    diagnoses = ehr_service.list_diagnoses_by_patient(db, patient_id, limit=5)
    medications = ehr_service.list_medication_statements_by_patient(db, patient_id, limit=5)
    immunizations = ehr_service.list_immunizations_by_patient(db, patient_id, limit=5)
    return {
        "patient_id": patient_id,
        "active_allergies": [a.to_dict() for a in allergies if a.status == AllergyStatus.ACTIVE],
        "active_conditions": [c.to_dict() for c in conditions if c.clinical_status == "active"],
        "active_diagnoses": [d.to_dict() for d in diagnoses if d.is_active],
        "current_medications": [m.to_dict() for m in medications if m.status == "active"],
        "immunizations": [i.to_dict() for i in immunizations],
    }
