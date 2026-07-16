from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.security.dependencies import get_current_user
from app.security.mfa_service import MFAService

router = APIRouter(prefix="/mfa", tags=["multi-factor-authentication"])


class TOTPSetupRequest(BaseModel):
    device_name: str = "Authenticator App"


class TOTPSetupResponse(BaseModel):
    secret: str
    uri: str
    backup_codes: list[str]
    device_id: int


class TOTPVerifyRequest(BaseModel):
    token: str


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
    session_token: str


class MFAStatusResponse(BaseModel):
    mfa_enabled: bool
    devices: list[dict]


@router.post("/totp/setup", response_model=TOTPSetupResponse)
async def setup_totp(
    req: TOTPSetupRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = MFAService(db)
    result = service.setup_totp(current_user.id, current_user.email, req.device_name)
    return TOTPSetupResponse(**result)


@router.post("/totp/verify")
async def verify_totp(
    req: TOTPVerifyRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = MFAService(db)
    if service.verify_totp(current_user.id, req.token):
        return {"verified": True}
    raise HTTPException(status_code=400, detail="Invalid TOTP token")


@router.post("/webauthn/register/begin", response_model=WebAuthnRegisterBeginResponse)
async def webauthn_register_begin(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = MFAService(db)
    options = service.begin_webauthn_registration(
        current_user.id, current_user.email or current_user.id,
        getattr(current_user, "full_name", current_user.email or ""),
    )
    return WebAuthnRegisterBeginResponse(options=options)


@router.post("/webauthn/register/complete")
async def webauthn_register_complete(
    req: WebAuthnRegisterCompleteRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = MFAService(db)
    service.complete_webauthn_registration(current_user.id, req.credential, req.device_name)
    return {"success": True}


@router.post("/webauthn/authenticate/begin", response_model=WebAuthnAuthenticateBeginResponse)
async def webauthn_authenticate_begin(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = MFAService(db)
    options = service.begin_webauthn_authentication(current_user.id)
    return WebAuthnAuthenticateBeginResponse(options=options)


@router.post("/webauthn/authenticate/complete")
async def webauthn_authenticate_complete(
    req: WebAuthnAuthenticateCompleteRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = MFAService(db)
    if service.complete_webauthn_authentication(current_user.id, req.credential):
        return {"verified": True}
    raise HTTPException(status_code=401, detail="WebAuthn authentication failed")


@router.get("/devices", response_model=MFAStatusResponse)
async def list_devices(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = MFAService(db)
    devices = service.get_user_devices(current_user.id)
    return MFAStatusResponse(mfa_enabled=len(devices) > 0, devices=devices)


@router.delete("/devices/{device_id}")
async def remove_device(
    device_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = MFAService(db)
    if service.remove_device(current_user.id, device_id):
        return {"success": True}
    raise HTTPException(status_code=404, detail="Device not found")


@router.get("/status", response_model=MFAStatusResponse)
async def mfa_status(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = MFAService(db)
    devices = service.get_user_devices(current_user.id)
    return MFAStatusResponse(mfa_enabled=service.has_mfa_enabled(current_user.id), devices=devices)
