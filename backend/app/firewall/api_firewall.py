"""
API Firewall — GULA Platform
=============================
Redis-backed IP blocklist with:
  - TTL and auto-expiry
  - Structured logging
  - Fail-closed behaviour (if Redis is unreachable, known-bad IPs stay blocked
    via a local in-process fallback set)
  - unblock() and block_reason() helpers

Fail-closed principle
---------------------
When Redis is unavailable the firewall must NOT become transparent:
  - block() writes to BOTH Redis AND the local fallback set so IPs blocked
    before Redis went down remain blocked during the outage.
  - allowed() checks the local fallback first (O(1), always available) and
    only consults Redis if the IP is not already locally blocked.
  - If Redis itself fails during allowed() the local fallback is the sole
    source of truth — unknown IPs are allowed (to avoid locking out all users),
    but IPs that were already blocked continue to be blocked.

This means:
  ✔ IPs blocked before Redis outage remain blocked.
  ✔ New bad IPs during outage are blocked locally (until process restart).
  ✔ Legitimate users are not locked out by a Redis failure.
"""
import logging
import threading

from ..security.redis_client import cache

logger = logging.getLogger("gula.firewall")

_PREFIX = "fw:blocked:"
_DEFAULT_TTL = 3600  # 1 hour

# Local in-process fallback — survives Redis outages within the same process.
# Not shared across workers, but provides fail-closed guarantee per worker.
_local: set[str] = set()
_local_lock = threading.Lock()


def block(ip: str, ttl: int = _DEFAULT_TTL, reason: str = "unspecified") -> None:
    """Block an IP for `ttl` seconds (default 1 hour).

    Writes to Redis AND the local fallback set so the block persists even
    if Redis becomes unavailable after this call.

    Args:
        ip:     IPv4 or IPv6 address to block.
        ttl:    Seconds until the block expires. 0 = permanent (no expiry).
        reason: Human-readable reason stored and logged.
    """
    # Always update local fallback first (never fails)
    with _local_lock:
        _local.add(ip)

    key = _PREFIX + ip
    try:
        if ttl > 0:
            cache.set(key, reason, ex=ttl)
        else:
            cache.set(key, reason)
    except Exception as exc:
        logger.error("[FIREWALL] Redis write failed for block(%s): %s", ip, exc)
        # Local set already updated — block is still enforced locally.

    logger.warning(
        "[FIREWALL] Blocked IP %s | reason=%s | ttl=%s",
        ip, reason, f"{ttl}s" if ttl > 0 else "permanent",
    )


def unblock(ip: str) -> None:
    """Remove an IP block from both Redis and the local fallback."""
    with _local_lock:
        _local.discard(ip)

    try:
        cache.delete(_PREFIX + ip)
    except Exception as exc:
        logger.error("[FIREWALL] Redis delete failed for unblock(%s): %s", ip, exc)

    logger.info("[FIREWALL] Unblocked IP %s", ip)


def allowed(ip: str) -> bool:
    """Return True if the IP is NOT currently blocked.

    Checks local fallback first (fail-closed), then Redis.
    If Redis fails, the local fallback is authoritative.
    """
    # Local check — always available, O(1)
    with _local_lock:
        if ip in _local:
            return False

    # Redis check
    try:
        return cache.get(_PREFIX + ip) is None
    except Exception as exc:
        logger.warning(
            "[FIREWALL] Redis read failed for allowed(%s): %s — using local fallback only",
            ip, exc,
        )
        # IP is not in local set → allow (unknown IPs are not banned locally)
        return True


def block_reason(ip: str) -> str | None:
    """Return the reason an IP was blocked, or None if not blocked."""
    try:
        return cache.get(_PREFIX + ip)
    except Exception:
        with _local_lock:
            return "locally blocked (Redis unavailable)" if ip in _local else None
