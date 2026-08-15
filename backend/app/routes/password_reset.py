from __future__ import annotations

import contextlib
import secrets
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app._compat import UTC
from app.database import get_db
from app.models.lab_user import LabUser
from app.models.user import User
from app.security.dependencies import get_current_user
from app.security.rate_limit import rate_limit_auth
from app.services.audit_service import log_action
from shared.auth.passwords import hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["password-reset"])
_RESETTABLE_MODELS = (User, LabUser)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


def _find_account_by_email(db: Session, email: str) -> User | LabUser | None:
    """Resolve either platform users or legacy laboratory users without leaking account type."""
    for model in _RESETTABLE_MODELS:
        account = db.query(model).filter(model.email == email).first()
        if account is not None:
            return account
    return None


def _find_account_by_reset_token(
    db: Session,
    token: str,
    now: datetime,
) -> User | LabUser | None:
    """Verify a raw token against hashed tokens in both account stores."""
    for model in _RESETTABLE_MODELS:
        candidates = db.query(model).filter(
            model.reset_token.isnot(None),
            model.reset_token_expires > now,
        ).all()
        for account in candidates:
            if account.reset_token and verify_password(token, account.reset_token):
                return account
    return None


@router.post("/forgot-password")
async def forgot_password(
    req: ForgotPasswordRequest,
    db: Session = Depends(get_db),
    _rate=Depends(rate_limit_auth),
):
    account = _find_account_by_email(db, str(req.email))
    if account is not None:
        token = secrets.token_urlsafe(32)
        account.reset_token = hash_password(token)
        account.reset_token_expires = datetime.now(UTC) + timedelta(hours=1)
        db.commit()
        with contextlib.suppress(Exception):
            log_action(
                db,
                action="password_reset_requested",
                resource_type="password_reset",
                user_id=account.id,
            )
    return {"message": "If the email exists, a reset link has been sent"}


@router.post("/reset-password")
async def reset_password(
    req: ResetPasswordRequest,
    db: Session = Depends(get_db),
    _rate=Depends(rate_limit_auth),
):
    account = _find_account_by_reset_token(db, req.token, datetime.now(UTC))
    if account is None:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    account.password_hash = hash_password(req.new_password)
    account.reset_token = None
    account.reset_token_expires = None
    db.commit()
    with contextlib.suppress(Exception):
        log_action(
            db,
            action="password_reset_completed",
            resource_type="password_reset",
            user_id=account.id,
        )
    return {"message": "Password reset successful"}


@router.post("/change-password")
async def change_password(
    req: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if not verify_password(req.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    current_user.password_hash = hash_password(req.new_password)
    from app.security.session import bump_perm_version
    bump_perm_version(db, current_user.id)
    db.commit()
    return {"message": "Password changed successfully"}
