"""Authentication — delegates to canonical shared.auth with backend-specific extensions.

Backend keeps:
- JWT blacklist (Redis-backed revocation)
- Token type discrimination (access vs refresh)
- build_token_payload for LabUser
- Dummy hash for timing-safe login
"""

from __future__ import annotations

from uuid import uuid4

from jose import JWTError

from shared.auth import (
    create_access_token as _shared_create_access_token,
    create_refresh_token as _shared_create_refresh_token,
    decode_access_token as _shared_decode_access_token,
    hash_password as _shared_hash_password,
    verify_password as _shared_verify_password,
)
from ..config import (
    JWT_ALGORITHM,
    JWT_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
    REFRESH_TOKEN_SECRET,
    SECRET_KEY,
)

# ── JWT Token Blacklist (revocation) ──────────────────────────────────────────

def blacklist_token(jti: str, ttl_seconds: int) -> None:
    from .redis_client import cache
    cache.set(f"blacklist:jti:{jti}", "1", ex=ttl_seconds)


def is_token_blacklisted(jti: str) -> bool:
    from .redis_client import cache
    return cache.get(f"blacklist:jti:{jti}") is not None


# Pre-computed dummy hash for timing-safe login (prevents user enumeration).
_DUMMY_HASH: str = "$2b$12$KOyWdwU2QI3BzsWt.4RGgua1dx53C7jHfc8UzpEKylbB5QwaGPJ6G"


def hash_password(password: str) -> str:
    return _shared_hash_password(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return _shared_verify_password(plain_password, hashed_password)


def build_token_payload(user) -> dict:
    return {
        "user_id": user.id,
        "lab_id": user.lab_id,
        "role": user.role,
        "perm_ver": user.perm_version if user.perm_version is not None else 1,
    }


def create_token(data: dict) -> str:
    to_encode = data.copy()
    to_encode.update({"type": "access", "jti": str(uuid4())})
    return _shared_create_access_token(
        to_encode,
        secret_key=SECRET_KEY,
        algorithm=JWT_ALGORITHM,
        expire_minutes=JWT_EXPIRE_MINUTES,
    )


def decode_token(token: str) -> dict | None:
    try:
        payload = _shared_decode_access_token(token, SECRET_KEY, [JWT_ALGORITHM])
        if payload.get("type") != "access":
            return None
        return payload
    except JWTError:
        return None


def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    to_encode.update({"type": "refresh", "jti": str(uuid4())})
    return _shared_create_refresh_token(
        to_encode,
        refresh_secret=REFRESH_TOKEN_SECRET,
        algorithm=JWT_ALGORITHM,
        expire_days=REFRESH_TOKEN_EXPIRE_DAYS,
    )


def decode_refresh_token(token: str) -> dict | None:
    try:
        payload = _shared_decode_access_token(token, REFRESH_TOKEN_SECRET, [JWT_ALGORITHM])
        if payload.get("type") != "refresh":
            return None
        jti = payload.get("jti")
        if jti and is_token_blacklisted(jti):
            return None
        return payload
    except JWTError:
        return None
