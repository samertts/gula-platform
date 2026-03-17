"""Intrusion detection with time-windowed tracking and memory safety."""

import time
import logging
from collections import defaultdict

logger = logging.getLogger("gula.security")

# Maximum tracked IPs to prevent memory exhaustion from distributed attacks
MAX_TRACKED_IPS = 10000


class IntrusionDetector:
    def __init__(self, max_attempts: int = 10, window_seconds: int = 300):
        self._attempts: dict[str, list[float]] = defaultdict(list)
        self._max = max_attempts
        self._window = window_seconds
        self._last_cleanup = time.time()

    def detect(self, ip: str) -> str:
        """Check if an IP should be blocked. Returns 'blocked' or 'ok'."""
        now = time.time()

        # Periodic cleanup to prevent memory leak
        if now - self._last_cleanup > 60:
            self._cleanup(now)

        # Clean old entries for this IP
        self._attempts[ip] = [t for t in self._attempts[ip] if now - t < self._window]
        self._attempts[ip].append(now)

        if len(self._attempts[ip]) > self._max:
            logger.warning("IP %s blocked: %d attempts in %ds", ip, len(self._attempts[ip]), self._window)
            return "blocked"
        return "ok"

    def reset(self, ip: str):
        """Reset attempts for an IP (e.g., after successful login)."""
        self._attempts.pop(ip, None)

    def _cleanup(self, now: float):
        """Remove expired entries and cap memory usage."""
        self._last_cleanup = now
        # Remove expired IPs
        expired = [ip for ip, times in self._attempts.items()
                   if not times or (now - times[-1]) > self._window]
        for ip in expired:
            del self._attempts[ip]

        # If still too many tracked IPs, remove oldest entries
        if len(self._attempts) > MAX_TRACKED_IPS:
            sorted_ips = sorted(self._attempts.items(), key=lambda x: x[1][-1] if x[1] else 0)
            for ip, _ in sorted_ips[:len(self._attempts) - MAX_TRACKED_IPS]:
                del self._attempts[ip]
            logger.warning("Intrusion detector: evicted old IPs, tracking %d", len(self._attempts))

    @property
    def tracked_count(self) -> int:
        return len(self._attempts)


detector = IntrusionDetector()
