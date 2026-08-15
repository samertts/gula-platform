"""Rate limiter for GULA Platform.

Uses Redis (via the shared `cache` singleton) when available — shared across
all uvicorn workers so the effective limit is exactly what's configured.
Falls back to the in-memory store in development (single-process).

Fixed-window algorithm: requests are counted per (key, time-bucket) pair.
A bucket rolls over every `window_seconds` seconds.

All public functions raise HTTPException(429) with standardised headers:
  X-RateLimit-Limit     — maximum requests per window
  X-RateLimit-Remaining — remaining requests (0 when blocked)
  X-RateLimit-Reset     — Unix timestamp when the window resets
  Retry-After           — seconds until next allowed request (on 429)
"""

import hashlib
import hmac
import ipaddress
import logging
import math
import os
import time

from fastapi import HTTPException, Request

from .redis_client import cache

logger = logging.getLogger("gula.rate_limit")


class RateLimiter:
    """Thin class wrapper around _check() for direct use and unit testing.

    Usage (without a Request object — e.g. in tests or background tasks):
        limiter = RateLimiter()
        allowed = limiter.check("my-key", max_requests=5, window_seconds=60)
    """

    def check(self, key: str, max_requests: int, window_seconds: int) -> bool:
        """Returns True if within limits, False if the limit is exceeded."""
        allowed, _, _ = _check(key, max_requests, window_seconds)
        return allowed


def _is_private_ip(ip: str) -> bool:
    """Return True for RFC-1918 / loopback / Docker addresses."""
    try:
        return ipaddress.ip_address(ip).is_private
    except ValueError:
        return False


def get_client_ip(request: Request) -> str:
    """Extract real client IP.

    Priority (in order):
      1. X-Real-IP header   — set by nginx with $remote_addr (the actual client)
      2. X-Forwarded-For    — first entry (leftmost) when behind a private proxy
      3. request.client.host — direct connection IP (fallback)

    We trust these headers only when the direct connection is from a private
    address (Docker network, loopback) — i.e. only our own nginx can set them.
    External clients connecting directly cannot spoof them.
    """
    direct_ip = request.client.host if request.client else "unknown"

    if _is_private_ip(direct_ip):
        real_ip = (request.headers.get("X-Real-IP") or "").strip()
        if real_ip:
            return real_ip
        forwarded = (request.headers.get("X-Forwarded-For") or "").strip()
        if forwarded:
            first_ip = forwarded.split(",")[0].strip()
            if first_ip:
                return first_ip

    return direct_ip


def _check(
    key: str,
    max_requests: int,
    window_seconds: int,
    request: Request | None = None,
) -> tuple[bool, int, int]:
    """Fixed-window rate check.

    Returns (allowed, remaining, reset_ts):
      allowed   — True if the request may proceed
      remaining — requests left in the current window (≥0)
      reset_ts  — Unix timestamp when this window expires
    """
    # HTTP integration tests pound the same loopback IP dozens of times per
    # second; honouring production rate limits there produces flaky 429s that
    # mask real assertion failures. Skip the counter for request-bound checks
    # when ENV=test. Direct RateLimiter.check() unit tests (no request) still
    # exercise the real path so rate-limiter behaviour stays covered.
    if request is not None and os.getenv("ENV", "").lower() == "test":
        return True, max_requests, int(time.time()) + window_seconds

    # Check if IP is already hard-blocked
    if request:
        client_ip = get_client_ip(request)
        if cache.get(f"block:{client_ip}"):
            return False, 0, int(time.time()) + window_seconds

    bucket = math.floor(time.time() / window_seconds)
    reset_ts = (bucket + 1) * window_seconds
    full_key = f"rl:{key}:{bucket}"

    count = cache.incr(full_key)
    if count == 1:
        cache.expire(full_key, window_seconds * 2)

    remaining = max(0, max_requests - count)

    if count > max_requests:
        # Significant abuse → dynamic IP block
        if key.startswith(("ip:", "public:", "auth:")) and count > max_requests * 5:
            client_ip = get_client_ip(request) if request else key.rsplit(":", maxsplit=1)[-1]
            block_dur = int(os.getenv("RATE_LIMIT_BLOCK_DURATION_SECONDS", "3600"))
            cache.set(f"block:{client_ip}", "1", ex=block_dur)
            logger.warning("IP %s blocked for %ds (rate limit 5x)", client_ip, block_dur)
        return False, 0, reset_ts

    return True, remaining, reset_ts


