from __future__ import annotations

import hashlib
import hmac as _hmac_module
import json
import logging
import os
import time
from datetime import datetime, timezone
from typing import Any

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from security.modules.crypto.models import EncryptionAlgorithm, KeyPurpose

logger = logging.getLogger("gula.security.modules.crypto.phi_encryption")


class PHIEncryptor:
    def __init__(self, master_key: bytes | None = None) -> None:
        if master_key is not None and len(master_key) != 32:
            raise ValueError("Master key must be 32 bytes")
        self._master_key = master_key or AESGCM.generate_key(bit_length=256)
        self._table_keys: dict[str, bytes] = {}
        self._column_keys: dict[str, bytes] = {}
        self._audit_log: list[dict[str, Any]] = []
        self._break_glass_enabled: bool = False
        self._break_glass_keys: dict[str, bytes] = {}

    def encrypt_phi_field(
        self, value: str, patient_id: str, table_name: str,
        column_name: str, consent_token: str | None = None,
    ) -> str:
        if not value:
            return value

        if consent_token is not None and not self._verify_consent(patient_id, consent_token):
            raise PermissionError(f"No consent for PHI encryption on patient {patient_id}")

        column_key = self._derive_column_key(table_name, column_name, patient_id)
        aesgcm = AESGCM(column_key)
        iv = os.urandom(12)
        aad = f"{table_name}:{column_name}:{patient_id}".encode()
        ciphertext = aesgcm.encrypt(iv, value.encode(), aad)

        import base64
        payload = {
            "version": 1,
            "patient_id": self._hash_patient_id(patient_id),
            "iv": base64.b64encode(iv).decode(),
            "data": base64.b64encode(ciphertext).decode(),
        }
        result = f"phi:{json.dumps(payload, separators=(',', ':'))}"

        self._audit("encrypt", table_name, column_name, patient_id)
        return result

    def decrypt_phi_field(
        self, encrypted_value: str, patient_id: str,
        table_name: str, column_name: str,
        break_glass: bool = False, break_glass_reason: str = "",
    ) -> str:
        if not encrypted_value:
            return encrypted_value

        if not encrypted_value.startswith("phi:"):
            raise ValueError("Invalid PHI-encrypted value format")

        payload = json.loads(encrypted_value[4:])
        import base64
        iv = base64.b64decode(payload["iv"])
        data = base64.b64decode(payload["data"])

        try:
            column_key = self._derive_column_key(table_name, column_name, patient_id)
            aad = f"{table_name}:{column_name}:{patient_id}".encode()
            aesgcm = AESGCM(column_key)
            plaintext = aesgcm.decrypt(iv, data, aad)
            self._audit("decrypt", table_name, column_name, patient_id)
            return plaintext.decode()
        except Exception as exc:
            if break_glass and self._break_glass_enabled:
                logger.warning(
                    "Break-glass decryption for %s.%s patient=%s reason=%s",
                    table_name, column_name, patient_id, break_glass_reason,
                )
                self._audit("break_glass", table_name, column_name, patient_id)
                return self._break_glass_decrypt(data, iv, table_name, column_name, patient_id)
            logger.error("PHI decryption failed for %s.%s: %s", table_name, column_name, exc)
            raise

    def re_encrypt_patient_data(
        self, patient_id: str, table_name: str,
        columns: dict[str, str],
        old_master_key: bytes,
    ) -> dict[str, str]:
        result: dict[str, str] = {}
        old_encryptor = PHIEncryptor(master_key=old_master_key)

        for column_name, encrypted_value in columns.items():
            try:
                plain = old_encryptor.decrypt_phi_field(
                    encrypted_value, patient_id, table_name, column_name,
                )
                result[column_name] = self.encrypt_phi_field(
                    plain, patient_id, table_name, column_name,
                )
            except Exception as exc:
                logger.error("Re-encryption failed for %s.%s: %s", table_name, column_name, exc)
                result[column_name] = encrypted_value

        return result

    def enable_break_glass(self, emergency_key: bytes) -> None:
        if len(emergency_key) != 32:
            raise ValueError("Emergency key must be 32 bytes")
        self._break_glass_enabled = True
        self._break_glass_keys["emergency"] = emergency_key
        logger.warning("Break-glass decryption enabled")

    def disable_break_glass(self) -> None:
        self._break_glass_enabled = False
        self._break_glass_keys.clear()
        logger.info("Break-glass decryption disabled")

    def _derive_column_key(self, table: str, column: str, patient_id: str) -> bytes:
        cache_key = f"{table}:{column}:{patient_id}"
        if cache_key in self._column_keys:
            return self._column_keys[cache_key]

        table_key = self._derive_table_key(table)
        info = f"phi:{table}:{column}:{patient_id}:column_key".encode()
        derived = self._hkdf(table_key, 32, info)
        self._column_keys[cache_key] = derived
        return derived

    def _derive_table_key(self, table_name: str) -> bytes:
        if table_name in self._table_keys:
            return self._table_keys[table_name]

        info = f"phi:{table_name}:table_key".encode()
        derived = self._hkdf(self._master_key, 32, info)
        self._table_keys[table_name] = derived
        return derived

    def _break_glass_decrypt(
        self, data: bytes, iv: bytes,
        table: str, column: str, patient_id: str,
    ) -> str:
        emergency_key = self._break_glass_keys.get("emergency")
        if emergency_key is None:
            raise PermissionError("Break-glass not available")

        info = f"phi:{table}:{column}:{patient_id}:emergency".encode()
        derived_key = self._hkdf(emergency_key, 32, info)
        aesgcm = AESGCM(derived_key)
        aad = f"{table}:{column}:{patient_id}".encode()
        return aesgcm.decrypt(iv, data, aad).decode()

    def _verify_consent(self, patient_id: str, consent_token: str) -> bool:
        expected = _hmac_module.new(
            self._master_key, f"consent:{patient_id}".encode(), hashlib.sha256,
        ).hexdigest()[:32]
        return _hmac_module.compare_digest(expected, consent_token)

    def generate_consent_token(self, patient_id: str) -> str:
        return _hmac_module.new(
            self._master_key, f"consent:{patient_id}".encode(), hashlib.sha256,
        ).hexdigest()[:32]

    def _hash_patient_id(self, patient_id: str) -> str:
        return hashlib.sha256(f"phi:{patient_id}".encode()).hexdigest()[:16]

    def _audit(self, action: str, table: str, column: str, patient_id: str) -> None:
        entry: dict[str, Any] = {
            "action": action,
            "table": table,
            "column": column,
            "patient_id_hash": self._hash_patient_id(patient_id),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._audit_log.append(entry)
        logger.info("PHI %s: %s.%s patient=%s", action, table, column, self._hash_patient_id(patient_id))

    def get_audit_log(self, limit: int = 100) -> list[dict[str, Any]]:
        return list(self._audit_log[-limit:])

    def rotate_master_key(self, new_master_key: bytes) -> None:
        if len(new_master_key) != 32:
            raise ValueError("New master key must be 32 bytes")
        old_key = self._master_key
        self._master_key = new_master_key
        self._table_keys.clear()
        self._column_keys.clear()
        logger.info("PHI master key rotated (old key retained for decryption of existing data)")

        self._break_glass_keys["previous_master"] = old_key

    def _hkdf(self, ikm: bytes, length: int, info: bytes) -> bytes:
        salt = b"gula-phi-encryption-v1"
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
