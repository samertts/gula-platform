"""
Auth utilities for NHOP Lab Platform
JWT via python-jose, password hashing via hashlib (pbkdf2)
"""

import hashlib
import os
import secrets
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from database.db import SessionLocal

SECRET_KEY   = os.getenv("JWT_SECRET", "nhop-python-secret-change-in-prod-2024")
ALGORITHM    = "HS256"
ACCESS_HOURS = 8

security = HTTPBearer(auto_error=False)


# -------------------------------------------------------
# Password helpers (pbkdf2 - no external dep needed)
# -------------------------------------------------------

def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    dk   = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 260000)
    return f"pbkdf2:sha256:260000:{salt}:{dk.hex()}"


def verify_password(plain: str, hashed: str) -> bool:
    try:
        parts = hashed.split(":")
        if len(parts) != 5:
            return False
        _, algo, iters, salt, stored = parts
        dk = hashlib.pbkdf2_hmac(algo, plain.encode(), salt.encode(), int(iters))
        return dk.hex() == stored
    except Exception:
        return False


# -------------------------------------------------------
# JWT helpers
# -------------------------------------------------------

def create_access_token(data: dict) -> str:
    payload = data.copy()
    payload["exp"] = datetime.utcnow() + timedelta(hours=ACCESS_HOURS)
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None


# -------------------------------------------------------
# Dependency: get current user from JWT
# -------------------------------------------------------

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
):
    from models.user import User

    if not credentials:
        raise HTTPException(status_code=401, detail="authentication_required")

    payload = decode_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="token_invalid_or_expired")

    user = db.query(User).filter(User.id == payload.get("id")).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="user_not_found_or_disabled")

    return user


def require_roles(*roles):
    """Returns a FastAPI dependency that enforces role access."""
    def checker(user=Depends(get_current_user)):
        if user.role not in roles:
            raise HTTPException(
                status_code=403,
                detail=f"insufficient_permissions. Required: {list(roles)}"
            )
        return user
    return checker
