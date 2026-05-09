"""Failure-isolation primitives for institutional adapters.

Pure-Python (stdlib only) helpers used by adapter implementations:

- ``CircuitBreaker`` — closed/open/half-open state machine
- ``RetryPolicy`` — bounded exponential backoff with jitter
- ``retry_with_backoff`` — apply a ``RetryPolicy`` to an awaitable

These are intentionally simple; they exist to keep the adapter contract
self-contained without pulling a third-party resilience library. Adapters
running in production may choose richer primitives, but they MUST honor
the same fail-closed semantics.

See ``docs/sovereign/phase16-interoperability/01-architecture.md``
("Failure Isolation").
"""

from __future__ import annotations

import asyncio
import random
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Awaitable, Callable, TypeVar


class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


T = TypeVar("T")


class CircuitBreaker:
    """Per-adapter circuit breaker.

    A breaker tracks consecutive failures and opens after
    ``open_threshold_failures``. While open, calls are short-circuited
    (the caller raises). After ``half_open_after_s`` seconds a single
    probe call is allowed; success closes the breaker, failure re-opens.

    Thread-safety: this implementation is single-event-loop safe; do not
    share an instance across threads without external locking.
    """

    def __init__(
        self,
        *,
        open_threshold_failures: int = 5,
        half_open_after_s: float = 60.0,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if open_threshold_failures < 1:
            raise ValueError("open_threshold_failures must be >= 1")
        if half_open_after_s < 0:
            raise ValueError("half_open_after_s must be >= 0")
        self._threshold = open_threshold_failures
        self._half_open_after_s = half_open_after_s
        self._clock = clock
        self._state: CircuitState = CircuitState.CLOSED
        self._failures: int = 0
        self._opened_at: float = 0.0

    @property
    def state(self) -> CircuitState:
        return self._state

    def allows(self) -> bool:
        """Return True iff a call is allowed at the current state."""
        if self._state is CircuitState.OPEN:
            if self._clock() - self._opened_at >= self._half_open_after_s:
                self._state = CircuitState.HALF_OPEN
                return True
            return False
        return True

    def record_success(self) -> None:
        self._failures = 0
        self._state = CircuitState.CLOSED

    def record_failure(self) -> None:
        if self._state is CircuitState.HALF_OPEN:
            self._open()
            return
        self._failures += 1
        if self._failures >= self._threshold:
            self._open()

    def _open(self) -> None:
        self._state = CircuitState.OPEN
        self._opened_at = self._clock()


@dataclass(frozen=True)
class RetryPolicy:
    """Bounded exponential backoff with jitter.

    ``initial_ms`` is the first delay. Each retry doubles the delay up to
    ``max_ms``. Jitter is uniform in ``[0, current_delay]`` to avoid
    synchronised retry storms across replicas.
    """

    max_retries: int = 5
    initial_ms: int = 200
    max_ms: int = 30_000
    jitter: bool = True


async def retry_with_backoff(
    op: Callable[[], Awaitable[T]],
    policy: RetryPolicy,
    *,
    is_retriable: Callable[[BaseException], bool] = lambda _e: True,
    rng: random.Random | None = None,
) -> T:
    """Run ``op`` with retries per ``policy``.

    The last exception is re-raised if all retries are exhausted. Callers
    are expected to wrap ``op`` to translate domain errors into either
    retriable or non-retriable exceptions via ``is_retriable``.
    """
    rng = rng or random.Random()
    delay_ms = policy.initial_ms
    last: BaseException | None = None
    for attempt in range(policy.max_retries + 1):
        try:
            return await op()
        except BaseException as exc:  # noqa: BLE001 — caller decides retriable
            last = exc
            if attempt >= policy.max_retries or not is_retriable(exc):
                raise
            sleep_ms = (
                rng.uniform(0, delay_ms) if policy.jitter else float(delay_ms)
            )
            await asyncio.sleep(sleep_ms / 1000.0)
            delay_ms = min(delay_ms * 2, policy.max_ms)
    # Defensive — unreachable because the loop always raises or returns.
    assert last is not None
    raise last
