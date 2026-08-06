from platform.api.dependencies.container import get_patient_service
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

router = APIRouter()


@router.post("/")
async def create_patient(
    data: dict[str, Any],
    patient_service=Depends(get_patient_service),
) -> dict[str, Any]:
    try:
        from datetime import date
        from platform.domain.services.patient import PatientData

        dob = None
        if data.get("date_of_birth"):
            dob = date.fromisoformat(data["date_of_birth"])

        pd = PatientData(
            lab_id=data.get("lab_id", ""),
            first_name=data.get("first_name", ""),
            father_name=data.get("father_name", ""),
            last_name=data.get("last_name", ""),
            date_of_birth=dob,
            gender=data.get("gender", ""),
            phone=data.get("phone", ""),
            national_id=data.get("national_id"),
        )
        result = await patient_service.create(pd)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{patient_id}")
async def get_patient(
    patient_id: str,
    patient_service=Depends(get_patient_service),
) -> dict[str, Any]:
    result = await patient_service.get_by_id(patient_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    return result


@router.get("/")
async def search_patients(
    q: str = Query("", alias="q"),
    lab_id: str = Query("", alias="lab_id"),
    limit: int = Query(20, alias="limit"),
    patient_service=Depends(get_patient_service),
) -> list[dict[str, Any]]:
    if not q or not lab_id:
        return []
    return await patient_service.search(q, lab_id, limit)
