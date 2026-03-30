"""
Rate limiter for GULA Platform.

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

import ipaddress
import os
import math
import time
import logging
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from .redis_client import cache

logger = logging.getLogger("gula.rate_limit")


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
        real_ip = request.headers.get("X-Real-IP", "").strip()
        if real_ip:
            return real_ip
        forwarded = request.headers.get("X-Forwarded-For", "").strip()
        if forwarded:
            first_ip = forwarded.split(",")[0].strip()
            if first_ip:
                return first_ip

    return direct_ip


def _check(
    key: str,
    max_requests: int,
    window_seconds: int,
    request: Request = None,
) -> tuple[bool, int, int]:
    """Fixed-window rate check.

    Returns (allowed, remaining, reset_ts):
      allowed   — True if the request may proceed
      remaining — requests left in the current window (≥0)
      reset_ts  — Unix timestamp when this window expires
    """
    # Check if IP is already hard-blocked
    if request:
        client_ip = get_client_ip(request)
        if cache.get(f"block:{client_ip}"):
            return False, 0, int(time.time()) + window_seconds

    bucket   = math.floor(time.time() / window_seconds)
    reset_ts = (bucket + 1) * window_seconds
    full_key = f"rl:{key}:{bucket}"

    count = cache.incr(full_key)
    if count == 1:
        cache.expire(full_key, window_seconds * 2)

    remaining = max(0, max_requests - count)

    if count > max_requests:
        # Significant abuse → dynamic IP block
        if key.startswith(("ip:", "public:", "auth:")) and count > max_requests * 5:
            client_ip = get_client_ip(request) if request else key.split(":")[-1]
            block_dur = int(os.getenv("RATE_LIMIT_BLOCK_DURATION_SECONDS", "3600"))
            cache.set(f"block:{client_ip}", "1", ex=block_dur)
            logger.warning("IP %s blocked for %ds (rate limit ×5)", client_ip, block_dur)
        return False, 0, reset_ts

    return True, remaining, reset_ts


def _rl_headers(limit: int, remaining: int, reset_ts: int) -> dict:
    return {
        "X-RateLimit-Limit":     str(limit),
        "X-RateLimit-Remaining": str(remaining),
        "X-RateLimit-Reset":     str(reset_ts),
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


def rate_limit_auth(request: Request, max_per_minute: int = 10) -> None:
    """Rate limit for auth endpoints (login/register) — keyed by IP."""
    client_ip = get_client_ip(request)
    ok, _, reset = _check(f"auth:{client_ip}", max_per_minute, 60, request)
    if not ok:
        _raise_429("Too many login attempts. Please wait a moment.", max_per_minute, reset)


def rate_limit_admin(request: Request, user_id: int, max_per_minute: int = 20) -> None:
    """Strict rate limit for /admin/* endpoints — keyed by user_id + IP."""
    client_ip = get_client_ip(request)

    ok, _, reset = _check(f"admin:user:{user_id}", max_per_minute, 60, request)
    if not ok:
        _raise_429(
            f"Admin rate limit exceeded. Maximum {max_per_minute} operations per minute.",
            max_per_minute, reset,
        )

    ok, _, reset = _check(f"admin:ip:{client_ip}", 60, 60, request)
    if not ok:
        _raise_429("Too many admin requests from this network.", 60, reset)
