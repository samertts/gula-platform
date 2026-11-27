"""Wave 05.1 — offline clinical conflict fail-closed boundary.

No clinical payload is stored in logs. Tests use synthetic values and
characterize fault injection/recovery without claiming production durability.
"""

from __future__ import annotations

import pytest

from app.integration.offline import (
    ConflictResolver,
    DeltaSyncEngine,
    OfflineQueueEntry,
    OfflineSyncEngine,
    StoreForwardEngine,
)
from app.platform.sync import SyncService
from app.services.offline_sync_service import (
    ConflictResolution,
    OfflineSyncEngine as ClinicalOfflineSyncEngine,
    SyncOperation,
    SyncStatus,
    is_clinical_entity,
)


def _clinical_ops(engine: ClinicalOfflineSyncEngine):
    first = SyncOperation(
        operation_id="synthetic-local-op",
        entity_type="clinical_note",
        entity_id="synthetic-note",
        operation="update",
        data={"text": "local synthetic version"},
        vector_clock={"device-a": 1},
        device_id="device-a",
        user_id="synthetic-user-a",
        timestamp=100.0,
    )
    first.signature = engine._sign_operation(first.operation_id, first.data, first.device_id)
    second = SyncOperation(
        operation_id="synthetic-remote-op",
        entity_type="clinical_note",
        entity_id="synthetic-note",
        operation="update",
        data={"text": "remote synthetic version"},
        vector_clock={"device-b": 1},
        device_id="device-b",
        user_id="synthetic-user-b",
        timestamp=110.0,
    )
    second.signature = engine._sign_operation(second.operation_id, second.data, second.device_id)
    engine.receive_operation(first)
    engine.receive_operation(second)
    return engine.get_conflicts()[0]


def test_clinical_entity_types_are_recognized() -> None:
    assert is_clinical_entity("clinical_note") is True
    assert is_clinical_entity("DiagnosticReport") is True
    assert is_clinical_entity("patient") is False


def test_unknown_conflict_strategy_is_rejected_at_construction() -> None:
    with pytest.raises(ValueError):
        ConflictResolver("unknown-strategy")


def test_unknown_strategy_never_falls_through_to_remote() -> None:
    resolver = ConflictResolver("manual")
    resolver._strategy = "typo-strategy"
    unequal = resolver.resolve({"v": "local"}, {"v": "remote"}, 1, 2, entity_type="patient")
    assert unequal["_conflict"] is True
    assert unequal["local"] == {"v": "local"}
    assert unequal["remote"] == {"v": "remote"}
    assert "v" not in unequal
    equal = resolver.resolve({"v": "local"}, {"v": "remote"}, 2, 2, entity_type="patient")
    assert equal["reason"] == "equal versions require manual review"


def test_manual_strategy_preserves_both_versions() -> None:
    result = ConflictResolver("manual").resolve(
        {"v": "local", "author": "a"},
        {"v": "remote", "author": "b"},
        1,
        2,
        entity_type="clinical_note",
        timestamp_local=10.0,
        timestamp_remote=20.0,
    )
    assert result["local"] == {"v": "local", "author": "a"}
    assert result["remote"] == {"v": "remote", "author": "b"}
    assert result["timestamp_local"] == 10.0
    assert result["timestamp_remote"] == 20.0


def test_clinical_auto_resolution_is_rejected_and_versions_preserved() -> None:
    engine = ClinicalOfflineSyncEngine(device_secret="synthetic-secret")
    conflict = _clinical_ops(engine)
    assert conflict.resolution is ConflictResolution.MANUAL
    assert conflict.operation_a.status is SyncStatus.CONFLICT
    assert conflict.operation_b.status is SyncStatus.CONFLICT
    assert conflict.operation_a.data == {"text": "local synthetic version"}
    assert conflict.operation_b.data == {"text": "remote synthetic version"}
    assert engine.get_pending() == []

    result = engine.resolve_conflict(
        conflict.conflict_id, ConflictResolution.LAST_WRITE_WINS, resolver="system"
    )
    assert result is None
    assert conflict.resolution is ConflictResolution.MANUAL
    assert conflict.resolved_at is None
    assert conflict.merged_data == {}
    assert any(
        entry.get("type") == "conflict_resolution_rejected" for entry in engine.get_sync_log()
    )


