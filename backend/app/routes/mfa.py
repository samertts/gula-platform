from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.security.dependencies import get_current_user
from app.security.mfa_service import MFAService
from app.security.rate_limit import get_client_ip, rate_limit_auth
from app.security.session import bump_perm_version
from app.services.audit_service import log_action

router = APIRouter(prefix="/mfa", tags=["multi-factor-authentication"])


def _rate_limit_mfa(request: Request, current_user, max_per_minute: int = 10) -> None:
    rate_limit_auth(request, max_per_minute=max_per_minute, identifier=str(current_user.id))


class TOTPSetupRequest(BaseModel):
    device_name: str = "Authenticator App"


class TOTPSetupResponse(BaseModel):
    secret: str
    uri: str
    backup_codes: list[str]
    device_id: int


class TOTPVerifyRequest(BaseModel):
    token: str = Field(min_length=6, max_length=16)


class WebAuthnRegisterBeginResponse(BaseModel):
    options: dict


class WebAuthnRegisterCompleteRequest(BaseModel):
    credential: dict
    device_name: str = "Security Key"


class WebAuthnAuthenticateBeginResponse(BaseModel):
    options: dict


class WebAuthnAuthenticateCompleteRequest(BaseModel):
    credential: dict


class MFASessionRequest(BaseModel):
    session_token: str = Field(min_length=32, max_length=128)


class MFAStatusResponse(BaseModel):
    mfa_enabled: bool
    devices: list[dict]


