from __future__ import annotations

import hashlib
import hmac
import logging
import secrets
from base64 import urlsafe_b64encode
from datetime import datetime, timedelta
from typing import Any
from uuid import uuid4

from joserfc import jwk
from joserfc import jwt as jose_jwt
from pydantic import BaseModel

from app._compat import UTC
from shared.auth import JWTError, create_access_token, decode_access_token

from ..config import BASE_URL, JWT_ALGORITHM, JWT_EXPIRE_MINUTES, SECRET_KEY

logger = logging.getLogger("gula.oauth2")


class OAuth2AuthorizationRequest(BaseModel):
    response_type: str
    client_id: str
    redirect_uri: str | None = None
    scope: str | None = None
    state: str | None = None
    code_challenge: str | None = None
    code_challenge_method: str | None = None


class OAuth2TokenRequest(BaseModel):
    grant_type: str
    code: str | None = None
    redirect_uri: str | None = None
    client_id: str | None = None
    client_secret: str | None = None
    refresh_token: str | None = None
    scope: str | None = None
    code_verifier: str | None = None


class OAuth2IntrospectRequest(BaseModel):
    token: str
    token_type_hint: str | None = None


class OAuth2RevokeRequest(BaseModel):
    token: str
    token_type_hint: str | None = None


def generate_client_id() -> str:
    return f"gula_{secrets.token_urlsafe(24)}"


def generate_client_secret() -> str:
    return secrets.token_urlsafe(48)


def hash_token(token: str) -> str:
    """Create a server-bound fingerprint for OAuth token lookup."""
    return hmac.new(
        SECRET_KEY.encode("utf-8"),
        token.encode("utf-8"),
        hashlib.sha3_512,
    ).hexdigest()


def generate_auth_code() -> str:
    return secrets.token_urlsafe(32)


def generate_token_id() -> str:
    return str(uuid4())


def verify_pkce(code_verifier: str, code_challenge: str, method: str) -> bool:
    if method != "S256":
        return False
    computed = urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode("ascii")).digest(),
    ).rstrip(b"=").decode()
    return computed == code_challenge


def create_id_token(
    user_id: int,
    client_id: str,
    nonce: str | None = None,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    now = datetime.now(UTC)
    payload = {
        "iss": f"{BASE_URL}/oauth2",
        "sub": str(user_id),
        "aud": client_id,
        "exp": now + timedelta(hours=1),
        "iat": now,
        "auth_time": int(now.timestamp()),
        "jti": generate_token_id(),
    }
    if nonce:
        payload["nonce"] = nonce
    if extra_claims:
        payload.update(extra_claims)
    return jose_jwt.encode({"alg": JWT_ALGORITHM}, payload, jwk.OctKey.import_key(SECRET_KEY))


def create_access_token_oauth2(
    client_id: str,
    user_id: int | None = None,
    scope: str | None = None,
    expires_in: int | None = None,
) -> tuple[str, int]:
    expire_minutes = expires_in // 60 if expires_in else JWT_EXPIRE_MINUTES
    payload = {
        "jti": generate_token_id(),
        "client_id": client_id,
        "type": "oauth2_access",
    }
    if user_id is not None:
        payload["user_id"] = user_id
    if scope:
        payload["scope"] = scope
    token = create_access_token(payload, secret_key=SECRET_KEY, algorithm=JWT_ALGORITHM, expire_minutes=expire_minutes)
    return token, expire_minutes * 60


def create_refresh_token_oauth2(client_id: str, user_id: int | None = None, scope: str | None = None) -> str:
    payload = {
        "jti": generate_token_id(),
        "client_id": client_id,
        "type": "oauth2_refresh",
    }
    if user_id is not None:
        payload["user_id"] = user_id
    if scope:
        payload["scope"] = scope
    from ..config import REFRESH_TOKEN_EXPIRE_DAYS, REFRESH_TOKEN_SECRET
    return create_access_token(
        payload,
        secret_key=REFRESH_TOKEN_SECRET,
        algorithm=JWT_ALGORITHM,
        expire_minutes=REFRESH_TOKEN_EXPIRE_DAYS * 1440,
    )


def decode_oauth2_token(token: str) -> dict[str, Any] | None:
    try:
        payload = decode_access_token(token, SECRET_KEY, [JWT_ALGORITHM])
        if payload.get("type") != "oauth2_access":
            return None
        return payload
    except JWTError:
        return None


def decode_oauth2_refresh_token(token: str) -> dict[str, Any] | None:
    from ..config import REFRESH_TOKEN_SECRET
    try:
        payload = decode_access_token(token, REFRESH_TOKEN_SECRET, [JWT_ALGORITHM])
        if payload.get("type") != "oauth2_refresh":
            return None
        return payload
    except JWTError:
        return None


def get_jwks() -> list[dict[str, Any]]:
    logger.warning(
        "JWKS endpoint called with symmetric HMAC signing — "
        "no asymmetric public keys are available. "
        "Clients expecting RSA/EC keys will receive an empty set.",
    )
    return []


def build_openid_config() -> dict[str, Any]:
    return {
        "issuer": f"{BASE_URL}/oauth2",
        "authorization_endpoint": f"{BASE_URL}/oauth2/authorize",
        "token_endpoint": f"{BASE_URL}/oauth2/token",
        "introspection_endpoint": f"{BASE_URL}/oauth2/introspect",
        "revocation_endpoint": f"{BASE_URL}/oauth2/revoke",
        "jwks_uri": f"{BASE_URL}/oauth2/jwks.json",
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code", "client_credentials", "refresh_token"],
        "token_endpoint_auth_methods_supported": ["client_secret_basic", "client_secret_post", "none"],
        "subject_types_supported": ["public"],
        "id_token_signing_alg_values_supported": ["HS256"],
        "scopes_supported": ["openid", "profile", "email", "read", "write"],
        "claims_supported": ["sub", "iss", "aud", "exp", "iat"],
        "code_challenge_methods_supported": ["S256"],
    }