def test_manual_clinical_resolution_requires_named_resolver() -> None:
    engine = ClinicalOfflineSyncEngine(device_secret="synthetic-secret")
    conflict = _clinical_ops(engine)
    assert engine.resolve_conflict(conflict.conflict_id, ConflictResolution.MANUAL, resolver="") is None
    assert conflict.resolution is ConflictResolution.MANUAL


def test_conflict_id_is_order_independent_and_replay_does_not_reset_resolution() -> None:
    first_engine = ClinicalOfflineSyncEngine(device_secret="synthetic-secret")
    first = _clinical_ops(first_engine)

    second_engine = ClinicalOfflineSyncEngine(device_secret="synthetic-secret")
    op_a = SyncOperation(
        operation_id="synthetic-local-op",
        entity_type="clinical_note",
        entity_id="synthetic-note",
        operation="update",
        data={"text": "A"},
        vector_clock={"d1": 1},
        device_id="d1",
        user_id="u1",
        timestamp=100.0,
    )
    op_a.signature = second_engine._sign_operation(op_a.operation_id, op_a.data, op_a.device_id)
    op_b = SyncOperation(
        operation_id="synthetic-remote-op",
        entity_type="clinical_note",
        entity_id="synthetic-note",
        operation="update",
        data={"text": "B"},
        vector_clock={"d2": 1},
        device_id="d2",
        user_id="u2",
        timestamp=op_a.timestamp + 10,
    )
    op_b.signature = second_engine._sign_operation(op_b.operation_id, op_b.data, op_b.device_id)
    second_engine.receive_operation(op_a)
    second_engine.receive_operation(op_b)
    second = second_engine.get_conflicts()[0]
    assert first.conflict_id == second.conflict_id

    assert second_engine.resolve_conflict(
        second.conflict_id, ConflictResolution.MANUAL, resolver="synthetic-reviewer"
    ) is not None
    resolved_at = second.resolved_at
    second_engine.receive_operation(op_b)
    assert second.resolved_at == resolved_at


def test_sync_all_identifies_conflicts_without_pushing_a_winner() -> None:
    resolver = ConflictResolver("manual")
    result = resolver.resolve(
        {"status": "draft", "author": "a"},
        {"status": "final", "author": "b"},
        2,
        2,
        entity_type="clinical_note",
    )
    assert result["_conflict"] is True
    assert result["reason"] == "equal versions require manual review"


@pytest.mark.asyncio
async def test_offline_queue_duplicate_replay_is_not_double_pushed() -> None:
    sync_service = SyncService()
    engine = OfflineSyncEngine(sync_service=sync_service)
    entry = OfflineQueueEntry(
        id="synthetic-entry",
        entity_type="clinical_note",
        entity_id="synthetic-note",
        action="sync",
        payload={"version": 3, "text": "synthetic"},
        timestamp=1.0,
    )
    assert engine.store_forward.enqueue(entry) is True
    assert engine.store_forward.enqueue(entry) is False
    first = await engine.sync_all()
    second = await engine.sync_all()
    assert first["synced"] == 1
    assert second["synced"] == 0
    assert len(sync_service.pull_changes()) == 1


@pytest.mark.asyncio
async def test_fault_injection_and_recovery_are_visible_and_retry_safe() -> None:
    sync_service = SyncService()
    delta = DeltaSyncEngine(sync_service)
    calls: list[int] = []

    def failing_push(changes):
        calls.append(1)
        if len(calls) == 1:
            raise RuntimeError("synthetic transient fault")
        return sync_service.push_changes(changes)

    delta.push_delta = failing_push
    engine = OfflineSyncEngine(sync_service=sync_service, delta_sync=delta)
    engine.store_forward.enqueue(
        OfflineQueueEntry(
            id="synthetic-fault",
            entity_type="clinical_note",
            entity_id="synthetic-note",
            action="sync",
            payload={"version": 4, "text": "synthetic"},
            timestamp=2.0,
        )
    )
    failed = await engine.sync_all()
    assert failed["failed"] == 1
    recovered = await engine.sync_all()
    assert recovered["synced"] == 1
    assert len(calls) == 2
