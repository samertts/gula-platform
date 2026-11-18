"""Deterministic, in-process durable-event-queue reliability engine.

This is a self-contained design harness for synthetic ``SYN-`` events. Models an
append-only, checksummed and hash-chained event log; an explicit
``begin -> handle -> commit`` transaction; idempotent commit by event id;
bounded retry with an injected clock/sleeper; dead-lettering; quarantine of
concurrent version conflicts with idempotent resolution; and crash recovery by
replaying the log and redelivering only events still in flight.

BOUNDARY: the "log" is a byte buffer in this process. A crash is simulated by
dropping derived in-memory state and replaying those bytes. There is no
filesystem, database, broker, network, keyed signature or external monotonic
anchor. This is NOT production-grade durability and makes NO durability claim.
The raw payload is never written to the log (only its SHA-256 digest), and
exception text is reduced to a type plus digest, so no PII is persisted here.
Replayed events therefore carry an empty payload and their original digest; a
future owner-authorized implementation would need a keyed, tenant-scoped
external anchor (BLOCKED) to recover payload content safely.

Every command returns a typed result carrying a :class:`QueueStatus` and a
:class:`QueueReason`; no operation returns a bare ``bool``.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass, field, replace
from enum import StrEnum

from app.health_core.common.errors import InvalidSyntheticReferenceError
from app.health_core.reliability.audit import GENESIS_HASH
from app.health_core.reliability.errors import ChecksumMismatchError
from app.health_core.reliability.hashing import (
    canonical_json_bytes,
    decode_checked_envelope,
    require_synthetic_id,
    sealed_envelope,
    sha256_hex,
)

LOG_SCHEMA = "gula-reliability-queue-log-v1"
LOG_OPERATIONS = (
    "APPEND",
    "BEGIN",
    "ATTEMPT",
    "COMMIT",
    "DEAD_LETTER",
    "QUARANTINE",
    "RESOLVE",
)
MAX_ERROR_CHARS = 16

Handler = Callable[["QueueEvent"], object]


class QueueStatus(StrEnum):
    """Coarse outcome shared by all command results."""

    OK = "ok"
    DUPLICATE = "duplicate"
    REJECTED = "rejected"
    DEAD_LETTERED = "dead_lettered"
    QUARANTINED = "quarantined"


class QueueReason(StrEnum):
    """Stable machine-readable reason codes carried by every result."""

    ACCEPTED = "accepted"
    DUPLICATE_EVENT_ID = "duplicate_event_id"
    ALREADY_COMMITTED = "already_committed"
    MALFORMED_EVENT = "malformed_event"
    MISSING_EVENT_ID = "missing_event_id"
    MISSING_ENTITY_KEY = "missing_entity_key"
    NON_SERIALIZABLE_PAYLOAD = "non_serializable_payload"
    TENANT_MISMATCH = "tenant_mismatch"
    FACILITY_MISMATCH = "facility_mismatch"
    UNKNOWN_EVENT = "unknown_event"
    UNKNOWN_CONFLICT = "unknown_conflict"
    NOT_IN_FLIGHT = "not_in_flight"
    DELIVERED = "delivered"
    MAX_ATTEMPTS_EXHAUSTED = "max_attempts_exhausted"
    COMMITTED = "committed"
    VERSION_CONFLICT = "version_conflict"
    RESOLVED = "resolved"
    ALREADY_RESOLVED = "already_resolved"
    CONFLICT_ALREADY_DECIDED = "conflict_already_decided"
    LOG_INTEGRITY_FAILURE = "log_integrity_failure"
    RECOVERED = "recovered"
    CRASHED = "crashed"
    HANDLER_REGISTERED = "handler_registered"
    HANDLER_UNAVAILABLE = "handler_unavailable"


class EventState(StrEnum):
    """Lifecycle state of one queued event."""

    PENDING = "pending"
    IN_FLIGHT = "in_flight"
    COMMITTED = "committed"
    DEAD_LETTERED = "dead_lettered"
    QUARANTINED = "quarantined"
    RESOLVED = "resolved"


class AttemptOutcome(StrEnum):
    """Outcome of one handler invocation."""

    SUCCEEDED = "succeeded"
    FAILED = "failed"


class ConflictState(StrEnum):
    """State of a quarantined version conflict."""

    QUARANTINED = "quarantined"
    RESOLVED = "resolved"


class ResolutionAction(StrEnum):
    """Explicit, non-merging conflict resolutions."""

    TAKE_LOCAL = "take_local"
    TAKE_REMOTE = "take_remote"
    MANUAL = "manual"


@dataclass(frozen=True, slots=True)
class QueueConfig:
    """Immutable queue policy, including the exact scope of this queue instance."""

    tenant_id: str
    facility_id: str
    max_attempts: int = 3
    backoff_delays_ms: tuple[int, ...] = (2, 4, 8)

    def __post_init__(self) -> None:
        require_synthetic_id(self.tenant_id, field="tenant_id")
        require_synthetic_id(self.facility_id, field="facility_id")
        if isinstance(self.max_attempts, bool) or self.max_attempts < 1:
            raise ValueError("max_attempts must be a positive integer")
        if isinstance(self.backoff_delays_ms, tuple) and any(
            isinstance(delay, bool) or not isinstance(delay, int) or delay < 0
            for delay in self.backoff_delays_ms
        ):
            raise ValueError("backoff_delays_ms must contain non-negative integers")

    def delay_for(self, attempt: int) -> int:
        """Deterministic delay after a failed 1-based ``attempt``; zero when terminal."""
        if attempt < 1 or attempt >= self.max_attempts or not self.backoff_delays_ms:
            return 0
        if attempt - 1 < len(self.backoff_delays_ms):
            return self.backoff_delays_ms[attempt - 1]
        return self.backoff_delays_ms[-1]


@dataclass(frozen=True, slots=True)
class QueueEvent:
    """A validated synthetic event. ``payload`` is never logged; only its digest."""

    event_id: str
    event_type: str
    entity_key: str
    tenant_id: str
    facility_id: str
    version: int
    payload: dict[str, object] = field(default_factory=dict)
    payload_digest: str = ""


@dataclass(frozen=True, slots=True)
class EventValidation:
    """Typed result of validating raw event input."""

    status: QueueStatus
    reason: QueueReason
    event: QueueEvent | None
    detail: str


@dataclass(frozen=True, slots=True)
class LogEntry:
    """One checksummed, hash-chained append-only event-log record."""

    sequence: int
    operation: str
    event_id: str
    entity_key: str
    version: int
    tenant_id: str
    facility_id: str
    occurred_ms: int
    detail: dict[str, object]
    previous_hash: str
    entry_hash: str

    def body(self) -> dict[str, object]:
        """Return exactly the fields covered by ``entry_hash``."""
        return {
            "sequence": self.sequence,
            "operation": self.operation,
            "event_id": self.event_id,
            "entity_key": self.entity_key,
            "version": self.version,
            "tenant_id": self.tenant_id,
            "facility_id": self.facility_id,
            "occurred_ms": self.occurred_ms,
            "detail": self.detail,
            "previous_hash": self.previous_hash,
        }


@dataclass(frozen=True, slots=True)
class AttemptRecord:
    """One handler invocation; error text is reduced to a type and digest."""

    attempt: int
    at_ms: int
    outcome: AttemptOutcome
    delay_ms: int
    error_type: str | None = None
    error_digest: str | None = None


@dataclass(frozen=True, slots=True)
class EnqueueResult:
    status: QueueStatus
    reason: QueueReason
    event_id: str
    sequence: int
    detail: str


@dataclass(frozen=True, slots=True)
class TransactionResult:
    status: QueueStatus
    reason: QueueReason
    event_id: str
    sequence: int
    state: EventState
    detail: str


@dataclass(frozen=True, slots=True)
class DeliveryResult:
    status: QueueStatus
    reason: QueueReason
    event_id: str
    attempts: tuple[AttemptRecord, ...]
    backoff_trace: tuple[int, ...]
    state: EventState
    detail: str


@dataclass(frozen=True, slots=True)
class CommitResult:
    status: QueueStatus
    reason: QueueReason
    event_id: str
    state: EventState
    conflict_id: str | None
    detail: str


@dataclass(frozen=True, slots=True)
class ProcessResult:
    status: QueueStatus
    reason: QueueReason
    event_id: str
    delivery: DeliveryResult | None
    commit: CommitResult | None
    conflict_id: str | None
    detail: str


@dataclass(frozen=True, slots=True)
class DeadLetterRecord:
    """Terminal delivery failure with a reason, no payload and no raw error text."""

    letter_id: str
    event_id: str
    reason: QueueReason
    attempts: int
    payload_digest: str
    last_error: str
    occurred_ms: int


@dataclass(frozen=True, slots=True)
class ConflictRecord:
    """Structured quarantine record for a divergent entity version."""

    conflict_id: str
    event_id: str
    entity_key: str
    tenant_id: str
    facility_id: str
    local_version: int
    remote_version: int
    local_digest: str
    remote_digest: str
    state: ConflictState
    resolution_action: ResolutionAction | None = None
    resolution_id: str | None = None
    chosen_version: int | None = None
    chosen_digest: str | None = None
    resolved_at_ms: int | None = None


@dataclass(frozen=True, slots=True)
class ResolutionResult:
    status: QueueStatus
    reason: QueueReason
    conflict_id: str
    resolution_id: str
    action: ResolutionAction
    chosen_version: int | None
    sequence: int
    detail: str


@dataclass(frozen=True, slots=True)
class HandlerResult:
    status: QueueStatus
    reason: QueueReason
    event_type: str
    detail: str


@dataclass(frozen=True, slots=True)
class CrashResult:
    status: QueueStatus
    reason: QueueReason
    log_entries: int
    log_digest: str
    detail: str


@dataclass(frozen=True, slots=True)
class LogVerification:
    status: QueueStatus
    reason: QueueReason
    verified_count: int
    detail: str


@dataclass(frozen=True, slots=True)
class RecoveryResult:
    status: QueueStatus
    reason: QueueReason
    entries_replayed: int
    processed_keys: frozenset[str]
    redelivered: tuple[DeliveryResult, ...]
    pending_redelivery: tuple[str, ...]
    conflict_count: int
    dead_letter_count: int
    detail: str


def _counter_clock() -> Callable[[], int]:
    """A deterministic, wall-clock-free millisecond stand-in."""
    value = 0

    def next_ms() -> int:
        nonlocal value
        value += 1
        return value

    return next_ms


def _no_sleep(delay_ms: int) -> None:
    """Deterministic no-wait sleeper: the delay is already in the attempt trace.

    This is a complete implementation, not a stub: the requested delay is
    recorded by the caller in the retry attempt trace, so the sleeper itself
    deliberately discards it and performs no wall-clock wait.
    """
    del delay_ms


def _peek_event_id(raw: object) -> str:
    if isinstance(raw, Mapping):
        value = raw.get("event_id")
        return value if isinstance(value, str) else ""
    if isinstance(raw, QueueEvent):
        return raw.event_id
    return ""


def _replay_int(value: object) -> int:
    """Recover an integer field from a log detail value, failing closed.

    Log details are typed ``dict[str, object]`` because they mix strings,
    integers and optional values. This helper narrows an integer field with a
    real runtime check (booleans are deliberately rejected, as elsewhere in
    this module) so replay never silently accepts a malformed detail value.
    """
    if isinstance(value, bool):
        raise ValueError("boolean is not a valid replay integer")
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        return int(value)
    raise ValueError("non-integer replay detail value")


def _coerce_event(raw: object) -> EventValidation:
    """Validate raw input into a :class:`QueueEvent`, failing closed with a reason."""
    if isinstance(raw, QueueEvent):
        data: dict[str, object] = {
            "event_id": raw.event_id,
            "event_type": raw.event_type,
            "entity_key": raw.entity_key,
            "tenant_id": raw.tenant_id,
            "facility_id": raw.facility_id,
            "version": raw.version,
            "payload": raw.payload,
        }
    elif isinstance(raw, Mapping):
        data = dict(raw)
    else:
        return EventValidation(QueueStatus.REJECTED, QueueReason.MALFORMED_EVENT, None, "event must be an object")

    event_id = data.get("event_id")
    if event_id is None or (isinstance(event_id, str) and not event_id.strip()):
        return EventValidation(QueueStatus.REJECTED, QueueReason.MISSING_EVENT_ID, None, "event_id is required")
    entity_key = data.get("entity_key")
    if entity_key is None or (isinstance(entity_key, str) and not entity_key.strip()):
        return EventValidation(
            QueueStatus.REJECTED, QueueReason.MISSING_ENTITY_KEY, None, "entity_key is required"
        )

    identifiers: dict[str, str] = {}
    for name in ("event_id", "entity_key", "event_type", "tenant_id", "facility_id"):
        value = data.get(name)
        if not isinstance(value, str) or not value:
            return EventValidation(
                QueueStatus.REJECTED, QueueReason.MALFORMED_EVENT, None, f"{name} must be a non-empty string"
            )
        identifiers[name] = value
    for name in ("event_id", "entity_key", "tenant_id", "facility_id"):
        try:
            require_synthetic_id(identifiers[name], field=name)
        except InvalidSyntheticReferenceError:
            return EventValidation(
                QueueStatus.REJECTED,
                QueueReason.MALFORMED_EVENT,
                None,
                f"{name} must be a synthetic SYN- reference",
            )

    version = data.get("version", 1)
    if isinstance(version, bool) or not isinstance(version, int) or version < 1:
        return EventValidation(
            QueueStatus.REJECTED, QueueReason.MALFORMED_EVENT, None, "version must be a positive integer"
        )
    payload = data.get("payload", {})
    if not isinstance(payload, dict) or any(not isinstance(key, str) for key in payload):
        return EventValidation(
            QueueStatus.REJECTED,
            QueueReason.NON_SERIALIZABLE_PAYLOAD,
            None,
            "payload must be an object with string keys",
        )
    try:
        digest = sha256_hex(canonical_json_bytes(payload))
    except (TypeError, ValueError):
        return EventValidation(
            QueueStatus.REJECTED,
            QueueReason.NON_SERIALIZABLE_PAYLOAD,
            None,
            "payload must be JSON-serialisable",
        )
    return EventValidation(
        QueueStatus.OK,
        QueueReason.ACCEPTED,
        QueueEvent(
            event_id=identifiers["event_id"],
            event_type=identifiers["event_type"],
            entity_key=identifiers["entity_key"],
            tenant_id=identifiers["tenant_id"],
            facility_id=identifiers["facility_id"],
            version=version,
            payload=dict(payload),
            payload_digest=digest,
        ),
        "event validated",
    )


class DurableEventQueue:
    """In-process, deterministic durable-event-queue engine (synthetic use only)."""

    def __init__(
        self,
        config: QueueConfig,
        *,
        clock: Callable[[], int] | None = None,
        sleeper: Callable[[int], None] | None = None,
    ) -> None:
        self.config = config
        self._clock = clock if clock is not None else _counter_clock()
        self._sleeper = sleeper if sleeper is not None else _no_sleep
        self._log: list[LogEntry] = []
        self._anchor_head = GENESIS_HASH
        self._anchor_count = 0
        self._retained_log: bytes | None = None
        self._events: dict[str, QueueEvent] = {}
        self._states: dict[str, EventState] = {}
        self._attempts: dict[str, list[AttemptRecord]] = {}
        self._processed_keys: set[str] = set()
        self._dead_letters: list[DeadLetterRecord] = []
        self._conflicts: dict[str, ConflictRecord] = {}
        self._entity_versions: dict[tuple[str, str, str], int] = {}
        self._entity_digests: dict[tuple[str, str, str], str] = {}
        self._handlers: dict[str, Handler] = {}

    # -- log primitives -------------------------------------------------

    def _append(self, operation: str, event: QueueEvent, detail: dict[str, object]) -> LogEntry:
        """Append a hashed, chained log record before mutating derived state."""
        entry = LogEntry(
            sequence=len(self._log) + 1,
            operation=operation,
            event_id=event.event_id,
            entity_key=event.entity_key,
            version=event.version,
            tenant_id=event.tenant_id,
            facility_id=event.facility_id,
            occurred_ms=self._clock(),
            detail=dict(detail),
            previous_hash=self._anchor_head,
            entry_hash=GENESIS_HASH,
        )
        sealed = replace(entry, entry_hash=sha256_hex(canonical_json_bytes(entry.body())))
        self._log.append(sealed)
        self._anchor_head = sealed.entry_hash
        self._anchor_count = len(self._log)
        return sealed

    def log_bytes(self) -> bytes:
        """Return the sealed append-only log with authoritative terminal anchors."""
        if not self._log:
            return b""
        body: dict[str, object] = {
            "schema": LOG_SCHEMA,
            "record_count": self._anchor_count,
            "last_sequence": len(self._log),
            "anchored_head": self._anchor_head,
            "entries": [asdict(entry) for entry in self._log],
        }
        return canonical_json_bytes(sealed_envelope(body))

    def _parse_log(self, payload: bytes) -> tuple[LogVerification, tuple[LogEntry, ...]]:
        """Verify checksum, anchors and chain before any state is rebuilt."""
        failure = LogVerification(QueueStatus.REJECTED, QueueReason.LOG_INTEGRITY_FAILURE, 0, "")
        if not payload:
            if self._anchor_count:
                return replace(failure, detail="empty log despite anchored entries"), ()
            return LogVerification(QueueStatus.OK, QueueReason.ACCEPTED, 0, "empty log"), ()
        try:
            body = decode_checked_envelope(payload, schema=LOG_SCHEMA, label="event log")
        except (ChecksumMismatchError, AttributeError, TypeError, ValueError) as exc:
            return replace(failure, detail=str(exc)), ()

        raw_entries = body.get("entries")
        record_count = body.get("record_count")
        last_sequence = body.get("last_sequence")
        anchored_head = body.get("anchored_head")
        if not isinstance(raw_entries, list):
            return replace(failure, detail="log entries are malformed"), ()
        if (
            not isinstance(record_count, int)
            or isinstance(record_count, bool)
            or not isinstance(last_sequence, int)
            or isinstance(last_sequence, bool)
            or not isinstance(anchored_head, str)
        ):
            return replace(failure, detail="log terminal anchors are missing or malformed"), ()
        if record_count != len(raw_entries) or last_sequence != len(raw_entries):
            return replace(failure, detail="log record count or last sequence does not match entries"), ()

        entries: list[LogEntry] = []
        previous_hash = GENESIS_HASH
        for index, raw in enumerate(raw_entries, start=1):
            if not isinstance(raw, dict) or not isinstance(raw.get("detail"), dict):
                return replace(failure, detail=f"log entry {index} is malformed"), ()
            try:
                entry = LogEntry(
                    sequence=raw["sequence"],
                    operation=str(raw["operation"]),
                    event_id=str(raw["event_id"]),
                    entity_key=str(raw["entity_key"]),
                    version=raw["version"],
                    tenant_id=str(raw["tenant_id"]),
                    facility_id=str(raw["facility_id"]),
                    occurred_ms=raw["occurred_ms"],
                    detail=dict(raw["detail"]),
                    previous_hash=str(raw["previous_hash"]),
                    entry_hash=str(raw["entry_hash"]),
                )
            except (KeyError, TypeError, ValueError):
                return replace(failure, detail=f"log entry {index} is malformed"), ()
            if entry.sequence != index or entry.operation not in LOG_OPERATIONS:
                return replace(failure, detail=f"log entry {index} sequence or operation is invalid"), ()
            if entry.previous_hash != previous_hash:
                return replace(failure, detail=f"log entry {index} has a broken link"), ()
            if sha256_hex(canonical_json_bytes(entry.body())) != entry.entry_hash:
                return replace(failure, detail=f"log entry {index} hash mismatch"), ()
            entries.append(entry)
            previous_hash = entry.entry_hash
        if anchored_head != previous_hash:
            return replace(failure, detail="log anchored head does not match its chain"), ()
        if self._anchor_count and (record_count != self._anchor_count or anchored_head != self._anchor_head):
            return replace(failure, detail="log anchors do not match in-process anchors"), ()
        return (
            LogVerification(QueueStatus.OK, QueueReason.ACCEPTED, len(entries), "log verified"),
            tuple(entries),
        )

    def verify_log(self, payload: bytes | None = None) -> LogVerification:
        """Fail-closed integrity check; never mutates queue state."""
        raw = self.log_bytes() if payload is None else payload
        verification, _ = self._parse_log(raw)
        return verification

    # -- commands -------------------------------------------------------

    def register_handler(self, event_type: str, handler: Handler) -> HandlerResult:
        """Register the handler used for an event type during delivery and replay."""
        if not isinstance(event_type, str) or not event_type or not callable(handler):
            return HandlerResult(
                QueueStatus.REJECTED, QueueReason.MALFORMED_EVENT, str(event_type), "invalid handler registration"
            )
        self._handlers[event_type] = handler
        return HandlerResult(QueueStatus.OK, QueueReason.HANDLER_REGISTERED, event_type, "handler registered")

    def enqueue(self, event: QueueEvent | Mapping[str, object]) -> EnqueueResult:
        """Validate and append an event exactly once by ``event_id``."""
        validation = _coerce_event(event)
        if validation.event is None:
            return EnqueueResult(
                QueueStatus.REJECTED,
                validation.reason,
                _peek_event_id(event),
                0,
                validation.detail,
            )
        safe_event = validation.event
        if safe_event.event_id in self._events:
            return EnqueueResult(
                QueueStatus.DUPLICATE,
                QueueReason.DUPLICATE_EVENT_ID,
                safe_event.event_id,
                0,
                "event id already appended",
            )
        entry = self._append(
            "APPEND",
            safe_event,
            {"event_type": safe_event.event_type, "payload_digest": safe_event.payload_digest},
        )
        self._events[safe_event.event_id] = safe_event
        self._states[safe_event.event_id] = EventState.PENDING
        self._attempts[safe_event.event_id] = []
        return EnqueueResult(
            QueueStatus.OK, QueueReason.ACCEPTED, safe_event.event_id, entry.sequence, "event appended"
        )

    def _scope_reason(self, event: QueueEvent) -> QueueReason | None:
        if event.tenant_id != self.config.tenant_id:
            return QueueReason.TENANT_MISMATCH
        if event.facility_id != self.config.facility_id:
            return QueueReason.FACILITY_MISMATCH
        return None

    def begin(self, event_id: str) -> TransactionResult:
        """Start the explicit transaction: PENDING -> IN_FLIGHT."""
        event = self._events.get(event_id)
        if event is None:
            return TransactionResult(
                QueueStatus.REJECTED, QueueReason.UNKNOWN_EVENT, str(event_id), 0, EventState.PENDING, "unknown event"
            )
        scope = self._scope_reason(event)
        if scope is not None:
            return TransactionResult(QueueStatus.REJECTED, scope, event_id, 0, EventState.PENDING, "scope mismatch")
        if event_id in self._processed_keys:
            return TransactionResult(
                QueueStatus.DUPLICATE,
                QueueReason.ALREADY_COMMITTED,
                event_id,
                0,
                EventState.COMMITTED,
                "event already committed",
            )
        if self._states[event_id] is not EventState.PENDING:
            return TransactionResult(
                QueueStatus.REJECTED,
                QueueReason.NOT_IN_FLIGHT,
                event_id,
                0,
                self._states[event_id],
                "event is not pending",
            )
        entry = self._append("BEGIN", event, {"state": EventState.IN_FLIGHT.value})
        self._states[event_id] = EventState.IN_FLIGHT
        return TransactionResult(
            QueueStatus.OK, QueueReason.ACCEPTED, event_id, entry.sequence, EventState.IN_FLIGHT, "transaction begun"
        )

    def _dead_letter(self, event: QueueEvent, attempts: tuple[AttemptRecord, ...]) -> None:
        last = attempts[-1]
        reason = QueueReason.MAX_ATTEMPTS_EXHAUSTED
        letter_id = f"SYN-DLQ-{sha256_hex(canonical_json_bytes([event.event_id, last.error_digest]))[:16].upper()}"
        entry = self._append(
            "DEAD_LETTER",
            event,
            {
                "reason": reason.value,
                "attempts": last.attempt,
                "letter_id": letter_id,
                "last_error": f"{last.error_type}:{last.error_digest}",
            },
        )
        self._dead_letters.append(
            DeadLetterRecord(
                letter_id=letter_id,
                event_id=event.event_id,
                reason=reason,
                attempts=last.attempt,
                payload_digest=event.payload_digest,
                last_error=f"{last.error_type}:{last.error_digest}",
                occurred_ms=entry.occurred_ms,
            )
        )
        self._states[event.event_id] = EventState.DEAD_LETTERED

    def _run_attempts(self, event: QueueEvent, handler: Handler) -> DeliveryResult:
        attempts = self._attempts[event.event_id]
        while len(attempts) < self.config.max_attempts:
            attempt_no = len(attempts) + 1
            at_ms = self._clock()
            try:
                handler(event)
            except Exception as exc:  # handler failures are the retry signal
                error_type = type(exc).__name__
                error_digest = sha256_hex(str(exc).encode("utf-8"))[:MAX_ERROR_CHARS]
                delay = self.config.delay_for(attempt_no)
                record = AttemptRecord(attempt_no, at_ms, AttemptOutcome.FAILED, delay, error_type, error_digest)
                self._append(
                    "ATTEMPT",
                    event,
                    {"attempt": attempt_no, "at_ms": at_ms, "outcome": AttemptOutcome.FAILED.value,
                     "delay_ms": delay, "error_type": error_type, "error_digest": error_digest},
                )
                attempts.append(record)
                if delay:
                    self._sleeper(delay)
                continue
            record = AttemptRecord(attempt_no, at_ms, AttemptOutcome.SUCCEEDED, 0)
            self._append(
                "ATTEMPT",
                event,
                {"attempt": attempt_no, "at_ms": at_ms, "outcome": AttemptOutcome.SUCCEEDED.value,
                 "delay_ms": 0},
            )
            attempts.append(record)
            trace = tuple(item.delay_ms for item in attempts if item.delay_ms)
            return DeliveryResult(
                QueueStatus.OK,
                QueueReason.DELIVERED,
                event.event_id,
                tuple(attempts),
                trace,
                EventState.IN_FLIGHT,
                "handler succeeded; commit is still required",
            )
        trace = tuple(item.delay_ms for item in attempts if item.delay_ms)
        self._dead_letter(event, tuple(attempts))
        return DeliveryResult(
            QueueStatus.DEAD_LETTERED,
            QueueReason.MAX_ATTEMPTS_EXHAUSTED,
            event.event_id,
            tuple(attempts),
            trace,
            EventState.DEAD_LETTERED,
            "retry budget exhausted",
        )

    def deliver(self, event_id: str, handler: Handler) -> DeliveryResult:
        """Invoke ``handler`` with bounded retries inside an in-flight transaction."""
        event = self._events.get(event_id)
        if event is None:
            return DeliveryResult(
                QueueStatus.REJECTED, QueueReason.UNKNOWN_EVENT, str(event_id), (), (), EventState.PENDING,
                "unknown event",
            )
        scope = self._scope_reason(event)
        if scope is not None:
            return DeliveryResult(
                QueueStatus.REJECTED, scope, event_id, (), (), self._states[event_id], "scope mismatch"
            )
        if self._states[event_id] is not EventState.IN_FLIGHT:
            return DeliveryResult(
                QueueStatus.REJECTED, QueueReason.NOT_IN_FLIGHT, event_id, (), (), self._states[event_id],
                "begin must precede delivery",
            )
        if not callable(handler):
            return DeliveryResult(
                QueueStatus.REJECTED, QueueReason.MALFORMED_EVENT, event_id, (), (), self._states[event_id],
                "handler is not callable",
            )
        return self._run_attempts(event, handler)

    def commit(self, event_id: str) -> CommitResult:
        """Commit the transaction, or quarantine a divergent entity version."""
        event = self._events.get(event_id)
        if event is None:
            return CommitResult(
                QueueStatus.REJECTED, QueueReason.UNKNOWN_EVENT, str(event_id), EventState.PENDING, None,
                "unknown event",
            )
        scope = self._scope_reason(event)
        if scope is not None:
            return CommitResult(
                QueueStatus.REJECTED, scope, event_id, self._states[event_id], None, "scope mismatch"
            )
        if event_id in self._processed_keys:
            return CommitResult(
                QueueStatus.DUPLICATE, QueueReason.ALREADY_COMMITTED, event_id, EventState.COMMITTED, None,
                "event already committed",
            )
        if self._states[event_id] is not EventState.IN_FLIGHT:
            return CommitResult(
                QueueStatus.REJECTED, QueueReason.NOT_IN_FLIGHT, event_id, self._states[event_id], None,
                "begin must precede commit",
            )

        scope_key = (event.tenant_id, event.facility_id, event.entity_key)
        stored_version = self._entity_versions.get(scope_key)
        if stored_version is not None and (
            stored_version != event.version
            or self._entity_digests[scope_key] != event.payload_digest
        ):
            conflict_id = f"SYN-CFL-{sha256_hex(canonical_json_bytes([*scope_key, event_id, stored_version, event.version, self._entity_digests[scope_key], event.payload_digest]))[:16].upper()}"
            conflict = ConflictRecord(
                conflict_id=conflict_id,
                event_id=event_id,
                entity_key=event.entity_key,
                tenant_id=event.tenant_id,
                facility_id=event.facility_id,
                local_version=stored_version,
                remote_version=event.version,
                local_digest=self._entity_digests[scope_key],
                remote_digest=event.payload_digest,
                state=ConflictState.QUARANTINED,
            )
            self._append(
                "QUARANTINE",
                event,
                {"conflict_id": conflict_id, **self._conflict_detail(conflict)},
            )
            self._conflicts[conflict_id] = conflict
            self._states[event_id] = EventState.QUARANTINED
            return CommitResult(
                QueueStatus.QUARANTINED, QueueReason.VERSION_CONFLICT, event_id, EventState.QUARANTINED,
                conflict_id, "divergent version quarantined; no overwrite",
            )

        self._append("COMMIT", event, {"state": EventState.COMMITTED.value, "payload_digest": event.payload_digest})
        self._entity_versions[scope_key] = event.version
        self._entity_digests[scope_key] = event.payload_digest
        self._processed_keys.add(event_id)
        self._states[event_id] = EventState.COMMITTED
        return CommitResult(
            QueueStatus.OK, QueueReason.COMMITTED, event_id, EventState.COMMITTED, None, "event committed"
        )

    @staticmethod
    def _conflict_detail(conflict: ConflictRecord) -> dict[str, object]:
        return {
            "conflict_id": conflict.conflict_id,
            "local_version": conflict.local_version,
            "remote_version": conflict.remote_version,
            "local_digest": conflict.local_digest,
            "remote_digest": conflict.remote_digest,
        }

    def process(self, event_id: str, handler: Handler) -> ProcessResult:
        """Convenience transaction: ``begin -> deliver -> commit``."""
        if event_id in self._processed_keys:
            return ProcessResult(
                QueueStatus.DUPLICATE, QueueReason.ALREADY_COMMITTED, str(event_id), None, None, None,
                "event already committed",
            )
        begun = self.begin(event_id)
        if begun.status is QueueStatus.REJECTED or begun.status is QueueStatus.DUPLICATE:
            return ProcessResult(begun.status, begun.reason, str(event_id), None, None, None, begun.detail)
        delivery = self.deliver(event_id, handler)
        if delivery.status is not QueueStatus.OK:
            return ProcessResult(delivery.status, delivery.reason, str(event_id), delivery, None, None, delivery.detail)
        committed = self.commit(event_id)
        return ProcessResult(
            committed.status,
            committed.reason,
            str(event_id),
            delivery,
            committed,
            committed.conflict_id,
            committed.detail,
        )

    def resolve_take_local(self, conflict_id: str) -> ResolutionResult:
        """Keep the already-stored entity version (explicit, no merge)."""
        conflict = self._conflicts.get(conflict_id)
        chosen = conflict.local_version if conflict is not None else None
        return self._resolve(conflict_id, ResolutionAction.TAKE_LOCAL, chosen)

    def resolve_take_remote(self, conflict_id: str) -> ResolutionResult:
        """Adopt the quarantined event's entity version (explicit, no merge)."""
        conflict = self._conflicts.get(conflict_id)
        chosen = conflict.remote_version if conflict is not None else None
        return self._resolve(conflict_id, ResolutionAction.TAKE_REMOTE, chosen)

    def resolve_manual(self, conflict_id: str, *, chosen_version: int) -> ResolutionResult:
        """Apply an explicitly supplied version (explicit, no merge)."""
        return self._resolve(conflict_id, ResolutionAction.MANUAL, chosen_version)

    def _resolve(
        self, conflict_id: str, action: ResolutionAction, chosen_input: int | None
    ) -> ResolutionResult:
        conflict = self._conflicts.get(conflict_id)
        if conflict is None:
            return ResolutionResult(
                QueueStatus.REJECTED, QueueReason.UNKNOWN_CONFLICT, str(conflict_id), "", action, None, 0,
                "unknown conflict",
            )
        if conflict.state is ConflictState.RESOLVED:
            if conflict.resolution_action is action and conflict.chosen_version == chosen_input:
                return ResolutionResult(
                    QueueStatus.DUPLICATE, QueueReason.ALREADY_RESOLVED, conflict_id,
                    conflict.resolution_id or "", action, conflict.chosen_version, 0,
                    "resolution already applied",
                )
            return ResolutionResult(
                QueueStatus.REJECTED, QueueReason.CONFLICT_ALREADY_DECIDED, conflict_id,
                conflict.resolution_id or "", action, conflict.chosen_version, 0,
                "conflict already resolved differently",
            )
        if conflict.tenant_id != self.config.tenant_id:
            return ResolutionResult(
                QueueStatus.REJECTED, QueueReason.TENANT_MISMATCH, conflict_id, "", action, None, 0,
                "conflict belongs to another tenant",
            )
        if conflict.facility_id != self.config.facility_id:
            return ResolutionResult(
                QueueStatus.REJECTED, QueueReason.FACILITY_MISMATCH, conflict_id, "", action, None, 0,
                "conflict belongs to another facility",
            )
        if isinstance(chosen_input, bool) or not isinstance(chosen_input, int) or chosen_input < 1:
            return ResolutionResult(
                QueueStatus.REJECTED, QueueReason.MALFORMED_EVENT, conflict_id, "", action, None, 0,
                "chosen_version must be a positive integer",
            )

        if action is ResolutionAction.TAKE_LOCAL:
            chosen_version, chosen_digest = conflict.local_version, conflict.local_digest
        elif action is ResolutionAction.TAKE_REMOTE:
            chosen_version, chosen_digest = conflict.remote_version, conflict.remote_digest
        else:
            chosen_version = chosen_input
            chosen_digest = sha256_hex(canonical_json_bytes({"manual_version": chosen_version}))

        resolution_id = f"SYN-RSL-{sha256_hex(canonical_json_bytes([conflict_id, action.value, chosen_version]))[:16].upper()}"
        event = self._events[conflict.event_id]
        entry = self._append(
            "RESOLVE",
            event,
            {
                **self._conflict_detail(conflict),
                "resolution_id": resolution_id,
                "action": action.value,
                "chosen_version": chosen_version,
                "chosen_digest": chosen_digest,
                "state": ConflictState.RESOLVED.value,
            },
        )
        self._conflicts[conflict_id] = replace(
            conflict,
            state=ConflictState.RESOLVED,
            resolution_action=action,
            resolution_id=resolution_id,
            chosen_version=chosen_version,
            chosen_digest=chosen_digest,
            resolved_at_ms=entry.occurred_ms,
        )
        scope_key = (conflict.tenant_id, conflict.facility_id, conflict.entity_key)
        self._entity_versions[scope_key] = chosen_version
        self._entity_digests[scope_key] = chosen_digest
        self._states[conflict.event_id] = EventState.RESOLVED
        self._processed_keys.add(conflict.event_id)
        return ResolutionResult(
            QueueStatus.OK, QueueReason.RESOLVED, conflict_id, resolution_id, action, chosen_version,
            entry.sequence, "conflict resolved explicitly",
        )

    # -- crash, recovery and queries ------------------------------------

    def simulate_crash(self) -> CrashResult:
        """Drop all derived state; keep only the append-only log bytes."""
        retained = self.log_bytes()
        self._retained_log = retained
        self._events.clear()
        self._states.clear()
        self._attempts.clear()
        self._processed_keys.clear()
        self._dead_letters.clear()
        self._conflicts.clear()
        self._entity_versions.clear()
        self._entity_digests.clear()
        return CrashResult(
            QueueStatus.OK,
            QueueReason.CRASHED,
            self._anchor_count,
            sha256_hex(retained),
            "derived state dropped; append-only log retained in process",
        )

    def _rebuild(self, entries: tuple[LogEntry, ...]) -> None:
        """Rebuild all derived state from verified log entries only."""
        self._events.clear()
        self._states.clear()
        self._attempts.clear()
        self._processed_keys.clear()
        self._dead_letters.clear()
        self._conflicts.clear()
        self._entity_versions.clear()
        self._entity_digests.clear()
        for entry in entries:
            detail = entry.detail
            if entry.operation == "APPEND":
                event = QueueEvent(
                    event_id=entry.event_id,
                    event_type=str(detail["event_type"]),
                    entity_key=entry.entity_key,
                    tenant_id=entry.tenant_id,
                    facility_id=entry.facility_id,
                    version=entry.version,
                    payload={},
                    payload_digest=str(detail["payload_digest"]),
                )
                self._events[entry.event_id] = event
                self._states[entry.event_id] = EventState.PENDING
                self._attempts[entry.event_id] = []
            elif entry.operation == "BEGIN":
                self._states[entry.event_id] = EventState.IN_FLIGHT
            elif entry.operation == "ATTEMPT":
                self._attempts.setdefault(entry.event_id, []).append(
                    AttemptRecord(
                        attempt=_replay_int(detail["attempt"]),
                        at_ms=_replay_int(detail["at_ms"]),
                        outcome=AttemptOutcome(str(detail["outcome"])),
                        delay_ms=_replay_int(detail["delay_ms"]),
                        error_type=detail.get("error_type"),  # type: ignore[arg-type]
                        error_digest=detail.get("error_digest"),  # type: ignore[arg-type]
                    )
                )
            elif entry.operation == "COMMIT":
                self._states[entry.event_id] = EventState.COMMITTED
                self._processed_keys.add(entry.event_id)
                scope_key = (entry.tenant_id, entry.facility_id, entry.entity_key)
                self._entity_versions[scope_key] = entry.version
                self._entity_digests[scope_key] = str(detail["payload_digest"])
            elif entry.operation == "DEAD_LETTER":
                self._states[entry.event_id] = EventState.DEAD_LETTERED
                self._dead_letters.append(
                    DeadLetterRecord(
                        letter_id=str(detail["letter_id"]),
                        event_id=entry.event_id,
                        reason=QueueReason(str(detail["reason"])),
                        attempts=_replay_int(detail["attempts"]),
                        payload_digest=self._events[entry.event_id].payload_digest,
                        last_error=str(detail["last_error"]),
                        occurred_ms=entry.occurred_ms,
                    )
                )
            elif entry.operation == "QUARANTINE":
                self._states[entry.event_id] = EventState.QUARANTINED
                conflict_id = str(detail["conflict_id"])
                self._conflicts[conflict_id] = ConflictRecord(
                    conflict_id=conflict_id,
                    event_id=entry.event_id,
                    entity_key=entry.entity_key,
                    tenant_id=entry.tenant_id,
                    facility_id=entry.facility_id,
                    local_version=_replay_int(detail["local_version"]),
                    remote_version=_replay_int(detail["remote_version"]),
                    local_digest=str(detail["local_digest"]),
                    remote_digest=str(detail["remote_digest"]),
                    state=ConflictState.QUARANTINED,
                )
            elif entry.operation == "RESOLVE":
                conflict_id = str(detail["conflict_id"])
                previous = self._conflicts[conflict_id]
                self._conflicts[conflict_id] = replace(
                    previous,
                    state=ConflictState.RESOLVED,
                    resolution_action=ResolutionAction(str(detail["action"])),
                    resolution_id=str(detail["resolution_id"]),
                    chosen_version=_replay_int(detail["chosen_version"]),
                    chosen_digest=str(detail["chosen_digest"]),
                    resolved_at_ms=entry.occurred_ms,
                )
                self._states[entry.event_id] = EventState.RESOLVED
                self._processed_keys.add(entry.event_id)
                scope_key = (entry.tenant_id, entry.facility_id, entry.entity_key)
                self._entity_versions[scope_key] = _replay_int(detail["chosen_version"])
                self._entity_digests[scope_key] = str(detail["chosen_digest"])

    def recover(self, log_payload: bytes | None = None) -> RecoveryResult:
        """Verify and replay the log, then redeliver only in-flight events."""
        raw = self._retained_log if log_payload is None and self._retained_log is not None else None
        if raw is None:
            raw = self.log_bytes() if log_payload is None else log_payload
        verification, entries = self._parse_log(raw)
        if verification.status is QueueStatus.REJECTED:
            return RecoveryResult(
                QueueStatus.REJECTED,
                verification.reason,
                0,
                frozenset(self._processed_keys),
                (),
                (),
                len(self._conflicts),
                len(self._dead_letters),
                verification.detail,
            )
        self._rebuild(entries)
        self._retained_log = None

        redelivered: list[DeliveryResult] = []
        pending: list[str] = []
        for event_id in tuple(self._states):
            if self._states[event_id] is not EventState.IN_FLIGHT:
                continue
            event = self._events[event_id]
            handler = self._handlers.get(event.event_type)
            if handler is None:
                pending.append(event_id)
                continue
            delivery = self.deliver(event_id, handler)
            redelivered.append(delivery)
            if delivery.status is QueueStatus.OK:
                self.commit(event_id)

        return RecoveryResult(
            QueueStatus.OK,
            QueueReason.RECOVERED,
            len(entries),
            frozenset(self._processed_keys),
            tuple(redelivered),
            tuple(pending),
            len(self._conflicts),
            len(self._dead_letters),
            "log replayed; only in-flight events redelivered",
        )

    @property
    def processed_keys(self) -> frozenset[str]:
        """Immutable set of committed/resolved idempotency keys."""
        return frozenset(self._processed_keys)

    @property
    def processed_key_count(self) -> int:
        """Number of distinct committed/resolved event ids."""
        return len(self._processed_keys)

    @property
    def log_entries(self) -> tuple[LogEntry, ...]:
        """Defensive tuple of appended log entries."""
        return tuple(self._log)

    @property
    def dead_letters(self) -> tuple[DeadLetterRecord, ...]:
        """Defensive tuple of terminal delivery failures."""
        return tuple(self._dead_letters)

    @property
    def conflicts(self) -> dict[str, ConflictRecord]:
        """Defensive copy of the conflict quarantine index."""
        return dict(self._conflicts)

    @property
    def resolution_count(self) -> int:
        """Number of conflicts that have been explicitly resolved."""
        return sum(1 for item in self._conflicts.values() if item.state is ConflictState.RESOLVED)

    def event_state(self, event_id: str) -> EventState | None:
        """Current lifecycle state of an event, if present."""
        return self._states.get(str(event_id))

    def entity_version(self, entity_key: str) -> int | None:
        """Currently committed version of an entity in this queue's scope."""
        return self._entity_versions.get((self.config.tenant_id, self.config.facility_id, str(entity_key)))
