from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app._compat import UTC

from ..database import get_db
from ..models.lab_user import LabUser
from ..models.service_account import ServiceAccount
from ..security.dependencies import get_current_user
from ..security.service_accounts import (
    create_service_account,
    list_service_accounts,
    revoke_service_account,
    rotate_api_key,
)

logger = logging.getLogger("gula.routes.service_accounts")

router = APIRouter(prefix="/service-accounts", tags=["service-accounts"])


class CreateServiceAccountRequest(BaseModel):
    name: str
    description: str | None = None
    roles: list[str] = ["staff"]
    scopes: list[str] = []


class ServiceAccountResponse(BaseModel):
    id: int
    name: str
    description: str | None = None
    roles: list[str]
    scopes: list[str]
    is_active: bool
    last_used_at: str | None = None
    created_by: int | None = None
    created_at: str | None = None
    expires_at: str | None = None


@router.post("")
def create(
    data: CreateServiceAccountRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role not in ("master_admin", "admin"):
        raise HTTPException(status_code=403, detail="Only admins can create service accounts")

    from ..security.service_accounts import create_service_account

    account, api_key = create_service_account(
        db=db,
        name=data.name,
        description=data.description,
        roles=data.roles,
        scopes=data.scopes,
        created_by=current_user.id,
    )
    return {
        "id": account.id,
        "name": account.name,
        "api_key": api_key,
        "roles": data.roles,
        "scopes": data.scopes,
    }


@router.get("")
def list_all(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role not in ("master_admin", "admin"):
        raise HTTPException(status_code=403, detail="Only admins can list service accounts")

    from ..security.service_accounts import list_service_accounts

    accounts = list_service_accounts(db)
    return [
        {
            "id": a.id,
            "name": a.name,
            "description": a.description,
            "is_active": bool(a.is_active),
            "last_used_at": a.last_used_at.isoformat() if a.last_used_at else None,
            "created_by": a.created_by,
            "created_at": a.created_at.isoformat() if a.created_at else None,
            "expires_at": a.expires_at.isoformat() if a.expires_at else None,
        }
        for a in accounts
    ]


@router.delete("/{account_id}")
def revoke(
    account_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role not in ("master_admin", "admin"):
        raise HTTPException(status_code=403, detail="Only admins can revoke service accounts")

    from ..security.service_accounts import revoke_service_account

    if not revoke_service_account(db, account_id):
        raise HTTPException(status_code=404, detail="Service account not found")
    return {"message": "Service account revoked"}


@router.post("/{account_id}/rotate")
def rotate(
    account_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role not in ("master_admin", "admin"):
        raise HTTPException(status_code=403, detail="Only admins can rotate API keys")

    from ..security.service_accounts import rotate_api_key

    new_key = rotate_api_key(db, account_id)
    if not new_key:
        raise HTTPException(status_code=404, detail="Service account not found or inactive")
    return {"api_key": new_key}
