from __future__ import annotations

import logging
import secrets
import time as time_module
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from security.modules.identity.jwt import JWTManager
from security.modules.identity.pkce import PKCEManager

logger = logging.getLogger("gula.security.modules.identity.oidc")

_OIDC_SCOPES = {"openid", "profile", "email", "address", "phone", "offline_access"}
_HEALTHCARE_EXTENSION_CLAIMS = {
    "national_id",
    "practitioner_role",
    "specialty",
    "organization",
    "healthcare_facility",
    "license_number",
    "permissions",
    "purpose_of_use",
}


class OIDCAuthorizationRequest(BaseModel):
    response_type: str = "code"
    client_id: str
    redirect_uri: str
    scope: str = "openid"
    state: str = ""
    nonce: str = ""
    code_challenge: str = ""
    code_challenge_method: str = ""
    response_mode: str = "query"
    prompt: str = ""
    max_age: int = 0
    ui_locales: str = ""
    claims_locales: str = ""
    id_token_hint: str = ""
    login_hint: str = ""
    acr_values: str = ""


class OIDCTokenResponse(BaseModel):
    access_token: str = ""
    token_type: str = "Bearer"
    expires_in: int = 3600
    id_token: str = ""
    refresh_token: str = ""
    scope: str = ""


class OIDCProviderConfig(BaseModel):
    issuer: str = "https://gula-platform.org"
    authorization_endpoint: str = "/oauth2/authorize"
    token_endpoint: str = "/oauth2/token"
    userinfo_endpoint: str = "/oauth2/userinfo"
    jwks_uri: str = "/oauth2/jwks.json"
    registration_endpoint: str = "/oauth2/register"
    scopes_supported: list[str] = Field(default_factory=lambda: list(_OIDC_SCOPES))
    response_types_supported: list[str] = Field(default_factory=lambda: ["code", "id_token", "code id_token", "id_token token"])
    grant_types_supported: list[str] = Field(default_factory=lambda: ["authorization_code", "implicit", "hybrid", "refresh_token"])
    acr_values_supported: list[str] = Field(default_factory=lambda: ["0", "1", "2", "3"])
    subject_types_supported: list[str] = Field(default_factory=lambda: ["public", "pairwise"])
    id_token_signing_alg_values_supported: list[str] = Field(default_factory=lambda: ["RS256", "ES256", "EdDSA", "HS256"])
    token_endpoint_auth_methods_supported: list[str] = Field(default_factory=lambda: [
        "client_secret_basic", "client_secret_post", "client_secret_jwt", "private_key_jwt", "none",
    ])
    claims_supported: list[str] = Field(default_factory=lambda: [
        "sub", "iss", "aud", "exp", "iat", "auth_time", "nonce",
        "name", "preferred_username", "email", "email_verified",
        "national_id", "practitioner_role", "specialty", "organization",
    ])
    code_challenge_methods_supported: list[str] = Field(default_factory=lambda: ["S256", "plain"])


