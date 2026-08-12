from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/consents", tags=["Consent"])


@router.post("/")
async def create_consent():
    return {"message": "Consent creation endpoint"}


@router.get("/{consent_id}")
async def get_consent(consent_id: str):
    return {"consent_id": consent_id, "message": "Consent retrieval endpoint"}


@router.put("/{consent_id}/revoke")
async def revoke_consent(consent_id: str):
    return {"consent_id": consent_id, "message": "Revoke consent endpoint"}
