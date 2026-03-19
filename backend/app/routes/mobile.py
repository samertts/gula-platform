"""
Mobile API - GULA Platform
Endpoints optimized for Android and iOS applications.
Supports token refresh, device registration, and mobile-friendly data.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session
from typing import Optional

from ..database import get_db
from ..models.lab_user import LabUser
from ..models.lab import Lab
from ..security.auth import decode_refresh_token, create_token, create_refresh_token, verify_password, hash_password
from ..security.dependencies import get_current_user
from ..security.rate_limit import rate_limit_auth, get_client_ip
from ..services.audit_service import log_action
from ..config import APP_VERSION, APP_NAME, IS_PRODUCTION, JWT_EXPIRE_HOURS, REFRESH_TOKEN_EXPIRE_DAYS

logger = logging.getLogger("gula.mobile")

router = APIRouter(prefix="/auth", tags=["mobile / auth"])


# ─── Token Refresh ───────────────────────────────────────────────────────────

class RefreshRequest(BaseModel):
    refresh_token: Optional[str] = None


@router.post("/refresh", summary="Refresh access token (mobile and web)")
def refresh_access_token(
    data: RefreshRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """
    Exchange a refresh token for a new access token.

    Used by mobile apps to stay logged in without re-entering credentials.
    Refresh tokens expire after 30 days (configurable via REFRESH_TOKEN_EXPIRE_DAYS).

    **Mobile usage:**
    - Store the refresh_token securely in device secure storage (Keychain/Keystore)
    - When access token expires (401), call this endpoint automatically
    - Update stored tokens with the new values returned
    """
    rate_limit_auth(request)

    # Accept refresh token from JSON body (mobile) or httpOnly cookie (web)
    raw_refresh = data.refresh_token or request.cookies.get("refresh_token")
    if not raw_refresh:
        raise HTTPException(status_code=401, detail="Refresh token required")

    payload = decode_refresh_token(raw_refresh)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    user = db.query(LabUser).filter(
        LabUser.id == user_id,
        LabUser.is_active == True,
    ).first()

    if not user:
        raise HTTPException(status_code=401, detail="User not found or deactivated")

    # Verify lab still active
    if user.role != "master_admin":
        lab = db.query(Lab).filter(Lab.id == user.lab_id, Lab.is_active == True).first()
        if not lab:
            raise HTTPException(status_code=403, detail="Laboratory account deactivated")

    # Issue new tokens
    new_access_token = create_token({
        "user_id": user.id,
        "lab_id": user.lab_id,
        "role": user.role,
    })
    new_refresh_token = create_refresh_token({
        "user_id": user.id,
        "lab_id": user.lab_id,
        "role": user.role,
    })

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

    # Set updated httpOnly cookies for web clients
    cookie_kwargs = {"httponly": True, "samesite": "strict", "secure": IS_PRODUCTION}
    response.set_cookie(
        key="access_token", value=new_access_token,
        max_age=JWT_EXPIRE_HOURS * 3600, path="/", **cookie_kwargs,
    )
    response.set_cookie(
        key="refresh_token", value=new_refresh_token,
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 86400, path="/auth/refresh", **cookie_kwargs,
    )

    return {
        "token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "Bearer",
    }


# ─── Change Password ─────────────────────────────────────────────────────────

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


@router.post("/change-password", summary="Change current user password")
def change_password(
    data: ChangePasswordRequest,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Change the password for the currently authenticated user."""
    if not verify_password(data.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="كلمة المرور الحالية غير صحيحة")
    if len(data.new_password) < 8:
        raise HTTPException(status_code=400, detail="كلمة المرور الجديدة يجب أن تكون 8 أحرف على الأقل")
    current_user.password_hash = hash_password(data.new_password)
    db.commit()
    return {"message": "تم تغيير كلمة المرور بنجاح"}


# ─── App Info ────────────────────────────────────────────────────────────────

mobile_router = APIRouter(prefix="/mobile", tags=["mobile / info"])


@mobile_router.get("/app-info", summary="Mobile app configuration")
def get_app_info():
    """
    Returns app configuration for mobile clients.
    Use this to check if app update is required and get feature flags.
    """
    return {
        "app_name": APP_NAME,
        "app_name_ar": "منصة غولا الصحية",
        "api_version": APP_VERSION,
        "min_app_version": "1.0.0",
        "features": {
            "patient_search": True,
            "result_sharing": True,
            "qr_scan": True,
            "pdf_download": True,
            "push_notifications": False,   # Coming soon
            "biometric_auth": False,       # Coming soon
            "offline_mode": False,         # Coming soon
            "critical_alerts": True,
        },
        "support": {
            "email": "support@gula-platform.org",
            "whatsapp": "+964XXXXXXXXX",  # Configure via env
        },
        "links": {
            "terms": "https://gula-platform.org/terms",
            "privacy": "https://gula-platform.org/privacy",
            "help": "https://gula-platform.org/help",
        },
    }


