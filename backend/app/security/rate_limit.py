"""
In-memory rate limiter for GULA Platform.
For production, use Redis-based rate limiting.
"""

import time
from collections import defaultdict
from fastapi import Request, HTTPException


# Trusted proxy CIDRs (Docker, localhost, common cloud providers)
TRUSTED_PROXIES = {"127.0.0.1", "::1", "172.17.0.1", "10.0.0.1"}


def get_client_ip(request: Request) -> str:
    """Extract real client IP, respecting X-Forwarded-For behind trusted proxies."""
    client_ip = request.client.host if request.client else "unknown"

    # Only trust X-Forwarded-For from known proxies
    if client_ip in TRUSTED_PROXIES:
        forwarded = request.headers.get("X-Forwarded-For", "")
        if forwarded:
            # Take the first (leftmost) IP — the original client
            real_ip = forwarded.split(",")[0].strip()
            if real_ip:
                return real_ip

    return client_ip


class RateLimiter:
    def __init__(self):
        self._requests: dict[str, list[float]] = defaultdict(list)
        self._last_cleanup = time.time()
        self._cleanup_interval = 300  # Clean stale keys every 5 minutes

    def check(self, key: str, max_requests: int = 60, window_seconds: int = 60) -> bool:
        """Check if request is allowed. Returns True if allowed."""
        now = time.time()
        cutoff = now - window_seconds

        # Periodic global cleanup to prevent memory leak from abandoned keys
        if now - self._last_cleanup > self._cleanup_interval:
            self._cleanup(now, window_seconds)

        # Clean old entries for this key
        self._requests[key] = [t for t in self._requests[key] if t > cutoff]

        if len(self._requests[key]) >= max_requests:
            return False

        self._requests[key].append(now)
        return True

    def _cleanup(self, now: float, default_window: int = 60):
        """Remove stale keys that have no recent requests."""
        self._last_cleanup = now
        cutoff = now - default_window * 2
        stale_keys = [k for k, v in self._requests.items() if not v or v[-1] < cutoff]
        for k in stale_keys:
            del self._requests[k]


# Global instance (in-memory only - resets on restart, not shared across processes)
# For production multi-process deployments, use Redis-based rate limiting
limiter = RateLimiter()


def rate_limit_public(request: Request, max_per_minute: int = 30):
    """Rate limit for public endpoints (result links)."""
    client_ip = get_client_ip(request)
    if not limiter.check(f"public:{client_ip}", max_requests=max_per_minute, window_seconds=60):
        raise HTTPException(
            status_code=429,
            detail="Too many requests. Please try again later.",
        )


def rate_limit_auth(request: Request, max_per_minute: int = 10):
    """Rate limit for auth endpoints (login/register)."""
    client_ip = get_client_ip(request)
    if not limiter.check(f"auth:{client_ip}", max_requests=max_per_minute, window_seconds=60):
        raise HTTPException(
            status_code=429,
            detail="Too many login attempts. Please wait a moment.",
        )
