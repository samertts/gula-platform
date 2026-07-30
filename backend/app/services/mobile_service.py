import logging
import time as _time
from datetime import datetime, timedelta

from fastapi import HTTPException, Request, Response
from sqlalchemy import func
from sqlalchemy.orm import Session

from app._compat import UTC

from ..config import (
    IS_PRODUCTION,
    JWT_EXPIRE_HOURS,
    REFRESH_TOKEN_EXPIRE_DAYS,
)
from ..models.lab import Lab
from ..models.lab_order import LabOrder
from ..models.lab_user import LabUser
from ..models.patient import Patient
from ..security.auth import (
    blacklist_token as _blacklist,
)
from ..security.auth import (
    build_token_payload,
    create_refresh_token,
    create_token,
    decode_refresh_token,
    hash_password,
    verify_password,
)
from ..security.rate_limit import get_client_ip, rate_limit_auth
from ..security.session import bump_perm_version, get_perm_version
from ..services.audit_service import log_action

logger = logging.getLogger("gula.mobile")


def refresh_token(
    raw_refresh: str | None,
    request: Request,
    response: Response,
    db: Session,
) -> dict:
    rate_limit_auth(request)

    if not raw_refresh:
        raise HTTPException(status_code=401, detail="Refresh token required")

    payload = decode_refresh_token(raw_refresh)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    user = db.query(LabUser).filter(LabUser.id == user_id, LabUser.is_active).first()

    if not user:
        raise HTTPException(status_code=401, detail="User not found or deactivated")

    if user.role != "master_admin":
        lab = db.query(Lab).filter(Lab.id == user.lab_id, Lab.is_active).first()
        if not lab:
            raise HTTPException(status_code=403, detail="Laboratory account deactivated")

    token_perm_ver = int(payload.get("perm_ver", 1))
    authoritative_ver = get_perm_version(user.id, user.perm_version or 1)
    if token_perm_ver != authoritative_ver:
        raise HTTPException(status_code=401, detail="Permissions updated — please log in again")

    base_payload = build_token_payload(user)
    new_access_token = create_token(base_payload)
    new_refresh_token = create_refresh_token(base_payload)

    _grace_seconds = 30
    old_jti = payload.get("jti")
    if old_jti:
        remaining = int((payload["exp"] - _time.time()) + _grace_seconds)
        if remaining > 0:
            _blacklist(old_jti, min(remaining, REFRESH_TOKEN_EXPIRE_DAYS * 86400))

    log_action(
        db,
        action="token_refresh",
        resource_type="auth",
        user_id=user.id,
        user_role=user.role,
        details="Token refreshed",
        ip_address=get_client_ip(request),
    )
    db.commit()

    cookie_kwargs = {"httponly": True, "samesite": "strict", "secure": IS_PRODUCTION}
    response.set_cookie(
        key="access_token",
        value=new_access_token,
        max_age=JWT_EXPIRE_HOURS * 3600,
        path="/",
        **cookie_kwargs,
    )
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        path="/",
        **cookie_kwargs,
    )

    return {
        "token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "Bearer",
    }


def change_user_password(
    current_password: str,
    new_password: str,
    current_user: LabUser,
    db: Session,
) -> dict:
    if not verify_password(current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="كلمة المرور الحالية غير صحيحة")
    if len(new_password) < 8:
        raise HTTPException(
            status_code=400,
            detail="كلمة المرور الجديدة يجب أن تكون 8 أحرف على الأقل",
        )
    current_user.password_hash = hash_password(new_password)
    bump_perm_version(
        current_user,
        db,
        actor_id=current_user.id,
        actor_role=current_user.role,
        reason="password_change",
    )
    db.commit()
    return {"message": "تم تغيير كلمة المرور بنجاح"}


def role_ar(role: str) -> str:
    return {
        "master_admin": "مدير المنصة",
        "admin": "مدير المختبر",
        "staff": "موظف",
        "technician": "تقني مختبر",
    }.get(role, role)


def get_permissions(role: str) -> list[str]:
    base = ["view_patients", "view_results", "create_order"]
    if role in ("admin", "master_admin"):
        return [*base, "manage_users", "manage_lab", "view_audit_logs"]
    if role == "technician":
        return [*base, "enter_results", "view_samples"]
    return base


def get_mobile_stats(lab_id: int, db: Session) -> dict:
    today = datetime.now(UTC).date()
    week_ago = datetime.now(UTC) - timedelta(days=7)

    total_patients = db.query(func.count(Patient.id)).filter(Patient.lab_id == lab_id).scalar() or 0
    total_orders = db.query(func.count(LabOrder.id)).filter(LabOrder.lab_id == lab_id).scalar() or 0
    orders_today = (
        db.query(func.count(LabOrder.id))
        .filter(LabOrder.lab_id == lab_id, func.date(LabOrder.created_at) == today)
        .scalar()
        or 0
    )
    orders_this_week = (
        db.query(func.count(LabOrder.id))
        .filter(LabOrder.lab_id == lab_id, LabOrder.created_at >= week_ago)
        .scalar()
        or 0
    )

    return {
        "total_patients": total_patients,
        "total_orders": total_orders,
        "orders_today": orders_today,
        "orders_this_week": orders_this_week,
        "timestamp": datetime.now(UTC).isoformat(),
    }
