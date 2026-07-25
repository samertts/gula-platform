from __future__ import annotations

import hashlib
import hmac
import logging
import secrets
from base64 import urlsafe_b64encode, urlsafe_b64decode
from typing import Any

logger = logging.getLogger("gula.security.modules.identity.pkce")


class PKCEManager:
    def __init__(self) -> None:
        self._stored_states: dict[str, dict[str, Any]] = {}
        self._stored_nonces: dict[str, dict[str, Any]] = {}

    def generate_code_verifier(self, length: int = 64) -> str:
        if length < 43 or length > 128:
            raise ValueError("Code verifier length must be between 43 and 128 characters")
        return urlsafe_b64encode(secrets.token_bytes(length)).rstrip(b"=").decode()[:length]

    def derive_code_challenge(self, code_verifier: str, method: str = "S256") -> str:
        if method == "S256":
            digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
            return urlsafe_b64encode(digest).rstrip(b"=").decode()
        if method == "plain":
            return code_verifier
        raise ValueError(f"Unsupported code challenge method: {method}")

    def verify_code_challenge(self, code_verifier: str, code_challenge: str, method: str) -> bool:
        computed = self.derive_code_challenge(code_verifier, method)
        if len(computed) != len(code_challenge):
            return False
        return hmac.compare_digest(computed, code_challenge)

    def generate_state(self, length: int = 32) -> str:
        return urlsafe_b64encode(secrets.token_bytes(length)).rstrip(b"=").decode()[:length]

    def store_state(self, state: str, data: dict[str, Any], ttl_seconds: int = 600) -> None:
        import time
        self._stored_states[state] = {"data": data, "expires_at": time.monotonic() + ttl_seconds}

    def validate_state(self, state: str, expected_data: dict[str, Any] | None = None) -> bool:
        import time
        stored = self._stored_states.pop(state, None)
        if stored is None:
            return False
        if time.monotonic() > stored["expires_at"]:
            return False
        if expected_data is not None:
            for key, value in expected_data.items():
                if stored["data"].get(key) != value:
                    return False
        return True

    def generate_nonce(self, length: int = 16) -> str:
        return secrets.token_hex(length)

    def store_nonce(self, nonce: str, data: dict[str, Any] | None = None, ttl_seconds: int = 600) -> None:
        import time
        self._stored_nonces[nonce] = {"data": data or {}, "expires_at": time.monotonic() + ttl_seconds}

    def validate_nonce(self, nonce: str) -> bool:
        import time
        stored = self._stored_nonces.pop(nonce, None)
        if stored is None:
            return False
        if time.monotonic() > stored["expires_at"]:
            return False
        return True

    def verify_pkce_pair(self, code_verifier: str, code_challenge: str, method: str) -> bool:
        return self.verify_code_challenge(code_verifier, code_challenge, method)

    def cleanup_expired(self) -> int:
        import time
        now = time.monotonic()
        count = 0
        expired_states = [s for s, v in self._stored_states.items() if now > v["expires_at"]]
        for s in expired_states:
            self._stored_states.pop(s, None)
            count += 1
        expired_nonces = [n for n, v in self._stored_nonces.items() if now > v["expires_at"]]
        for n in expired_nonces:
            self._stored_nonces.pop(n, None)
            count += 1
        return count
