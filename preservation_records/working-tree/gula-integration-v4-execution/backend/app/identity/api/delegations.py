"""B5 — canonical NIAM delegation API (owner directive GULA-MASTER-AUTH-2026-11-19 §5/B5).

Thin, account-based surface over the ONE B5 ``DelegationService``. All authority
checks stay in that service and in the canonical ``RolePermissionService``
consumer; this module adds no authorization engine, role or permission. It never
accepts legacy integer user IDs and never writes the ungoverned ``delegations``
table. The legacy ``/authz/delegations`` surface is failed closed separately.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.identity.api.workspaces import NiamActor, get_current_niam_actor
from app.identity.models.delegation import NiamDelegation
from app.identity.services.delegation_service import (
    DelegationDenied,
    DelegationPolicyError,
    DelegationService,
)

router = APIRouter(prefix="/delegations", tags=["NIAM Delegation"])


class DelegationGrantRequest(BaseModel):
    delegate_account_id: str = Field(min_length=1, max_length=26)
    role_id: str = Field(min_length=1, max_length=26)
    organization_id: str = Field(min_length=1, max_length=26)
    permission_keys: list[str] = Field(min_length=1, max_length=100)
    duration_hours: int = Field(ge=1, le=720)
    reason: str = Field(min_length=10, max_length=500)
    facility_id: str | None = Field(default=None, max_length=26)
    department_id: str | None = Field(default=None, max_length=26)
    unit_id: str | None = Field(default=None, max_length=26)
    workspace_id: str | None = Field(default=None, max_length=26)


class DelegationRevokeRequest(BaseModel):
    reason: str = Field(min_length=10, max_length=500)


def _serialize(delegation: NiamDelegation) -> dict[str, Any]:
    status_value = delegation.status
    if hasattr(status_value, "value"):
        status_value = status_value.value
    return {
        "id": delegation.id,
        "delegator_account_id": delegation.delegator_account_id,
        "delegate_account_id": delegation.delegate_account_id,
        "role_id": delegation.role_id,
        "organization_id": delegation.organization_id,
        "permission_keys": list(delegation.permission_keys or []),
        "depth": delegation.depth,
        "status": status_value,
        "reason": delegation.reason,
        "starts_at": delegation.starts_at.isoformat() if delegation.starts_at else None,
        "expires_at": delegation.expires_at.isoformat() if delegation.expires_at else None,
        "revoked_at": delegation.revoked_at.isoformat() if delegation.revoked_at else None,
        "version": delegation.version,
    }


@router.post("", status_code=status.HTTP_201_CREATED)
async def grant_delegation(
    body: DelegationGrantRequest,
    actor: NiamActor = Depends(get_current_niam_actor),
    db: AsyncSession = Depends(get_db),
):
    """Grant a bounded delegation using the actor's canonical NIAM account."""
    try:
        delegation = await DelegationService(db).delegate_role(
            actor_id=actor.account.id,
            delegate_account_id=body.delegate_account_id,
            role_id=body.role_id,
            organization_id=body.organization_id,
            permission_keys=body.permission_keys,
            duration_hours=body.duration_hours,
            reason=body.reason,
            facility_id=body.facility_id,
            department_id=body.department_id,
            unit_id=body.unit_id,
            workspace_id=body.workspace_id,
        )
    except DelegationDenied as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except DelegationPolicyError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return _serialize(delegation)


@router.get("")
async def list_delegations(
    actor: NiamActor = Depends(get_current_niam_actor),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(100, ge=1, le=500),
):
    """List delegations where the actor is either party (never a global read)."""
    rows = (await db.execute(
        select(NiamDelegation)
        .where(
            or_(
                NiamDelegation.delegate_account_id == actor.account.id,
                NiamDelegation.delegator_account_id == actor.account.id,
            )
        )
        .order_by(NiamDelegation.starts_at.desc())
        .limit(limit)
    )).scalars().all()
    return {"items": [_serialize(row) for row in rows]}


@router.post("/{delegation_id}/revoke")
async def revoke_delegation(
    delegation_id: str,
    body: DelegationRevokeRequest,
    actor: NiamActor = Depends(get_current_niam_actor),
    db: AsyncSession = Depends(get_db),
):
    """Revoke a delegation; only its delegator or an org manager may do so."""
    try:
        delegation = await DelegationService(db).revoke_delegation(
            delegation_id=delegation_id,
            actor_id=actor.account.id,
            reason=body.reason,
        )
    except DelegationDenied as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except DelegationPolicyError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return _serialize(delegation)


__all__ = ["router"]
