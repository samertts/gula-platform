from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.national.domain.encounter import Encounter
from app.national.enums import EncounterStatus, EncounterType
from app.national.exceptions import EncounterNotFoundError
from app.national.services.encounter_service import (
    cancel_encounter as service_cancel_encounter,
)
from app.national.services.encounter_service import (
    complete_encounter as service_complete_encounter,
)
from app.national.services.encounter_service import (
    create_encounter as service_create_encounter,
)
from app.national.services.encounter_service import (
    delete_encounter as service_delete_encounter,
)
from app.national.services.encounter_service import (
    get_encounter as service_get_encounter,
)
from app.national.services.encounter_service import (
    get_encounters_by_patient as service_get_encounters_by_patient,
)
from app.national.services.encounter_service import (
    search_encounters as service_search_encounters,
)
from app.national.services.encounter_service import (
    update_encounter as service_update_encounter,
)
from app.security.dependencies import get_current_user

router = APIRouter(prefix="/encounters", tags=["Encounters"])


class EncounterCreate(BaseModel):
    encounter_type: EncounterType
    patient_id: str
    citizen_id: str | None = None
    organization_id: str | None = None
    facility_id: str | None = None
    department_id: str | None = None
    practitioner_id: str | None = None
    referral_id: str | None = None
    period_start: datetime
    period_end: datetime | None = None
    duration_minutes: int | None = None
    reason_code: str | None = None
    reason_description: str | None = None
    diagnosis_code: str | None = None
    diagnosis_description: str | None = None
    icd10_code: str | None = None
    priority: str | None = "routine"
    is_emergency: bool = False
    disposition: str | None = None
    notes: str | None = None


class EncounterUpdate(BaseModel):
    encounter_type: EncounterType | None = None
    facility_id: str | None = None
    department_id: str | None = None
    practitioner_id: str | None = None
    period_start: datetime | None = None
    period_end: datetime | None = None
    duration_minutes: int | None = None
    reason_code: str | None = None
    reason_description: str | None = None
    diagnosis_code: str | None = None
    diagnosis_description: str | None = None
    icd10_code: str | None = None
    priority: str | None = None
    is_emergency: bool | None = None
    disposition: str | None = None
    notes: str | None = None


class EncounterResponse(BaseModel):
    id: str
    encounter_type: str
    status: str
    patient_id: str
    citizen_id: str | None
    organization_id: str | None
    facility_id: str | None
    department_id: str | None
    practitioner_id: str | None
    referral_id: str | None
    period_start: datetime | None
    period_end: datetime | None
    duration_minutes: int | None
    reason_code: str | None
    reason_description: str | None
    diagnosis_code: str | None
    diagnosis_description: str | None
    icd10_code: str | None
    priority: str | None
    is_emergency: bool | None
    disposition: str | None
    notes: str | None
    is_deleted: bool
    created_at: datetime | None
    updated_at: datetime | None

    class Config:
        from_attributes = True


class EncounterListResponse(BaseModel):
    items: list[EncounterResponse]
    total: int
    skip: int
    limit: int


class FHIREncounterResponse(BaseModel):
    resourceType: str = "Encounter"
    id: str
    status: str
    class_: dict[str, Any]
    subject: dict[str, Any] | None
    participant: list[dict[str, Any]] | None
    period: dict[str, Any] | None
    reasonCode: list[dict[str, Any]] | None
    diagnosis: list[dict[str, Any]] | None
    hospitalization: dict[str, Any] | None
    location: list[dict[str, Any]] | None


