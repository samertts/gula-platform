from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.national.exceptions import ForeignerRegistrationError, NewbornRegistrationError
from app.national.repositories.citizen_repository import CitizenRepository
from app.national.services.citizen_service import CitizenService
from app.national.services.identity_service import IdentityService
from app.security.dependencies import get_current_user

router = APIRouter(prefix="/identity", tags=["Identity"])


class NewbornRegister(BaseModel):
    birth_certificate_number: str
    first_name: str = ""
    last_name: str = ""
    date_of_birth: date | None = None
    gender: str = "unknown"
    mother_id: str
    mother_name: str | None = None
    father_id: str | None = None
    father_name: str | None = None
    birth_weight_grams: int | None = None
    hospital_id: str | None = None


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
    is_temporary: bool = False
    requires_merge: bool = False


def _get_identity_service(db: Session = Depends(get_db)) -> IdentityService:
    repo = CitizenRepository(db)
    citizen_service = CitizenService(repo, db)
    return IdentityService(citizen_service, repo)


@router.post("/newborn", response_model=IdentityResponse, status_code=201)
async def register_newborn(
    data: NewbornRegister,
    service: IdentityService = Depends(_get_identity_service),
    current_user=Depends(get_current_user),
):
    try:
        result = await service.register_newborn(data.model_dump())
        return IdentityResponse(
            citizen_id=result["citizen"].id,
            health_number=result["health_number"],
        )
    except NewbornRegistrationError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


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
        raise HTTPException(status_code=400, detail=str(e)) from e


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
