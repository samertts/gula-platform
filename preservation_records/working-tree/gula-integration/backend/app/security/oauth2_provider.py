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
from .auth import ACCOUNT_KIND_LAB, ACCOUNT_KIND_USER

logger = logging.getLogger("gula.oauth2")


def _has_resolvable_account_domain(payload: dict[str, Any]) -> bool:
    """Whether a token can resolve its account family without guessing.

    AUD-SEC-002 / AUD-API-002: ``resolve_token_account_kind()`` derives the
    family from a signed ``account_kind`` or a signed ``lab_id``, but defaults
    to ``user`` when BOTH are absent. Emitting a ``user_id`` in that state would
    let a legacy LabUser subject bind to a colliding User account — the exact
    cross-family collision this remediation exists to prevent. Such a token is
    therefore minted *without* a subject so the canonical chain rejects it.
    """
    return (
        payload.get("account_kind") in (ACCOUNT_KIND_LAB, ACCOUNT_KIND_USER)
        or payload.get("lab_id") is not None
    )


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
    *,
    claims: dict[str, Any] | None = None,
) -> tuple[str, int]:
    """Mint an OAuth2 access token that the canonical API chain accepts.

    AUD-API-002: the old ``type="oauth2_access"`` payload could only be decoded
    by an orphaned decoder with zero call sites, so every OAuth2 token was
    rejected by ``get_current_user()``. Access tokens now use the canonical
    ``type="access"`` and carry the same identity claims (``user_id``,
    ``account_kind``, ``lab_id``, ``role``, ``perm_ver``) as a normal login
    token, supplied through ``claims`` from :func:`build_token_payload`.

    Machine tokens (client_credentials, no subject) still get ``type="access"``
    but carry no ``user_id``; ``get_current_user()`` correctly rejects them
    because they have no end-user identity.
    """
    expire_minutes = expires_in // 60 if expires_in else JWT_EXPIRE_MINUTES
    payload: dict[str, Any] = {
        "jti": generate_token_id(),
        "client_id": client_id,
        "type": "access",
    }
    if claims:
        payload.update(claims)
    # A bare user_id with no signed domain resolves by *guess* (USER) in
    # get_current_user(), reintroducing the LabUser/User collision. Only embed
    # a subject when the token carries a resolvable domain (AUD-SEC-002).
    if user_id is not None and _has_resolvable_account_domain(payload):
        payload["user_id"] = user_id
    if scope:
        payload["scope"] = scope
    token = create_access_token(payload, secret_key=SECRET_KEY, algorithm=JWT_ALGORITHM, expire_minutes=expire_minutes)
    return token, expire_minutes * 60


def create_refresh_token_oauth2(
    client_id: str,
    user_id: int | None = None,
    scope: str | None = None,
    *,
    account_kind: str | None = None,
) -> str:
    payload = {
        "jti": generate_token_id(),
        "client_id": client_id,
        "type": "oauth2_refresh",
    }
    if account_kind is not None:
        # Carried across the refresh rotation so the new access token can be
        # resolved to the correct account family (AUD-SEC-002).
        payload["account_kind"] = account_kind
    # Same invariant as access tokens: never carry a subject whose family
    # cannot be resolved from signed claims (AUD-SEC-002 / AUD-API-002).
    if user_id is not None and _has_resolvable_account_domain(payload):
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
    """Decode an OAuth2-issued token.

    AUD-API-002: canonical OAuth2 access tokens now use ``type="access"`` and
    are decoded by the shared chain. ``oauth2_access`` is accepted only for
    legacy tokens minted before the fix. A token is considered OAuth2-issued
    only when it carries a ``client_id`` claim, so ordinary user login tokens
    are not misclassified here.
    """
    try:
        payload = decode_access_token(token, SECRET_KEY, [JWT_ALGORITHM])
        if payload.get("type") not in ("access", "oauth2_access"):
            return None
        if not payload.get("client_id"):
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
    """Return published asymmetric public keys (currently none).

    This deployment signs tokens with symmetric HS256. There are no RSA/EC
    public keys to publish, so the JWKS is empty by design. Callers must use
    :func:`jwks_available` and fail closed rather than treating an empty set
    as a usable OIDC discovery document.
    """
    return []


def jwks_available() -> bool:
    """Whether a conforming RP can validate ID tokens via published JWKS keys.

    P0-B: OIDC/JWKS readiness requires an approved asymmetric key-management
    design (key generation, rotation, distribution). Until then this returns
    ``False`` and the JWKS endpoint fails closed — no keys are generated here.
    """
    return bool(get_jwks())


JWKS_UNAVAILABLE_DETAIL = (
    "OIDC JWKS is not available in this deployment: tokens are signed with "
    "symmetric keys and no public verification keys are published. Asymmetric "
    "key management must be approved before OIDC reliance."
)


def build_openid_config() -> dict[str, Any]:
    # ``jwks_uri`` is published for OIDC discovery spec compliance. The endpoint
    # itself fails closed (503) until asymmetric key management is approved;
    # tokens are currently HS256 (shared secret), never validated via JWKS.
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
