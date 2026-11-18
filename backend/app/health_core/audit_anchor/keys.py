"""Synthetic HMAC key management with rotation for the audit anchor.

Keys here are derived deterministically from a synthetic seed string. They are
test/demo material, never real credentials. Old key ids stay in the registry for
verification only; signing always uses the current key id.
"""

from __future__ import annotations

import hashlib
import hmac
from typing import Protocol


class KeyProvider(Protocol):
    """Minimal key contract required by the audit-anchor chain."""

    def current_key_id(self) -> str:
        """Return the key id used for newly created signatures."""

    def sign(self, data: bytes) -> str:
        """Return a hexadecimal signature over ``data`` with the current key."""

    def verify(self, key_id: str, data: bytes, signature: str) -> bool:
        """Return True only if ``signature`` matches ``data`` under ``key_id``."""

    def has_key(self, key_id: str) -> bool:
        """Return True when ``key_id`` is known (needed to report unknown ids)."""


class RotatingKeyProvider:
    """In-memory registry of synthetic HMAC-SHA256 keys with rotation support."""

    def __init__(
        self,
        *,
        seed: str = "SYNTHETIC-AUDIT-ANCHOR-SEED",
        key_id_prefix: str = "synthetic-key",
    ) -> None:
        if not seed:
            raise ValueError("synthetic seed must not be empty")
        if not key_id_prefix:
            raise ValueError("key id prefix must not be empty")
        self._seed = seed
        self._prefix = key_id_prefix
        self._keys: dict[str, bytes] = {}
        self._current = ""
        self._counter = 0
        self._install_key()

    def _install_key(self) -> str:
        self._counter += 1
        key_id = f"{self._prefix}-{self._counter}"
        material = f"{self._seed}:{key_id}:v1".encode()
        self._keys[key_id] = hashlib.sha256(material).digest()
        self._current = key_id
        return key_id

    def rotate(self) -> str:
        """Install a new synthetic key; older keys remain verifiable."""
        return self._install_key()

    def current_key_id(self) -> str:
        return self._current

    def has_key(self, key_id: str) -> bool:
        return key_id in self._keys

    def key_ids(self) -> tuple[str, ...]:
        """Return installed key ids (identifiers only, never key material)."""
        return tuple(self._keys)

    def sign(self, data: bytes) -> str:
        return hmac.new(self._keys[self._current], data, hashlib.sha256).hexdigest()

    def verify(self, key_id: str, data: bytes, signature: str) -> bool:
        key = self._keys.get(key_id)
        if key is None:
            return False
        expected = hmac.new(key, data, hashlib.sha256).hexdigest()
        try:
            return hmac.compare_digest(expected, signature)
        except TypeError:
            # Non-ASCII signatures are invalid input, never a crash or a log event.
            return False

    def __repr__(self) -> str:
        # Never expose derived key bytes in logs or reports.
        return (
            f"RotatingKeyProvider(current_key_id={self._current!r}, "
            f"key_ids={self.key_ids()!r})"
        )


__all__ = ["KeyProvider", "RotatingKeyProvider"]
