"""Phase C (F-069 / D-023) — offline conflict resolution, synthetic data only.

All entities, devices and values are fictional. No DB, no network, no device.

The former `CRDT_MERGE` was first-seen-key-wins and could silently overwrite a
clinical value. The honest replacement (`CONFLICT_QUARANTINE`) merges only
non-contested keys, preserves every contested version with provenance, never
uses local device time to select a value, and is idempotent/replayable.

CRDT convergence is NOT claimed: with no per-field versioned registers,
tombstones or deterministic actor tie-break, CRDT properties cannot be proven.
Crash durability remains NOT VERIFIED (F-028: in-memory store).

Evidence id: E-055 (see GOVERNANCE/GECS/EVIDENCE_REGISTRY.md).
"""

from __future__ import annotations

import pytest

from app.services.offline_sync_service import (
    ConflictResolution,
    OfflineSyncEngine,
    SyncOperation,
    SyncStatus,
)

SECRET = "synthetic-secret"


def _engine() -> OfflineSyncEngine:
    return OfflineSyncEngine(device_secret=SECRET)


def _op(
    engine: OfflineSyncEngine,
    op_id: str,
    entity_id: str,
    data: dict,
    device: str,
    clock: dict[str, int],
    timestamp: float = 100.0,
) -> SyncOperation:
    op = SyncOperation(
        operation_id=op_id,
        entity_type="lab_result",
        entity_id=entity_id,
        operation="update",
        data=data,
        vector_clock=clock,
        device_id=device,
        user_id="synthetic-user",
        timestamp=timestamp,
        signature="",
    )
    op.signature = engine._sign_operation(op.operation_id, op.data, op.device_id)
    return op


def _conflict_pair(engine, data_a, data_b, ts_a=100.0, ts_b=9999.0):
    """Two concurrent, same-entity operations from two devices."""
    a = _op(engine, "op-A", "lab-1", data_a, "device-A", {"device-A": 1}, ts_a)
    b = _op(engine, "op-B", "lab-1", data_b, "device-B", {"device-B": 1}, ts_b)
    engine.receive_operation(a)
    result_b = engine.receive_operation(b)
    conflicts = engine.get_conflicts()
    assert result_b.status == SyncStatus.CONFLICT
    assert len(conflicts) == 1
    return conflicts[0]


