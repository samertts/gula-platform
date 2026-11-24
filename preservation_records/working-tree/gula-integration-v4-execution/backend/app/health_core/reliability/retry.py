"""Bounded, deterministic retry with jitter-free backoff and a dead-letter queue.

Delays are computed and reported, never slept: this is an isolated design harness,
not a runtime executor. Outcomes are deterministic for a given policy and failure
pattern, and terminal failures are recorded as synthetic dead-letter entries.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum

from app.health_core.common.errors import InvalidSyntheticReferenceError
from app.health_core.reliability.hashing import (
    canonical_json_bytes,
    require_synthetic_id,
    sha256_hex,
)

Operation = Callable[[], str]
OPERATION_ID_PREFIX = "SYN-OP-"


class RetryStatus(StrEnum):
    """Terminal outcome of an executed operation."""

    SUCCEEDED = "succeeded"
    DEAD_LETTERED = "dead_lettered"


@dataclass(frozen=True, slots=True)
class BackoffPolicy:
    """Jitter-free exponential backoff with a cap and a hard attempt limit."""

    base_delay_ms: int = 2
    multiplier: int = 2
    max_delay_ms: int = 8
    max_attempts: int = 4

    def __post_init__(self) -> None:
        if self.base_delay_ms < 1 or self.multiplier < 1 or self.max_delay_ms < 1:
            raise ValueError("backoff delays and multiplier must be positive")
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")

    def delay_for(self, attempt: int) -> int:
        """Delay after failed 1-based ``attempt``; zero after the final attempt."""
        if attempt < 1 or attempt >= self.max_attempts:
            return 0
        delay = self.base_delay_ms
        for _ in range(attempt - 1):
            delay = min(delay * self.multiplier, self.max_delay_ms)
        return delay

    def planned_delays(self) -> tuple[int, ...]:
        """All delays the policy would apply across its full attempt budget."""
        return tuple(self.delay_for(attempt) for attempt in range(1, self.max_attempts))


@dataclass(frozen=True, slots=True)
class RetryOutcome:
    """Full record of attempts, planned delays and terminal status."""

    operation_id: str
    status: RetryStatus
    attempts: int
    delays_ms: tuple[int, ...]
    result: str | None
    last_error: str | None


@dataclass(frozen=True, slots=True)
class DeadLetterEntry:
    """Immutable terminal-failure record; payload is reduced to a digest."""

    letter_id: str
    operation_id: str
    attempts: int
    reason: str
    last_error: str
    payload_digest: str


class RetryExecutor:
    """Execute synthetic operations with bounded retries and dead-lettering."""

    def __init__(self, policy: BackoffPolicy | None = None) -> None:
        self.policy = policy if policy is not None else BackoffPolicy()
        self._dead_letters: list[DeadLetterEntry] = []

    def execute(
        self,
        operation_id: str,
        operation: Operation,
        *,
        payload: dict[str, object] | None = None,
    ) -> RetryOutcome:
        """Call ``operation`` up to ``max_attempts`` times, then dead-letter."""
        safe_id = require_synthetic_id(operation_id, field="operation_id")
        if not isinstance(operation_id, str) or not operation_id.startswith(OPERATION_ID_PREFIX):
            raise InvalidSyntheticReferenceError(
                f"operation_id must start with {OPERATION_ID_PREFIX}",
                details={"field": "operation_id"},
            )
        payload_digest = sha256_hex(canonical_json_bytes(payload or {}))
        delays: list[int] = []
        last_error = ""
        for attempt in range(1, self.policy.max_attempts + 1):
            try:
                result = operation()
            except Exception as exc:
                last_error = f"{type(exc).__name__}: {exc}"
                delay = self.policy.delay_for(attempt)
                if delay:
                    delays.append(delay)
                continue
            return RetryOutcome(
                operation_id=safe_id,
                status=RetryStatus.SUCCEEDED,
                attempts=attempt,
                delays_ms=tuple(delays),
                result=result,
                last_error=None,
            )
        letter = DeadLetterEntry(
            letter_id=f"SYN-DLQ-{sha256_hex(canonical_json_bytes([safe_id, last_error]))[:16].upper()}",
            operation_id=safe_id,
            attempts=self.policy.max_attempts,
            reason="max_attempts_exhausted",
            last_error=last_error,
            payload_digest=payload_digest,
        )
        self._dead_letters.append(letter)
        return RetryOutcome(
            operation_id=safe_id,
            status=RetryStatus.DEAD_LETTERED,
            attempts=self.policy.max_attempts,
            delays_ms=tuple(delays),
            result=None,
            last_error=last_error,
        )

    @property
    def dead_letters(self) -> tuple[DeadLetterEntry, ...]:
        """Defensive tuple of terminal failures in occurrence order."""
        return tuple(self._dead_letters)
