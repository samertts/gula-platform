"""
API Firewall — GULA Platform
=============================
Redis-backed IP blocklist with fail-closed guarantee, TTL-aware local
fallback, and bounded eviction to prevent memory growth.

Fail-closed model
-----------------
  block() → writes to Redis + local store (both, atomically best-effort)
  allowed() → checks local first (O(1)), then Redis; if Redis fails → local
  unblock() → removes from Redis + local

Local fallback store
--------------------
The in-process store serves two purposes:
  1. Fail-closed: IPs blocked before a Redis outage stay blocked per-worker.
  2. Performance: local lookup is ~100x faster than a Redis round-trip.

Eviction policy (prevents unbounded memory growth):
  - Each entry carries a monotonic expire_at timestamp.
  - When the store exceeds MAX_LOCAL_SIZE, the oldest 20% are evicted.
  - Expired entries are lazily removed on every access to the store.
  - MAX_LOCAL_SECONDS caps how long an entry lives locally even without
    an explicit unblock() — prevents permanent bans surviving restarts.
"""

from __future__ import annotations

import logging
import threading
import time

from ..security.redis_client import cache

logger = logging.getLogger("gula.firewall")

_PREFIX = "fw:blocked:"
_DEFAULT_TTL = 3600  # 1 hour (Redis TTL)
MAX_LOCAL_SIZE = 5_000  # max IPs in local store before eviction
MAX_LOCAL_SECONDS = 3_600  # local entries expire after at most 1 hour


# ── Local store ────────────────────────────────────────────────────────────────
# Maps ip → (reason, expire_at)  where expire_at is monotonic seconds.
_local: dict[str, tuple[str, float]] = {}
_local_lock = threading.Lock()


def _local_expire_at(ttl: int) -> float:
    """Convert a Redis TTL (seconds) to a local monotonic deadline."""
    effective = min(ttl, MAX_LOCAL_SECONDS) if ttl > 0 else MAX_LOCAL_SECONDS
    return time.monotonic() + effective


def _evict_expired() -> None:
    """Remove entries whose local TTL has passed. Call under _local_lock."""
    now = time.monotonic()
    expired = [ip for ip, (_, exp) in _local.items() if exp <= now]
    for ip in expired:
        del _local[ip]


def _evict_oldest() -> None:
    """Evict the oldest 20% of entries when store exceeds MAX_LOCAL_SIZE."""
    if len(_local) <= MAX_LOCAL_SIZE:
        return
    # Sort by expire_at ascending → oldest first
    sorted_ips = sorted(_local, key=lambda ip: _local[ip][1])
    evict_count = max(1, len(_local) // 5)
    for ip in sorted_ips[:evict_count]:
        del _local[ip]
    logger.warning("[FIREWALL] Local store evicted %d entries (size limit)", evict_count)


# ── Public API ─────────────────────────────────────────────────────────────────


def block(ip: str, ttl: int = _DEFAULT_TTL, reason: str = "unspecified") -> None:
    """Block an IP for `ttl` seconds (default 1 hour).

    Writes to both Redis and the local store.  If Redis is unavailable the
    local store is still updated so the block is enforced within this process.

    Args:
        ip:     IPv4 or IPv6 address to block.
        ttl:    Block duration in seconds. 0 = permanent in Redis (still
                expires locally after MAX_LOCAL_SECONDS).
        reason: Human-readable reason stored in Redis and logged.
    """
    # Local store first — always succeeds
    with _local_lock:
        _evict_expired()
        _evict_oldest()
        _local[ip] = (reason, _local_expire_at(ttl))

    # Redis — best-effort
    key = _PREFIX + ip
    try:
        if ttl > 0:
            cache.set(key, reason, ex=ttl)
        else:
            cache.set(key, reason)
    except Exception as exc:
        logger.error("[FIREWALL] Redis write failed for block(%s): %s", ip, exc)

    logger.warning(
        "[FIREWALL] Blocked IP %s | reason=%s | ttl=%s",
        ip,
        reason,
        f"{ttl}s" if ttl > 0 else "permanent",
    )


def unblock(ip: str) -> None:
    """Remove an IP block from both Redis and the local store."""
    with _local_lock:
        _local.pop(ip, None)

    try:
        cache.delete(_PREFIX + ip)
    except Exception as exc:
        logger.error("[FIREWALL] Redis delete failed for unblock(%s): %s", ip, exc)

    logger.info("[FIREWALL] Unblocked IP %s", ip)


def allowed(ip: str) -> bool:
    """Return True if the IP is NOT currently blocked.

    1. Checks local store (fast, O(1), always available).
    2. If not locally blocked, checks Redis.
    3. If Redis fails, falls back to local-only result (unknown IPs allowed).
    """
    now = time.monotonic()
    with _local_lock:
        entry = _local.get(ip)
        if entry is not None:
            _reason, exp = entry
            if exp > now:
                return False  # locally blocked, not yet expired
            # Expired locally — remove it and continue to Redis check
            del _local[ip]

    try:
        return cache.get(_PREFIX + ip) is None
    except Exception as exc:
        logger.warning(
            "[FIREWALL] Redis read failed for allowed(%s): %s — local-only",
            ip,
            exc,
        )
        return True  # IP not in local store → allow (avoid global lockout)


def block_reason(ip: str) -> str | None:
    """Return the reason an IP was blocked, or None if not blocked."""
    now = time.monotonic()
    with _local_lock:
        entry = _local.get(ip)
        if entry is not None and entry[1] > now:
            return entry[0]

    try:
        return cache.get(_PREFIX + ip)
    except Exception:
        return None


def local_stats() -> dict:
    """Return current local store stats (for monitoring / health checks)."""
    now = time.monotonic()
    with _local_lock:
        active = sum(1 for _, (_, exp) in _local.items() if exp > now)
        return {"total": len(_local), "active": active, "max": MAX_LOCAL_SIZE}