def _rl_headers(limit: int, remaining: int, reset_ts: int) -> dict[str, str]:
    return {
        "X-RateLimit-Limit": str(limit),
        "X-RateLimit-Remaining": str(remaining),
        "X-RateLimit-Reset": str(reset_ts),
    }


def _raise_429(detail: str, limit: int, reset_ts: int) -> None:
    retry_after = max(1, reset_ts - int(time.time()))
    raise HTTPException(
        status_code=429,
        detail=detail,
        headers={
            **_rl_headers(limit, 0, reset_ts),
            "Retry-After": str(retry_after),
        },
    )


# ── Public helpers ────────────────────────────────────────────────────────────


def rate_limit_public(request: Request, max_per_minute: int = 30) -> None:
    """Rate limit for public endpoints (result links) — keyed by IP."""
    client_ip = get_client_ip(request)
    ok, _, reset = _check(f"public:{client_ip}", max_per_minute, 60, request)
    if not ok:
        _raise_429("Too many requests. Please try again later.", max_per_minute, reset)


def rate_limit_user(request: Request, user_id: int, max_per_minute: int = 60) -> None:
    """Authenticated endpoint rate limit — dual-key (user_id + IP).

    Two-key strategy:
      user:{id}  → prevents account hammering even with rotating IPs
      ip:{addr}  → prevents multi-account bypass from one IP
    Both must pass; the stricter one wins.
    """
    client_ip = get_client_ip(request)

    ok, _, reset = _check(f"user:{user_id}", max_per_minute, 60, request)
    if not ok:
        _raise_429("Rate limit exceeded. Please slow down.", max_per_minute, reset)

    ip_max = max_per_minute * 3
    ok, _, reset = _check(f"ip:{client_ip}", ip_max, 60, request)
    if not ok:
        _raise_429("Too many requests from this network.", ip_max, reset)


def rate_limit_auth(
    request: Request,
    max_per_minute: int = 10,
    identifier: str | None = None,
) -> None:
    """Rate-limit auth by IP and, when available, by a keyed identifier.

    The identifier key is an HMAC digest, never the submitted email/phone. This
    prevents attackers from bypassing account-targeted throttling by rotating IPs
    while keeping sensitive identifiers out of Redis keys and logs.
    """
    client_ip = get_client_ip(request)
    ok, _, reset = _check(f"auth:{client_ip}", max_per_minute, 60, request)
    if not ok:
        _raise_429("Too many login attempts. Please wait a moment.", max_per_minute, reset)

    normalized = identifier.strip().lower()[:320] if identifier else ""
    if not normalized:
        return

    from ..config import NID_HMAC_KEY

    key = NID_HMAC_KEY.encode("utf-8") if NID_HMAC_KEY else b"gula-development-auth-rate-limit"
    identifier_digest = hmac.new(key, normalized.encode("utf-8"), hashlib.sha256).hexdigest()
    ok, _, reset = _check(f"auth-id:{identifier_digest}", max_per_minute, 60, request)
    if not ok:
        _raise_429("Too many login attempts. Please wait a moment.", max_per_minute, reset)


def rate_limit_ai(request: Request, max_per_minute: int = 30) -> None:
    """Protect expensive AI and RAG endpoints from burst abuse.

    The limit is intentionally IP-based at the router boundary; authenticated
    route guards still enforce actor and tenant permissions. Redis keeps the
    budget shared across API workers.
    """
    client_ip = get_client_ip(request)
    ok, _, reset = _check(f"ai:{client_ip}", max_per_minute, 60, request)
    if not ok:
        _raise_429("AI request rate limit exceeded. Please try again later.", max_per_minute, reset)


def rate_limit_admin(request: Request, user_id: int, max_per_minute: int = 20) -> None:
    """Strict rate limit for /admin/* endpoints — keyed by user_id + IP."""
    client_ip = get_client_ip(request)

    ok, _, reset = _check(f"admin:user:{user_id}", max_per_minute, 60, request)
    if not ok:
        _raise_429(
            f"Admin rate limit exceeded. Maximum {max_per_minute} operations per minute.",
            max_per_minute,
            reset,
        )

    ok, _, reset = _check(f"admin:ip:{client_ip}", 60, 60, request)
    if not ok:
        _raise_429("Too many admin requests from this network.", 60, reset)
