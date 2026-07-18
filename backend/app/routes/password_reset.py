from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app._compat import UTC
from app.database import get_db
from app.models.lab_user import LabUser
from app.security.dependencies import get_current_user
from app.security.rate_limit import rate_limit_auth
from shared.auth.passwords import hash_password

router = APIRouter(prefix="/auth", tags=["password-reset"])


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


@router.post("/forgot-password")
async def forgot_password(
    req: ForgotPasswordRequest,
    db: Session = Depends(get_db),
    _rate=Depends(rate_limit_auth),
):
    user = db.query(LabUser).filter(LabUser.email == req.email).first()
    if not user:
        return {"message": "If the email exists, a reset link has been sent"}
    import hashlib
    import secrets
    token = secrets.token_urlsafe(32)
    hashed = hashlib.sha256(token.encode()).hexdigest()
    user.reset_token = hashed
    user.reset_token_expires = datetime.now(UTC) + timedelta(hours=1)
    db.commit()
    return {"message": "If the email exists, a reset link has been sent"}


@router.post("/reset-password")
async def reset_password(
    req: ResetPasswordRequest,
    db: Session = Depends(get_db),
    _rate=Depends(rate_limit_auth),
):
    import hashlib
    hashed = hashlib.sha256(req.token.encode()).hexdigest()
    user = db.query(LabUser).filter(
        LabUser.reset_token == hashed,
        LabUser.reset_token_expires > datetime.now(UTC),
    ).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    user.password_hash = hash_password(req.new_password)
    user.reset_token = None
    user.reset_token_expires = None
    db.commit()
    return {"message": "Password reset successful"}


@router.post("/change-password")
async def change_password(
    req: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    from shared.auth.passwords import verify_password
    if not verify_password(req.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    current_user.password_hash = hash_password(req.new_password)
    from app.security.session import bump_perm_version
    bump_perm_version(db, current_user.id)
    db.commit()
    return {"message": "Password changed successfully"}
