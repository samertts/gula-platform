"""Non-functional FHIR stub endpoints.

These handlers return fixed placeholder payloads only. No resource is read or
written, and this router is not a canonical FHIR implementation.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.security.dependencies import require_permission

router = APIRouter(
    prefix="/fhir",
    tags=["FHIR"],
    dependencies=[Depends(require_permission("system:admin"))],
)


@router.get(
    "/Patient/{patient_id}",
    summary="[STUB] FHIR Patient placeholder",
    description="Placeholder only; no resource is read or written.",
)
async def get_fhir_patient(patient_id: str):
    return {"resourceType": "Patient", "id": patient_id, "message": "FHIR Patient endpoint"}


@router.get(
    "/Practitioner/{practitioner_id}",
    summary="[STUB] FHIR Practitioner placeholder",
    description="Placeholder only; no resource is read or written.",
)
async def get_fhir_practitioner(practitioner_id: str):
    return {"resourceType": "Practitioner", "id": practitioner_id, "message": "FHIR Practitioner endpoint"}


@router.get(
    "/Organization/{org_id}",
    summary="[STUB] FHIR Organization placeholder",
    description="Placeholder only; no resource is read or written.",
)
async def get_fhir_organization(org_id: str):
    return {"resourceType": "Organization", "id": org_id, "message": "FHIR Organization endpoint"}


@router.get(
    "/Encounter/{encounter_id}",
    summary="[STUB] FHIR Encounter placeholder",
    description="Placeholder only; no resource is read or written.",
)
async def get_fhir_encounter(encounter_id: str):
    return {"resourceType": "Encounter", "id": encounter_id, "message": "FHIR Encounter endpoint"}


@router.get(
    "/{resource_type}",
    summary="[STUB] FHIR search placeholder",
    description="Placeholder only; no resource is read or written.",
)
async def fhir_search(resource_type: str):
    return {"resourceType": "Bundle", "type": "searchset", "message": f"FHIR {resource_type} search endpoint"}
