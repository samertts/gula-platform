"""Tests for the Offline Identity Sync Engine."""

from app.services.offline_sync_service import (
    ConflictResolution,
    OfflineSyncEngine,
    EncryptedSyncStore,
    SyncOperation,
)


class TestOfflineSyncEngine:
    def test_create_operation(self):
        engine = OfflineSyncEngine(device_secret="test-secret")
        op = engine.create_operation(
            entity_type="patient",
            entity_id="patient-001",
            operation="update",
            data={"name": "Test Patient"},
            device_id="device-001",
            user_id="user-001",
        )
        assert op.operation_id
        assert op.entity_type == "patient"
        assert op.entity_id == "patient-001"
        assert op.operation == "update"
        assert op.data == {"name": "Test Patient"}
        assert op.device_id == "device-001"
        assert op.signature
        assert op.status.value == "pending"

    def test_receive_and_mark_synced(self):
        engine = OfflineSyncEngine(device_secret="test-secret")
        op = engine.create_operation(
            entity_type="patient",
            entity_id="patient-002",
            operation="create",
            data={"name": "Valid"},
            device_id="device-001",
            user_id="user-001",
        )
        result = engine.receive_operation(op)
        assert result.status.value == "pending"
        assert engine.mark_synced(op.operation_id)
        assert op.status.value == "synced"

    def test_reject_invalid_signature(self):
        engine = OfflineSyncEngine(device_secret="test-secret")
        op = SyncOperation(
            operation_id="bad-op",
            entity_type="patient",
            entity_id="patient-003",
            operation="update",
            data={"name": "Tampered"},
            device_id="device-001",
            user_id="user-001",
            timestamp=1000,
            signature="invalid-signature",
        )
        result = engine.receive_operation(op)
        assert result.status.value == "failed"

    def test_pending_operations(self):
        engine = OfflineSyncEngine(device_secret="test-secret")
        op = engine.create_operation(
            entity_type="patient",
            entity_id="patient-004",
            operation="update",
            data={"name": "Pending"},
            device_id="device-001",
            user_id="user-001",
        )
        pending = engine.get_pending()
        assert len(pending) == 1
        assert pending[0].operation_id == op.operation_id
        assert pending[0].status.value == "pending"

    def test_mark_synced(self):
        engine = OfflineSyncEngine(device_secret="test-secret")
        op = engine.create_operation(
            entity_type="patient",
            entity_id="patient-005",
            operation="update",
            data={},
            device_id="device-001",
            user_id="user-001",
        )
        assert engine.mark_synced(op.operation_id)
        assert op.status.value == "synced"

    def test_clear_synced(self):
        engine = OfflineSyncEngine(device_secret="test-secret")
        op1 = engine.create_operation(
            entity_type="patient", entity_id="p1",
            operation="update", data={},
            device_id="d1", user_id="u1",
        )
        op2 = engine.create_operation(
            entity_type="patient", entity_id="p2",
            operation="update", data={},
            device_id="d1", user_id="u1",
        )
        engine.mark_synced(op1.operation_id)
        cleared = engine.clear_synced()
        assert cleared == 1
        pending = engine.get_pending()
        assert len(pending) == 1
        assert pending[0].operation_id == op2.operation_id

    def test_vector_clock(self):
        engine = OfflineSyncEngine(device_secret="test-secret")
        engine.create_operation(
            entity_type="patient", entity_id="p-clock",
            operation="update", data={"v": 1},
            device_id="d1", user_id="u1",
        )
        engine.create_operation(
            entity_type="patient", entity_id="p-clock",
            operation="update", data={"v": 2},
            device_id="d2", user_id="u1",
        )
        clock = engine.get_vector_clock("p-clock")
        assert clock.get("d1", 0) >= 1
        assert clock.get("d2", 0) >= 1

    def test_last_write_wins_resolution(self):
        engine = OfflineSyncEngine(device_secret="test-secret")
        op_a = engine.create_operation(
            entity_type="patient", entity_id="p-conflict",
            operation="update", data={"name": "Alice"},
            device_id="d1", user_id="u1",
        )
        op_a.timestamp = 1000
        op_b = SyncOperation(
            operation_id="lww-op-2",
            entity_type="patient",
            entity_id="p-conflict",
            operation="update",
            data={"name": "Bob"},
            vector_clock={"d2": 1},
            device_id="d2",
            user_id="u2",
            timestamp=2000,
            signature="",
        )
        op_b.signature = engine._sign_operation(
            op_b.operation_id, op_b.data, op_b.device_id
        )

        engine.receive_operation(op_a)
        engine.receive_operation(op_b)

        conflicts = engine.get_conflicts()
        assert len(conflicts) >= 1

        result = engine.resolve_conflict(
            conflicts[0].conflict_id,
            ConflictResolution.LAST_WRITE_WINS,
            resolver="system",
        )
        assert result is not None
        assert result["name"] == "Bob"

    def test_conflict_detection(self):
        engine = OfflineSyncEngine(device_secret="test-secret")
        op1 = engine.create_operation(
            entity_type="patient", entity_id="p-cd",
            operation="update", data={"field": "a"},
            device_id="d1", user_id="u1",
        )
        op2 = SyncOperation(
            operation_id="cd-op-2",
            entity_type="patient",
            entity_id="p-cd",
            operation="update",
            data={"field": "b"},
            vector_clock={"d99": 1},
            device_id="d99",
            user_id="u1",
            timestamp=9999,
            signature="",
        )
        op2.signature = engine._sign_operation(
            op2.operation_id, op2.data, op2.device_id
        )

        engine.receive_operation(op1)
        result = engine.receive_operation(op2)
        assert result.status.value == "conflict"

        conflicts = engine.get_conflicts()
        assert len(conflicts) >= 1

    def test_crdt_merge(self):
        engine = OfflineSyncEngine(device_secret="test-secret")
        op_a = engine.create_operation(
            entity_type="patient", entity_id="p-crdt",
            operation="update", data={"name": "Ali", "phone": "123"},
            device_id="d1", user_id="u1",
        )
        op_b = SyncOperation(
            operation_id="crdt-op-2",
            entity_type="patient",
            entity_id="p-crdt",
            operation="update",
            data={"name": "Ahmed", "email": "a@b.com"},
            vector_clock={"d2": 1},
            device_id="d2",
            user_id="u2",
            timestamp=9999,
            signature="",
        )
        op_b.signature = engine._sign_operation(
            op_b.operation_id, op_b.data, op_b.device_id
        )

        engine.receive_operation(op_a)
        engine.receive_operation(op_b)
        conflicts = engine.get_conflicts()
        assert len(conflicts) >= 1

        result = engine.resolve_conflict(
            conflicts[0].conflict_id,
            ConflictResolution.CRDT_MERGE,
            resolver="system",
        )
        assert result is not None
        assert "name" in result
        assert "phone" in result or "email" in result

    def test_sync_log(self):
        engine = OfflineSyncEngine(device_secret="test-secret")
        op = engine.create_operation(
            entity_type="patient", entity_id="p-log",
            operation="update", data={},
            device_id="d1", user_id="u1",
        )
        engine.mark_synced(op.operation_id)
        log = engine.get_sync_log()
        assert len(log) >= 1
        assert log[0]["type"] == "synced"

    def test_receive_duplicate(self):
        engine = OfflineSyncEngine(device_secret="test-secret")
        op = engine.create_operation(
            entity_type="patient", entity_id="p-dup",
            operation="update", data={"x": 1},
            device_id="d1", user_id="u1",
        )
        r1 = engine.receive_operation(op)
        r2 = engine.receive_operation(op)
        assert r1.operation_id == r2.operation_id

    def test_no_conflict_causal_ops(self):
        engine = OfflineSyncEngine(device_secret="test-secret")
        op1 = engine.create_operation(
            entity_type="patient", entity_id="p-causal",
            operation="update", data={"v": 1},
            device_id="d1", user_id="u1",
        )
        op2 = engine.create_operation(
            entity_type="patient", entity_id="p-causal",
            operation="update", data={"v": 2},
            device_id="d1", user_id="u1",
        )
        engine.receive_operation(op1)
        result = engine.receive_operation(op2)
        assert result.status.value != "conflict"

    def test_vector_clock_increments(self):
        engine = OfflineSyncEngine(device_secret="test-secret")
        op1 = engine.create_operation(
            entity_type="patient", entity_id="p-vc",
            operation="update", data={},
            device_id="d1", user_id="u1",
        )
        assert op1.vector_clock["d1"] == 1
        op2 = engine.create_operation(
            entity_type="patient", entity_id="p-vc",
            operation="update", data={},
            device_id="d1", user_id="u1",
        )
        assert op2.vector_clock["d1"] == 2


