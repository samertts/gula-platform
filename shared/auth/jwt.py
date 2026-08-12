from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from joserfc import jwt as jose_jwt
from joserfc import jwk
from joserfc.jwt import JWTClaimsRegistry

logger = logging.getLogger("gula.auth.jwt")


class JWTError(Exception):
    """Generic JWT error, kept for backward compatibility with shared.auth consumers."""


def _make_key(secret: str) -> jwk.OctKey:
    return jwk.OctKey.import_key(secret)


def _validate_claims(claims: dict[str, Any]) -> None:
    """Validate JWT claims (exp, iat) using joserfc's registry."""
    registry = JWTClaimsRegistry(
        exp={"essential": True},
        iat={"essential": True},
    )
    registry.validate(claims)


def create_access_token(
    data: dict[str, Any],
    secret_key: str,
    algorithm: str = "HS256",
    expire_minutes: int = 30,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=expire_minutes)
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    if extra_claims:
        to_encode.update(extra_claims)
    key = _make_key(secret_key)
    return jose_jwt.encode({"alg": algorithm}, to_encode, key)


def create_refresh_token(
    data: dict[str, Any],
    refresh_secret: str,
    algorithm: str = "HS256",
    expire_days: int = 30,
) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=expire_days)
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc), "type": "refresh"})
    key = _make_key(refresh_secret)
    return jose_jwt.encode({"alg": algorithm}, to_encode, key)


def decode_access_token(
    token: str,
    secret_key: str,
    algorithms: list[str] | None = None,
) -> dict[str, Any]:
    try:
        key = _make_key(secret_key)
        decoded = jose_jwt.decode(token, key, algorithms=algorithms or ["HS256"])
        claims = dict(decoded.claims)
        _validate_claims(claims)
        return claims
    except Exception as exc:
        logger.warning("JWT decode failed: %s", exc)
        raise JWTError(str(exc)) from exc


def decode_refresh_token(
    token: str,
    refresh_secret: str,
    algorithms: list[str] | None = None,
) -> dict[str, Any]:
    payload = decode_access_token(token, refresh_secret, algorithms)
    if payload.get("type") != "refresh":
        raise JWTError("Token is not a refresh token")
    return payload
