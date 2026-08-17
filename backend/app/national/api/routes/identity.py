from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.national.exceptions import (
    DuplicateNewbornRegistrationError,
    ForeignerRegistrationError,
    NewbornRegistrationError,
)
from app.national.repositories.citizen_repository import CitizenRepository
from app.national.services.citizen_service import CitizenService
from app.national.services.identity_service import IdentityService
from app.security.dependencies import get_current_user, require_permission

router = APIRouter(prefix="/identity", tags=["Identity"])


class NewbornRegister(BaseModel):
    birth_certificate_number: str = Field(min_length=3, max_length=50)
    mother_national_id: str = Field(pattern=r"^\d{4,16}$")
    father_national_id: str = Field(pattern=r"^\d{4,16}$")
    first_name: str = Field(default="", max_length=100)
    last_name: str = Field(default="", max_length=100)
    date_of_birth: date
    gender: str = "unknown"
    birth_weight_grams: int | None = Field(default=None, ge=200, le=10000)
    hospital_registration_number: str | None = Field(default=None, max_length=50)
    birth_place: str | None = Field(default=None, max_length=200)
    birth_place_type: str | None = Field(default=None, max_length=50)
    delivery_method: str | None = Field(default=None, max_length=50)
    notes: str | None = Field(default=None, max_length=2000)


class ForeignerRegister(BaseModel):
    passport_number: str
    passport_country: str
    visa_number: str | None = None
    first_name: str
    last_name: str
    date_of_birth: date | None = None
    gender: str = "unknown"
    nationality: str = ""
    phone: str | None = None
    email: str | None = None


class VisitorRegister(BaseModel):
    passport_number: str
    first_name: str = ""
    last_name: str = ""
    date_of_birth: date | None = None
    gender: str = "unknown"
    nationality: str = ""
    passport_country: str = ""
    phone: str | None = None


class UnknownPatientRegister(BaseModel):
    description: str = "Unknown"
    approximate_date_of_birth: str | None = None
    gender: str = "unknown"
    found_location: str | None = None
    found_by: str | None = None


class IdentityMergeRequest(BaseModel):
    primary_citizen_id: str
    secondary_citizen_id: str
    reason: str
    method: str = "manual"


class IdentityResponse(BaseModel):
    citizen_id: str
    health_number: str
    newborn_id: str | None = None
    is_temporary: bool = False
    requires_merge: bool = False


def _get_identity_service(db: Session = Depends(get_db)) -> IdentityService:
    repo = CitizenRepository(db)
    citizen_service = CitizenService(repo, db)
    return IdentityService(citizen_service, repo, db)


@router.post("/newborn", response_model=IdentityResponse, status_code=201)
async def register_newborn(
    data: NewbornRegister,
    service: IdentityService = Depends(_get_identity_service),
    current_user=Depends(require_permission("newborn:register")),
):
    try:
        payload = data.model_dump()
        payload["actor_id"] = getattr(current_user, "id", None)
        payload["lab_id"] = getattr(current_user, "lab_id", None)
        payload["registered_by_hospital"] = getattr(current_user, "role", "") != "midwife"
        result = await service.register_newborn(payload)
        return IdentityResponse(
            citizen_id=result["citizen"].id,
            health_number=result["health_number"],
            newborn_id=result["newborn_id"],
            is_temporary=True,
        )
    except DuplicateNewbornRegistrationError as e:
        raise HTTPException(status_code=409, detail="Newborn record already exists") from e
    except NewbornRegistrationError as e:
        raise HTTPException(status_code=400, detail="Invalid request") from e


@router.post("/foreigner", response_model=IdentityResponse, status_code=201)
async def register_foreigner(
    data: ForeignerRegister,
    service: IdentityService = Depends(_get_identity_service),
    current_user=Depends(get_current_user),
):
    try:
        result = await service.register_foreigner(data.model_dump())
        return IdentityResponse(
            citizen_id=result["citizen"].id,
            health_number=result["health_number"],
        )
    except ForeignerRegistrationError as e:
        raise HTTPException(status_code=400, detail="Invalid request") from e


@router.post("/visitor", response_model=IdentityResponse, status_code=201)
async def register_visitor(
    data: VisitorRegister,
    service: IdentityService = Depends(_get_identity_service),
    current_user=Depends(get_current_user),
):
    result = await service.register_visitor(data.model_dump())
    return IdentityResponse(
        citizen_id=result["citizen"].id,
        health_number=result["health_number"],
        is_temporary=True,
    )


@router.post("/unknown", response_model=IdentityResponse, status_code=201)
async def register_unknown(
    data: UnknownPatientRegister,
    service: IdentityService = Depends(_get_identity_service),
    current_user=Depends(get_current_user),
):
    result = await service.register_unknown_patient(data.model_dump())
    return IdentityResponse(
        citizen_id=result["citizen"].id,
        health_number=result["health_number"],
        is_temporary=True,
        requires_merge=True,
    )


@router.post("/merge")
async def merge_identities(
    data: IdentityMergeRequest,
    current_user=Depends(get_current_user),
):
    return {
        "status": "pending",
        "primary_citizen_id": data.primary_citizen_id,
        "secondary_citizen_id": data.secondary_citizen_id,
        "reason": data.reason,
        "message": "Merge submitted for review",
    }
