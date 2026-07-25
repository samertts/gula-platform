"""Intrusion detection with time-windowed tracking and memory safety.

Thread-safe implementation with per-IP attempt caps and periodic cleanup.
"""

import logging
import threading
import time
from collections import defaultdict

logger = logging.getLogger("gula.security")

MAX_TRACKED_IPS = 10000
MAX_ATTEMPTS_PER_IP = 100


class IntrusionDetector:
    def __init__(self, max_attempts: int = 10, window_seconds: int = 300):
        self._attempts: dict[str, list[float]] = defaultdict(list)
        self._max = max_attempts
        self._window = window_seconds
        self._last_cleanup = time.time()
        self._lock = threading.Lock()

    def detect(self, ip: str) -> str:
        with self._lock:
            now = time.time()

            if now - self._last_cleanup > 60:
                self._cleanup(now)

            times = self._attempts[ip]
            times[:] = [t for t in times if now - t < self._window]
            times.append(now)

            if len(times) > MAX_ATTEMPTS_PER_IP:
                times[:] = times[-MAX_ATTEMPTS_PER_IP:]

            if len(times) > self._max:
                logger.warning(
                    "IP %s blocked: %d attempts in %ds",
                    ip,
                    len(times),
                    self._window,
                )
                return "blocked"
        return "ok"

    def reset(self, ip: str):
        with self._lock:
            self._attempts.pop(ip, None)

    def _cleanup(self, now: float):
        self._last_cleanup = now
        expired = [
            ip
            for ip, times in self._attempts.items()
            if not times or (now - times[-1]) > self._window
        ]
        for ip in expired:
            del self._attempts[ip]

        if len(self._attempts) > MAX_TRACKED_IPS:
            sorted_ips = sorted(self._attempts.items(), key=lambda x: x[1][-1] if x[1] else 0)
            for ip, _ in sorted_ips[: len(self._attempts) - MAX_TRACKED_IPS]:
                del self._attempts[ip]
            logger.warning("Intrusion detector: evicted old IPs, tracking %d", len(self._attempts))

    @property
    def tracked_count(self) -> int:
        with self._lock:
            return len(self._attempts)


detector = IntrusionDetector()
