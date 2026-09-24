"""The canonical server-side idempotency claim, shared by every mutating path.

An idempotency key is chosen by the caller, so it is only ever unique *within*
a tenant: clients pick invoice numbers, counters and dates, which collide
across tenants by construction. This module therefore puts the tenant in the
cache key rather than in a filter, so two tenants cannot name the same entry at
all. NR-094 is the same rule expressed in the database, where `claims` had a
globally unique index and one lab's key locked every other lab out of it.

Three things have to hold together, and the reason this is one module rather
than a pattern people re-type is that omitting any one of them still looks like
it works:

* **The tenant is in the key.** `idempotency:{scope}:{tenant_id}:{key}`.
* **The payload is fingerprinted.** Reusing a key for different content is a
  client bug, and returning the first response for the second payload would
  silently discard a clinical write. It is refused with 409 instead.
* **The claim is atomic.** `set_if_absent` is the only thing standing between
  two concurrent retries; a get-then-set would let both through.

Replaces the copy that lived inline in `order_service.create_order`, which was
the only correct implementation of the several the platform had. NR-091 records
the others.

**A limitation that is deliberately not hidden.** The store is
`app.security.redis_client.cache`, which falls back to a per-process
`_MemoryStore` when `REDIS_URL` is unset or Redis is unreachable -- including in
production, where `_build_cache` logs CRITICAL and continues in degraded mode.
Executed: two `_MemoryStore` instances, standing for two gunicorn workers, do
not see each other's claims, so a retry landing on another worker is treated as
a new request. `is_shared()` reports this, and `/compliance/system-status`
publishes it as a measured fact rather than asserting that replay protection
holds. The durable fix is a database-backed store -- `idempotency_keys` exists
for it -- and is recorded in NR-091 and NR-095.
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass
from typing import Any

from ..security.redis_client import _MemoryStore
from ..security.redis_client import cache as _cache

logger = logging.getLogger("gula.idempotency")

#: How long a claim may stay "processing" before another attempt may take it.
#: Short, because it only has to cover one request's own execution.
CLAIM_TTL_SECONDS = 300

#: How long a completed response stays replayable.
COMPLETED_TTL_SECONDS = 86_400

_CONFLICT_DIFFERENT_PAYLOAD = {
    "error": "Idempotency key was already used with a different payload",
    "status_code": 409,
}
_CONFLICT_IN_FLIGHT = {
    "error": "A request with this idempotency key is already processing",
    "status_code": 409,
}


def is_shared() -> bool:
    """Whether the claim store is visible to every worker.

    False means idempotency is per-process: correct within one worker, absent
    across them. Callers must not treat a False here as a reason to refuse a
    clinical write -- that is a deployment problem, not the caller's -- but it
    must not be reported as protection either.
    """
    return not isinstance(_cache, _MemoryStore)


def fingerprint(payload: Any) -> str:
    """A stable digest of the request content a key is claimed for."""
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, default=str).encode("utf-8"),
    ).hexdigest()


@dataclass
class Idempotency:
    """The outcome of claiming a key, and the handle used to complete it.

    Exactly one of `conflict` and `replay` may be set. When both are None the
    caller holds the claim and must do the work, then call `complete()`.
    """

    key: str | None
    conflict: dict | None = None
    replay: Any | None = None
    _cache_key: str | None = None
    _fingerprint: str | None = None

    @property
    def claimed(self) -> bool:
        """True when the caller should proceed with the operation."""
        return self.conflict is None and self.replay is None

    def complete(self, response: Any) -> None:
        """Record the response so a retry replays it instead of repeating the work."""
        if not self._cache_key or not self._fingerprint:
            return
        _cache.set(
            self._cache_key,
            json.dumps(
                {
                    "fingerprint": self._fingerprint,
                    "status": "completed",
                    "response": response,
                },
                default=str,
            ),
            ex=COMPLETED_TTL_SECONDS,
        )

    def release(self) -> None:
        """Drop an unfinished claim so a retry is not told it is still in flight.

        Call this when the operation failed in a way the caller may legitimately
        retry. Leaving the claim would make the next attempt wait out
        CLAIM_TTL_SECONDS for no reason.
        """
        if self._cache_key:
            _cache.delete(self._cache_key)


def begin(scope: str, tenant_id: Any, key: str | None, payload: Any) -> Idempotency:
    """Claim `key` for `payload` within `tenant_id`.

    With no key the request is unprotected and proceeds: not every client sends
    one, and refusing those would break existing callers. `scope` separates
    operations so the same key may be used for an order and for a sample.
    """
    if not key:
        return Idempotency(key=None)

    cache_key = f"idempotency:{scope}:{tenant_id}:{key}"
    digest = fingerprint(payload)

    cached = _cache.get(cache_key)
    if cached:
        return _from_envelope(key, cached, digest)

    claim = json.dumps({"fingerprint": digest, "status": "processing"})
    if not _cache.set_if_absent(cache_key, claim, ex=CLAIM_TTL_SECONDS):
        # Lost the race. Re-read: the winner may already have completed.
        cached = _cache.get(cache_key)
        if cached:
            return _from_envelope(key, cached, digest, in_flight_only=True)
        # The claim vanished between set_if_absent and get -- it expired, or
        # another attempt released it. Treat it as in flight rather than
        # racing again, so two callers never both proceed.
        return Idempotency(key=key, conflict=dict(_CONFLICT_IN_FLIGHT))

    return Idempotency(key=key, _cache_key=cache_key, _fingerprint=digest)


def _from_envelope(
    key: str, cached: str, digest: str, *, in_flight_only: bool = False,
) -> Idempotency:
    try:
        envelope = json.loads(cached)
    except (TypeError, ValueError):
        logger.warning("[IDEMPOTENCY] unreadable envelope for a claimed key; refusing")
        return Idempotency(key=key, conflict=dict(_CONFLICT_IN_FLIGHT))

    if envelope.get("fingerprint") != digest:
        return Idempotency(key=key, conflict=dict(_CONFLICT_DIFFERENT_PAYLOAD))
    if in_flight_only or envelope.get("status") == "processing":
        return Idempotency(key=key, conflict=dict(_CONFLICT_IN_FLIGHT))
    return Idempotency(key=key, replay=envelope.get("response"))
