"""
API Firewall — GULA Platform
=============================
Redis-backed IP blocklist with TTL, auto-expiry, and structured logging.

Previously this was an in-memory set that:
  - Did not persist across restarts
  - Was not shared across workers
  - Had no TTL (permanent block with no auto-unblock)
  - Had no logging

Now uses the shared `cache` (Redis in production, MemoryStore in dev) so
blocks are visible to all workers and survive process restarts.
"""
import logging

from ..security.redis_client import cache

logger = logging.getLogger("gula.firewall")

_PREFIX = "fw:blocked:"
_DEFAULT_TTL = 3600  # 1 hour


def block(ip: str, ttl: int = _DEFAULT_TTL, reason: str = "unspecified") -> None:
    """Block an IP for `ttl` seconds (default 1 hour).

    Args:
        ip:     IPv4 or IPv6 address to block.
        ttl:    Seconds until the block expires. 0 = permanent (no expiry).
        reason: Human-readable reason logged for audit trail.
    """
    key = _PREFIX + ip
    if ttl > 0:
        cache.set(key, reason, ex=ttl)
    else:
        cache.set(key, reason)
    logger.warning(
        "[FIREWALL] Blocked IP %s | reason=%s | ttl=%ss",
        ip, reason, ttl if ttl > 0 else "permanent",
    )


def unblock(ip: str) -> None:
    """Remove an IP block immediately."""
    cache.delete(_PREFIX + ip)
    logger.info("[FIREWALL] Unblocked IP %s", ip)


def allowed(ip: str) -> bool:
    """Return True if the IP is NOT currently blocked."""
    return cache.get(_PREFIX + ip) is None


def block_reason(ip: str) -> str | None:
    """Return the reason an IP was blocked, or None if not blocked."""
    return cache.get(_PREFIX + ip)
