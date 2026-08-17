from __future__ import annotations

import hashlib
import json
import logging
import time
import zlib
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger("gula.offline.sync")


class ConflictResolution(Enum):
    LAST_WRITE_WINS = "lww"
    TIMESTAMP_MERGE = "timestamp_merge"
    MANUAL = "manual"
    CRDT_MERGE = "crdt_merge"


class SyncStatus(Enum):
    PENDING = "pending"
    SYNCED = "synced"
    CONFLICT = "conflict"
    FAILED = "failed"


@dataclass
class SyncOperation:
    operation_id: str = ""
    entity_type: str = ""
    entity_id: str = ""
    operation: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    vector_clock: dict[str, int] = field(default_factory=dict)
    device_id: str = ""
    user_id: str = ""
    timestamp: float = 0.0
    signature: str = ""
    status: SyncStatus = SyncStatus.PENDING

    def to_dict(self) -> dict[str, Any]:
        return {
            "operation_id": self.operation_id,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "operation": self.operation,
            "data": self.data,
            "vector_clock": self.vector_clock,
            "device_id": self.device_id,
            "user_id": self.user_id,
            "timestamp": self.timestamp,
            "signature": self.signature,
            "status": self.status.value,
        }

    def compute_hash(self) -> str:
        raw = json.dumps(self.to_dict(), sort_keys=True)
        return hashlib.sha256(raw.encode()).hexdigest()


@dataclass
class ConflictRecord:
    conflict_id: str = ""
    operation_a: SyncOperation = field(default_factory=SyncOperation)
    operation_b: SyncOperation = field(default_factory=SyncOperation)
    resolution: ConflictResolution = ConflictResolution.MANUAL
    resolved_at: float | None = None
    resolved_by: str = ""
    merged_data: dict[str, Any] = field(default_factory=dict)


