from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt

logger = logging.getLogger("gula.auth.jwt")


def create_access_token(
    data: dict[str, Any],
    secret_key: str,
    algorithm: str = "HS256",
    expire_minutes: int = 30,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(minutes=expire_minutes)
    to_encode.update({"exp": expire, "iat": datetime.now(UTC)})
    if extra_claims:
        to_encode.update(extra_claims)
    return jwt.encode(to_encode, secret_key, algorithm=algorithm)


def create_refresh_token(
    data: dict[str, Any],
    refresh_secret: str,
    algorithm: str = "HS256",
    expire_days: int = 30,
) -> str:
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(days=expire_days)
    to_encode.update({"exp": expire, "iat": datetime.now(UTC), "type": "refresh"})
    return jwt.encode(to_encode, refresh_secret, algorithm=algorithm)


def decode_access_token(
    token: str,
    secret_key: str,
    algorithms: list[str] | None = None,
) -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            secret_key,
            algorithms=algorithms or ["HS256"],
            options={"require": ["exp", "iat"]},
        )
        return payload
    except JWTError as exc:
        logger.warning("JWT decode failed: %s", exc)
        raise


def decode_refresh_token(
    token: str,
    refresh_secret: str,
    algorithms: list[str] | None = None,
) -> dict[str, Any]:
    payload = decode_access_token(token, refresh_secret, algorithms)
    if payload.get("type") != "refresh":
        raise JWTError("Token is not a refresh token")
    return payload
