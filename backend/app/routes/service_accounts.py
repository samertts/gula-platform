from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.lab import Lab
from ..security.dependencies import get_current_user
from ..security.service_accounts import (
    create_service_account,
    list_service_accounts,
    revoke_service_account,
    rotate_api_key,
    validate_requested_scopes,
)

logger = logging.getLogger("gula.routes.service_accounts")

router = APIRouter(prefix="/service-accounts", tags=["service-accounts"])


class CreateServiceAccountRequest(BaseModel):
    name: str
    description: str | None = None
    roles: list[str] = ["staff"]
    scopes: list[str] = []
    # Required for PIXm/MHD machine identities; nullable for legacy admin keys.
    lab_id: int | None = None


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

    try:
        scopes = validate_requested_scopes(data.scopes)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    requested_lab_id = data.lab_id
    if current_user.role != "master_admin":
        if current_user.lab_id is None:
            raise HTTPException(status_code=403, detail="An organisation-bound admin is required")
        if requested_lab_id is not None and requested_lab_id != current_user.lab_id:
            raise HTTPException(status_code=403, detail="Admins may manage only their own laboratory")
        requested_lab_id = current_user.lab_id

    if requested_lab_id is not None:
        lab = db.query(Lab).filter(Lab.id == requested_lab_id, Lab.is_active).first()
        if lab is None:
            raise HTTPException(status_code=404, detail="Active laboratory not found")

    account, api_key = create_service_account(
        db=db,
        name=data.name,
        description=data.description,
        roles=data.roles,
        scopes=scopes,
        created_by=current_user.id,
        lab_id=requested_lab_id,
    )
    return {
        "id": account.id,
        "name": account.name,
            "api_key": api_key,
            "roles": data.roles,
            "scopes": scopes,
            "lab_id": account.lab_id,
    }


@router.get("")
def list_all(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role not in ("master_admin", "admin"):
        raise HTTPException(status_code=403, detail="Only admins can list service accounts")


    lab_id = None if current_user.role == "master_admin" else current_user.lab_id
    if current_user.role != "master_admin" and lab_id is None:
        raise HTTPException(status_code=403, detail="An organisation-bound admin is required")
    accounts = list_service_accounts(db, lab_id=lab_id)
    return [
        {
            "id": a.id,
            "name": a.name,
            "description": a.description,
            "is_active": bool(a.is_active),
            "lab_id": a.lab_id,
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


    lab_id = None if current_user.role == "master_admin" else current_user.lab_id
    if current_user.role != "master_admin" and lab_id is None:
        raise HTTPException(status_code=403, detail="An organisation-bound admin is required")
    if not revoke_service_account(db, account_id, lab_id=lab_id):
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


    lab_id = None if current_user.role == "master_admin" else current_user.lab_id
    if current_user.role != "master_admin" and lab_id is None:
        raise HTTPException(status_code=403, detail="An organisation-bound admin is required")
    new_key = rotate_api_key(db, account_id, lab_id=lab_id)
    if not new_key:
        raise HTTPException(status_code=404, detail="Service account not found or inactive")
    return {"api_key": new_key}