def _to_fhir(encounter: Encounter) -> dict[str, Any]:
    status_map = {
        EncounterStatus.PLANNED: "planned",
        EncounterStatus.IN_PROGRESS: "in-progress",
        EncounterStatus.ON_HOLD: "on-hold",
        EncounterStatus.DISCHARGED: "discharged",
        EncounterStatus.COMPLETED: "completed",
        EncounterStatus.CANCELLED: "cancelled",
        EncounterStatus.ENTERED_IN_ERROR: "entered-in-error",
        EncounterStatus.UNKNOWN: "unknown",
    }
    class_map = {
        EncounterType.OUTPATIENT: {"system": "http://terminology.hl7.org/CodeSystem/v3-ActCode", "code": "AMB", "display": "ambulatory"},
        EncounterType.INPATIENT: {"system": "http://terminology.hl7.org/CodeSystem/v3-ActCode", "code": "IMP", "display": "inpatient encounter"},
        EncounterType.EMERGENCY: {"system": "http://terminology.hl7.org/CodeSystem/v3-ActCode", "code": "EMER", "display": "emergency"},
        EncounterType.HOME_HEALTH: {"system": "http://terminology.hl7.org/CodeSystem/v3-ActCode", "code": "HH", "display": "home health"},
        EncounterType.TELEHEALTH: {"system": "http://terminology.hl7.org/CodeSystem/v3-ActCode", "code": "VR", "display": "virtual"},
        EncounterType.VIRTUAL: {"system": "http://terminology.hl7.org/CodeSystem/v3-ActCode", "code": "VR", "display": "virtual"},
        EncounterType.FOLLOW_UP: {"system": "http://terminology.hl7.org/CodeSystem/v3-ActCode", "code": "FLD", "display": "field"},
        EncounterType.CONSULTATION: {"system": "http://terminology.hl7.org/CodeSystem/v3-ActCode", "code": "CONSULT", "display": "consultation"},
        EncounterType.OTHER: {"system": "http://terminology.hl7.org/CodeSystem/v3-ActCode", "code": "OTHER", "display": "other"},
    }
    return {
        "resourceType": "Encounter",
        "id": encounter.id,
        "status": status_map.get(encounter.status, "unknown"),
        "class": class_map.get(encounter.encounter_type, {"code": "OTHER", "display": "other"}),
        "subject": {"reference": f"Patient/{encounter.patient_id}"} if encounter.patient_id else None,
        "participant": [{"individual": {"reference": f"Practitioner/{encounter.practitioner_id}"}}] if encounter.practitioner_id else None,
        "period": {
            "start": encounter.period_start.isoformat() if encounter.period_start else None,
            "end": encounter.period_end.isoformat() if encounter.period_end else None,
        },
        "reasonCode": [{"coding": [{"code": encounter.reason_code}], "text": encounter.reason_description}] if encounter.reason_code else None,
        "diagnosis": [{"condition": {"coding": [{"code": encounter.diagnosis_code}]}, "use": {"coding": [{"code": "DD"}]}}] if encounter.diagnosis_code else None,
    }


@router.post("/", response_model=EncounterResponse, status_code=status.HTTP_201_CREATED)
async def create_encounter(
    data: EncounterCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    encounter_data = data.model_dump(exclude_none=True)
    encounter_data["status"] = EncounterStatus.PLANNED
    encounter = service_create_encounter(db, encounter_data)
    db.commit()
    return encounter


@router.get("/{encounter_id}", response_model=EncounterResponse)
async def get_encounter(
    encounter_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    encounter = service_get_encounter(db, encounter_id)
    if not encounter:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Encounter not found: {encounter_id}")
    return encounter


@router.put("/{encounter_id}", response_model=EncounterResponse)
async def update_encounter(
    encounter_id: str,
    data: EncounterUpdate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    try:
        encounter = service_update_encounter(db, encounter_id, data.model_dump(exclude_none=True))
        db.commit()
        return encounter
    except EncounterNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Encounter not found: {encounter_id}") from e


@router.delete("/{encounter_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_encounter(
    encounter_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    try:
        service_delete_encounter(db, encounter_id)
        db.commit()
    except EncounterNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Encounter not found: {encounter_id}") from e


@router.put("/{encounter_id}/complete", response_model=EncounterResponse)
async def complete_encounter(
    encounter_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    try:
        encounter = service_complete_encounter(db, encounter_id, user.id)
        db.commit()
        return encounter
    except EncounterNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Encounter not found: {encounter_id}") from e


@router.put("/{encounter_id}/cancel", response_model=EncounterResponse)
async def cancel_encounter(
    encounter_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    try:
        encounter = service_cancel_encounter(db, encounter_id, user.id)
        db.commit()
        return encounter
    except EncounterNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Encounter not found: {encounter_id}") from e


@router.get("/by-patient/{patient_id}", response_model=EncounterListResponse)
async def get_encounters_by_patient(
    patient_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    encounters = service_get_encounters_by_patient(db, patient_id, skip=skip, limit=limit)
    return EncounterListResponse(
        items=encounters,
        total=len(encounters),
        skip=skip,
        limit=limit,
    )


@router.get("/search", response_model=EncounterListResponse)
async def search_encounters(
    patient_id: str | None = Query(None),
    encounter_type: str | None = Query(None),
    status: str | None = Query(None),
    facility_id: str | None = Query(None),
    practitioner_id: str | None = Query(None),
    period_start: datetime | None = Query(None),
    period_end: datetime | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    encounters = service_search_encounters(
        db,
        patient_id=patient_id,
        encounter_type=encounter_type,
        status=status,
        facility_id=facility_id,
        practitioner_id=practitioner_id,
        period_start=period_start,
        period_end=period_end,
        skip=skip,
        limit=limit,
    )
    return EncounterListResponse(
        items=encounters,
        total=len(encounters),
        skip=skip,
        limit=limit,
    )


@router.get("/{encounter_id}/fhir", response_model=FHIREncounterResponse)
async def get_encounter_fhir(
    encounter_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    encounter = service_get_encounter(db, encounter_id)
    if not encounter:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Encounter not found: {encounter_id}")
    return _to_fhir(encounter)