class OIDCProvider:
    def __init__(
        self,
        jwt_manager: JWTManager | None = None,
        pkce_manager: PKCEManager | None = None,
        config: OIDCProviderConfig | None = None,
    ):
        self._jwt = jwt_manager or JWTManager()
        self._pkce = pkce_manager or PKCEManager()
        self._config = config or OIDCProviderConfig()
        self._authorization_codes: dict[str, dict[str, Any]] = {}
        self._clients: dict[str, dict[str, Any]] = {}
        self._sessions: dict[str, dict[str, Any]] = {}

        try:
            from backend.app.security.oauth2_provider import (
                build_openid_config as _backend_config,
            )
            from backend.app.security.oauth2_provider import (
                get_jwks as _backend_jwks,
            )
            self._backend_config_fn = _backend_config
            self._backend_jwks_fn = _backend_jwks
        except ImportError:
            self._backend_config_fn = None
            self._backend_jwks_fn = None

        try:
            from backend.app.security.oauth2_provider import (
                generate_auth_code as _backend_auth_code,
            )
            from backend.app.security.oauth2_provider import (
                generate_client_id as _backend_client_id,
            )
            from backend.app.security.oauth2_provider import (
                generate_client_secret as _backend_client_secret,
            )
            self._backend_auth_code = _backend_auth_code
            self._backend_client_id = _backend_client_id
            self._backend_client_secret = _backend_client_secret
        except ImportError:
            self._backend_auth_code = None
            self._backend_client_id = None
            self._backend_client_secret = None

    def get_discovery_document(self, base_url: str = "") -> dict[str, Any]:
        config = {
            "issuer": self._config.issuer,
            "authorization_endpoint": f"{base_url}{self._config.authorization_endpoint}",
            "token_endpoint": f"{base_url}{self._config.token_endpoint}",
            "userinfo_endpoint": f"{base_url}{self._config.userinfo_endpoint}",
            "jwks_uri": f"{base_url}{self._config.jwks_uri}",
            "registration_endpoint": f"{base_url}{self._config.registration_endpoint}",
            "scopes_supported": self._config.scopes_supported,
            "response_types_supported": self._config.response_types_supported,
            "grant_types_supported": self._config.grant_types_supported,
            "acr_values_supported": self._config.acr_values_supported,
            "subject_types_supported": self._config.subject_types_supported,
            "id_token_signing_alg_values_supported": self._config.id_token_signing_alg_values_supported,
            "token_endpoint_auth_methods_supported": self._config.token_endpoint_auth_methods_supported,
            "claims_supported": self._config.claims_supported,
            "code_challenge_methods_supported": self._config.code_challenge_methods_supported,
            "claims_parameter_supported": True,
            "request_parameter_supported": True,
            "request_uri_parameter_supported": True,
            "require_request_uri_registration": True,
        }

        if self._backend_config_fn is not None:
            try:
                backend = self._backend_config_fn()
                config.update(backend)
            except Exception:
                pass

        return config

    def get_jwks(self) -> list[dict[str, Any]]:
        if self._backend_jwks_fn is not None:
            try:
                backend = self._backend_jwks_fn()
                if backend:
                    return backend
            except Exception:
                pass
        return self._jwt.get_jwks()

    def register_client(
        self,
        client_id: str = "",
        client_name: str = "",
        redirect_uris: list[str] | None = None,
        grant_types: list[str] | None = None,
        response_types: list[str] | None = None,
        token_endpoint_auth_method: str = "client_secret_basic",
        **kwargs: Any,
    ) -> dict[str, Any]:
        client_id = client_id or (self._backend_client_id() if self._backend_client_id else f"gula_{secrets.token_urlsafe(24)}")
        client_secret = self._backend_client_secret() if self._backend_client_secret else secrets.token_urlsafe(48)

        self._clients[client_id] = {
            "client_id": client_id,
            "client_secret": client_secret,
            "client_name": client_name,
            "redirect_uris": redirect_uris or [],
            "grant_types": grant_types or ["authorization_code"],
            "response_types": response_types or ["code"],
            "token_endpoint_auth_method": token_endpoint_auth_method,
            "created_at": datetime.now(UTC).isoformat(),
            "is_active": True,
            **kwargs,
        }

        return {
            "client_id": client_id,
            "client_secret": client_secret,
            "client_id_issued_at": int(time_module.time()),
            "client_secret_expires_at": 0,
            **kwargs,
        }

    def authorize(
        self,
        request: OIDCAuthorizationRequest,
        user_id: str,
        auth_time: int | None = None,
    ) -> dict[str, Any]:
        client = self._clients.get(request.client_id)
        if not client or not client.get("is_active"):
            return {"error": "invalid_client", "error_description": "Client not found or inactive"}

        if request.redirect_uri and request.redirect_uri not in client.get("redirect_uris", []):
            return {"error": "invalid_redirect_uri", "error_description": "Redirect URI not registered"}

        scopes = request.scope.split()
        unsupported = set(scopes) - _OIDC_SCOPES
        if unsupported:
            return {"error": "invalid_scope", "error_description": f"Unsupported scopes: {unsupported}"}

        if request.code_challenge_method and request.code_challenge_method not in {"S256", "plain"}:
            return {"error": "invalid_request", "error_description": "Unsupported code challenge method"}

        response_type = request.response_type
        if response_type not in self._config.response_types_supported:
            return {"error": "unsupported_response_type", "error_description": f"Unsupported response type: {response_type}"}

        code = self._backend_auth_code() if self._backend_auth_code else secrets.token_urlsafe(32)
        now = datetime.now(UTC)
        code_data: dict[str, Any] = {
            "code": code,
            "client_id": request.client_id,
            "redirect_uri": request.redirect_uri,
            "scope": request.scope,
            "user_id": user_id,
            "nonce": request.nonce,
            "code_challenge": request.code_challenge,
            "code_challenge_method": request.code_challenge_method,
            "auth_time": auth_time or int(now.timestamp()),
            "expires_at": now + timedelta(minutes=10),
            "used": False,
        }
        self._authorization_codes[code] = code_data

        result: dict[str, Any] = {"code": code, "state": request.state}

        if "id_token" in response_type:
            id_token = self._jwt.create_id_token(
                subject=user_id,
                audience=request.client_id,
                extra_claims={
                    "nonce": request.nonce,
                    "auth_time": code_data["auth_time"],
                    "acr": "1",
                },
            )
            result["id_token"] = id_token

        return result

    def exchange_code(
        self,
        code: str,
        client_id: str,
        client_secret: str = "",
        redirect_uri: str = "",
        code_verifier: str = "",
    ) -> OIDCTokenResponse:
        code_data = self._authorization_codes.pop(code, None)
        if code_data is None:
            return OIDCTokenResponse(access_token="", expires_in=0)
        if code_data.get("used"):
            return OIDCTokenResponse(access_token="", expires_in=0)
        if code_data["client_id"] != client_id:
            return OIDCTokenResponse(access_token="", expires_in=0)
        if redirect_uri and code_data["redirect_uri"] != redirect_uri:
            return OIDCTokenResponse(access_token="", expires_in=0)
        if datetime.now(UTC) > code_data["expires_at"]:
            return OIDCTokenResponse(access_token="", expires_in=0)

        client = self._clients.get(client_id, {})
        auth_method = client.get("token_endpoint_auth_method", "client_secret_basic")
        if auth_method not in {"none"} and client.get("client_secret", "") != client_secret:
            return OIDCTokenResponse(access_token="", expires_in=0)

        cc = code_data.get("code_challenge", "")
        ccm = code_data.get("code_challenge_method", "")
        if cc and ccm:
            if not code_verifier:
                return OIDCTokenResponse(access_token="", expires_in=0)
            valid = self._pkce.verify_code_challenge(code_verifier, cc, ccm)
            if not valid:
                return OIDCTokenResponse(access_token="", expires_in=0)

        code_data["used"] = True
        user_id = code_data["user_id"]
        scopes = code_data["scope"]

        access_token = self._jwt.create_access_token(
            subject=user_id,
            extra_claims={
                "client_id": client_id,
                "scope": scopes,
                "auth_time": code_data["auth_time"],
            },
        )

        id_token = self._jwt.create_id_token(
            subject=user_id,
            audience=client_id,
            extra_claims={
                "nonce": code_data.get("nonce", ""),
                "auth_time": code_data.get("auth_time", int(time_module.time())),
                "acr": "1",
            },
        )

        refresh_token = ""
        if "offline_access" in scopes:
            refresh_token = self._jwt.create_refresh_token(subject=user_id)

        return OIDCTokenResponse(
            access_token=access_token,
            expires_in=self._jwt._access_token_ttl if hasattr(self._jwt, "_access_token_ttl") else 3600,
            id_token=id_token,
            refresh_token=refresh_token,
            scope=scopes,
        )

    def get_userinfo(self, access_token: str, claims: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = self._jwt.verify_access_token(access_token)
        if payload is None:
            return {"error": "invalid_token", "error_description": "Access token is invalid or expired"}

        sub = payload.get("sub", "")
        userinfo: dict[str, Any] = {
            "sub": sub,
        }

        if claims:
            requested = claims.get("userinfo", {})
            for claim_name, claim_detail in requested.items():
                if isinstance(claim_detail, dict) and "value" in claim_detail:
                    userinfo[claim_name] = claim_detail["value"]

        return userinfo

    def refresh_token_grant(self, refresh_token: str, client_id: str) -> OIDCTokenResponse:
        claims = self._jwt.verify_refresh_token(refresh_token)
        if claims is None:
            return OIDCTokenResponse(access_token="", expires_in=0)
        if claims.get("client_id", "") != client_id:
            return OIDCTokenResponse(access_token="", expires_in=0)

        subject = claims.get("sub", "")
        result = self._jwt.rotate_refresh_token(refresh_token, subject)
        if result is None:
            return OIDCTokenResponse(access_token="", expires_in=0)

        new_access, new_refresh = result
        return OIDCTokenResponse(
            access_token=new_access,
            expires_in=self._jwt._access_token_ttl if hasattr(self._jwt, "_access_token_ttl") else 3600,
            refresh_token=new_refresh,
        )

    def create_session(self, user_id: str, client_id: str, scopes: str = "openid") -> str:
        session_id = str(uuid4())
        self._sessions[session_id] = {
            "user_id": user_id,
            "client_id": client_id,
            "scopes": scopes,
            "created_at": datetime.now(UTC).isoformat(),
            "is_active": True,
        }
        return session_id

    def end_session(self, session_id: str) -> bool:
        session = self._sessions.get(session_id)
        if session is None:
            return False
        session["is_active"] = False
        return True

    def rp_initiated_logout(
        self,
        id_token_hint: str,
        post_logout_redirect_uri: str = "",
        state: str = "",
    ) -> dict[str, Any]:
        payload = self._jwt.verify_token(id_token_hint, expected_type="id_token")
        if payload is None:
            return {"error": "invalid_id_token"}

        result: dict[str, Any] = {"logout_successful": True}
        for session_id, session in list(self._sessions.items()):
            if session.get("user_id") == payload.get("sub"):
                session["is_active"] = False

        if post_logout_redirect_uri:
            result["post_logout_redirect_uri"] = post_logout_redirect_uri
            result["state"] = state

        return result

    def get_authorization_code_data(self, code: str) -> dict[str, Any] | None:
        return self._authorization_codes.get(code)

    def get_client(self, client_id: str) -> dict[str, Any] | None:
        return self._clients.get(client_id)
