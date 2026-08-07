from __future__ import annotations

import hashlib
import hmac
import logging
import time
from dataclasses import dataclass, field

logger = logging.getLogger("gula.integration.api_management.auth")


@dataclass
class APIKey:
    key: str = ""
    secret: str = ""
    app_id: str = ""
    permissions: list[str] = field(default_factory=list)
    rate_limit: int = 1000
    expires_at: float = 0.0
    active: bool = True


class APIAuth:
    def __init__(self):
        self._api_keys: dict[str, APIKey] = {}
        self._hmac_keys: dict[str, str] = {}

    def register_key(self, api_key: APIKey) -> None:
        self._api_keys[api_key.key] = api_key
        logger.info("API key registered for app: %s", api_key.app_id)

    def revoke_key(self, key: str) -> bool:
        api_key = self._api_keys.get(key)
        if api_key:
            api_key.active = False
            logger.info("API key revoked: %s", key)
            return True
        return False

    def validate_token(self, token: str) -> bool:
        if not token:
            return False
        token = token.removeprefix("Bearer ")
        api_key = self._api_keys.get(token)
        if not api_key:
            return False
        if not api_key.active:
            return False
        return not (api_key.expires_at and time.time() > api_key.expires_at)

    def validate_hmac(self, key_id: str, signature: str, message: str) -> bool:
        secret = self._hmac_keys.get(key_id)
        if not secret:
            return False
        expected = hmac.new(secret.encode(), message.encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature)

    def register_hmac_key(self, key_id: str, secret: str) -> None:
        self._hmac_keys[key_id] = secret
        logger.info("HMAC key registered: %s", key_id)

    def revoke_hmac_key(self, key_id: str) -> bool:
        if key_id in self._hmac_keys:
            del self._hmac_keys[key_id]
            logger.info("HMAC key revoked: %s", key_id)
            return True
        return False

    def check_permission(self, key: str, permission: str) -> bool:
        api_key = self._api_keys.get(key)
        if not api_key or not api_key.active:
            return False
        return "*" in api_key.permissions or permission in api_key.permissions

    def list_keys(self) -> list[APIKey]:
        return list(self._api_keys.values())
