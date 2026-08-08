from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_niam_db as get_db
from app.identity.security import get_current_identity

from .services import (
    CitizenRegistryError,
    CitizenRegistryService,
    ProviderDisabledError,
    UnsupportedIdentifierTypeError,
)

router = APIRouter(
    prefix="/citizens",
    tags=["NIAM Citizen Registry"],
    dependencies=[Depends(get_current_identity)],
)


@router.post("/providers")
async def register_provider(
    provider_id: str,
    name_en: str,
    provider_type: str,
    country: str,
    identifier_types: list[str],
    name_ar: str | None = None,
    verification_methods: list[str] | None = None,
    configuration: dict | None = None,
    is_default: bool = False,
    db: AsyncSession = Depends(get_db),
):
    service = CitizenRegistryService(db)
    try:
        provider = await service.register_provider(
            provider_id=provider_id,
            name_en=name_en,
            provider_type=provider_type,
            country=country,
            identifier_types=identifier_types,
            name_ar=name_ar,
            verification_methods=verification_methods,
            configuration=configuration,
            is_default=is_default,
        )
    except CitizenRegistryError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"provider": provider.to_dict()}


@router.get("/providers")
async def list_providers(country: str | None = None, db: AsyncSession = Depends(get_db)):
    service = CitizenRegistryService(db)
    providers = await service.list_providers(country)
    return {"providers": [p.to_dict() for p in providers], "count": len(providers)}


@router.get("/providers/default")
async def get_default_provider(db: AsyncSession = Depends(get_db)):
    service = CitizenRegistryService(db)
    provider = await service.get_default_provider()
    if not provider:
        raise HTTPException(status_code=404, detail="no_default_provider")
    return {"provider": provider.to_dict()}


@router.post("/verify-identifier")
async def verify_identifier(
    person_id: str,
    provider_id: str,
    identifier_type: str,
    identifier: str,
    db: AsyncSession = Depends(get_db),
):
    service = CitizenRegistryService(db)
    try:
        ok = await service.verify_citizen_identifier(
            person_id=person_id,
            provider_id=provider_id,
            identifier_type=identifier_type,
            identifier=identifier,
        )
    except UnsupportedIdentifierTypeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ProviderDisabledError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except CitizenRegistryError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"verified": ok}
