import logging
import os

from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from ..config import APP_NAME, APP_VERSION
from ..database import get_db
from ..models.lab import Lab
from ..models.lab_user import LabUser
from ..security.dependencies import get_current_user
from ..services.audit_service import log_action
from ..services.mobile_service import (
    change_user_password,
    get_mobile_stats,
    get_permissions,
    refresh_token,
    role_ar,
)

logger = logging.getLogger("gula.mobile")

router = APIRouter(prefix="/auth", tags=["mobile / auth"])


class RefreshRequest(BaseModel):
    refresh_token: str | None = None


@router.post("/refresh", summary="Refresh access token (mobile and web)")
def refresh_access_token(
    data: RefreshRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    return refresh_token(
        data.refresh_token or request.cookies.get("refresh_token"), request, response, db
    )


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


@router.post("/change-password", summary="Change current user password")
def change_password(
    data: ChangePasswordRequest,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return change_user_password(data.current_password, data.new_password, current_user, db)


mobile_router = APIRouter(prefix="/mobile", tags=["mobile / info"])


@mobile_router.get("/app-info", summary="Mobile app configuration")
def get_app_info():
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
            "push_notifications": False,
            "biometric_auth": False,
            "offline_mode": False,
            "critical_alerts": True,
        },
        "support": {
            "email": "support@gula-platform.org",
            "whatsapp": os.getenv("WHATSAPP_SUPPORT", ""),
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
    lab = None
    if current_user.lab_id:
        lab = db.query(Lab).filter(Lab.id == current_user.lab_id).first()

    return {
        "user": {
            "id": current_user.id,
            "name": current_user.name,
            "email": current_user.email,
            "role": current_user.role,
            "role_ar": role_ar(current_user.role),
            "permissions": get_permissions(current_user.role),
        },
        "lab": {
            "id": lab.id if lab else None,
            "name": lab.name if lab else None,
            "city": lab.city if lab else None,
            "phone": lab.phone if lab else None,
            "is_active": lab.is_active if lab else False,
        }
        if lab
        else None,
    }


class DeviceTokenRequest(BaseModel):
    device_token: str
    platform: str
    app_version: str | None = None

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


@mobile_router.post(
    "/register-device", status_code=201, summary="Register device for push notifications"
)
def register_device(
    data: DeviceTokenRequest,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
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
        current_user.id,
        data.platform,
        data.app_version,
    )

    return {
        "message": "Device registered successfully",
        "message_ar": "تم تسجيل الجهاز بنجاح",
        "push_enabled": False,
    }


@mobile_router.get("/stats", summary="Quick stats for mobile dashboard")
def mobile_stats(
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_mobile_stats(current_user.lab_id, db)


router.include_router(mobile_router)
