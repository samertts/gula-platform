"""Backup/restore integrity and synthetic idempotency processing tests."""

from __future__ import annotations

from dataclasses import replace

import pytest
from app.health_core.common.errors import InvalidSyntheticReferenceError
from app.health_core.reliability import (
    BackupIntegrityError,
    IdempotencyConflictError,
    IdempotentProcessor,
    InMemoryWALStore,
    ProcessStatus,
    assert_data_equal,
    create_backup,
    restore_backup,
    verify_backup,
)

CREATED_AT = "2026-01-01T00:00:00+00:00"


def _source_store() -> InMemoryWALStore:
    store = InMemoryWALStore()
    for index in range(1, 4):
        store.put(f"SYN-EVT-{index:06d}", {"sequence": index})
    return store


def test_backup_artifact_has_bytes_checksum_and_metadata() -> None:
    artifact = create_backup(_source_store(), artifact_id="SYN-BKP-000001", created_at=CREATED_AT)
    assert isinstance(artifact.payload, bytes) and artifact.payload
    assert len(artifact.metadata.checksum) == 64
    assert artifact.metadata.record_count == 3
    assert artifact.metadata.schema == "gula-reliability-snapshot-v1"
    assert artifact.metadata.artifact_id == "SYN-BKP-000001"
    assert set(artifact.metadata.to_dict()) == {
        "artifact_id",
        "created_at",
        "schema",
        "record_count",
        "checksum",
        "data_digest",
    }


def test_backup_restores_into_fresh_store_with_data_equality() -> None:
    source = _source_store()
    artifact = create_backup(source, artifact_id="SYN-BKP-000002", created_at=CREATED_AT)
    restored = restore_backup(artifact)
    assert restored.data == source.data
    assert restored.snapshot_bytes() == artifact.payload
    assert_data_equal(restored, source)
    assert verify_backup(artifact) is None


def test_corrupt_backup_payload_is_rejected() -> None:
    artifact = create_backup(_source_store(), artifact_id="SYN-BKP-000003", created_at=CREATED_AT)
    corrupted = replace(artifact, payload=artifact.payload + b" ")
    with pytest.raises(BackupIntegrityError) as exc:
        restore_backup(corrupted)
    assert exc.value.to_dict()["code"] == "BACKUP_INTEGRITY"


def test_corrupt_backup_checksum_is_rejected_without_decoding_payload() -> None:
    artifact = create_backup(_source_store(), artifact_id="SYN-BKP-000004", created_at=CREATED_AT)
    metadata = replace(artifact.metadata, checksum="0" * 64)
    with pytest.raises(BackupIntegrityError):
        restore_backup(replace(artifact, metadata=metadata))


def test_backup_count_and_digest_tampering_is_detected() -> None:
    artifact = create_backup(_source_store(), artifact_id="SYN-BKP-000005", created_at=CREATED_AT)
    with pytest.raises(BackupIntegrityError):
        restore_backup(replace(artifact, metadata=replace(artifact.metadata, record_count=99)))
    with pytest.raises(BackupIntegrityError):
        restore_backup(replace(artifact, metadata=replace(artifact.metadata, data_digest="f" * 64)))


def test_backup_requires_synthetic_artifact_id() -> None:
    with pytest.raises(InvalidSyntheticReferenceError):
        create_backup(_source_store(), artifact_id="BK-123", created_at=CREATED_AT)


def test_identical_replay_creates_no_second_effect() -> None:
    processor = IdempotentProcessor()
    payload = {"event_id": "SYN-EVT-000001", "value": 1}
    first = processor.process("SYN-KEY-000001", payload)
    replay = processor.process("SYN-KEY-000001", dict(payload))
    assert first.status is ProcessStatus.NEW
    assert replay.status is ProcessStatus.DUPLICATE
    assert replay.effect_id == first.effect_id
    assert replay.fingerprint == first.fingerprint
    assert processor.effect_count == 1
    assert processor.effects == (first.effect_id,)
    assert len(processor.records) == 1


def test_conflicting_key_reuse_raises_structured_error() -> None:
    processor = IdempotentProcessor()
    processor.process("SYN-KEY-000002", {"value": 1})
    with pytest.raises(IdempotencyConflictError) as exc:
        processor.process("SYN-KEY-000002", {"value": 2})
    body = exc.value.to_dict()
    assert body["code"] == "IDEMPOTENCY_KEY_CONFLICT"
    assert body["status_code"] == 409
    assert body["retryable"] is False
    assert body["details"]["key"] == "SYN-KEY-000002"
    assert body["details"]["expected_fingerprint"] != body["details"]["observed_fingerprint"]
    assert processor.effect_count == 1


def test_distinct_keys_and_invalid_key_shapes() -> None:
    processor = IdempotentProcessor()
    first = processor.process("SYN-KEY-000003", {"value": 1})
    second = processor.process("SYN-KEY-000004", {"value": 1})
    assert first.effect_id != second.effect_id
    assert processor.effect_count == 2
    with pytest.raises(InvalidSyntheticReferenceError):
        processor.process("KEY-000005", {"value": 1})
