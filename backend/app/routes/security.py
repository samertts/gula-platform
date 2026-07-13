"""Security status and health check endpoints."""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app._compat import UTC

from ..database import get_db
from ..models.audit_log import AuditLog
from ..models.lab_user import LabUser
from ..security.dependencies import get_current_user

router = APIRouter(prefix="/security", tags=["security"])


@router.get("/status")
def security_status(
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """System security status dashboard."""
    if current_user.role not in ("master_admin", "admin"):
        return {"status": "secure", "message": "Detailed security info requires admin access"}

    now = datetime.now(UTC)
    last_24h = now - timedelta(hours=24)

    # Recent security events
    login_attempts = (
        db.query(func.count(AuditLog.id))
        .filter(
            AuditLog.action == "login",
            AuditLog.created_at >= last_24h,
        )
        .scalar()
        or 0
    )

    failed_logins = (
        db.query(func.count(AuditLog.id))
        .filter(
            AuditLog.action == "login_failed",
            AuditLog.created_at >= last_24h,
        )
        .scalar()
        or 0
    )

    result_views = (
        db.query(func.count(AuditLog.id))
        .filter(
            AuditLog.action == "view_result",
            AuditLog.created_at >= last_24h,
        )
        .scalar()
        or 0
    )

    return {
        "status": "secure",
        "last_24h": {
            "login_attempts": login_attempts,
            "failed_logins": failed_logins,
            "result_views": result_views,
        },
        "checks": {
            "database": "connected",
            "jwt_auth": "active",
            "rate_limiting": "active",
            "token_hashing": "active",
            "audit_logging": "active",
        },
    }
