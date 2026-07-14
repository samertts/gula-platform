from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/health-cards", tags=["Health Cards"])


@router.post("/")
async def issue_health_card():
    return {"message": "Health card issuance endpoint"}


@router.get("/{card_id}")
async def get_health_card(card_id: str):
    return {"card_id": card_id, "message": "Health card retrieval endpoint"}


@router.get("/citizen/{citizen_id}")
async def get_citizen_health_card(citizen_id: str):
    return {"citizen_id": citizen_id, "message": "Citizen health card endpoint"}
