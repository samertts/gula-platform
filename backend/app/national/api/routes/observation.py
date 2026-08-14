from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.database import get_db
from app.national.services.observation_service import (
    create_observation as service_create_observation,
)
from app.national.services.observation_service import (
    delete_observation as service_delete_observation,
)
from app.national.services.observation_service import (
    get_observation as service_get_observation,
)
from app.national.services.observation_service import (
    get_observations_by_encounter as service_get_observations_by_encounter,
)
from app.national.services.observation_service import (
    get_observations_by_patient as service_get_observations_by_patient,
)
from app.national.services.observation_service import (
    get_vital_signs_by_patient as service_get_vital_signs_by_patient,
)
from app.national.services.observation_service import (
    search_observations as service_search_observations,
)
from app.national.services.observation_service import (
    update_observation as service_update_observation,
)
from app.security.dependencies import get_current_user

router = APIRouter(prefix="/observations", tags=["Observations"])


class ObservationCreate(BaseModel):
    patient_id: str
    citizen_id: str | None = None
    encounter_id: str | None = None
    practitioner_id: str | None = None
    category: str | None = None
    code: str
    code_system: str | None = None
    code_display: str | None = None
    code_display_ar: str | None = None
    value_quantity: str | None = None
    value_text: str | None = None
    value_boolean: bool | None = None
    value_integer: int | None = None
    value_range_low: str | None = None
    value_range_high: str | None = None
    unit: str | None = None
    data_absent_reason: str | None = None
    interpretation: str | None = None
    reference_range_low: str | None = None
    reference_range_high: str | None = None
    reference_range_text: str | None = None
    status: str | None = "final"
    effective_datetime: datetime | None = None
    issued_at: datetime | None = None
    body_site: str | None = None
    method: str | None = None
    device_id: str | None = None
    notes: str | None = None


class ObservationUpdate(BaseModel):
    category: str | None = None
    code: str | None = None
    code_system: str | None = None
    code_display: str | None = None
    code_display_ar: str | None = None
    value_quantity: str | None = None
    value_text: str | None = None
    value_boolean: bool | None = None
    value_integer: int | None = None
    value_range_low: str | None = None
    value_range_high: str | None = None
    unit: str | None = None
    data_absent_reason: str | None = None
    interpretation: str | None = None
    reference_range_low: str | None = None
    reference_range_high: str | None = None
    reference_range_text: str | None = None
    status: str | None = None
    effective_datetime: datetime | None = None
    body_site: str | None = None
    method: str | None = None
    device_id: str | None = None
    notes: str | None = None


class ObservationResponse(BaseModel):
    id: str
    patient_id: str
    citizen_id: str | None
    encounter_id: str | None
    practitioner_id: str | None
    category: str | None
    code: str
    code_system: str | None
    code_display: str | None
    code_display_ar: str | None
    value_quantity: str | None
    value_text: str | None
    value_boolean: bool | None
    value_integer: int | None
    value_range_low: str | None
    value_range_high: str | None
    unit: str | None
    data_absent_reason: str | None
    interpretation: str | None
    reference_range_low: str | None
    reference_range_high: str | None
    reference_range_text: str | None
    status: str | None
    effective_datetime: datetime | None
    issued_at: datetime | None
    body_site: str | None
    method: str | None
    device_id: str | None
    notes: str | None
    is_deleted: bool
    created_at: datetime | None
    updated_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class ObservationListResponse(BaseModel):
    items: list[ObservationResponse]
    total: int
    skip: int
    limit: int


@router.post("/", response_model=ObservationResponse, status_code=status.HTTP_201_CREATED)
async def create_observation(
    data: ObservationCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    observation = service_create_observation(db, data.model_dump(exclude_none=True))
    db.commit()
    return observation


@router.get("/{observation_id}", response_model=ObservationResponse)
async def get_observation(
    observation_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    observation = service_get_observation(db, observation_id)
    if not observation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Observation not found: {observation_id}")
    return observation


@router.put("/{observation_id}", response_model=ObservationResponse)
async def update_observation(
    observation_id: str,
    data: ObservationUpdate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    try:
        observation = service_update_observation(db, observation_id, data.model_dump(exclude_none=True))
        db.commit()
        return observation
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Observation not found: {observation_id}") from e


@router.delete("/{observation_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def delete_observation(
    observation_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    try:
        service_delete_observation(db, observation_id)
        db.commit()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Observation not found: {observation_id}") from e


@router.get("/by-patient/{patient_id}", response_model=ObservationListResponse)
async def get_observations_by_patient(
    patient_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    observations = service_get_observations_by_patient(db, patient_id, skip=skip, limit=limit)
    return ObservationListResponse(
        items=observations,
        total=len(observations),
        skip=skip,
        limit=limit,
    )


@router.get("/by-encounter/{encounter_id}", response_model=ObservationListResponse)
async def get_observations_by_encounter(
    encounter_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    observations = service_get_observations_by_encounter(db, encounter_id, skip=skip, limit=limit)
    return ObservationListResponse(
        items=observations,
        total=len(observations),
        skip=skip,
        limit=limit,
    )


@router.get("/vital-signs/{patient_id}", response_model=ObservationListResponse)
async def get_vital_signs(
    patient_id: str,
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    observations = service_get_vital_signs_by_patient(db, patient_id, limit=limit)
    return ObservationListResponse(
        items=observations,
        total=len(observations),
        skip=0,
        limit=limit,
    )


@router.get("/search", response_model=ObservationListResponse)
async def search_observations(
    patient_id: str | None = Query(None),
    category: str | None = Query(None),
    code: str | None = Query(None),
    status: str | None = Query(None),
    effective_start: datetime | None = Query(None),
    effective_end: datetime | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    observations = service_search_observations(
        db,
        patient_id=patient_id,
        category=category,
        code=code,
        status=status,
        effective_start=effective_start,
        effective_end=effective_end,
        skip=skip,
        limit=limit,
    )
    return ObservationListResponse(
        items=observations,
        total=len(observations),
        skip=skip,
        limit=limit,
    )
