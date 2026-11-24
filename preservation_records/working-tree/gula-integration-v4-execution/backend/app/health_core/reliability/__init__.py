"""Isolated reliability and operations designs for synthetic Health Core development.

Everything in this package is process-local and in-memory. Nothing here is wired into
the application, writes to a filesystem, opens a database, publishes to a broker, or
sends telemetry. It exists so reliability behaviour can be implemented and tested with
synthetic ``SYN-`` data before any owner-authorized production design is approved.
"""

from __future__ import annotations

from app.health_core.reliability.audit import (
    GENESIS_HASH,
    AuditFailure,
    AuditLog,
    AuditRecord,
    AuditVerification,
    chain_head,
    verify_chain,
)
from app.health_core.reliability.backup import (
    BackupArtifact,
    BackupMetadata,
    assert_data_equal,
    create_backup,
    restore_backup,
    verify_backup,
)
from app.health_core.reliability.durable import (
    SNAPSHOT_SCHEMA,
    WAL_SCHEMA,
    DurableStore,
    InMemoryWALStore,
    WALRecord,
    make_wal_record,
    validate_snapshot,
)
from app.health_core.reliability.errors import (
    AuditChainError,
    BackupIntegrityError,
    ChecksumMismatchError,
    ConflictAccountingError,
    IdempotencyConflictError,
    InvalidMetricNameError,
    InvalidStoreValueError,
    ReliabilityError,
)
from app.health_core.reliability.hashing import (
    canonical_json_bytes,
    decode_checked_envelope,
    require_synthetic_id,
    require_text,
    sealed_envelope,
    sha256_hex,
)
from app.health_core.reliability.idempotency import (
    IdempotentProcessor,
    ProcessingRecord,
    ProcessingResult,
    ProcessStatus,
)
from app.health_core.reliability.metrics import MetricsRegistry
from app.health_core.reliability.performance import (
    PerformanceMeasurement,
    percentile,
    run_pipeline_load,
    summarize_durations,
)
from app.health_core.reliability.retry import (
    BackoffPolicy,
    DeadLetterEntry,
    RetryExecutor,
    RetryOutcome,
    RetryStatus,
)
from app.health_core.reliability.sync_conflicts import (
    CandidateDisposition,
    DispositionReason,
    ResolutionLedger,
    SyncCandidate,
    SyncOutcome,
    SyncPolicy,
    assert_full_accounting,
    make_candidate,
    resolve_sync_conflict,
)

__all__ = [
    "GENESIS_HASH",
    "SNAPSHOT_SCHEMA",
    "WAL_SCHEMA",
    "AuditChainError",
    "AuditFailure",
    "AuditLog",
    "AuditRecord",
    "AuditVerification",
    "BackoffPolicy",
    "BackupArtifact",
    "BackupIntegrityError",
    "BackupMetadata",
    "CandidateDisposition",
    "ChecksumMismatchError",
    "ConflictAccountingError",
    "DeadLetterEntry",
    "DispositionReason",
    "DurableStore",
    "IdempotencyConflictError",
    "IdempotentProcessor",
    "InMemoryWALStore",
    "InvalidMetricNameError",
    "InvalidStoreValueError",
    "MetricsRegistry",
    "PerformanceMeasurement",
    "ProcessStatus",
    "ProcessingRecord",
    "ProcessingResult",
    "ReliabilityError",
    "ResolutionLedger",
    "RetryExecutor",
    "RetryOutcome",
    "RetryStatus",
    "SyncCandidate",
    "SyncOutcome",
    "SyncPolicy",
    "WALRecord",
    "assert_data_equal",
    "assert_full_accounting",
    "canonical_json_bytes",
    "chain_head",
    "create_backup",
    "decode_checked_envelope",
    "make_candidate",
    "make_wal_record",
    "percentile",
    "require_synthetic_id",
    "require_text",
    "resolve_sync_conflict",
    "restore_backup",
    "run_pipeline_load",
    "sealed_envelope",
    "sha256_hex",
    "summarize_durations",
    "validate_snapshot",
    "verify_backup",
    "verify_chain",
]
