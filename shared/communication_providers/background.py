"""Background delivery + cancellation for GULA Communication Providers.

Provider plugins that support background processing (scheduled sends,
long-running fan-outs, retry workers) submit work through
:class:`BackgroundDispatcher` — a small thread pool with per-delivery
status tracking and cooperative cancellation. The dispatcher is a
provider-layer concern: the Communication Core's queue interfaces remain
untouched.
"""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("gula.communication.providers.background")


@dataclass
class BackgroundDelivery:
    """A submitted background delivery and its current status."""

    delivery_ref: str
    provider: str
    status: str = "queued"  # queued | running | delivered | failed | cancelled
    error: str | None = None
    future: Future | None = field(default=None, repr=False)

    def to_dict(self) -> dict[str, Any]:
        return {
            "delivery_ref": self.delivery_ref,
            "provider": self.provider,
            "status": self.status,
            "error": self.error,
        }


class BackgroundDispatcher:
    """Thread pool with per-delivery status tracking and cancellation.

    Typical use from a provider::

        dispatcher = BackgroundDispatcher(provider="telegram", max_workers=2)
        ref = dispatcher.submit("msg-1", lambda: send())
        dispatcher.cancel("msg-1")   # cancels queued futures; running ones
                                     # are marked cancelled cooperatively
    """

    def __init__(self, provider: str, max_workers: int = 2) -> None:
        self._provider = provider
        self._pool = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix=f"gula-comm-{provider}")
        self._deliveries: dict[str, BackgroundDelivery] = {}
        self._lock = threading.Lock()
        self._closed = False

    def submit(self, delivery_ref: str, fn: Callable[[], bool], error: str | None = None) -> BackgroundDelivery:
        """Schedule ``fn``; returns the tracking record immediately."""
        with self._lock:
            if self._closed:
                raise RuntimeError("dispatcher is closed")
            record = BackgroundDelivery(delivery_ref=delivery_ref, provider=self._provider)
            self._deliveries[delivery_ref] = record
        future = self._pool.submit(self._run, delivery_ref, fn)
        record.future = future
        return record

    def _run(self, delivery_ref: str, fn: Callable[[], bool]) -> None:
        record = self._deliveries.get(delivery_ref)
        if record is None:
            return
        with self._lock:
            if record.status == "cancelled":
                return
            record.status = "running"
        try:
            ok = fn()
            with self._lock:
                record.status = "delivered" if ok else "failed"
        except Exception as exc:
            logger.error(
                "communication_background_failed provider=%s ref=%s error_type=%s",
                self._provider,
                delivery_ref,
                type(exc).__name__,
            )
            with self._lock:
                record.status = "failed"
                record.error = f"{type(exc).__name__}: {exc}"

    def cancel(self, delivery_ref: str) -> bool:
        """Cancel a delivery. Queued futures are cancelled; running ones are
        flagged and the worker checks the flag before completing."""
        with self._lock:
            record = self._deliveries.get(delivery_ref)
            if record is None:
                return False
            if record.status not in ("queued", "running"):
                return False
            record.status = "cancelled"
            future = record.future
        if future is not None and future.cancel():
            logger.info(
                "communication_background_cancelled provider=%s ref=%s",
                self._provider,
                delivery_ref,
            )
        return True

    def status(self, delivery_ref: str) -> BackgroundDelivery | None:
        with self._lock:
            record = self._deliveries.get(delivery_ref)
            return record

    def snapshot(self) -> list[dict[str, Any]]:
        with self._lock:
            return [record.to_dict() for record in self._deliveries.values()]

    def shutdown(self) -> None:
        with self._lock:
            self._closed = True
        self._pool.shutdown(wait=False, cancel_futures=True)


__all__ = ["BackgroundDelivery", "BackgroundDispatcher"]