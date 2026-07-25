from __future__ import annotations

import hashlib
import json
import logging
import os
import threading
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Callable

from security.modules.crypto.models import (
    EncryptionAlgorithm,
    EncryptionConfig,
    KeyMetadata,
    KeyPurpose,
)
from security.modules.crypto.random import SecureRandom

logger = logging.getLogger("gula.security.modules.crypto.key_rotation")


class KeyRotationManager:
    def __init__(self, config: EncryptionConfig | None = None) -> None:
        self._config = config or EncryptionConfig()
        self._keys: dict[str, bytes] = {}
        self._metadata: dict[str, KeyMetadata] = {}
        self._active_key_id: str = ""
        self._lock = threading.Lock()
        self._rotation_history: list[dict[str, Any]] = []
        self._notification_hooks: list[Callable[[str, str], None]] = []
        self._running = False
        self._thread: threading.Thread | None = None
        self._grace_periods: dict[str, datetime] = {}

    @property
    def active_key_id(self) -> str:
        return self._active_key_id

    def add_key(self, key_id: str, key_bytes: bytes, purpose: KeyPurpose, algorithm: Any = None) -> None:
        if len(key_bytes) not in (16, 32, 64):
            raise ValueError(f"Invalid key length: {len(key_bytes)}")

        alg = algorithm or EncryptionAlgorithm.AES_256_GCM
        metadata = KeyMetadata(
            key_id=key_id,
            purpose=purpose,
            algorithm=alg,
            created_at=datetime.now(timezone.utc),
            rotation_count=0,
            status="active",
        )
        with self._lock:
            self._keys[key_id] = key_bytes
            self._metadata[key_id] = metadata
            if not self._active_key_id:
                self._active_key_id = key_id
        logger.info("Key added: %s (purpose=%s)", key_id, purpose.value)

    def get_current_key(self) -> bytes:
        if not self._active_key_id:
            raise ValueError("No active key configured")
        return self.get_key_by_id(self._active_key_id)

    def get_current_key_id(self) -> str:
        return self._active_key_id

    def get_key_by_id(self, key_id: str) -> bytes:
        with self._lock:
            if key_id not in self._keys:
                raise ValueError(f"Key not found: {key_id}")
            return self._keys[key_id]

    def get_metadata(self, key_id: str) -> KeyMetadata:
        with self._lock:
            if key_id not in self._metadata:
                raise ValueError(f"Key metadata not found: {key_id}")
            return self._metadata[key_id]

    def set_active_key(self, key_id: str) -> None:
        with self._lock:
            if key_id not in self._keys:
                raise ValueError(f"Cannot activate unknown key: {key_id}")
            old_id = self._active_key_id
            self._active_key_id = key_id
            logger.info("Active key changed: %s -> %s", old_id, key_id)

    def rotate(self, key_id: str | None = None) -> str:
        target_key_id = key_id or self._active_key_id
        if not target_key_id:
            raise ValueError("No key to rotate")

        with self._lock:
            if target_key_id not in self._keys:
                raise ValueError(f"Key not found: {target_key_id}")

            old_metadata = self._metadata[target_key_id]
            new_key_id = f"{target_key_id}_rot{old_metadata.rotation_count + 1}_{int(time.time())}"
            new_key = SecureRandom.bytes(32)

            self._keys[new_key_id] = new_key
            self._metadata[new_key_id] = KeyMetadata(
                key_id=new_key_id,
                purpose=old_metadata.purpose,
                algorithm=old_metadata.algorithm,
                created_at=datetime.now(timezone.utc),
                rotation_count=old_metadata.rotation_count + 1,
                status="active",
            )

            old_metadata.status = "rotated"
            self._active_key_id = new_key_id

            self._grace_periods[target_key_id] = datetime.now(timezone.utc) + timedelta(
                days=self._config.key_rotation_days // 2
            )

            record: dict[str, Any] = {
                "old_key_id": target_key_id,
                "new_key_id": new_key_id,
                "purpose": old_metadata.purpose.value,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "success": True,
            }
            self._rotation_history.append(record)
            logger.info("Key rotated: %s -> %s", target_key_id, new_key_id)

        for hook in self._notification_hooks:
            try:
                hook(target_key_id, new_key_id)
            except Exception as exc:
                logger.error("Rotation notification hook failed: %s", exc)

        return new_key_id

    def emergency_rotation(self) -> str:
        if not self._active_key_id:
            raise ValueError("No active key to rotate")
        logger.warning("EMERGENCY KEY ROTATION initiated for %s", self._active_key_id)
        return self.rotate(self._active_key_id)

    def start_auto_rotation(self, interval_hours: int = 24) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._auto_rotation_loop,
            args=(interval_hours,),
            daemon=True,
            name="gula-key-rotator",
        )
        self._thread.start()
        logger.info("Auto key rotation started (interval=%dh)", interval_hours)

    def stop_auto_rotation(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=10)
        logger.info("Auto key rotation stopped")

    def _auto_rotation_loop(self, interval_hours: int) -> None:
        interval_seconds = interval_hours * 3600
        while self._running:
            try:
                for key_id in list(self._keys.keys()):
                    meta = self._metadata.get(key_id)
                    if meta and meta.status == "active" and key_id != self._active_key_id:
                        expired = datetime.now(timezone.utc) - (meta.created_at or datetime.now(timezone.utc))
                        if expired.days >= self._config.key_rotation_days:
                            self._metadata[key_id].status = "expired"
                            logger.info("Key expired: %s", key_id)

                last_rotation = self._metadata.get(self._active_key_id)
                if last_rotation and last_rotation.created_at:
                    age = datetime.now(timezone.utc) - last_rotation.created_at
                    if age.days >= self._config.key_rotation_days:
                        self.rotate()
                        logger.info("Auto rotation completed for %s", self._active_key_id)
            except Exception as exc:
                logger.error("Auto rotation error: %s", exc)

            for _ in range(interval_seconds // 10):
                if not self._running:
                    return
                time.sleep(10)

    def re_encrypt_data(self, data: bytes, old_key_id: str, purpose: KeyPurpose) -> bytes:
        old_key = self.get_key_by_id(old_key_id)
        new_key = self.get_current_key()

        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        aesgcm = AESGCM(old_key)
        iv = data[:12]
        ciphertext = data[12:]
        plaintext = aesgcm.decrypt(iv, ciphertext, b"")

        aesgcm_new = AESGCM(new_key)
        new_iv = SecureRandom.bytes(12)
        new_ciphertext = aesgcm_new.encrypt(new_iv, plaintext, b"")

        return new_iv + new_ciphertext

    def register_notification_hook(self, hook: Callable[[str, str], None]) -> None:
        self._notification_hooks.append(hook)

    def get_rotation_history(self, limit: int = 100) -> list[dict[str, Any]]:
        return list(self._rotation_history[-limit:])

    def list_keys(self, purpose: KeyPurpose | None = None) -> list[KeyMetadata]:
        with self._lock:
            if purpose:
                return [m for m in self._metadata.values() if m.purpose == purpose]
            return list(self._metadata.values())

    def is_key_in_grace_period(self, key_id: str) -> bool:
        if key_id in self._grace_periods:
            return datetime.now(timezone.utc) < self._grace_periods[key_id]
        return False

    def backup_keys(self, passphrase: bytes) -> bytes:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        key_data: dict[str, Any] = {}
        with self._lock:
            for key_id, key_bytes in self._keys.items():
                key_data[key_id] = key_bytes.hex()
            key_data["active_key_id"] = self._active_key_id

        serialized = json.dumps(key_data, separators=(",", ":")).encode()
        aesgcm = AESGCM(hashlib.sha256(passphrase).digest())
        iv = SecureRandom.bytes(12)
        ciphertext = aesgcm.encrypt(iv, serialized, b"backup")
        return iv + ciphertext

    def restore_keys(self, backup_data: bytes, passphrase: bytes) -> None:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        iv = backup_data[:12]
        ciphertext = backup_data[12:]
        aesgcm = AESGCM(hashlib.sha256(passphrase).digest())
        serialized = aesgcm.decrypt(iv, ciphertext, b"backup")
        key_data: dict[str, Any] = json.loads(serialized.decode())

        with self._lock:
            for key_id, key_hex in key_data.items():
                if key_id == "active_key_id":
                    continue
                self._keys[key_id] = bytes.fromhex(key_hex)
                self._metadata[key_id] = KeyMetadata(
                    key_id=key_id,
                    purpose=KeyPurpose.DATA_ENCRYPTION,
                    algorithm=EncryptionAlgorithm.AES_256_GCM,
                    created_at=datetime.now(timezone.utc),
                    status="active",
                )
            self._active_key_id = key_data.get("active_key_id", "")
        logger.info("Keys restored from backup (%d keys)", len(key_data) - 1)