class TestConflictQuarantine:
    def test_clinical_value_never_silently_overwritten(self):
        engine = _engine()
        conflict = _conflict_pair(
            engine,
            {"result": "POSITIVE", "unit": "IU/L"},
            {"result": "NEGATIVE", "note": "retest"},
            ts_a=100.0, ts_b=9999.0,  # later timestamp must NOT win a clinical value
        )
        result = engine.resolve_conflict(
            conflict.conflict_id, ConflictResolution.CONFLICT_QUARANTINE,
            resolver="synthetic-reviewer", resolved_at=2000.0,
        )
        assert result["_resolution_status"] == "CONFLICT_QUARANTINED"
        assert "result" not in result                     # no auto-selection
        contested = result["_conflicts"]["result"]
        assert {contested[k]["value"] for k in ("operation_a", "operation_b")} == {"POSITIVE", "NEGATIVE"}
        assert contested["operation_b"]["timestamp"] == 9999.0  # provenance kept, not used to pick
        # Non-contested keys are merged without loss.
        assert result["unit"] == "IU/L"
        assert result["note"] == "retest"

    def test_agreed_values_merge_without_quarantine(self):
        engine = _engine()
        conflict = _conflict_pair(
            engine, {"result": "NEGATIVE", "unit": "IU/L"},
            {"result": "NEGATIVE", "note": "ok"},
        )
        result = engine.resolve_conflict(
            conflict.conflict_id, ConflictResolution.CONFLICT_QUARANTINE,
            resolved_at=2000.0,
        )
        assert result["_resolution_status"] == "MERGED"
        assert result["result"] == "NEGATIVE"
        assert result["unit"] == "IU/L" and result["note"] == "ok"
        assert "_conflicts" not in result

    def test_out_of_order_arrival_retains_same_versions(self):
        # The set of retained conflicting values is independent of arrival order
        # (the property we CAN claim — this is not CRDT state convergence).
        seen = []
        for order in (("op-A", "op-B"), ("op-B", "op-A")):
            engine = _engine()
            data = {"op-A": {"result": "POSITIVE"}, "op-B": {"result": "NEGATIVE"}}[order[0]]
            other = {"op-A": {"result": "POSITIVE"}, "op-B": {"result": "NEGATIVE"}}[order[1]]
            a = _op(engine, order[0], "lab-1", data, order[0], {order[0]: 1}, 100.0)
            b = _op(engine, order[1], "lab-1", other, order[1], {order[1]: 1}, 9000.0)
            for op in (a, b):
                engine.receive_operation(op)
            conflict = engine.get_conflicts()[0]
            result = engine.resolve_conflict(
                conflict.conflict_id, ConflictResolution.CONFLICT_QUARANTINE, resolved_at=1.0
            )
            values = {v["value"] for v in result["_conflicts"]["result"].values()}
            seen.append(values)
        assert seen[0] == seen[1] == {"POSITIVE", "NEGATIVE"}

    def test_two_node_sync_and_reconnect_with_conflict(self):
        node_a, node_b, reconciler = _engine(), _engine(), _engine()
        op_a = node_a.create_operation("lab_result", "lab-2", "update",
                                       {"result": "HIGH"}, device_id="device-A")
        op_b = node_b.create_operation("lab_result", "lab-2", "update",
                                       {"result": "LOW"}, device_id="device-B")
        # Each node accepts its own write while partitioned.
        assert node_a.receive_operation(op_a).status == SyncStatus.PENDING
        assert node_b.receive_operation(op_b).status == SyncStatus.PENDING
        # Reconnect: the reconciler sees both concurrent writes.
        reconciler.receive_operation(op_a)
        reconciler.receive_operation(op_b)
        conflict = reconciler.get_conflicts()[0]
        result = reconciler.resolve_conflict(
            conflict.conflict_id, ConflictResolution.CONFLICT_QUARANTINE, resolved_at=1.0
        )
        assert result["_resolution_status"] == "CONFLICT_QUARANTINED"
        assert len(result["_conflicts"]["result"]) == 2

    def test_multi_node_no_data_loss(self):
        engine = _engine()
        inputs = [
            _op(engine, "op-1", "lab-3", {"glucose": "90"}, "d1", {"d1": 1}),
            _op(engine, "op-2", "lab-3", {"glucose": "300", "critical": True}, "d2", {"d2": 1}),
            _op(engine, "op-3", "lab-3", {"glucose": "95", "unit": "mg/dL"}, "d3", {"d3": 1}),
        ]
        for op in inputs:
            engine.receive_operation(op)
        for conflict in engine.get_conflicts():
            engine.resolve_conflict(
                conflict.conflict_id, ConflictResolution.CONFLICT_QUARANTINE,
                resolved_at=1.0,
            )
        # Every distinct value from every node survives either in the merged
        # projection or in a conflict record.
        retained = set()
        for record in engine.get_conflicts():
            retained.update(v["value"] for v in record.merged_data.get("_conflicts", {}).values()
                            for v in v.values())
            for key, value in record.merged_data.items():
                if not key.startswith("_"):
                    retained.add(value)
        assert 300 in retained or "300" in retained
        assert True in retained
        assert "mg/dL" in retained

    def test_duplicate_event_and_business_key_no_false_conflict(self):
        engine = _engine()
        op = _op(engine, "op-dup", "lab-4", {"result": "OK"}, "d1", {"d1": 1})
        first = engine.receive_operation(op)
        second = engine.receive_operation(op)          # exact replay
        assert first is second
        assert len(engine.get_conflicts()) == 0

    def test_idempotent_resolution_and_single_audit_row(self):
        engine = _engine()
        conflict = _conflict_pair(engine, {"a": "1"}, {"a": "2"})
        first = engine.resolve_conflict(
            conflict.conflict_id, ConflictResolution.CONFLICT_QUARANTINE,
            resolver="reviewer", resolved_at=123.0,
        )
        for _ in range(3):
            replay = engine.resolve_conflict(
                conflict.conflict_id, ConflictResolution.CONFLICT_QUARANTINE,
                resolver="reviewer",
            )
            assert replay == first
        rows = [r for r in engine.get_sync_log()
                if r["type"] == "conflict_resolved" and r["conflict_id"] == conflict.conflict_id]
        assert len(rows) == 1
        assert rows[0]["operation_a_id"] == "op-A"
        assert rows[0]["operation_b_id"] == "op-B"
        assert rows[0]["timestamp"] == 123.0

    def test_manual_resolution_remains_available_and_deterministic(self):
        engine = _engine()
        conflict = _conflict_pair(engine, {"v": "A"}, {"v": "B"})
        chosen = {"v": "B", "reviewed": True}
        result = engine.resolve_conflict(
            conflict.conflict_id, ConflictResolution.MANUAL,
            resolver="human", merged_data=chosen, resolved_at=7.0,
        )
        assert result == chosen
        assert engine.resolve_conflict(
            conflict.conflict_id, ConflictResolution.MANUAL, resolver="human"
        ) == chosen

    def test_invalid_signature_is_rejected(self):
        engine = _engine()
        op = _op(engine, "op-bad", "lab-5", {"v": "1"}, "d1", {"d1": 1})
        op.signature = "tampered"
        assert engine.receive_operation(op).status == SyncStatus.FAILED

    def test_replay_based_recovery_rebuilds_state(self):
        # Logical recovery from replayed event log works. Physical durability
        # across a process crash is NOT VERIFIED (F-028, in-memory store).
        original = _engine()
        op = original.create_operation("lab_result", "lab-6", "update",
                                       {"result": "NORMAL"}, device_id="d1")
        recovered = _engine()
        recovered.receive_operation(op)
        assert recovered.get_pending()[0].data == {"result": "NORMAL"}


class TestNoCRDTClaim:
    def test_no_crdt_enum_value_remains(self):
        values = {v.value for v in ConflictResolution}
        assert "crdt_merge" not in values
        assert "conflict_quarantine" in values
        assert not any("crdt" in v.value for v in ConflictResolution)
