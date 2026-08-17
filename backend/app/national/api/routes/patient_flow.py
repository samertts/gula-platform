"""High-throughput government-hospital patient flow endpoints.

The API intentionally exposes a small command surface: create an arrival,
inspect a queue, and perform a guarded state transition. Clinical detail stays
in Encounter/EHR services; this module orchestrates the operational path.
"""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import case
from sqlalchemy.orm import Session

from app._compat import UTC
from app.database import get_db
from app.domain.exceptions import ConflictError, NotFoundError
from app.models.lab_user import LabUser
from app.national.domain.encounter import Encounter
from app.national.domain.patient import Patient as NationalPatient
from app.national.enums import EncounterStatus, EncounterType
from app.national.exceptions import EncounterNotFoundError
from app.national.services.encounter_service import (
    transition_flow_state,
)
from app.security.dependencies import get_current_user, require_permission
from app.services.route_audit import audit_mutation
from app.services.hospital_service import HospitalService

# AUDIT_DELEGATED: transition_flow_state records immutable before/after audit entries.

router = APIRouter(prefix="/patient-flow", tags=["Patient Flow"])


class ArrivalCreate(BaseModel):
    patient_id: str
    hospital_id: int
    encounter_type: EncounterType = EncounterType.OUTPATIENT
    priority: str = "routine"
    reason_code: str | None = None
    reason_description: str | None = None
    is_emergency: bool = False
    idempotency_key: str | None = Field(default=None, max_length=64)

    @field_validator("patient_id")
    @classmethod
    def validate_patient_id(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized or len(normalized) > 26:
            raise ValueError("patient_id must be between 1 and 26 characters")
        return normalized

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {"routine", "urgent", "asap", "stat"}:
            raise ValueError("priority must be routine, urgent, asap, or stat")
        return normalized

    @field_validator("idempotency_key")
    @classmethod
    def validate_idempotency_key(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized:
            raise ValueError("idempotency_key cannot be empty")
        return normalized


class TransitionCommand(BaseModel):
    target_state: str = Field(min_length=3, max_length=30)
    expected_version: int | None = Field(default=None, ge=1)


class PatientFlowResponse(BaseModel):
    id: str
    patient_id: str
    hospital_id: int | None
    encounter_type: str
    status: str
    flow_state: str
    priority: str | None
    is_emergency: bool
    version: int
    period_start: datetime | None
    arrival_at: datetime | None
    triage_at: datetime | None
    admission_at: datetime | None
    discharge_at: datetime | None


def _response(encounter: Encounter) -> PatientFlowResponse:
    return PatientFlowResponse(
        id=encounter.id,
        patient_id=encounter.patient_id,
        hospital_id=encounter.hospital_id,
        encounter_type=encounter.encounter_type.value,
        status=encounter.status.value,
        flow_state=encounter.flow_state,
        priority=encounter.priority,
        is_emergency=bool(encounter.is_emergency),
        version=encounter.version,
        period_start=encounter.period_start,
        arrival_at=encounter.arrival_at,
        triage_at=encounter.triage_at,
        admission_at=encounter.admission_at,
        discharge_at=encounter.discharge_at,
    )


@router.post(
    "/arrivals",
    response_model=PatientFlowResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("hospital:flow:write"))],
)
def create_arrival(
    data: ArrivalCreate,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    try:
        HospitalService.get_hospital(db, data.hospital_id, current_user.lab_id)
        patient = db.query(NationalPatient).filter(
            NationalPatient.id == data.patient_id,
            NationalPatient.lab_id == current_user.lab_id,
            ~NationalPatient.is_deleted,
            NationalPatient.is_active,
            ~NationalPatient.is_merged,
        ).first()
        if patient is None:
            raise NotFoundError("National patient not found or identity is not active")

        if data.idempotency_key:
            existing = db.query(Encounter).filter(
                Encounter.lab_id == current_user.lab_id,
                Encounter.hospital_id == data.hospital_id,
                Encounter.idempotency_key == data.idempotency_key,
                ~Encounter.is_deleted,
            ).first()
            if existing is not None:
                return _response(existing)

        now = datetime.now(UTC)
        encounter = Encounter(
            lab_id=current_user.lab_id,
            created_by=current_user.id,
            patient_id=data.patient_id,
            hospital_id=data.hospital_id,
            encounter_type=data.encounter_type,
            status=EncounterStatus.PLANNED,
            flow_state="planned",
            priority=data.priority,
            is_emergency=data.is_emergency,
            reason_code=data.reason_code,
            reason_description=data.reason_description,
            period_start=now,
            idempotency_key=data.idempotency_key,
        )
        db.add(encounter)
        db.flush()
        audit_mutation(
            db,
            action="encounter.arrival.create",
            resource_type="Encounter",
            resource_id=encounter.id,
            user=current_user,
            lab_id=current_user.lab_id,
            after={"patient_id": data.patient_id, "hospital_id": data.hospital_id, "flow_state": "planned", "version": encounter.version},
            details={"idempotency_key": data.idempotency_key},
        )
        encounter = transition_flow_state(
            db,
            encounter.id,
            "arrived",
            current_user.id,
            expected_version=encounter.version,
            lab_id=current_user.lab_id,
        )
        db.commit()
        return _response(encounter)
    except (ConflictError, NotFoundError) as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get(
    "/queue",
    response_model=list[PatientFlowResponse],
    dependencies=[Depends(require_permission("hospital:flow:read"))],
)
def get_queue(
    hospital_id: int,
    flow_state: str | None = Query(None, min_length=3, max_length=30),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    query = db.query(Encounter).filter(
        Encounter.lab_id == current_user.lab_id,
        Encounter.hospital_id == hospital_id,
        ~Encounter.is_deleted,
        Encounter.flow_state.notin_(["discharged", "cancelled"]),
    )
    if flow_state:
        query = query.filter(Encounter.flow_state == flow_state)
    priority_rank = case(
        (Encounter.priority == "stat", 0),
        (Encounter.priority == "asap", 1),
        (Encounter.priority == "urgent", 2),
        else_=3,
    )
    return [_response(item) for item in query.order_by(
        case((Encounter.is_emergency.is_(True), 0), else_=1),
        priority_rank,
        Encounter.period_start.asc(),
    ).limit(limit).all()]


@router.post(
    "/{encounter_id}/transition",
    response_model=PatientFlowResponse,
    dependencies=[Depends(require_permission("hospital:flow:write"))],
)
def transition(
    encounter_id: str,
    command: TransitionCommand,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    try:
        encounter = db.query(Encounter).filter(
            Encounter.id == encounter_id,
            Encounter.lab_id == current_user.lab_id,
            ~Encounter.is_deleted,
        ).first()
        if encounter is None:
            raise EncounterNotFoundError(encounter_id)
        updated = transition_flow_state(
            db,
            encounter_id,
            command.target_state,
            current_user.id,
            expected_version=command.expected_version,
            lab_id=current_user.lab_id,
        )

        db.commit()
        return _response(updated)
    except EncounterNotFoundError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Encounter not found") from exc
    except ConflictError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
