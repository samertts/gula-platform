"""Checksummed backup artifacts and verified restore into a fresh in-memory store.

A backup is a canonical JSON snapshot payload plus SHA-256 checksum and explicit
metadata. Restore fails closed on checksum, schema, count or data mismatch. No file,
bucket, database or live data is involved.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.health_core.reliability.durable import (
    SNAPSHOT_SCHEMA,
    DurableStore,
    InMemoryWALStore,
    validate_snapshot,
)
from app.health_core.reliability.errors import BackupIntegrityError
from app.health_core.reliability.hashing import (
    canonical_json_bytes,
    require_synthetic_id,
    sha256_hex,
)


@dataclass(frozen=True, slots=True)
class BackupMetadata:
    """Descriptive metadata that travels with a backup payload."""

    artifact_id: str
    created_at: str
    schema: str
    record_count: int
    checksum: str
    data_digest: str

    def to_dict(self) -> dict[str, object]:
        """Stable serialisable view for audit and contract tests."""
        return {
            "artifact_id": self.artifact_id,
            "created_at": self.created_at,
            "schema": self.schema,
            "record_count": self.record_count,
            "checksum": self.checksum,
            "data_digest": self.data_digest,
        }


@dataclass(frozen=True, slots=True)
class BackupArtifact:
    """Payload bytes plus checksummed metadata (in memory only)."""

    metadata: BackupMetadata
    payload: bytes


def create_backup(
    store: DurableStore, *, artifact_id: str, created_at: str
) -> BackupArtifact:
    """Checkpoint the store and create a backup of the resulting snapshot."""
    safe_id = require_synthetic_id(artifact_id, field="artifact_id")
    if not isinstance(created_at, str) or not created_at:
        raise BackupIntegrityError("created_at must be a non-empty timestamp")
    store.commit()
    payload = store.snapshot_bytes()
    if not payload:
        raise BackupIntegrityError("cannot back up an empty snapshot")
    committed = store.committed_data
    metadata = BackupMetadata(
        artifact_id=safe_id,
        created_at=created_at,
        schema=SNAPSHOT_SCHEMA,
        record_count=len(committed),
        checksum=sha256_hex(payload),
        data_digest=sha256_hex(canonical_json_bytes(committed)),
    )
    return BackupArtifact(metadata=metadata, payload=payload)


def verify_backup(artifact: BackupArtifact) -> None:
    """Raise a structured error unless checksum and snapshot structure are valid."""
    if sha256_hex(artifact.payload) != artifact.metadata.checksum:
        raise BackupIntegrityError(
            "backup checksum mismatch",
            details={"artifact_id": artifact.metadata.artifact_id},
        )
    if artifact.metadata.schema != SNAPSHOT_SCHEMA:
        raise BackupIntegrityError("backup schema is not supported")
    try:
        validate_snapshot(artifact.payload)
    except BackupIntegrityError:
        raise
    except Exception as exc:  # checksum/schema failures are ReliabilityError subclasses
        raise BackupIntegrityError(f"backup payload is invalid: {exc}") from exc


def restore_backup(artifact: BackupArtifact) -> InMemoryWALStore:
    """Restore into a fresh store and prove checksum, metadata and data equality."""
    verify_backup(artifact)
    restored = InMemoryWALStore()
    restored.restore(artifact.payload)
    if len(restored.data) != artifact.metadata.record_count:
        raise BackupIntegrityError(
            "restored record count does not match backup metadata",
            details={"artifact_id": artifact.metadata.artifact_id},
        )
    if restored.snapshot_bytes() != artifact.payload:
        raise BackupIntegrityError("restored snapshot bytes differ from the backup payload")
    if sha256_hex(canonical_json_bytes(restored.data)) != artifact.metadata.data_digest:
        raise BackupIntegrityError("restored data digest does not match backup metadata")
    assert_data_equal(restored, restored_from_payload(artifact.payload))
    return restored


def restored_from_payload(payload: bytes) -> InMemoryWALStore:
    """Build a second independent restore used for data-equality confirmation."""
    second = InMemoryWALStore()
    second.restore(payload)
    return second


def assert_data_equal(left: DurableStore, right: DurableStore) -> None:
    """Fail closed if two stores differ in data or canonical snapshot bytes."""
    if left.data != right.data or left.snapshot_bytes() != right.snapshot_bytes():
        raise BackupIntegrityError("restored store data is not equal to the source")
