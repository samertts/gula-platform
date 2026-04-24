"""Resilience utilities — retry, timeout, and safe-call helpers.

Designed for service-to-service calls and external integrations.
All helpers are pure functions with no global state, making them safe for
concurrent use and straightforward to unit-test.

Usage:
    # Retry an async call up to 3 times with exponential backoff
    result = await retry_async(call_insurance_api, url, max_attempts=3)

    # Wrap a sync call with timeout protection
    result = call_with_timeout(expensive_db_query, timeout=5.0)

    # Safe call that returns a default on failure (never raises)
    result = safe_call(risky_operation, default=None)
"""
from __future__ import annotations

import asyncio
import functools
import logging
import time
from typing import Any, Callable, TypeVar

logger = logging.getLogger("gula.resilience")

T = TypeVar("T")

# ── Retry configuration defaults ─────────────────────────────────────────────
_DEFAULT_MAX_ATTEMPTS = 3
_DEFAULT_BASE_DELAY   = 0.5   # seconds
_DEFAULT_MAX_DELAY    = 30.0  # seconds cap
_DEFAULT_BACKOFF      = 2.0   # exponential multiplier


# ── Sync retry decorator ──────────────────────────────────────────────────────

def retry(
    max_attempts: int = _DEFAULT_MAX_ATTEMPTS,
    base_delay:   float = _DEFAULT_BASE_DELAY,
    max_delay:    float = _DEFAULT_MAX_DELAY,
    backoff:      float = _DEFAULT_BACKOFF,
    exceptions:   tuple = (Exception,),
    on_retry:     Callable | None = None,
):
    """Decorator: retry a synchronous function on failure with exponential backoff.

    Args:
        max_attempts: Total call attempts (1 = no retry).
        base_delay:   Initial sleep between attempts (seconds).
        max_delay:    Maximum sleep cap (seconds).
        backoff:      Multiplier applied to delay each attempt.
        exceptions:   Only retry on these exception types.
        on_retry:     Optional callback(attempt, exc) called before each retry.

    Example:
        @retry(max_attempts=3, exceptions=(IOError, TimeoutError))
        def fetch_nid(nid: str) -> dict:
            return requests.get(f"{NID_API}/lookup/{nid}").json()
    """
    def decorator(fn: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs) -> T:
            delay = base_delay
            last_exc: Exception | None = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return fn(*args, **kwargs)
                except exceptions as exc:
                    last_exc = exc
                    if attempt == max_attempts:
                        logger.error(
                            "[RETRY] %s failed after %d attempts: %s",
                            fn.__qualname__, max_attempts, exc,
                        )
                        raise
                    sleep_for = min(delay, max_delay)
                    logger.warning(
                        "[RETRY] %s attempt %d/%d failed: %s — retrying in %.1fs",
                        fn.__qualname__, attempt, max_attempts, exc, sleep_for,
                    )
                    if on_retry:
                        try:
                            on_retry(attempt, exc)
                        except Exception:
                            pass
                    time.sleep(sleep_for)
                    delay *= backoff
            raise last_exc  # unreachable, satisfies type checker
        return wrapper
    return decorator


# ── Async retry decorator ─────────────────────────────────────────────────────

def retry_async(
    max_attempts: int = _DEFAULT_MAX_ATTEMPTS,
    base_delay:   float = _DEFAULT_BASE_DELAY,
    max_delay:    float = _DEFAULT_MAX_DELAY,
    backoff:      float = _DEFAULT_BACKOFF,
    exceptions:   tuple = (Exception,),
):
    """Decorator: retry an async function on failure with exponential backoff.

    Example:
        @retry_async(max_attempts=3, exceptions=(httpx.TransportError,))
        async def post_to_insurance(payload: dict) -> dict:
            async with httpx.AsyncClient(timeout=5) as c:
                r = await c.post(INSURANCE_URL, json=payload)
                r.raise_for_status()
                return r.json()
    """
    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(fn)
        async def wrapper(*args, **kwargs) -> Any:
            delay = base_delay
            last_exc: Exception | None = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return await fn(*args, **kwargs)
                except exceptions as exc:
                    last_exc = exc
                    if attempt == max_attempts:
                        logger.error(
                            "[RETRY-ASYNC] %s failed after %d attempts: %s",
                            fn.__qualname__, max_attempts, exc,
                        )
                        raise
                    sleep_for = min(delay, max_delay)
                    logger.warning(
                        "[RETRY-ASYNC] %s attempt %d/%d failed: %s — retrying in %.1fs",
                        fn.__qualname__, attempt, max_attempts, exc, sleep_for,
                    )
                    await asyncio.sleep(sleep_for)
                    delay *= backoff
            raise last_exc
        return wrapper
    return decorator


