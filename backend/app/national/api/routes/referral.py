from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/referrals", tags=["Referrals"])


@router.post("/")
async def create_referral():
    return {"message": "Referral creation endpoint"}


@router.get("/{referral_id}")
async def get_referral(referral_id: str):
    return {"referral_id": referral_id, "message": "Referral retrieval endpoint"}


@router.put("/{referral_id}/accept")
async def accept_referral(referral_id: str):
    return {"referral_id": referral_id, "message": "Accept referral endpoint"}


@router.put("/{referral_id}/reject")
async def reject_referral(referral_id: str):
    return {"referral_id": referral_id, "message": "Reject referral endpoint"}