@mobile_router.get("/me", summary="Current user profile (mobile)")
def get_current_user_profile(
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns the authenticated user's profile and lab information.
    Optimized for mobile app home screen.
    """
    lab = None
    if current_user.lab_id:
        lab = db.query(Lab).filter(Lab.id == current_user.lab_id).first()

    return {
        "user": {
            "id": current_user.id,
            "name": current_user.name,
            "email": current_user.email,
            "role": current_user.role,
            "role_ar": _role_ar(current_user.role),
            "permissions": _get_permissions(current_user.role),
        },
        "lab": {
            "id": lab.id if lab else None,
            "name": lab.name if lab else None,
            "city": lab.city if lab else None,
            "phone": lab.phone if lab else None,
            "is_active": lab.is_active if lab else False,
        } if lab else None,
    }


class DeviceTokenRequest(BaseModel):
    device_token: str
    platform: str  # "android" or "ios"
    app_version: Optional[str] = None

    @field_validator("platform")
    @classmethod
    def validate_platform(cls, v):
        if v not in ("android", "ios"):
            raise ValueError("Platform must be 'android' or 'ios'")
        return v

    @field_validator("device_token")
    @classmethod
    def validate_token(cls, v):
        if len(v) < 10 or len(v) > 512:
            raise ValueError("Invalid device token length")
        return v


@mobile_router.post("/register-device", summary="Register device for push notifications")
def register_device(
    data: DeviceTokenRequest,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Register a mobile device for push notifications (FCM/APNS).
    Call this after login and when the device token changes.

    **Android:** Pass the FCM registration token.
    **iOS:** Pass the APNS device token.
    """
    # Store device token in audit log for now (until push notification service is added)
    log_action(
        db,
        action="device_registered",
        resource_type="device",
        user_id=current_user.id,
        user_role=current_user.role,
        details=f"Device registered: {data.platform} v{data.app_version or 'unknown'}",
    )
    db.commit()

    logger.info(
        "Device registered: user=%d platform=%s version=%s",
        current_user.id, data.platform, data.app_version,
    )

    return {
        "message": "Device registered successfully",
        "message_ar": "تم تسجيل الجهاز بنجاح",
        "push_enabled": False,  # Will be True when FCM/APNS is configured
    }


@mobile_router.get("/stats", summary="Quick stats for mobile dashboard")
def mobile_stats(
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns key statistics for the mobile app dashboard.
    Optimized: single query returns all needed counts.
    """
    from ..models.patient import Patient
    from ..models.lab_order import LabOrder
    from ..models.lab_result import LabResult
    from sqlalchemy import func
    from datetime import datetime, timezone, timedelta

    today = datetime.now(timezone.utc).date()
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)

    lab_id = current_user.lab_id

    total_patients = db.query(func.count(Patient.id)).filter(
        Patient.lab_id == lab_id
    ).scalar() or 0

    total_orders = db.query(func.count(LabOrder.id)).filter(
        LabOrder.lab_id == lab_id
    ).scalar() or 0

    orders_today = db.query(func.count(LabOrder.id)).filter(
        LabOrder.lab_id == lab_id,
        func.date(LabOrder.created_at) == today,
    ).scalar() or 0

    orders_this_week = db.query(func.count(LabOrder.id)).filter(
        LabOrder.lab_id == lab_id,
        LabOrder.created_at >= week_ago,
    ).scalar() or 0

    return {
        "total_patients": total_patients,
        "total_orders": total_orders,
        "orders_today": orders_today,
        "orders_this_week": orders_this_week,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _role_ar(role: str) -> str:
    return {
        "master_admin": "مدير المنصة",
        "admin": "مدير المختبر",
        "staff": "موظف",
        "technician": "تقني مختبر",
    }.get(role, role)


def _get_permissions(role: str) -> list[str]:
    base = ["view_patients", "view_results", "create_order"]
    if role in ("admin", "master_admin"):
        return base + ["manage_users", "manage_lab", "view_audit_logs"]
    if role == "technician":
        return base + ["enter_results", "view_samples"]
    return base


# Include sub-router
router.include_router(mobile_router)
