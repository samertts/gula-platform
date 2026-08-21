from __future__ import annotations

from typing import Any, cast

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.clinical_gateway.access_context import ClinicalAccessContext
from app.clinical_gateway.context import ClinicalGatewayBlocked, ClinicalGatewayContextResolver
from app.clinical_gateway.encounter_service import EncounterService
from app.database import get_db
from app.identity.api.workspaces import NiamActor, get_current_niam_actor_sync
from app.national.domain.encounter import Encounter
from app.national.domain.patient import Patient as NationalPatient

router = APIRouter(prefix="/api/v1/clinical", tags=["Canonical Clinical Encounters"])


class EncounterCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    patient_id: int = Field(gt=0)
    encounter_type: str = Field(min_length=1, max_length=32)
    reason_code: str | None = Field(default=None, max_length=50)
    reason_description: str | None = Field(default=None, max_length=2000)
    priority: str = Field(default="routine", min_length=1, max_length=20)
    is_emergency: bool = False


class EncounterCompleteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    disposition: str | None = Field(default=None, max_length=200)
    notes: str | None = Field(default=None, max_length=4000)


def _access_for_patient(db: Session, actor: NiamActor, patient_id: int, purpose: str, permissions: frozenset[str]) -> ClinicalAccessContext:
    gateway = ClinicalGatewayContextResolver(db).resolve(actor)
    return ClinicalAccessContext.from_gateway_for_patient(
        db,
        gateway,
        patient_id=patient_id,
        purpose=purpose,
        permissions=permissions,
    )


def _access_for_encounter(db: Session, actor: NiamActor, encounter_id: str, purpose: str, permissions: frozenset[str]) -> ClinicalAccessContext:
    encounter = db.get(Encounter, encounter_id)
    if encounter is None:
        raise ClinicalGatewayBlocked("encounter_not_found")
    patient = db.get(NationalPatient, encounter.patient_id)
    if patient is None or patient.lab_patient_id is None:
        raise ClinicalGatewayBlocked("national_patient_mapping_missing")
    return _access_for_patient(db, actor, int(patient.lab_patient_id), purpose, permissions)


@router.post("/encounters", status_code=status.HTTP_201_CREATED)
def create_encounter(
    payload: EncounterCreateRequest,
    actor: NiamActor = Depends(get_current_niam_actor_sync),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    try:
        access = _access_for_patient(db, actor, payload.patient_id, "encounter.create", frozenset({"create"}))
        encounter = EncounterService(db).create(
            access=access,
            patient_id=payload.patient_id,
            encounter_type=payload.encounter_type,
            reason_code=payload.reason_code,
            reason_description=payload.reason_description,
            priority=payload.priority,
            is_emergency=payload.is_emergency,
        )
        db.commit()
        return cast(dict[str, Any], EncounterService.to_safe_dict(encounter))
    except ClinicalGatewayBlocked as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Encounter creation is not authorized") from exc


@router.post("/encounters/{encounter_id}/start")
def start_encounter(
    encounter_id: str,
    actor: NiamActor = Depends(get_current_niam_actor_sync),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    try:
        access = _access_for_encounter(db, actor, encounter_id, "encounter.start", frozenset({"update"}))
        encounter = EncounterService(db).start(access=access, encounter_id=encounter_id)
        db.commit()
        return cast(dict[str, Any], EncounterService.to_safe_dict(encounter))
    except ClinicalGatewayBlocked as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Encounter start is not authorized") from exc


@router.post("/encounters/{encounter_id}/complete")
def complete_encounter(
    encounter_id: str,
    payload: EncounterCompleteRequest,
    actor: NiamActor = Depends(get_current_niam_actor_sync),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    try:
        access = _access_for_encounter(db, actor, encounter_id, "encounter.complete", frozenset({"update"}))
        encounter = EncounterService(db).complete(
            access=access,
            encounter_id=encounter_id,
            disposition=payload.disposition,
            notes=payload.notes,
        )
        db.commit()
        return cast(dict[str, Any], EncounterService.to_safe_dict(encounter))
    except ClinicalGatewayBlocked as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Encounter completion is not authorized") from exc
