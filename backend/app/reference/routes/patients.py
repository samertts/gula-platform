from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query

from app.reference.infrastructure.dependencies import get_patient_service
from app.reference.services import (
    DomainError,
    DuplicatePatientError,
    Gender,
    InvalidPatientDataError,
    PatientDomain,
    PatientNotFoundError,
)
from app.reference.services.patient_service import PatientService

router = APIRouter(prefix="/reference/patients", tags=["reference-patients"])


@router.get("/{patient_id}")
async def get_patient(
    patient_id: str,
    service: PatientService = Depends(get_patient_service),
) -> dict:
    try:
        patient = await service.get_patient(patient_id)
    except PatientNotFoundError as e:
        raise HTTPException(status_code=404, detail="Resource not found") from e
    return _patient_to_response(patient)


@router.post("")
async def create_patient(
    name: str = Query(..., description="اسم المريض"),
    date_of_birth: date | None = Query(None, description="تاريخ الميلاد"),
    gender: Gender | None = Query(None, description="الجنس (ذكر / أنثى)"),
    phone: str = Query("", description="رقم الهاتف"),
    lab_id: str = Query(..., description="معرف المختبر"),
    national_id: str | None = Query(None, description="الرقم الوطني"),
    address: str = Query("", description="العنوان"),
    service: PatientService = Depends(get_patient_service),
) -> dict:
    patient = PatientDomain(
        name=name,
        date_of_birth=date_of_birth,
        gender=gender,
        phone=phone,
        lab_id=lab_id,
        national_id=national_id,
        address=address,
    )
    try:
        created = await service.create_patient(patient)
    except InvalidPatientDataError as e:
        raise HTTPException(status_code=400, detail="Invalid request") from e
    except DuplicatePatientError as e:
        raise HTTPException(status_code=409, detail="Resource already exists") from e
    except DomainError as e:
        raise HTTPException(status_code=400, detail="Invalid request") from e
    return _patient_to_response(created)


@router.get("")
async def search_patients(
    name: str | None = Query(None, description="البحث بالاسم"),
    phone: str | None = Query(None, description="رقم الهاتف"),
    lab_id: str | None = Query(None, description="معرف المختبر"),
    national_id: str | None = Query(None, description="الرقم الوطني"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: PatientService = Depends(get_patient_service),
) -> dict:
    results, total = await service.search_patients(
        name=name,
        phone=phone,
        lab_id=lab_id,
        national_id=national_id,
        limit=limit,
        offset=offset,
    )
    return {
        "results": [_patient_to_response(p) for p in results],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


def _patient_to_response(patient: PatientDomain) -> dict:
    return {
        "patient_id": patient.patient_id,
        "name": patient.name,
        "date_of_birth": (
            patient.date_of_birth.isoformat()
            if patient.date_of_birth
            else None
        ),
        "gender": patient.gender.value if patient.gender else None,
        "phone": patient.phone,
        "lab_id": patient.lab_id,
        "national_id": patient.national_id,
        "address": patient.address,
        "age": patient.age,
        "created_at": (
            patient.created_at.isoformat() if patient.created_at else None
        ),
        "updated_at": (
            patient.updated_at.isoformat() if patient.updated_at else None
        ),
    }
