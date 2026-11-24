"""In-memory durable store with write-ahead logging and atomic snapshots.

This is an isolated design, not a persistence implementation for production. It
demonstrates WAL ordering (log before applying), atomic checkpointing, checksummed
JSON snapshots and deterministic recovery after a simulated in-process restart.
There is no filesystem, database, network or real patient data.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from app.health_core.reliability.errors import ChecksumMismatchError, InvalidStoreValueError
from app.health_core.reliability.hashing import (
    canonical_json_bytes,
    decode_checked_envelope,
    require_synthetic_id,
    sealed_envelope,
    sha256_hex,
)

SNAPSHOT_SCHEMA = "gula-reliability-snapshot-v1"
WAL_SCHEMA = "gula-reliability-wal-v1"


@dataclass(frozen=True, slots=True)
class WALRecord:
    """One checksummed, sequenced write-ahead record."""

    sequence: int
    operation: str
    key: str
    value: dict[str, object] | None
    checksum: str

    def __post_init__(self) -> None:
        if self.sequence < 1:
            raise InvalidStoreValueError("WAL sequence must start at 1")
        if self.operation not in ("put", "delete"):
            raise InvalidStoreValueError("WAL operation must be 'put' or 'delete'")
        expected = sha256_hex(
            canonical_json_bytes(_record_body(self.sequence, self.operation, self.key, self.value))
        )
        if self.checksum != expected:
            raise ChecksumMismatchError("WAL record checksum mismatch")


def _record_body(
    sequence: int, operation: str, key: str, value: dict[str, object] | None
) -> dict[str, object]:
    return {"sequence": sequence, "operation": operation, "key": key, "value": value}


def make_wal_record(
    sequence: int, operation: str, key: str, value: dict[str, object] | None
) -> WALRecord:
    """Build a WAL record with a freshly computed checksum."""
    body = _record_body(sequence, operation, key, value)
    return WALRecord(sequence=sequence, operation=operation, key=key, value=value,
                     checksum=sha256_hex(canonical_json_bytes(body)))


def validate_snapshot(payload: bytes) -> None:
    """Raise a structured error unless ``payload`` is a well-formed snapshot."""
    _decode_snapshot(payload)


def _decode_snapshot(payload: bytes) -> dict[str, object]:
    body = decode_checked_envelope(payload, schema=SNAPSHOT_SCHEMA, label="snapshot")
    state = body.get("state")
    sequence = body.get("sequence")
    if not isinstance(state, dict) or not isinstance(sequence, int) or sequence < 0:
        raise ChecksumMismatchError("snapshot state or sequence is malformed")
    for key, value in state.items():
        if not isinstance(key, str) or not isinstance(value, dict):
            raise ChecksumMismatchError("snapshot state must map keys to objects")
    return body


def _decode_wal(payload: bytes) -> dict[str, object]:
    return decode_checked_envelope(payload, schema=WAL_SCHEMA, label="wal")


class DurableStore(Protocol):
    """The minimal contract a backup/restart workflow requires from a store."""

    def put(self, key: str, value: dict[str, object]) -> None: ...

    def delete(self, key: str) -> None: ...

    def get(self, key: str) -> dict[str, object] | None: ...

    def commit(self) -> bytes: ...

    def snapshot_bytes(self) -> bytes: ...

    def wal_bytes(self) -> bytes: ...

    def restore(self, snapshot: bytes) -> None: ...

    def simulate_restart(self) -> DurableStore: ...

    @property
    def data(self) -> dict[str, dict[str, object]]: ...

    @property
    def committed_data(self) -> dict[str, dict[str, object]]: ...


class InMemoryWALStore:
    """A process-local WAL store used only for isolated reliability testing."""

    def __init__(self) -> None:
        self._committed: dict[str, dict[str, object]] = {}
        self._working: dict[str, dict[str, object]] = {}
        self._wal: list[WALRecord] = []
        self._sequence = 0
        self._committed_sequence = 0
        self._snapshot = self._encode_snapshot()

    def _encode_snapshot(self) -> bytes:
        body: dict[str, object] = {
            "schema": SNAPSHOT_SCHEMA,
            "sequence": self._committed_sequence,
            "state": {key: dict(value) for key, value in self._committed.items()},
        }
        return canonical_json_bytes(sealed_envelope(body))

    @staticmethod
    def _check_key(key: object) -> str:
        """Accept only real ``SYN-`` keys, never empty or real-looking identifiers."""
        return require_synthetic_id(key, field="key")

    @staticmethod
    def _check_value(value: object, *, key: str) -> dict[str, object]:
        if not isinstance(value, dict):
            raise InvalidStoreValueError("store value must be an object", details={"key": key})
        try:
            canonical_json_bytes(value)
        except (TypeError, ValueError) as exc:
            raise InvalidStoreValueError(
                "store value must be JSON-serialisable", details={"key": key}
            ) from exc
        return {str(item_key): item_value for item_key, item_value in value.items()}

    def put(self, key: str, value: dict[str, object]) -> None:
        """Append a WAL record first, then expose the write in the working view."""
        safe_key = self._check_key(key)
        safe_value = self._check_value(value, key=safe_key)
        # Write-ahead: the durable record is created before the working copy changes.
        self._sequence += 1
        record = make_wal_record(self._sequence, "put", safe_key, safe_value)
        self._wal.append(record)
        self._working[safe_key] = dict(safe_value)

    def delete(self, key: str) -> None:
        """Append a delete record and remove the key from the working view."""
        safe_key = self._check_key(key)
        if safe_key not in self._working:
            raise InvalidStoreValueError("cannot delete an unknown key", details={"key": safe_key})
        self._sequence += 1
        self._wal.append(make_wal_record(self._sequence, "delete", safe_key, None))
        del self._working[safe_key]

    def get(self, key: str) -> dict[str, object] | None:
        """Return a defensive copy of the current working value, if present."""
        value = self._working.get(self._check_key(key))
        return None if value is None else dict(value)

    @property
    def data(self) -> dict[str, dict[str, object]]:
        """Defensive copy of the current working state."""
        return {key: dict(value) for key, value in self._working.items()}

    @property
    def committed_data(self) -> dict[str, dict[str, object]]:
        """Defensive copy of the last checkpointed state."""
        return {key: dict(value) for key, value in self._committed.items()}

    @property
    def sequence(self) -> int:
        """Monotonic write sequence (committed writes plus WAL writes)."""
        return self._sequence

    def commit(self) -> bytes:
        """Atomically checkpoint the working state into a new snapshot."""
        # Build the complete snapshot first; only then swap state and clear the WAL.
        candidate = {key: dict(value) for key, value in self._working.items()}
        candidate_sequence = self._sequence
        body: dict[str, object] = {
            "schema": SNAPSHOT_SCHEMA,
            "sequence": candidate_sequence,
            "state": candidate,
        }
        encoded = canonical_json_bytes(sealed_envelope(body))
        self._committed = candidate
        self._committed_sequence = candidate_sequence
        self._snapshot = encoded
        self._wal.clear()
        return encoded

    def snapshot_bytes(self) -> bytes:
        """Return the last committed snapshot bytes."""
        return self._snapshot

    def wal_bytes(self) -> bytes:
        """Return checksummed WAL bytes, or ``b""`` when the WAL is empty.

        ``record_count`` and ``last_sequence`` are authoritative terminal anchors
        sourced from the live WAL bookkeeping, not from the serialised records. A
        truncate-and-rechecksum attacker who leaves them stale cannot produce a
        valid shorter WAL.
        """
        if not self._wal:
            return b""
        body: dict[str, object] = {
            "schema": WAL_SCHEMA,
            "base_sequence": self._committed_sequence,
            "record_count": len(self._wal),
            "last_sequence": self._sequence,
            "records": [
                {
                    "sequence": record.sequence,
                    "operation": record.operation,
                    "key": record.key,
                    "value": record.value,
                    "checksum": record.checksum,
                }
                for record in self._wal
            ],
        }
        return canonical_json_bytes(sealed_envelope(body))

    def restore(self, snapshot: bytes) -> None:
        """Replace all state with a checksummed snapshot (clears the WAL)."""
        body = _decode_snapshot(snapshot)
        state = body["state"]
        sequence = body["sequence"]
        if not isinstance(state, dict) or not isinstance(sequence, int):
            raise ChecksumMismatchError("snapshot state or sequence is malformed")
        restored = {str(key): dict(value) for key, value in state.items()}
        self._committed = restored
        self._working = {key: dict(value) for key, value in restored.items()}
        self._wal.clear()
        self._sequence = sequence
        self._committed_sequence = sequence
        self._snapshot = self._encode_snapshot()

    def _replay_wal(self, payload: bytes) -> None:
        if not payload:
            return
        body = _decode_wal(payload)
        base_sequence = body.get("base_sequence")
        records = body.get("records")
        if not isinstance(base_sequence, int) or not isinstance(records, list):
            raise ChecksumMismatchError("WAL envelope is malformed")
        if base_sequence != self._committed_sequence:
            raise ChecksumMismatchError("WAL base sequence does not match the snapshot")
        record_count = body.get("record_count")
        last_sequence = body.get("last_sequence")
        if (
            not isinstance(record_count, int)
            or isinstance(record_count, bool)
            or not isinstance(last_sequence, int)
            or isinstance(last_sequence, bool)
        ):
            raise ChecksumMismatchError("WAL terminal anchors are missing or malformed")
        if record_count != len(records):
            raise ChecksumMismatchError("WAL record count does not match its records")
        if last_sequence != base_sequence + record_count:
            raise ChecksumMismatchError("WAL last sequence does not match its terminal anchors")
        replayed: list[WALRecord] = []
        expected = base_sequence + 1
        for raw in records:
            if not isinstance(raw, dict):
                raise ChecksumMismatchError("WAL record is malformed")
            record = make_wal_record(
                sequence=raw["sequence"] if isinstance(raw.get("sequence"), int) else 0,
                operation=str(raw.get("operation", "")),
                key=str(raw.get("key", "")),
                value=raw.get("value") if isinstance(raw.get("value"), dict) else None,
            )
            supplied = raw.get("checksum")
            if supplied != record.checksum:
                raise ChecksumMismatchError("WAL record checksum mismatch")
            if record.sequence != expected:
                raise ChecksumMismatchError("WAL record sequence is not contiguous")
            if record.operation == "put":
                if record.value is None:
                    raise ChecksumMismatchError("WAL put record has no value")
                self._working[record.key] = dict(record.value)
            else:
                self._working.pop(record.key, None)
            replayed.append(record)
            expected += 1
        if replayed and replayed[-1].sequence != last_sequence:
            raise ChecksumMismatchError("WAL terminal record does not match last_sequence")
        self._wal = replayed
        self._sequence = expected - 1

    @classmethod
    def restore_from(cls, snapshot: bytes, wal: bytes = b"") -> InMemoryWALStore:
        """Restore a fresh store from a snapshot and optional WAL tail."""
        store = cls()
        store.restore(snapshot)
        store._replay_wal(wal)
        return store

    def simulate_restart(self) -> InMemoryWALStore:
        """Return a fresh store recovered from this store's snapshot plus WAL.

        A crash before ``commit`` loses nothing that was already written to the WAL;
        a crash after ``commit`` restores the checkpointed snapshot exactly.
        """
        return self.restore_from(self._snapshot, self.wal_bytes())
