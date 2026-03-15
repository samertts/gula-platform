"""Basic intrusion detection with time-windowed tracking."""

import time
from collections import defaultdict


class IntrusionDetector:
    def __init__(self, max_attempts: int = 10, window_seconds: int = 300):
        self._attempts: dict[str, list[float]] = defaultdict(list)
        self._max = max_attempts
        self._window = window_seconds

    def detect(self, ip: str) -> str:
        """Check if an IP should be blocked. Returns 'blocked' or 'ok'."""
        now = time.time()
        # Clean old entries
        self._attempts[ip] = [t for t in self._attempts[ip] if now - t < self._window]
        self._attempts[ip].append(now)

        if len(self._attempts[ip]) > self._max:
            return "blocked"
        return "ok"

    def reset(self, ip: str):
        """Reset attempts for an IP (e.g., after successful login)."""
        self._attempts.pop(ip, None)


detector = IntrusionDetector()
