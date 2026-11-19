from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import time
import uuid
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)


class EncryptionService:
    def __init__(self, key: bytes | None = None):
        import base64
        raw = key or os.urandom(32)
        self._key = base64.urlsafe_b64encode(raw[:32])

    def encrypt(self, data: bytes) -> bytes:
        from cryptography.fernet import Fernet
        f = Fernet(self._key)
        return f.encrypt(data)

    def decrypt(self, data: bytes) -> bytes:
        from cryptography.fernet import Fernet
        f = Fernet(self._key)
        return f.decrypt(data)


class InputValidator:
    MAX_STRING_LENGTH = 10000
    MAX_LIST_SIZE = 1000
    MAX_DICT_DEPTH = 10

    _UUID_PATTERN = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE)

    @staticmethod
    def sanitize_string(value: str, max_length: int = MAX_STRING_LENGTH) -> str:
        if not isinstance(value, str):
            return ""
        return value.strip()[:max_length]

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        cleaned = re.sub(r"[^\w\-_.() ]", "", filename)
        cleaned = re.sub(r"\.\.", ".", cleaned)
        cleaned = cleaned.strip()
        if not cleaned or cleaned.startswith("."):
            return "unnamed_file"
        return cleaned[:255]

    @staticmethod
    def is_valid_uuid(value: str) -> bool:
        return bool(InputValidator._UUID_PATTERN.match(value))

    @staticmethod
    def validate_email(email: str) -> bool:
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(pattern, email.strip()))

    @staticmethod
    def validate_national_id(national_id: str) -> bool:
        return bool(re.match(r"^\d{10,16}$", national_id.strip()))

    @staticmethod
    def sanitize_dict(data: dict[str, Any], max_depth: int = MAX_DICT_DEPTH) -> dict[str, Any]:
        def _sanitize(obj: Any, depth: int) -> Any:
            if depth > max_depth:
                return str(obj)[:100]
            if isinstance(obj, dict):
                return {str(k)[:200]: _sanitize(v, depth + 1) for k, v in obj.items()}
            if isinstance(obj, list):
                return [_sanitize(item, depth + 1) for item in obj[:InputValidator.MAX_LIST_SIZE]]
            if isinstance(obj, str):
                return obj[:InputValidator.MAX_STRING_LENGTH]
            return obj
        return _sanitize(data, 0)

    @staticmethod
    def strip_html(value: str) -> str:
        return re.sub(r"<[^>]*>", "", value)


class RateLimiter:
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self._max = max_requests
        self._window = window_seconds
        self._buckets: dict[str, list[float]] = {}

    async def check(self, key: str) -> bool:
        now = time.time()
        cutoff = now - self._window
        if key not in self._buckets:
            self._buckets[key] = []
        self._buckets[key] = [t for t in self._buckets[key] if t > cutoff]
        if len(self._buckets[key]) >= self._max:
            return False
        self._buckets[key].append(now)
        return True

    async def remaining(self, key: str) -> int:
        now = time.time()
        cutoff = now - self._window
        entries = [t for t in self._buckets.get(key, []) if t > cutoff]
        return max(0, self._max - len(entries))

    def reset(self, key: str | None = None):
        if key:
            self._buckets.pop(key, None)
        else:
            self._buckets.clear()


class AuditLogger:
    def __init__(self):
        self._entries: list[dict[str, Any]] = []

    async def log(
        self,
        action: str,
        entity_type: str,
        entity_id: str,
        actor: str,
        changes: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        entry = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now(UTC).isoformat(),
            "action": action,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "actor": actor,
            "changes": changes or {},
            "metadata": metadata or {},
        }
        self._entries.append(entry)
        logger.info("Audit: %s %s %s by %s", action, entity_type, entity_id, actor)
        return entry

    def get_entries(self, entity_id: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        if entity_id:
            return [e for e in self._entries if e["entity_id"] == entity_id][-limit:]
        return self._entries[-limit:]

    def search(self, query: str) -> list[dict[str, Any]]:
        q = query.lower()
        return [e for e in self._entries if q in json.dumps(e, default=str).lower()]


_audit_logger = AuditLogger()


def get_audit_logger() -> AuditLogger:
    return _audit_logger


class IntegrityChecker:
    def __init__(self):
        self._chain: list[dict[str, Any]] = []

    async def add_entry(self, entry: dict[str, Any]) -> dict[str, Any]:
        previous_hash = self._chain[-1]["hash"] if self._chain else "0" * 64
        combined = json.dumps(entry, sort_keys=True, default=str) + previous_hash
        entry_hash = hashlib.sha256(combined.encode()).hexdigest()
        record = {
            **entry,
            "previous_hash": previous_hash,
            "hash": entry_hash,
            "timestamp": datetime.now(UTC).isoformat(),
        }
        self._chain.append(record)
        return record

    def verify_chain(self) -> bool:
        for i in range(1, len(self._chain)):
            prev = self._chain[i - 1]
            current = self._chain[i]
            expected_prev_hash = prev["hash"]
            if current["previous_hash"] != expected_prev_hash:
                return False
            entry_data = {k: v for k, v in current.items() if k not in ("previous_hash", "hash", "timestamp")}
            combined = json.dumps(entry_data, sort_keys=True, default=str) + expected_prev_hash
            expected_hash = hashlib.sha256(combined.encode()).hexdigest()
            if current["hash"] != expected_hash:
                return False
        return True

    def get_chain(self) -> list[dict[str, Any]]:
        return self._chain

    def get_latest_hash(self) -> str:
        if self._chain:
            return self._chain[-1]["hash"]
        return "0" * 64