class OfflineSyncEngine:
    def __init__(self, device_secret: str = ""):
        self._operations: dict[str, SyncOperation] = {}
        self._conflicts: dict[str, ConflictRecord] = {}
        self._device_secret = device_secret
        self._vector_clocks: dict[str, dict[str, int]] = {}
        self._sync_log: list[dict[str, Any]] = []

    def create_operation(
        self,
        entity_type: str,
        entity_id: str,
        operation: str,
        data: dict[str, Any],
        device_id: str = "",
        user_id: str = "",
    ) -> SyncOperation:
        ts = time.time()
        raw_id = f"{entity_type}:{entity_id}:{ts}:{device_id}"
        op_id = hashlib.sha256(raw_id.encode()).hexdigest()[:16]

        clock = dict(self._vector_clocks.get(entity_id, {}))
        clock[device_id] = clock.get(device_id, 0) + 1

        op = SyncOperation(
            operation_id=op_id,
            entity_type=entity_type,
            entity_id=entity_id,
            operation=operation,
            data=data,
            vector_clock=clock,
            device_id=device_id,
            user_id=user_id,
            timestamp=ts,
            signature=self._sign_operation(op_id, data, device_id),
            status=SyncStatus.PENDING,
        )
        self._operations[op_id] = op
        self._vector_clocks[entity_id] = clock
        return op

    def receive_operation(self, op: SyncOperation) -> SyncOperation:
        if not self._verify_signature(op):
            logger.warning("Invalid signature for operation %s", op.operation_id)
            op.status = SyncStatus.FAILED
            return op

        existing = self._operations.get(op.operation_id)
        if existing:
            return existing

        conflict = self._detect_conflict(op)
        if conflict:
            op.status = SyncStatus.CONFLICT
            self._conflicts[conflict.conflict_id] = conflict
            logger.info("Conflict detected: %s", conflict.conflict_id)
            return op

        self._operations[op.operation_id] = op
        self._update_vector_clock(op)
        return op

    def mark_synced(self, operation_id: str) -> bool:
        op = self._operations.get(operation_id)
        if not op:
            return False
        op.status = SyncStatus.SYNCED
        self._sync_log.append({
            "type": "synced",
            "operation_id": operation_id,
            "timestamp": time.time(),
        })
        return True

    def resolve_conflict(
        self,
        conflict_id: str,
        resolution: ConflictResolution,
        resolver: str = "",
        merged_data: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        conflict = self._conflicts.get(conflict_id)
        if not conflict:
            return None

        if resolution != ConflictResolution.MANUAL:
            raise ValueError(
                "Automatic conflict resolution is disabled for clinical data; "
                "use MANUAL with an explicit reviewed merged_data payload"
            )
        if not merged_data:
            raise ValueError("Manual conflict resolution requires merged_data")
        result = merged_data

        conflict.resolution = resolution
        conflict.resolved_at = time.time()
        conflict.resolved_by = resolver
        conflict.merged_data = result

        self._sync_log.append({
            "type": "conflict_resolved",
            "conflict_id": conflict_id,
            "resolution": resolution.value,
            "resolver": resolver,
            "timestamp": time.time(),
        })

        return result

    def get_pending(self) -> list[SyncOperation]:
        return [op for op in self._operations.values() if op.status == SyncStatus.PENDING]

    def get_conflicts(self) -> list[ConflictRecord]:
        return list(self._conflicts.values())

    def get_sync_log(self, limit: int = 100) -> list[dict[str, Any]]:
        return list(self._sync_log[-limit:])

    def get_vector_clock(self, entity_id: str) -> dict[str, int]:
        return dict(self._vector_clocks.get(entity_id, {}))

    def clear_synced(self) -> int:
        count = 0
        for op_id, op in list(self._operations.items()):
            if op.status == SyncStatus.SYNCED:
                del self._operations[op_id]
                count += 1
        return count

    def _detect_conflict(self, incoming: SyncOperation) -> ConflictRecord | None:
        for existing in self._operations.values():
            if existing.operation_id == incoming.operation_id:
                continue
            if not self._same_entity(existing, incoming):
                continue
            if not self._has_causal_relationship(existing.vector_clock, incoming.vector_clock):
                conflict_id = hashlib.sha256(
                    f"{existing.operation_id}:{incoming.operation_id}".encode(),
                ).hexdigest()[:16]
                return ConflictRecord(
                    conflict_id=conflict_id,
                    operation_a=existing,
                    operation_b=incoming,
                    resolution=ConflictResolution.MANUAL,
                )
        return None

    def _same_entity(self, a: SyncOperation, b: SyncOperation) -> bool:
        return a.entity_type == b.entity_type and a.entity_id == b.entity_id

    def _has_causal_relationship(self, clock_a: dict[str, int], clock_b: dict[str, int]) -> bool:
        if not clock_a or not clock_b:
            return False
        all_keys = set(clock_a) | set(clock_b)
        a_leq_b = all(clock_a.get(k, 0) <= clock_b.get(k, 0) for k in all_keys)
        b_leq_a = all(clock_b.get(k, 0) <= clock_a.get(k, 0) for k in all_keys)
        return a_leq_b or b_leq_a

    def _update_vector_clock(self, op: SyncOperation) -> None:
        entity_id = op.entity_id
        current = self._vector_clocks.setdefault(entity_id, {})
        for dev, count in op.vector_clock.items():
            current[dev] = max(current.get(dev, 0), count)

    def _sign_operation(self, op_id: str, data: dict[str, Any], device_id: str) -> str:
        raw = f"{op_id}:{json.dumps(data, sort_keys=True)}:{device_id}:{self._device_secret}"
        return hashlib.sha256(raw.encode()).hexdigest()

    def _verify_signature(self, op: SyncOperation) -> bool:
        if not op.signature:
            return False
        expected = self._sign_operation(op.operation_id, op.data, op.device_id)
        return op.signature == expected


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