# ── Safe call (never raises) ──────────────────────────────────────────────────

def safe_call(fn: Callable[..., T], *args, default: T | None = None, **kwargs) -> T | None:
    """Call fn(*args, **kwargs) and return default on ANY exception.

    Use for non-critical enrichment paths where a failure should degrade
    gracefully rather than surface as an error.

    Example:
        citizen_ulid = safe_call(mint_citizen, db, full_name=name, default=None)
    """
    try:
        return fn(*args, **kwargs)
    except Exception as exc:
        logger.debug("[SAFE-CALL] %s raised %s — returning default", fn.__qualname__, exc)
        return default


async def safe_call_async(fn: Callable[..., Any], *args, default: Any = None, **kwargs) -> Any:
    """Async version of safe_call."""
    try:
        return await fn(*args, **kwargs)
    except Exception as exc:
        logger.debug("[SAFE-CALL-ASYNC] %s raised %s — returning default", fn.__qualname__, exc)
        return default


# ── Timeout wrapper ───────────────────────────────────────────────────────────

def call_with_timeout(fn: Callable[..., T], *args, timeout: float = 5.0, **kwargs) -> T:
    """Call fn with a wall-clock timeout using threading.

    Raises TimeoutError if fn does not complete within `timeout` seconds.
    This is a last-resort guard for blocking calls that lack built-in timeouts.
    For async code, use asyncio.wait_for() instead.

    Example:
        result = call_with_timeout(fetch_residency_data, nid, timeout=3.0)
    """
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(fn, *args, **kwargs)
        try:
            return future.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            raise TimeoutError(
                f"{fn.__qualname__} timed out after {timeout}s"
            )


# ── Bulkhead (concurrency limiter for external calls) ────────────────────────

class Bulkhead:
    """Limit concurrent calls to an external service to prevent cascade failures.

    Rejects calls with BulkheadFullError when the concurrency cap is reached
    instead of queuing indefinitely (which would exhaust threads/memory).

    Usage:
        insurance_gate = Bulkhead(max_concurrent=5, name="insurance_api")

        with insurance_gate:
            result = call_insurance_api(claim_id)
    """

    class BulkheadFullError(Exception):
        pass

    def __init__(self, max_concurrent: int, name: str = "bulkhead"):
        self._sem   = asyncio.Semaphore(max_concurrent) if False else None
        self._max   = max_concurrent
        self._count = 0
        self._name  = name
        self._lock  = __import__("threading").Lock()

    def __enter__(self):
        with self._lock:
            if self._count >= self._max:
                raise Bulkhead.BulkheadFullError(
                    f"Bulkhead '{self._name}' full ({self._count}/{self._max} slots used)"
                )
            self._count += 1
        return self

    def __exit__(self, *_):
        with self._lock:
            self._count = max(0, self._count - 1)

    async def __aenter__(self):
        with self._lock:
            if self._count >= self._max:
                raise Bulkhead.BulkheadFullError(
                    f"Bulkhead '{self._name}' full ({self._count}/{self._max} slots used)"
                )
            self._count += 1
        return self

    async def __aexit__(self, *_):
        with self._lock:
            self._count = max(0, self._count - 1)

    @property
    def active(self) -> int:
        return self._count


# ── Pre-configured bulkheads for external services ───────────────────────────
# Import these in route handlers to limit concurrent external calls.

nid_gateway_gate       = Bulkhead(max_concurrent=10, name="nid_gateway")
insurance_gateway_gate = Bulkhead(max_concurrent=5,  name="insurance_gateway")
residency_gateway_gate = Bulkhead(max_concurrent=5,  name="residency_gateway")
ai_service_gate        = Bulkhead(max_concurrent=20, name="ai_service")
