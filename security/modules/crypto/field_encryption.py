from __future__ import annotations

import hashlib
import hmac as _hmac_module
import json
import logging
import os
import time
from typing import Any

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from security.modules.crypto.models import EncryptionAlgorithm, EncryptionConfig, KeyPurpose

logger = logging.getLogger("gula.security.modules.crypto.field_encryption")


class FieldEncryptor:
    def __init__(
        self,
        master_key: bytes | None = None,
        config: EncryptionConfig | None = None,
    ) -> None:
        if master_key is not None and len(master_key) != 32:
            raise ValueError("Master key must be 32 bytes")
        self._master_key = master_key or AESGCM.generate_key(bit_length=256)
        self._config = config or EncryptionConfig()
        self._field_keys: dict[str, bytes] = {}

    def encrypt_field(
        self, value: str, field_name: str, table_name: str = "",
        deterministic: bool = False,
    ) -> str:
        if not value:
            return value

        field_key = self._derive_field_key(field_name, table_name)

        if deterministic:
            return self._encrypt_deterministic(value, field_key)
        return self._encrypt_probabilistic(value, field_key)

    def decrypt_field(
        self, encrypted_value: str, field_name: str, table_name: str = "",
    ) -> str:
        if not encrypted_value:
            return encrypted_value

        field_key = self._derive_field_key(field_name, table_name)

        try:
            data = self._decode_field_value(encrypted_value)
            if data["type"] == "deterministic":
                return self._decrypt_deterministic(encrypted_value, field_key)
            return self._decrypt_probabilistic(encrypted_value, field_key)
        except Exception as exc:
            logger.error("Field decryption failed for %s.%s: %s", table_name, field_name, exc)
            raise

    def encrypt_int(self, value: int, field_name: str, table_name: str = "") -> str:
        return self.encrypt_field(str(value), field_name, table_name, deterministic=True)

    def decrypt_int(self, encrypted_value: str, field_name: str, table_name: str = "") -> int:
        result = self.decrypt_field(encrypted_value, field_name, table_name)
        return int(result)

    def encrypt_float(self, value: float, field_name: str, table_name: str = "") -> str:
        return self.encrypt_field(str(value), field_name, table_name, deterministic=True)

    def decrypt_float(self, encrypted_value: str, field_name: str, table_name: str = "") -> float:
        result = self.decrypt_field(encrypted_value, field_name, table_name)
        return float(result)

    def encrypt_bool(self, value: bool, field_name: str, table_name: str = "") -> str:
        return self.encrypt_field(str(value), field_name, table_name, deterministic=True)

    def decrypt_bool(self, encrypted_value: str, field_name: str, table_name: str = "") -> bool:
        result = self.decrypt_field(encrypted_value, field_name, table_name)
        return result.lower() == "true"

    def encrypt_json(self, value: Any, field_name: str, table_name: str = "") -> str:
        serialized = json.dumps(value, separators=(",", ":"))
        return self.encrypt_field(serialized, field_name, table_name, deterministic=False)

    def decrypt_json(self, encrypted_value: str, field_name: str, table_name: str = "") -> Any:
        result = self.decrypt_field(encrypted_value, field_name, table_name)
        return json.loads(result)

    def generate_blind_index(self, value: str, field_name: str, table_name: str = "") -> str:
        index_key = self._derive_index_key(field_name, table_name)
        h = _hmac_module.new(index_key, value.encode(), hashlib.sha256).hexdigest()
        return h[:32]

    def create_encrypted_with_index(
        self, value: str, field_name: str, table_name: str = "",
    ) -> tuple[str, str]:
        encrypted = self.encrypt_field(value, field_name, table_name, deterministic=False)
        blind_index = self.generate_blind_index(value, field_name, table_name)
        return encrypted, blind_index

    def _derive_field_key(self, field_name: str, table_name: str) -> bytes:
        cache_key = f"{table_name}.{field_name}"
        if cache_key in self._field_keys:
            return self._field_keys[cache_key]

        info = f"{table_name}:{field_name}:field_key".encode()
        derived = self._hkdf(self._master_key, 32, info)
        self._field_keys[cache_key] = derived
        return derived

    def _derive_index_key(self, field_name: str, table_name: str) -> bytes:
        info = f"{table_name}:{field_name}:index_key".encode()
        return self._hkdf(self._master_key, 32, info)

    def _encrypt_probabilistic(self, value: str, key: bytes) -> str:
        aesgcm = AESGCM(key)
        iv = os.urandom(12)
        ciphertext = aesgcm.encrypt(iv, value.encode(), b"")
        import base64
        payload = {
            "type": "probabilistic",
            "iv": base64.b64encode(iv).decode(),
            "data": base64.b64encode(ciphertext).decode(),
        }
        return f"enc:{json.dumps(payload, separators=(',', ':'))}"

    def _decrypt_probabilistic(self, encrypted: str, key: bytes) -> str:
        data = self._decode_field_value(encrypted)
        import base64
        iv = base64.b64decode(data["iv"])
        ciphertext = base64.b64decode(data["data"])
        aesgcm = AESGCM(key)
        return aesgcm.decrypt(iv, ciphertext, b"").decode()

    def _encrypt_deterministic(self, value: str, key: bytes) -> str:
        import base64
        iv = _hmac_module.new(key, value.encode(), hashlib.sha256).digest()[:12]
        aesgcm = AESGCM(key)
        ciphertext = aesgcm.encrypt(iv, value.encode(), b"")
        payload = {
            "type": "deterministic",
            "iv": base64.b64encode(iv).decode(),
            "data": base64.b64encode(ciphertext).decode(),
        }
        return f"enc:{json.dumps(payload, separators=(',', ':'))}"

    def _decrypt_deterministic(self, encrypted: str, key: bytes) -> str:
        return self._decrypt_probabilistic(encrypted, key)

    def _decode_field_value(self, encrypted: str) -> dict[str, Any]:
        if not encrypted.startswith("enc:"):
            raise ValueError("Invalid encrypted field format")
        return json.loads(encrypted[4:])

    def _hkdf(self, ikm: bytes, length: int, info: bytes) -> bytes:
        salt = b"gula-field-encryption-v1"
        prk = _hmac_module.new(salt, ikm, hashlib.sha256).digest()
        n = (length + 32 - 1) // 32
        if n > 255:
            raise ValueError("Length too large")
        okm = b""
        t = b""
        for i in range(1, n + 1):
            t = _hmac_module.new(prk, t + info + bytes([i]), hashlib.sha256).digest()
            okm += t
        return okm[:length]

    def rotate_key(self, new_master_key: bytes) -> None:
        if len(new_master_key) != 32:
            raise ValueError("New master key must be 32 bytes")
        self._master_key = new_master_key
        self._field_keys.clear()
        logger.info("Field encryption master key rotated")
