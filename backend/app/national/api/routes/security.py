from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.audit_log import AuditLog
from app.national.security.break_glass import BreakGlassService
from app.national.security.consent_enforcement import ConsentEnforcementService
from app.security.dependencies import get_current_user

router = APIRouter(prefix="/security", tags=["Healthcare Security"])


class BreakGlassRequest(BaseModel):
    citizen_id: str
    reason: str
    duration_minutes: int = 60


class ConsentCheck(BaseModel):
    citizen_id: str
    scope: str


class BreakGlassResponse(BaseModel):
    access_id: str | None = None
    granted: bool
    expires_at: str | None = None
    reason: str = ""


class ConsentCheckResponse(BaseModel):
    granted: bool
    consent_id: str | None = None
    reason: str = ""


class AuditLogResponse(BaseModel):
    id: str
    user_id: str | None = None
    action: str
    resource_type: str
    resource_id: str | None = None
    details: str | None = None
    created_at: str

    @classmethod
    def from_orm(cls, log: AuditLog) -> AuditLogResponse:
        return cls(
            id=log.id,
            user_id=log.user_id,
            action=log.action,
            resource_type=log.resource_type,
            resource_id=log.resource_id,
            details=str(log.details) if log.details else None,
            created_at=log.created_at.isoformat() if log.created_at else "",
        )


@router.post("/break-glass", response_model=BreakGlassResponse)
async def request_break_glass(
    data: BreakGlassRequest,
    current_user=Depends(get_current_user),
):
    service = BreakGlassService()
    result = service.request_access(
        citizen_id=data.citizen_id,
        requested_by=getattr(current_user, "id", "unknown"),
        reason=data.reason,
        duration_minutes=data.duration_minutes,
    )
    if result:
        return BreakGlassResponse(
            access_id=result.access_id,
            granted=True,
            expires_at=result.expires_at.isoformat() if result.expires_at else None,
            reason="Break glass access granted",
        )
    return BreakGlassResponse(granted=False, reason="Break glass access denied")


@router.post("/consent/check", response_model=ConsentCheckResponse)
async def check_consent(
    data: ConsentCheck,
    current_user=Depends(get_current_user),
):
    service = ConsentEnforcementService()
    result = await service.check_consent(citizen_id=data.citizen_id, scope=data.scope)
    return ConsentCheckResponse(
        granted=result.granted,
        consent_id=result.consent_id,
        reason=result.reason or "",
    )


@router.get("/audit/{entity_type}/{entity_id}", response_model=list[AuditLogResponse])
async def get_audit_log(
    entity_type: str,
    entity_id: str,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    logs = (
        db.query(AuditLog)
        .filter(
            AuditLog.resource_type == entity_type,
            AuditLog.resource_id == entity_id,
        )
        .order_by(AuditLog.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [AuditLogResponse.from_orm(log) for log in logs]
