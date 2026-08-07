"""Archived Shared Core `encryption` reimplementation (ADR-028).

Commit 1.6 (PROGRAM-01, Wave 1 order 3): `EncryptedSyncStore` was dead code
(zero production importers; sole consumer was `backend/tests/test_offline_sync.py`)
and a reimplementation of the canonical `shared/security/encryption.py` Fernet
provider. Preserved byte-for-byte (with the imports required for standalone
execution) so the migration is independently reversible.

Class preserved from `backend/app/services/offline_sync_service.py` (lines
272-326 at time of archive). Canonical provider: `shared/security/encryption.py`
(`encrypt_value` / `decrypt_value`).
"""

from __future__ import annotations

import hashlib
import json
import logging
import zlib
from typing import Any

logger = logging.getLogger("gula.offline.sync")


class EncryptedSyncStore:
    def __init__(self, encryption_key: str = ""):
        self._key = encryption_key
        self._store: dict[str, bytes] = {}

    def put(self, key: str, value: dict[str, Any]) -> None:
        raw = json.dumps(value).encode()
        compressed = zlib.compress(raw)
        encrypted = self._encrypt(compressed)
        self._store[key] = encrypted

    def get(self, key: str) -> dict[str, Any] | None:
        encrypted = self._store.get(key)
        if not encrypted:
            return None
        try:
            decrypted = self._decrypt(encrypted)
            decompressed = zlib.decompress(decrypted)
            return json.loads(decompressed)
        except Exception as exc:
            logger.error("Failed to decrypt/deserialize key %s: %s", key, exc)
            return None

    def delete(self, key: str) -> bool:
        return self._store.pop(key, None) is not None

    def list_keys(self) -> list[str]:
        return list(self._store.keys())

    def clear(self) -> None:
        self._store.clear()

    def _encrypt(self, data: bytes) -> bytes:
        if not self._key:
            return data
        from cryptography.fernet import Fernet

        key = self._derive_key()
        f = Fernet(key)
        return f.encrypt(data)

    def _decrypt(self, data: bytes) -> bytes:
        if not self._key:
            return data
        from cryptography.fernet import Fernet

        key = self._derive_key()
        f = Fernet(key)
        return f.decrypt(data)

    def _derive_key(self) -> bytes:
        raw = hashlib.sha256(self._key.encode()).digest()
        import base64

        return base64.urlsafe_b64encode(raw)
