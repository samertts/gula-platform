from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/encounters", tags=["Encounters"])


@router.post("/")
async def create_encounter():
    return {"message": "Encounter creation endpoint"}


@router.get("/{encounter_id}")
async def get_encounter(encounter_id: str):
    return {"encounter_id": encounter_id, "message": "Encounter retrieval endpoint"}


@router.put("/{encounter_id}/complete")
async def complete_encounter(encounter_id: str):
    return {"encounter_id": encounter_id, "message": "Complete encounter endpoint"}


@router.put("/{encounter_id}/cancel")
async def cancel_encounter(encounter_id: str):
    return {"encounter_id": encounter_id, "message": "Cancel encounter endpoint"}
