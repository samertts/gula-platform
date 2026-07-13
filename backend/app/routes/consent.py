"""Consent HTTP API — grant / revoke / check.

All endpoints require authentication. Only the citizen themselves or an
authorized admin/doctor may grant consent on their behalf.

MVP policy
----------
- Grant: the authenticated user grants consent over their OWN record
  (gpid must equal their citizen_ulid). Non-citizen roles may also grant
  consent on behalf of the subject when the request carries a verified
  out-of-band consent signature (future work). For now, non-citizen roles
  can grant only if they are master_admin or ministry_admin (administrative
  grant), which is rare and fully audited.
- Revoke: the subject may always revoke; master/ministry admins may too.
- Check: any authenticated actor can check if THEY have consent.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.lab_user import LabUser
from ..security.dependencies import get_current_user
from ..security.rate_limit import rate_limit_user
from ..services import consent_service
from ..services.consent_service import (
    ALLOWED_SCOPES,
    MAX_CONSENT_HOURS,
    ConsentError,
)

router = APIRouter(prefix="/consent", tags=["consent"])


# ── Schemas ───────────────────────────────────────────────────────────────────


class GrantRequest(BaseModel):
    gpid: str = Field(..., min_length=26, max_length=26, description="Subject citizen_ulid")
    grantee_id: str = Field(
        ..., min_length=3, max_length=64, description="Actor being authorized (e.g. 'user:42')"
    )
    scope: str = Field(..., min_length=3, max_length=64)
    expires_in_hours: int = Field(..., ge=1, le=MAX_CONSENT_HOURS)


class GrantResponse(BaseModel):
    consent_id: str
    gpid: str
    grantee_id: str
    scope: str
    expires_at: datetime


class RevokeRequest(BaseModel):
    gpid: str = Field(..., min_length=26, max_length=26)
    grantee_id: str = Field(..., min_length=3, max_length=64)
    scope: str = Field(..., min_length=3, max_length=64)


class RevokeResponse(BaseModel):
    revoked: bool


class CheckResponse(BaseModel):
    allowed: bool
    scope: str
    expires_at: datetime | None = None


# ── Authorization helpers ─────────────────────────────────────────────────────

_ADMIN_GRANT_ROLES = {"master_admin", "ministry_admin"}


def _user_owns_gpid(user: LabUser, gpid: str) -> bool:
    owned = getattr(user, "citizen_ulid", None)
    return user.role == "citizen" and owned is not None and owned == gpid


# ── POST /consent/grant ──────────────────────────────────────────────────────


@router.post("/grant", response_model=GrantResponse, status_code=201)
def grant(
    data: GrantRequest,
    request: Request,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> GrantResponse:
    """Grant an actor time-bounded access to the caller's record.

    403 unless the caller is the subject themselves OR a platform admin.
    """
    rate_limit_user(request, current_user.id, max_per_minute=30)

    if data.scope not in ALLOWED_SCOPES:
        raise HTTPException(status_code=400, detail=f"scope '{data.scope}' is not allowed")

    if not (_user_owns_gpid(current_user, data.gpid) or current_user.role in _ADMIN_GRANT_ROLES):
        raise HTTPException(
            status_code=403,
            detail={
                "error": "grant_forbidden",
                "message": "Only the subject or platform admin may grant consent.",
            },
        )

    try:
        row = consent_service.grant_consent(
            db,
            gpid=data.gpid,
            grantee_id=data.grantee_id,
            scope=data.scope,
            expires_in_hours=data.expires_in_hours,
            actor_user_id=current_user.id,
            actor_role=current_user.role,
            ip_address=request.client.host if request.client else None,
        )
    except ConsentError as e:
        raise HTTPException(status_code=400, detail=str(e))

    db.commit()
    return GrantResponse(
        consent_id=row.id,
        gpid=row.gpid,
        grantee_id=row.grantee_id,
        scope=row.scope,
        expires_at=row.expires_at,
    )


# ── POST /consent/revoke ──────────────────────────────────────────────────────


@router.post("/revoke", response_model=RevokeResponse)
def revoke(
    data: RevokeRequest,
    request: Request,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RevokeResponse:
    """Revoke an active consent. Subject or platform admin only."""
    rate_limit_user(request, current_user.id, max_per_minute=30)

    if not (_user_owns_gpid(current_user, data.gpid) or current_user.role in _ADMIN_GRANT_ROLES):
        raise HTTPException(
            status_code=403,
            detail={
                "error": "revoke_forbidden",
                "message": "Only the subject or platform admin may revoke consent.",
            },
        )

    revoked = consent_service.revoke_consent(
        db,
        gpid=data.gpid,
        grantee_id=data.grantee_id,
        scope=data.scope,
        actor_user_id=current_user.id,
        actor_role=current_user.role,
        ip_address=request.client.host if request.client else None,
    )
    db.commit()
    return RevokeResponse(revoked=revoked)


# ── GET /consent/check ────────────────────────────────────────────────────────


@router.get("/check", response_model=CheckResponse)
def check(
    gpid: str,
    scope: str,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CheckResponse:
    """Does the current actor hold active consent for (gpid, scope)?"""
    actor_id = f"user:{current_user.id}"
    row = consent_service.check_active_consent(
        db,
        gpid=gpid,
        grantee_id=actor_id,
        scope=scope,
    )
    if row is None:
        return CheckResponse(allowed=False, scope=scope)
    return CheckResponse(allowed=True, scope=scope, expires_at=row.expires_at)
