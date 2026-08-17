from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.audit_log import AuditLog
from app.national.security.break_glass import BreakGlassService
from app.national.security.consent_enforcement import ConsentEnforcementService
from app.security.dependencies import get_current_user, require_permission
from app.security.rate_limit import rate_limit_user

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
            id=str(log.id),
            user_id=str(log.user_id) if log.user_id is not None else None,
            action=log.action,
            resource_type=log.resource_type,
            resource_id=str(log.resource_id) if log.resource_id is not None else None,
            details=str(log.details) if log.details else None,
            created_at=log.created_at.isoformat() if log.created_at else "",
        )


@router.post("/break-glass", response_model=BreakGlassResponse, dependencies=[Depends(require_permission("security:break_glass"))])
async def request_break_glass(
    data: BreakGlassRequest,
    request: Request,
    current_user=Depends(get_current_user),
):
    rate_limit_user(request, current_user.id, max_per_minute=5)
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


@router.post("/consent/check", response_model=ConsentCheckResponse, dependencies=[Depends(require_permission("patients:read"))])
async def check_consent(
    data: ConsentCheck,
    request: Request,
    current_user=Depends(get_current_user),
):
    rate_limit_user(request, current_user.id, max_per_minute=30)
    service = ConsentEnforcementService()
    result = await service.check_consent(citizen_id=data.citizen_id, scope=data.scope)
    return ConsentCheckResponse(
        granted=result.granted,
        consent_id=result.consent_id,
        reason=result.reason or "",
    )


@router.get("/audit/{entity_type}/{entity_id}", response_model=list[AuditLogResponse], dependencies=[Depends(require_permission("audit:read"))])
async def get_audit_log(
    entity_type: str,
    entity_id: str,
    request: Request,
    skip: int = Query(0, ge=0, le=100000),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    rate_limit_user(request, current_user.id, max_per_minute=30)
    query = (
        db.query(AuditLog)
        .filter(
            AuditLog.resource_type == entity_type,
            AuditLog.resource_id == entity_id,
        )
    )
    if getattr(current_user, "lab_id", None) is not None and current_user.role not in {"master_admin", "ministry_admin", "auditor"}:
        query = query.filter(AuditLog.lab_id == current_user.lab_id)
    logs = (
        query
        .order_by(AuditLog.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [AuditLogResponse.from_orm(log) for log in logs]
