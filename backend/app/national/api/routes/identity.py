from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/identity", tags=["Identity"])


@router.post("/newborn")
async def register_newborn():
    return {"message": "Newborn registration endpoint"}


@router.post("/foreigner")
async def register_foreigner():
    return {"message": "Foreigner registration endpoint"}


@router.post("/visitor")
async def register_visitor():
    return {"message": "Visitor registration endpoint"}


@router.post("/unknown")
async def register_unknown():
    return {"message": "Unknown patient registration endpoint"}


@router.post("/merge")
async def merge_identities():
    return {"message": "Identity merge endpoint"}
