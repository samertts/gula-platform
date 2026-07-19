from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.national.domain.citizen import Citizen
from app.national.exceptions import CitizenNotFoundError, DuplicateHealthNumberError
from app.national.repositories.citizen_repository import CitizenRepository
from app.national.services.citizen_service import CitizenService
from app.security.dependencies import get_current_user

router = APIRouter(prefix="/citizens", tags=["Citizens"])


class CitizenCreate(BaseModel):
    first_name: str
    father_name: str | None = None
    grandfather_name: str | None = None
    last_name: str
    mother_name: str | None = None
    date_of_birth: date | None = None
    gender: str = "unknown"
    phone: str | None = None
    email: str | None = None
    governorate: str | None = None
    nationality: str = "Iraqi"
    marital_status: str | None = None


class CitizenUpdate(BaseModel):
    first_name: str | None = None
    father_name: str | None = None
    grandfather_name: str | None = None
    last_name: str | None = None
    mother_name: str | None = None
    date_of_birth: date | None = None
    gender: str | None = None
    phone: str | None = None
    email: str | None = None
    governorate: str | None = None
    nationality: str | None = None
    marital_status: str | None = None


class CitizenResponse(BaseModel):
    id: str
    health_number: str
    first_name: str
    father_name: str | None = None
    grandfather_name: str | None = None
    last_name: str
    mother_name: str | None = None
    date_of_birth: str | None = None
    gender: str
    phone: str | None = None
    email: str | None = None
    governorate: str | None = None
    nationality: str
    identity_status: str
    is_deceased: bool = False
    is_vip: bool = False
    created_at: str
    updated_at: str

    @classmethod
    def from_orm(cls, citizen: Citizen) -> CitizenResponse:
        return cls(
            id=citizen.id,
            health_number=citizen.health_number or "",
            first_name=citizen.first_name or "",
            father_name=citizen.father_name,
            grandfather_name=citizen.grandfather_name,
            last_name=citizen.last_name or "",
            mother_name=citizen.mother_name,
            date_of_birth=citizen.date_of_birth.isoformat() if citizen.date_of_birth else None,
            gender=citizen.gender or "unknown",
            phone=citizen.phone,
            email=citizen.email,
            governorate=citizen.governorate,
            nationality=citizen.nationality or "Iraqi",
            identity_status=citizen.identity_status or "active",
            is_deceased=citizen.is_deceased or False,
            is_vip=citizen.is_vip or False,
            created_at=citizen.created_at.isoformat() if citizen.created_at else "",
            updated_at=citizen.updated_at.isoformat() if citizen.updated_at else "",
        )


def _get_citizen_service(db: Session = Depends(get_db)) -> CitizenService:
    repo = CitizenRepository(db)
    return CitizenService(repo, db)


@router.post("/", response_model=CitizenResponse, status_code=201)
async def create_citizen(
    data: CitizenCreate,
    service: CitizenService = Depends(_get_citizen_service),
    current_user=Depends(get_current_user),
):
    try:
        citizen = await service.register_citizen(data.model_dump())
        return CitizenResponse.from_orm(citizen)
    except DuplicateHealthNumberError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e


@router.get("/{citizen_id}", response_model=CitizenResponse)
async def get_citizen(
    citizen_id: str,
    service: CitizenService = Depends(_get_citizen_service),
    current_user=Depends(get_current_user),
):
    try:
        citizen = await service.get_citizen(citizen_id)
        return CitizenResponse.from_orm(citizen)
    except CitizenNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.put("/{citizen_id}", response_model=CitizenResponse)
async def update_citizen(
    citizen_id: str,
    data: CitizenUpdate,
    service: CitizenService = Depends(_get_citizen_service),
    current_user=Depends(get_current_user),
):
    try:
        citizen = await service.update_citizen(citizen_id, data.model_dump(exclude_none=True))
        return CitizenResponse.from_orm(citizen)
    except CitizenNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.get("/search/{query}", response_model=list[CitizenResponse])
async def search_citizens(
    query: str,
    skip: int = 0,
    limit: int = 20,
    service: CitizenService = Depends(_get_citizen_service),
    current_user=Depends(get_current_user),
):
    citizens = await service.search_citizens(query, skip=skip, limit=limit)
    return [CitizenResponse.from_orm(c) for c in citizens]
