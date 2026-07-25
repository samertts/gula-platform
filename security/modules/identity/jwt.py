from __future__ import annotations

import logging
import secrets
import threading
import time
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from joserfc import jwk, jwt as jose_jwt
from joserfc.errors import JoseError

from security.modules.identity.models import TokenClaims

logger = logging.getLogger("gula.security.modules.identity.jwt")

_SUPPORTED_ALGORITHMS = {"RS256", "RS384", "RS512", "ES256", "ES384", "ES512", "EdDSA", "HS256", "HS384", "HS512"}


class JWTManager:
    def __init__(
        self,
        issuer: str = "gula-platform",
        access_token_ttl: int = 1800,
        refresh_token_ttl: int = 2592000,
        key_rotation_interval: int = 86400,
        redis_client: Any = None,
    ):
        self._issuer = issuer
        self._access_token_ttl = access_token_ttl
        self._refresh_token_ttl = refresh_token_ttl
        self._key_rotation_interval = key_rotation_interval
        self._redis = redis_client
        self._lock = threading.Lock()
        self._keys: dict[str, tuple[jwk.Key, float]] = {}
        self._active_kid: str = ""
        self._blacklist: dict[str, float] = {}
        self._last_rotation: float = 0.0

        self._setup_initial_keys()

        try:
            from backend.app.security.auth import blacklist_token as _backend_blacklist
            self._backend_blacklist = _backend_blacklist
        except ImportError:
            self._backend_blacklist = None

        try:
            from backend.app.config import SECRET_KEY, REFRESH_TOKEN_SECRET, JWT_ALGORITHM
            self._backend_secret = SECRET_KEY
            self._backend_refresh_secret = REFRESH_TOKEN_SECRET
            self._backend_algorithm = JWT_ALGORITHM
        except ImportError:
            self._backend_secret = None
            self._backend_refresh_secret = None
            self._backend_algorithm = "HS256"

    def _setup_initial_keys(self) -> None:
        for alg in ["RS256", "ES256", "EdDSA"]:
            try:
                if alg == "RS256":
                    key = jwk.RSAKey.generate_key(2048)
                elif alg == "ES256":
                    key = jwk.ECKey.generate_key("P-256")
                elif alg == "EdDSA":
                    key = jwk.OKPKey.generate_key("Ed25519")
                else:
                    continue
                kid = f"{alg.lower()}-{secrets.token_hex(8)}"
                self._keys[kid] = (key, time.monotonic())
                if not self._active_kid:
                    self._active_kid = kid
            except Exception as exc:
                logger.warning("Failed to generate %s key: %s", alg, exc)

        if not self._keys:
            secret = secrets.token_bytes(32)
            key = jwk.OctKey.import_key(secret)
            kid = f"hs-{secrets.token_hex(8)}"
            self._keys[kid] = (key, time.monotonic())
            self._active_kid = kid

    def _rotate_keys_if_needed(self) -> None:
        now = time.monotonic()
        if now - self._last_rotation < self._key_rotation_interval:
            return
        with self._lock:
            if now - self._last_rotation < self._key_rotation_interval:
                return
            self._last_rotation = now
            old_keys = dict(self._keys)
            for kid, (key, created) in old_keys.items():
                if now - created > self._key_rotation_interval * 3:
                    self._keys.pop(kid, None)
            for alg in ["RS256", "ES256", "EdDSA"]:
                try:
                    if alg == "RS256":
                        new_key = jwk.RSAKey.generate_key(2048)
                    elif alg == "ES256":
                        new_key = jwk.ECKey.generate_key("P-256")
                    elif alg == "EdDSA":
                        new_key = jwk.OKPKey.generate_key("Ed25519")
                    else:
                        continue
                    kid = f"{alg.lower()}-{secrets.token_hex(8)}"
                    self._keys[kid] = (new_key, now)
                    self._active_kid = kid
                except Exception:
                    pass
            logger.info("JWT keys rotated: %d active keys", len(self._keys))

    def _get_key(self, kid: str | None = None) -> tuple[jwk.Key, str]:
        self._rotate_keys_if_needed()
        if kid and kid in self._keys:
            return self._keys[kid][0], kid
        kid = self._active_kid
        return self._keys[kid][0], kid

    def _get_key_for_algorithm(self, algorithm: str) -> tuple[jwk.Key, str]:
        self._rotate_keys_if_needed()
        for kid, (key, _) in self._keys.items():
            if kid.startswith(algorithm.lower()[:2]):
                return key, kid
        secret = secrets.token_bytes(32)
        return jwk.OctKey.import_key(secret), f"hs-{secrets.token_hex(8)}"

    def create_access_token(
        self,
        subject: str,
        extra_claims: dict[str, Any] | None = None,
        algorithm: str = "RS256",
    ) -> str:
        now = datetime.now(timezone.utc)
        payload: dict[str, Any] = {
            "sub": subject,
            "iss": self._issuer,
            "aud": self._issuer,
            "exp": int((now + timedelta(seconds=self._access_token_ttl)).timestamp()),
            "nbf": int(now.timestamp()),
            "iat": int(now.timestamp()),
            "jti": str(uuid4()),
            "type": "access",
        }
        if extra_claims:
            payload.update(extra_claims)

        key, kid = self._get_key_for_algorithm(algorithm)
        header = {"alg": algorithm, "kid": kid, "typ": "JWT"}
        return jose_jwt.encode(header, payload, key)

    def create_refresh_token(
        self,
        subject: str,
        extra_claims: dict[str, Any] | None = None,
    ) -> str:
        now = datetime.now(timezone.utc)
        payload: dict[str, Any] = {
            "sub": subject,
            "iss": self._issuer,
            "exp": int((now + timedelta(seconds=self._refresh_token_ttl)).timestamp()),
            "iat": int(now.timestamp()),
            "jti": str(uuid4()),
            "type": "refresh",
        }
        if extra_claims:
            payload.update(extra_claims)

        key, kid = self._get_key_for_algorithm("HS256")
        header = {"alg": "HS256", "kid": kid, "typ": "JWT"}
        return jose_jwt.encode(header, payload, key)

    def create_id_token(
        self,
        subject: str,
        audience: str,
        extra_claims: dict[str, Any] | None = None,
        algorithm: str = "RS256",
    ) -> str:
        now = datetime.now(timezone.utc)
        payload: dict[str, Any] = {
            "sub": subject,
            "iss": self._issuer,
            "aud": audience,
            "exp": int((now + timedelta(hours=1)).timestamp()),
            "iat": int(now.timestamp()),
            "auth_time": int(now.timestamp()),
            "jti": str(uuid4()),
            "type": "id_token",
        }
        if extra_claims:
            payload.update(extra_claims)

        key, kid = self._get_key_for_algorithm(algorithm)
        header = {"alg": algorithm, "kid": kid, "typ": "JWT"}
        return jose_jwt.encode(header, payload, key)

    def verify_token(self, token: str, expected_type: str | None = None) -> dict[str, Any] | None:
        try:
            header = jose_jwt.decode_header(token)
            kid = header.get("kid", "")
            key, _ = self._get_key(kid)
            payload = jose_jwt.decode(token, key)
            claims = dict(payload.claims)

            if expected_type and claims.get("type") != expected_type:
                logger.warning("Token type mismatch: expected=%s got=%s", expected_type, claims.get("type"))
                return None

            jti = claims.get("jti", "")
            if jti and self._is_revoked(jti):
                logger.warning("Token revoked: jti=%s", jti)
                return None

            return claims
        except JoseError as exc:
            logger.debug("Token verification failed: %s", exc)
            return None
        except Exception as exc:
            logger.error("Unexpected token verification error: %s", exc)
            return None

    def verify_access_token(self, token: str) -> dict[str, Any] | None:
        return self.verify_token(token, expected_type="access")

    def verify_refresh_token(self, token: str) -> dict[str, Any] | None:
        return self.verify_token(token, expected_type="refresh")

    def revoke_token(self, jti: str, ttl_seconds: int | None = None) -> None:
        ttl = ttl_seconds or max(self._access_token_ttl, self._refresh_token_ttl)
        expiry = time.monotonic() + ttl
        with self._lock:
            self._blacklist[jti] = expiry

        if self._redis is not None:
            try:
                self._redis.set(f"blacklist:jti:{jti}", "1", ex=ttl)
            except Exception as exc:
                logger.warning("Redis blacklist set failed: %s", exc)

        if self._backend_blacklist is not None:
            try:
                self._backend_blacklist(jti, ttl)
            except Exception:
                pass

    def _is_revoked(self, jti: str) -> bool:
        with self._lock:
            expiry = self._blacklist.get(jti)
            if expiry is not None:
                if time.monotonic() < expiry:
                    return True
                self._blacklist.pop(jti, None)

        if self._redis is not None:
            try:
                if self._redis.get(f"blacklist:jti:{jti}") is not None:
                    return True
            except Exception:
                pass

        try:
            from backend.app.security.auth import is_token_blacklisted
            if is_token_blacklisted(jti):
                return True
        except ImportError:
            pass

        return False

    def rotate_refresh_token(self, old_token: str, subject: str) -> tuple[str, str] | None:
        claims = self.verify_refresh_token(old_token)
        if claims is None:
            return None

        jti = claims.get("jti", "")
        self.revoke_token(jti, self._refresh_token_ttl)

        new_access = self.create_access_token(subject)
        new_refresh = self.create_refresh_token(subject)
        return new_access, new_refresh

    def get_jwks(self) -> list[dict[str, Any]]:
        jwks: list[dict[str, Any]] = []
        for kid, (key, _) in self._keys.items():
            try:
                public_key = key.as_dict(private=False)
                public_key["kid"] = kid
                public_key["alg"] = kid.split("-")[0].upper() if "-" in kid else "RS256"
                jwks.append(public_key)
            except Exception as exc:
                logger.debug("Could not export public key %s: %s", kid, exc)
        return jwks

    def introspect_token(self, token: str) -> dict[str, Any]:
        claims = self.verify_token(token)
        if claims is None:
            return {"active": False}
        now = int(time.time())
        return {
            "active": True,
            "sub": claims.get("sub", ""),
            "iss": claims.get("iss", ""),
            "aud": claims.get("aud", ""),
            "exp": claims.get("exp", 0),
            "nbf": claims.get("nbf", 0),
            "iat": claims.get("iat", 0),
            "jti": claims.get("jti", ""),
            "token_type": claims.get("type", ""),
            "client_id": claims.get("client_id", ""),
            "scope": claims.get("scope", ""),
            "active_at": now,
        }

    def validate_claims(self, token: str, expected_iss: str | None = None, expected_aud: str | None = None) -> bool:
        claims = self.verify_token(token)
        if claims is None:
            return False

        now = int(time.time())
        exp = claims.get("exp", 0)
        nbf = claims.get("nbf", 0)
        if exp and now > exp:
            logger.debug("Token expired")
            return False
        if nbf and now < nbf:
            logger.debug("Token not yet valid (nbf)")
            return False
        if expected_iss and claims.get("iss") != expected_iss:
            logger.debug("Issuer mismatch: expected=%s got=%s", expected_iss, claims.get("iss"))
            return False
        if expected_aud:
            aud = claims.get("aud", "")
            if isinstance(aud, list) and expected_aud not in aud:
                return False
            if isinstance(aud, str) and aud != expected_aud:
                return False

        return True

    def parse_claims(self, token: str) -> TokenClaims | None:
        claims = self.verify_token(token)
        if claims is None:
            return None
        return TokenClaims(
            sub=claims.get("sub", ""),
            iss=claims.get("iss", ""),
            aud=claims.get("aud", ""),
            exp=claims.get("exp", 0),
            nbf=claims.get("nbf", 0),
            iat=claims.get("iat", 0),
            jti=claims.get("jti", ""),
            auth_time=claims.get("auth_time", 0),
            acr=claims.get("acr", ""),
            amr=claims.get("amr", []),
            roles=claims.get("roles", []),
            permissions=claims.get("permissions", []),
        )

    def get_key_id(self, token: str) -> str | None:
        try:
            header = jose_jwt.decode_header(token)
            return header.get("kid")
        except JoseError:
            return None

    def set_access_token_ttl(self, ttl: int) -> None:
        self._access_token_ttl = ttl

    def set_refresh_token_ttl(self, ttl: int) -> None:
        self._refresh_token_ttl = ttl
