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

# ── Account-domain discrimination (AUD-SEC-002) ───────────────────────────────
# LabUser.id and User.id are independent primary-key spaces. A bare integer
# user_id claim is therefore ambiguous: LabUser #N and User #N can coexist and
# a token minted for one family could resolve to the other. Every access token
# must carry a signed ``account_kind`` claim naming the family it belongs to.
ACCOUNT_KIND_LAB = "lab"
ACCOUNT_KIND_USER = "user"
ACCOUNT_KIND_NIAM = "niam_account"
_ACCESS_ACCOUNT_KINDS = frozenset({ACCOUNT_KIND_LAB, ACCOUNT_KIND_USER})


def account_kind_for_principal(principal: object) -> str:
    """Classify an authenticated principal into its token account domain.

    Uses a local import to avoid a module-level cycle (models → security).
    Unknown synthetic objects are treated as individual ``User`` accounts —
    the conservative default, since lab scope is the elevated domain.
    """
    from ..models.lab_user import LabUser

    return ACCOUNT_KIND_LAB if isinstance(principal, LabUser) else ACCOUNT_KIND_USER


def resolve_token_account_kind(payload: JWTClaims) -> str | None:
    """Resolve the account domain declared by a *signed* access token.

    Returns ``None`` for an unknown ``account_kind`` (callers must reject).
    Legacy tokens issued before this claim existed are derived from the signed
    ``lab_id`` claim: institutional accounts always carry a non-null lab_id and
    citizen accounts always carry null. This keeps legacy tokens working while
    eliminating cross-family resolution — the root cause of AUD-SEC-002.
    """
    declared = payload.get("account_kind")
    if declared is not None:
        return declared if declared in _ACCESS_ACCOUNT_KINDS else None
    return ACCOUNT_KIND_LAB if payload.get("lab_id") is not None else ACCOUNT_KIND_USER


# ── JWT Token Blacklist (revocation) ──────────────────────────────────────────


def blacklist_token(jti: str, ttl_seconds: int) -> None:
    from .redis_client import security_store

    security_store("Token revocation").set(f"blacklist:jti:{jti}", "1", ex=ttl_seconds)


def is_token_blacklisted(jti: str) -> bool:
    from .redis_client import security_store

    return security_store("Token revocation").get(f"blacklist:jti:{jti}") is not None


# Generate a process-local dummy hash so missing-user login paths have the
# same bcrypt work factor without embedding credential-like material in source.
_DUMMY_HASH: str = _shared_hash_password(f"gula-timing-dummy:{uuid4().hex}")


def hash_password(password: str) -> str:
    return cast(str, _shared_hash_password(password))


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return cast(bool, _shared_verify_password(plain_password, hashed_password))


def build_token_payload(user: _TokenUser) -> JWTClaims:
    return {
        "user_id": user.id,
        "lab_id": user.lab_id,
        "role": user.role,
        "perm_ver": user.perm_version if user.perm_version is not None else 1,
        # A signed domain qualifier prevents LabUser/User primary-key collisions
        # from resolving a token to the wrong account family (AUD-SEC-002).
        "account_kind": account_kind_for_principal(user),
    }


def create_token(data: JWTClaims) -> str:
    to_encode = data.copy()
    to_encode.update({"type": "access", "jti": str(uuid4())})
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


# ── Scoped MFA-pending token (AUD-SEC-003) ────────────────────────────────────
# After a privileged account passes credential verification, the server issues
# this short-lived, single-purpose token instead of a full access token. Its
# distinct ``type`` means decode_token() rejects it on every protected route,
# and decode_mfa_pending_token() rejects ordinary access tokens. Full tokens
# are minted only after a real second factor is verified.
MFA_PENDING_TYPE = "mfa_pending"
MFA_PENDING_PURPOSE = "mfa_login"
MFA_PENDING_TTL_MINUTES = 5


def create_mfa_pending_token(data: JWTClaims) -> str:
    to_encode = data.copy()
    to_encode.update(
        {
            "type": MFA_PENDING_TYPE,
            "purpose": MFA_PENDING_PURPOSE,
            "jti": str(uuid4()),
        }
    )
    return cast(
        str,
        _shared_create_access_token(
            to_encode,
            secret_key=SECRET_KEY,
            algorithm=JWT_ALGORITHM,
            expire_minutes=MFA_PENDING_TTL_MINUTES,
        ),
    )


def decode_mfa_pending_token(token: str) -> JWTClaims | None:
    try:
        payload = _shared_decode_access_token(token, SECRET_KEY, [JWT_ALGORITHM])
        if payload.get("type") != MFA_PENDING_TYPE:
            return None
        if payload.get("purpose") != MFA_PENDING_PURPOSE:
            return None
        return cast(JWTClaims, payload)
    except JWTError:
        return None


def create_refresh_token(data: JWTClaims) -> str:
    to_encode = data.copy()
    to_encode.update({"type": "refresh", "jti": str(uuid4())})
    return cast(str, _shared_create_refresh_token(
        to_encode,
        refresh_secret=REFRESH_TOKEN_SECRET,
        algorithm=JWT_ALGORITHM,
        expire_days=REFRESH_TOKEN_EXPIRE_DAYS,
    ))


def decode_refresh_token(token: str) -> JWTClaims | None:
    try:
        payload = _shared_decode_access_token(token, REFRESH_TOKEN_SECRET, [JWT_ALGORITHM])
        if payload.get("type") != "refresh":
            return None
        jti = payload.get("jti")
        if jti and is_token_blacklisted(jti):
            return None
        return cast(JWTClaims, payload)
    except JWTError:
        return None
