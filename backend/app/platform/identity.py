"""Standardized identity module — wraps existing security/auth.py."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass

from ..security.auth import (
    blacklist_token,
    create_refresh_token,
    decode_token,
    is_token_blacklisted,
)
from . import PlatformRegistry

logger = logging.getLogger("gula.platform.identity")


@dataclass
class IdentityVerificationResult:
    valid: bool = False
    user_id: int | None = None
    lab_id: int | None = None
    role: str | None = None
    payload: dict | None = None
    error: str | None = None


class IdentityProvider(ABC):
    @abstractmethod
    def verify_token(self, token: str) -> IdentityVerificationResult:
        ...

    @abstractmethod
    def refresh_identity(self, identity: dict) -> str | None:
        ...

    @abstractmethod
    def revoke_identity(self, identity_id: str) -> bool:
        ...


class JWTIdentityProvider(IdentityProvider):
    def verify_token(self, token: str) -> IdentityVerificationResult:
        payload = decode_token(token)
        if payload is None:
            return IdentityVerificationResult(valid=False, error="Invalid or expired token")
        jti = payload.get("jti")
        if jti and is_token_blacklisted(jti):
            return IdentityVerificationResult(valid=False, error="Token revoked")
        return IdentityVerificationResult(
            valid=True,
            user_id=payload.get("user_id"),
            lab_id=payload.get("lab_id"),
            role=payload.get("role"),
            payload=payload,
        )

    def refresh_identity(self, identity: dict) -> str | None:
        return create_refresh_token(identity)

    def revoke_identity(self, identity_id: str) -> bool:
        try:
            blacklist_token(identity_id, ttl_seconds=86400)
            return True
        except Exception:
            return False


PlatformRegistry.register("identity", JWTIdentityProvider(), capabilities=[
    {"name": "verify_token", "description": "Verify and decode a JWT access token"},
    {"name": "refresh_identity", "description": "Issue a new refresh token"},
    {"name": "revoke_identity", "description": "Revoke a token by JTI"},
])
