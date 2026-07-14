from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/fhir", tags=["FHIR"])


@router.get("/Patient/{patient_id}")
async def get_fhir_patient(patient_id: str):
    return {"resourceType": "Patient", "id": patient_id, "message": "FHIR Patient endpoint"}


@router.get("/Practitioner/{practitioner_id}")
async def get_fhir_practitioner(practitioner_id: str):
    return {"resourceType": "Practitioner", "id": practitioner_id, "message": "FHIR Practitioner endpoint"}


@router.get("/Organization/{org_id}")
async def get_fhir_organization(org_id: str):
    return {"resourceType": "Organization", "id": org_id, "message": "FHIR Organization endpoint"}


@router.get("/Encounter/{encounter_id}")
async def get_fhir_encounter(encounter_id: str):
    return {"resourceType": "Encounter", "id": encounter_id, "message": "FHIR Encounter endpoint"}


@router.get("/{resource_type}")
async def fhir_search(resource_type: str):
    return {"resourceType": "Bundle", "type": "searchset", "message": f"FHIR {resource_type} search endpoint"}