@router.post("/totp/setup", response_model=TOTPSetupResponse)
async def setup_totp(
    req: TOTPSetupRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    _rate_limit_mfa(request, current_user, max_per_minute=5)
    service = MFAService(db)
    result = service.setup_totp(current_user.id, current_user.email, req.device_name)
    log_action(
        db,
        action="mfa_changed",
        resource_type="mfa_device",
        resource_id=result["device_id"],
        user_id=current_user.id,
        user_role=getattr(current_user, "role", None),
        lab_id=getattr(current_user, "lab_id", None),
        details={"change": "mfa_setup", "device_type": "totp"},
        ip_address=get_client_ip(request),
    )
    db.commit()
    return TOTPSetupResponse(**result)


@router.post("/totp/verify")
async def verify_totp(
    req: TOTPVerifyRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    _rate_limit_mfa(request, current_user, max_per_minute=5)
    service = MFAService(db)
    if service.verify_totp(current_user.id, req.token):
        step_up_token = service.create_mfa_session(current_user.id, "totp")
        log_action(
            db,
            action="mfa_verification_succeeded",
            resource_type="mfa_session",
            user_id=current_user.id,
            user_role=getattr(current_user, "role", None),
            lab_id=getattr(current_user, "lab_id", None),
            details={"method": "totp", "purpose": "security_step_up"},
            ip_address=get_client_ip(request),
        )
        db.commit()
        return {"verified": True, "mfa_session_token": step_up_token}
    log_action(
        db,
        action="mfa_verification_failed",
        resource_type="mfa_session",
        user_id=current_user.id,
        user_role=getattr(current_user, "role", None),
        lab_id=getattr(current_user, "lab_id", None),
        details={"method": "totp", "purpose": "security_step_up"},
        ip_address=get_client_ip(request),
    )
    db.commit()
    raise HTTPException(status_code=400, detail="Invalid TOTP token")


@router.post("/webauthn/register/begin", response_model=WebAuthnRegisterBeginResponse)
async def webauthn_register_begin(
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    _rate_limit_mfa(request, current_user)
    service = MFAService(db)
    try:
        options = service.begin_webauthn_registration(
            current_user.id, current_user.email or current_user.id,
            getattr(current_user, "full_name", current_user.email or ""),
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail="MFA service temporarily unavailable") from exc
    return WebAuthnRegisterBeginResponse(options=options)


@router.post("/webauthn/register/complete")
async def webauthn_register_complete(
    req: WebAuthnRegisterCompleteRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    _rate_limit_mfa(request, current_user)
    service = MFAService(db)
    try:
        device = service.complete_webauthn_registration(current_user.id, req.credential, req.device_name)
        log_action(
            db,
            action="passkey_changed",
            resource_type="mfa_device",
            resource_id=device.id,
            user_id=current_user.id,
            user_role=getattr(current_user, "role", None),
            lab_id=getattr(current_user, "lab_id", None),
            details={"change": "passkey_added", "device_type": "webauthn"},
            ip_address=get_client_ip(request),
        )
        db.commit()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail="MFA service temporarily unavailable") from exc
    return {"success": True}


@router.post("/webauthn/authenticate/begin", response_model=WebAuthnAuthenticateBeginResponse)
async def webauthn_authenticate_begin(
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    _rate_limit_mfa(request, current_user)
    service = MFAService(db)
    try:
        options = service.begin_webauthn_authentication(current_user.id)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail="MFA service temporarily unavailable") from exc
    return WebAuthnAuthenticateBeginResponse(options=options)


@router.post("/webauthn/authenticate/complete")
async def webauthn_authenticate_complete(
    req: WebAuthnAuthenticateCompleteRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    _rate_limit_mfa(request, current_user)
    service = MFAService(db)
    try:
        authenticated = service.complete_webauthn_authentication(current_user.id, req.credential)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail="MFA service temporarily unavailable") from exc
    if authenticated:
        step_up_token = service.create_mfa_session(current_user.id, "webauthn")
        log_action(
            db,
            action="mfa_verification_succeeded",
            resource_type="mfa_session",
            user_id=current_user.id,
            user_role=getattr(current_user, "role", None),
            lab_id=getattr(current_user, "lab_id", None),
            details={"method": "webauthn", "purpose": "security_step_up"},
            ip_address=get_client_ip(request),
        )
        db.commit()
        return {"verified": True, "mfa_session_token": step_up_token}
    log_action(
        db,
        action="mfa_verification_failed",
        resource_type="mfa_session",
        user_id=current_user.id,
        user_role=getattr(current_user, "role", None),
        lab_id=getattr(current_user, "lab_id", None),
        details={"method": "webauthn", "purpose": "security_step_up"},
        ip_address=get_client_ip(request),
    )
    db.commit()
    raise HTTPException(status_code=401, detail="WebAuthn authentication failed")


@router.get("/devices", response_model=MFAStatusResponse)
async def list_devices(
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    _rate_limit_mfa(request, current_user, max_per_minute=30)
    service = MFAService(db)
    devices = service.get_user_devices(current_user.id)
    return MFAStatusResponse(mfa_enabled=len(devices) > 0, devices=devices)


@router.delete("/devices/{device_id}")
async def remove_device(
    device_id: int,
    req: MFASessionRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    _rate_limit_mfa(request, current_user)
    service = MFAService(db)
    step_up_user_id = service.verify_mfa_session(req.session_token)
    if step_up_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Recent MFA verification is required")
    if service.remove_device(current_user.id, device_id):
        bump_perm_version(
            current_user,
            db,
            actor_id=current_user.id,
            actor_role=getattr(current_user, "role", None),
            reason="mfa_device_removed",
        )
        log_action(
            db,
            action="mfa_changed",
            resource_type="mfa_device",
            resource_id=device_id,
            user_id=current_user.id,
            user_role=getattr(current_user, "role", None),
            lab_id=getattr(current_user, "lab_id", None),
            details={"change": "mfa_device_removed", "reason_code": "step_up_verified"},
            ip_address=get_client_ip(request),
        )
        log_action(
            db,
            action="session_revoked",
            resource_type="account_security",
            resource_id=current_user.id,
            user_id=current_user.id,
            user_role=getattr(current_user, "role", None),
            lab_id=getattr(current_user, "lab_id", None),
            details={"reason_code": "mfa_device_removed"},
            ip_address=get_client_ip(request),
        )
        db.commit()
        return {"success": True}
    raise HTTPException(status_code=404, detail="Device not found")


@router.get("/status", response_model=MFAStatusResponse)
async def mfa_status(
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    _rate_limit_mfa(request, current_user, max_per_minute=30)
    service = MFAService(db)
    devices = service.get_user_devices(current_user.id)
    return MFAStatusResponse(mfa_enabled=service.has_mfa_enabled(current_user.id), devices=devices)
