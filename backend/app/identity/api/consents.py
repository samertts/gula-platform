from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.identity.api.workspaces import NiamActor, get_current_niam_actor
from app.identity.models.consent import NiamConsent
from app.identity.services.consent_service_v2 import (
    NiamConsentAccessDenied,
    NiamConsentError,
    NiamConsentService,
)

router = APIRouter(prefix="/consents", tags=["NIAM Consent"])


class ConsentGrantRequest(BaseModel):
    subject_account_id: str = Field(min_length=1, max_length=26)
    grantee_account_id: str = Field(min_length=1, max_length=26)
    purpose: str = Field(min_length=1, max_length=80)
    scope: dict[str, Any] = Field(min_length=1, max_length=20)
    resource_domain: str = Field(min_length=1, max_length=120)
    expires_at: datetime
    legal_basis: str | None = Field(default=None, max_length=120)
    reason: str | None = Field(default=None, max_length=500)


class ConsentWithdrawRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=500)


def _serialize(consent: NiamConsent) -> dict[str, Any]:
    return {
        "id": consent.id,
        "uuid": consent.uuid,
        "subject_account_id": consent.subject_account_id,
        "grantee_account_id": consent.grantee_account_id,
        "purpose": consent.purpose,
        "scope": consent.scope,
        "resource_domain": consent.resource_domain,
        "status": consent.status,
        "granted_at": consent.granted_at.isoformat(),
        "withdrawn_at": consent.withdrawn_at.isoformat() if consent.withdrawn_at else None,
        "expires_at": consent.expires_at.isoformat(),
        "version": consent.version,
        "source": consent.source,
        "legal_basis": consent.legal_basis,
        "supersedes_id": consent.supersedes_id,
        "reason": consent.reason,
    }


@router.post("", status_code=status.HTTP_201_CREATED)
async def grant_consent(
    body: ConsentGrantRequest,
    actor: NiamActor = Depends(get_current_niam_actor),
    db: AsyncSession = Depends(get_db),
):
    try:
        consent = await NiamConsentService(db).grant(
            actor_account_id=actor.account.id,
            subject_account_id=body.subject_account_id,
            grantee_account_id=body.grantee_account_id,
            purpose=body.purpose,
            scope=body.scope,
            resource_domain=body.resource_domain,
            expires_at=body.expires_at,
            legal_basis=body.legal_basis,
            reason=body.reason,
        )
    except NiamConsentAccessDenied as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Consent grant denied") from exc
    except NiamConsentError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return _serialize(consent)


@router.get("/me")
async def list_my_consents(
    limit: int = Query(default=100, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    actor: NiamActor = Depends(get_current_niam_actor),
    db: AsyncSession = Depends(get_db),
):
    consents = await NiamConsentService(db).list_for_account(actor_account_id=actor.account.id, limit=limit, offset=offset)
    return {"consents": [_serialize(consent) for consent in consents], "limit": limit, "offset": offset}


@router.get("/{consent_id}/check")
async def check_consent(
    consent_id: str,
    actor: NiamActor = Depends(get_current_niam_actor),
    db: AsyncSession = Depends(get_db),
):
    try:
        consent = await NiamConsentService(db).check(actor_account_id=actor.account.id, consent_id=consent_id)
    except NiamConsentAccessDenied as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Consent check denied") from exc
    return {"active": consent is not None, "consent": _serialize(consent) if consent else None}


@router.post("/{consent_id}/withdraw")
async def withdraw_consent(
    consent_id: str,
    body: ConsentWithdrawRequest | None = None,
    actor: NiamActor = Depends(get_current_niam_actor),
    db: AsyncSession = Depends(get_db),
):
    try:
        consent = await NiamConsentService(db).withdraw(
            actor_account_id=actor.account.id,
            consent_id=consent_id,
            reason=body.reason if body else None,
        )
    except NiamConsentAccessDenied as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Consent withdrawal denied") from exc
    except NiamConsentError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return _serialize(consent)