class TestEncryptedSyncStore:
    def test_put_and_get(self):
        store = EncryptedSyncStore(encryption_key="test-key-32-chars-long!!")
        store.put("test-key", {"name": "Test", "value": 42})
        result = store.get("test-key")
        assert result is not None
        assert result["name"] == "Test"
        assert result["value"] == 42

    def test_get_missing(self):
        store = EncryptedSyncStore()
        result = store.get("nonexistent")
        assert result is None

    def test_delete(self):
        store = EncryptedSyncStore()
        store.put("del-key", {"data": "to-delete"})
        assert store.delete("del-key")
        assert store.get("del-key") is None

    def test_list_keys(self):
        store = EncryptedSyncStore()
        store.put("k1", {"d": 1})
        store.put("k2", {"d": 2})
        keys = store.list_keys()
        assert "k1" in keys
        assert "k2" in keys

    def test_clear(self):
        store = EncryptedSyncStore()
        store.put("k1", {"d": 1})
        store.put("k2", {"d": 2})
        store.clear()
        assert len(store.list_keys()) == 0

    def test_encryption_integrity(self):
        store = EncryptedSyncStore(encryption_key="my-secure-key-12345")
        store.put("sensitive", {"national_id": "1234567890"})
        stored = store._store["sensitive"]
        raw = store.get("sensitive")
        assert raw is not None
        assert raw["national_id"] == "1234567890"
        assert stored != b'{"national_id": "1234567890"}'
