"""
Rate limiter for GULA Platform.

Uses Redis (via the shared `cache` singleton) when available — shared across
all uvicorn workers so the effective limit is exactly what's configured.
Falls back to the in-memory store in development (single-process).

Fixed-window algorithm: requests are counted per (key, time-bucket) pair.
A bucket rolls over every `window_seconds` seconds.
"""

import ipaddress
import os
import math
import time
import logging
from fastapi import Request, HTTPException
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

    # Only trust injected headers when the direct connection is from our nginx
    # (private address = Docker network, localhost)
    if _is_private_ip(direct_ip):
        # X-Real-IP is the most reliable — nginx sets it from $remote_addr
        real_ip = request.headers.get("X-Real-IP", "").strip()
        if real_ip:
            return real_ip

        # Fallback: X-Forwarded-For (first entry = original client)
        forwarded = request.headers.get("X-Forwarded-For", "").strip()
        if forwarded:
            first_ip = forwarded.split(",")[0].strip()
            if first_ip:
                return first_ip

    return direct_ip


def _check(key: str, max_requests: int, window_seconds: int, request: Request = None) -> bool:
    """Fixed-window rate check using the shared cache (Redis or in-memory).

    Returns True if the request is allowed, False if limit is exceeded.
    The key is scoped to the current time bucket so the window resets cleanly.
    """
    # Check if IP is already blocked in Redis (dynamic firewall)
    if request:
        client_ip = get_client_ip(request)
        if cache.get(f"block:{client_ip}"):
            return False

    bucket = math.floor(time.time() / window_seconds)
    full_key = f"rl:{key}:{bucket}"

    count = cache.incr(full_key)
    if count == 1:
        # First request in this window — set expiry so the key auto-expires
        cache.expire(full_key, window_seconds * 2)

    if count > max_requests:
        # If it's an IP-based key and limit is exceeded significantly, block the IP
        if key.startswith(("ip:", "public:", "auth:")) and count > max_requests * 5:
            client_ip = get_client_ip(request) if request else key.split(":")[-1]
            # Block for configurable duration (default 1 hour)
            block_duration = int(os.getenv("RATE_LIMIT_BLOCK_DURATION_SECONDS", "3600"))
            cache.set(f"block:{client_ip}", "1", expire=block_duration)
            logger.warning(f"IP {client_ip} blocked for {block_duration} seconds due to excessive rate limit violations.")
        return False

    return True


def rate_limit_public(request: Request, max_per_minute: int = 30):
    """Rate limit for public endpoints (result links) — keyed by IP."""
    client_ip = get_client_ip(request)
    if not _check(f"public:{client_ip}", max_requests=max_per_minute, window_seconds=60, request=request):
        raise HTTPException(
            status_code=429,
            detail="Too many requests. Please try again later.",
        )


def rate_limit_user(request: Request, user_id: int, max_per_minute: int = 60):
    """
    Rate limit for authenticated endpoints — keyed by user_id (primary) + IP (secondary).

    Two-key strategy:
    - user:{id}  → prevents a single account from hammering even with rotating IPs
    - ip:{addr}  → prevents a single IP from using many accounts to bypass per-user limit
    Both must pass; the stricter one wins.
    """
    client_ip = get_client_ip(request)

    # Per-user check (primary) — e.g. 60 req/min per account
    if not _check(f"user:{user_id}", max_requests=max_per_minute, window_seconds=60, request=request):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please slow down.",
        )

    # Per-IP check (secondary) — allows 3× the per-user limit across all users on that IP
    ip_max = max_per_minute * 3
    if not _check(f"ip:{client_ip}", max_requests=ip_max, window_seconds=60, request=request):
        raise HTTPException(
            status_code=429,
            detail="Too many requests from this network.",
        )


def rate_limit_auth(request: Request, max_per_minute: int = 10):
    """Rate limit for auth endpoints (login/register) — keyed by IP."""
    client_ip = get_client_ip(request)
    if not _check(f"auth:{client_ip}", max_requests=max_per_minute, window_seconds=60, request=request):
        raise HTTPException(
            status_code=429,
            detail="Too many login attempts. Please wait a moment.",
        )


def rate_limit_admin(request: Request, user_id: int, max_per_minute: int = 20):
    """Strict rate limit for /admin/* endpoints — keyed by user_id + IP.

    Admin actions are sensitive; a lower limit protects against:
    - Brute-force role enumeration
    - Bulk account manipulation scripts
    - Compromised admin token abuse
    """
    client_ip = get_client_ip(request)
    if not _check(f"admin:user:{user_id}", max_requests=max_per_minute, window_seconds=60, request=request):
        raise HTTPException(
            status_code=429,
            detail="Admin rate limit exceeded. Maximum 20 operations per minute.",
        )
    # Secondary: per-IP across all admin users (blocks scripted attacks from one IP)
    if not _check(f"admin:ip:{client_ip}", max_requests=60, window_seconds=60, request=request):
        raise HTTPException(
            status_code=429,
            detail="Too many admin requests from this network.",
        )
