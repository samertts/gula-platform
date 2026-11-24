"""Synthetic-key idempotent processing with structured conflict reporting.

An identical replay returns the original effect without creating a second one.
Reusing a key with a different request fingerprint is a structured 409-style error,
never a silent overwrite. All keys and effects are synthetic ``SYN-`` values.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.health_core.common.errors import InvalidSyntheticReferenceError
from app.health_core.reliability.errors import IdempotencyConflictError
from app.health_core.reliability.hashing import canonical_json_bytes, sha256_hex

KEY_PREFIX = "SYN-KEY-"
EFFECT_PREFIX = "SYN-EFF-"


class ProcessStatus(StrEnum):
    """Whether this call created a new effect or replayed an existing one."""

    NEW = "new"
    DUPLICATE = "duplicate"


@dataclass(frozen=True, slots=True)
class ProcessingRecord:
    """The immutable record stored the first time a key is processed."""

    key: str
    fingerprint: str
    effect_id: str


@dataclass(frozen=True, slots=True)
class ProcessingResult:
    """Outcome of one processing call."""

    key: str
    status: ProcessStatus
    effect_id: str
    fingerprint: str
    effect_count: int


class IdempotentProcessor:
    """Process synthetic requests at most once per idempotency key."""

    def __init__(self) -> None:
        self._records: dict[str, ProcessingRecord] = {}
        self._effects: list[str] = []

    @staticmethod
    def _check_key(key: object) -> str:
        if not isinstance(key, str) or not key.startswith(KEY_PREFIX) or len(key) <= len(KEY_PREFIX):
            raise InvalidSyntheticReferenceError(
                f"idempotency key must start with {KEY_PREFIX}", details={"field": "key"}
            )
        return key

    def process(self, key: str, payload: dict[str, object]) -> ProcessingResult:
        """Return the original effect for a replay, or record a new effect."""
        safe_key = self._check_key(key)
        if not isinstance(payload, dict):
            raise InvalidSyntheticReferenceError("payload must be an object", details={"field": "payload"})
        fingerprint = sha256_hex(canonical_json_bytes(payload))
        existing = self._records.get(safe_key)
        if existing is not None:
            if existing.fingerprint != fingerprint:
                raise IdempotencyConflictError(
                    "idempotency key reused with a different request fingerprint",
                    details={
                        "key": safe_key,
                        "expected_fingerprint": existing.fingerprint,
                        "observed_fingerprint": fingerprint,
                    },
                )
            return ProcessingResult(
                key=safe_key,
                status=ProcessStatus.DUPLICATE,
                effect_id=existing.effect_id,
                fingerprint=fingerprint,
                effect_count=len(self._effects),
            )
        effect_id = f"{EFFECT_PREFIX}{sha256_hex(canonical_json_bytes([safe_key, fingerprint]))[:16].upper()}"
        self._records[safe_key] = ProcessingRecord(
            key=safe_key, fingerprint=fingerprint, effect_id=effect_id
        )
        self._effects.append(effect_id)
        return ProcessingResult(
            key=safe_key,
            status=ProcessStatus.NEW,
            effect_id=effect_id,
            fingerprint=fingerprint,
            effect_count=len(self._effects),
        )

    @property
    def effect_count(self) -> int:
        """Number of distinct effects created (replays never increment this)."""
        return len(self._effects)

    @property
    def effects(self) -> tuple[str, ...]:
        """Defensive tuple of created effect ids."""
        return tuple(self._effects)

    @property
    def records(self) -> tuple[ProcessingRecord, ...]:
        """Defensive tuple of processing records in first-seen order."""
        return tuple(self._records.values())
