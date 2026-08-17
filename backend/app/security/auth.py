"""Authentication — delegates to canonical shared.auth with backend-specific extensions.

Backend keeps:
- JWT blacklist (Redis-backed revocation)
- Token type discrimination (access vs refresh)
- build_token_payload for LabUser
- Dummy hash for timing-safe login
"""

from __future__ import annotations

from typing import Any, Protocol, cast
from uuid import uuid4

from shared.auth import JWTError
from shared.auth import (
    create_access_token as _shared_create_access_token,
)
from shared.auth import (
    create_refresh_token as _shared_create_refresh_token,
)
from shared.auth import (
    decode_access_token as _shared_decode_access_token,
)
from shared.auth import (
    hash_password as _shared_hash_password,
)
from shared.auth import (
    verify_password as _shared_verify_password,
)

from ..config import (
    JWT_ALGORITHM,
    JWT_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
    REFRESH_TOKEN_SECRET,
    SECRET_KEY,
)


class _TokenUser(Protocol):
    id: int
    lab_id: int | None
    role: str
    perm_version: int | None


JWTClaims = dict[str, Any]


# ── JWT Token Blacklist (revocation) ──────────────────────────────────────────


def blacklist_token(jti: str, ttl_seconds: int) -> None:
    from .redis_client import cache

    cache.set(f"blacklist:jti:{jti}", "1", ex=ttl_seconds)


def is_token_blacklisted(jti: str) -> bool:
    from .redis_client import cache

    return cache.get(f"blacklist:jti:{jti}") is not None


def consume_refresh_jti(jti: str, ttl_seconds: int) -> bool:
    """Atomically consume a refresh JTI for single-use rotation."""
    from .redis_client import cache

    return cache.set_if_absent(f"refresh:consumed:{jti}", "1", ex=ttl_seconds)


# Generate a process-local dummy hash so missing-user login paths have the
# same bcrypt work factor without embedding credential-like material in source.
_DUMMY_HASH: str = _shared_hash_password(f"gula-timing-dummy:{uuid4().hex}")


def hash_password(password: str) -> str:
    return cast(str, _shared_hash_password(password))


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return cast(bool, _shared_verify_password(plain_password, hashed_password))


def build_token_payload(user: _TokenUser, *, account_kind: str = "lab") -> JWTClaims:
    if account_kind not in {"lab", "user"}:
        raise ValueError("Unsupported account kind")
    return {
        "user_id": user.id,
        "lab_id": user.lab_id,
        "role": user.role,
        "account_kind": account_kind,
        "perm_ver": user.perm_version if user.perm_version is not None else 1,
    }


def create_token(data: JWTClaims) -> str:
    to_encode = data.copy()
    to_encode.setdefault("jti", str(uuid4()))
    to_encode["type"] = "access"
    return cast(str, _shared_create_access_token(
        to_encode,
        secret_key=SECRET_KEY,
        algorithm=JWT_ALGORITHM,
        expire_minutes=JWT_EXPIRE_MINUTES,
    ))


def decode_token(token: str) -> JWTClaims | None:
    try:
        payload = _shared_decode_access_token(token, SECRET_KEY, [JWT_ALGORITHM])
        if payload.get("type") != "access":
            return None
        return cast(JWTClaims, payload)
    except JWTError:
        return None


def create_refresh_token(data: JWTClaims) -> str:
    to_encode = data.copy()
    to_encode.setdefault("jti", str(uuid4()))
    to_encode["type"] = "refresh"
    return cast(str, _shared_create_refresh_token(
        to_encode,
        refresh_secret=REFRESH_TOKEN_SECRET,
        algorithm=JWT_ALGORITHM,
        expire_days=REFRESH_TOKEN_EXPIRE_DAYS,
    ))


def decode_refresh_token(token: str, *, check_blacklist: bool = True) -> JWTClaims | None:
    try:
        payload = _shared_decode_access_token(token, REFRESH_TOKEN_SECRET, [JWT_ALGORITHM])
        if payload.get("type") != "refresh":
            return None
        jti = payload.get("jti")
        if check_blacklist and jti and is_token_blacklisted(jti):
            return None
        return cast(JWTClaims, payload)
    except JWTError:
        return None
