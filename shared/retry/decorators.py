from __future__ import annotations

import asyncio
import functools
import logging
import threading
import time
from collections.abc import Callable
from contextlib import suppress
from typing import Any, TypeVar

logger = logging.getLogger("gula.retry")

T = TypeVar("T")

_DEFAULT_MAX_ATTEMPTS = 3
_DEFAULT_BASE_DELAY = 0.5
_DEFAULT_MAX_DELAY = 30.0
_DEFAULT_BACKOFF = 2.0


def retry(
    max_attempts: int = _DEFAULT_MAX_ATTEMPTS,
    base_delay: float = _DEFAULT_BASE_DELAY,
    max_delay: float = _DEFAULT_MAX_DELAY,
    backoff: float = _DEFAULT_BACKOFF,
    exceptions: tuple[type[Exception], ...] = (Exception,),
    on_retry: Callable[[int, Exception], None] | None = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    def decorator(fn: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            delay = base_delay
            last_exc: Exception | None = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return fn(*args, **kwargs)
                except exceptions as exc:
                    last_exc = exc
                    if attempt == max_attempts:
                        logger.error("[RETRY] %s failed after %d attempts: %s", fn.__qualname__, max_attempts, exc)
                        raise
                    sleep_for = min(delay, max_delay)
                    logger.warning("[RETRY] %s attempt %d/%d failed — retrying in %.1fs", fn.__qualname__, attempt, max_attempts, sleep_for)
                    if on_retry:
                        with suppress(Exception):
                            on_retry(attempt, exc)
                    time.sleep(sleep_for)
                    delay *= backoff
            raise last_exc
        return wrapper
    return decorator


def retry_async(
    max_attempts: int = _DEFAULT_MAX_ATTEMPTS,
    base_delay: float = _DEFAULT_BASE_DELAY,
    max_delay: float = _DEFAULT_MAX_DELAY,
    backoff: float = _DEFAULT_BACKOFF,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(fn)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            delay = base_delay
            last_exc: Exception | None = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return await fn(*args, **kwargs)
                except exceptions as exc:
                    last_exc = exc
                    if attempt == max_attempts:
                        logger.error("[RETRY-ASYNC] %s failed after %d attempts: %s", fn.__qualname__, max_attempts, exc)
                        raise
                    sleep_for = min(delay, max_delay)
                    logger.warning("[RETRY-ASYNC] %s attempt %d/%d failed — retrying in %.1fs", fn.__qualname__, attempt, max_attempts, sleep_for)
                    await asyncio.sleep(sleep_for)
                    delay *= backoff
            raise last_exc
        return wrapper
    return decorator


def safe_call(fn: Callable[..., T], *args, default: T | None = None, **kwargs) -> T | None:
    try:
        return fn(*args, **kwargs)
    except Exception as exc:
        logger.debug("[SAFE-CALL] %s raised %s — returning default", fn.__qualname__, exc)
        return default


async def safe_call_async(fn: Callable[..., Any], *args, default: Any = None, **kwargs) -> Any:
    try:
        return await fn(*args, **kwargs)
    except Exception as exc:
        logger.debug("[SAFE-CALL-ASYNC] %s raised %s — returning default", fn.__qualname__, exc)
        return default


def call_with_timeout(fn: Callable[..., T], *args, timeout: float = 5.0, **kwargs) -> T:
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(fn, *args, **kwargs)
        try:
            return future.result(timeout=timeout)
        except concurrent.futures.TimeoutError as exc:
            raise TimeoutError(f"{fn.__qualname__} timed out after {timeout}s") from exc


class BulkheadFullError(Exception):
    pass


class Bulkhead:
    def __init__(self, max_concurrent: int, name: str = "bulkhead") -> None:
        self._max = max_concurrent
        self._count = 0
        self._name = name
        self._lock = threading.Lock()

    def __enter__(self) -> Bulkhead:
        with self._lock:
            if self._count >= self._max:
                raise BulkheadFullError(f"Bulkhead '{self._name}' full ({self._count}/{self._max} slots used)")
            self._count += 1
        return self

    def __exit__(self, *_: object) -> None:
        with self._lock:
            self._count = max(0, self._count - 1)

    async def __aenter__(self) -> Bulkhead:
        return self.__enter__()

    async def __aexit__(self, *_: object) -> None:
        self.__exit__()

    @property
    def active(self) -> int:
        return self._count
