from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/families", tags=["Family Registry"])


@router.post("/")
async def create_family():
    return {"message": "Family creation endpoint"}


@router.get("/{family_id}")
async def get_family(family_id: str):
    return {"family_id": family_id, "message": "Family retrieval endpoint"}


@router.post("/{family_id}/members")
async def add_family_member(family_id: str):
    return {"family_id": family_id, "message": "Add family member endpoint"}


@router.delete("/{family_id}/members/{member_id}")
async def remove_family_member(family_id: str, member_id: str):
    return {"family_id": family_id, "member_id": member_id, "message": "Remove family member endpoint"}
