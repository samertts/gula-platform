from __future__ import annotations

import logging
import time
from collections import deque

logger = logging.getLogger("gula.kernel.gateway.rate_limiting")


class RateLimiter:
    def __init__(self):
        self._limits: dict[str, tuple[int, int]] = {}
        self._windows: dict[str, deque[float]] = {}

    def set_limit(self, key: str, max_requests: int, window_seconds: int) -> None:
        self._limits[key] = (max_requests, window_seconds)

    def check(self, key: str) -> bool:
        limit = self._limits.get(key)
        if not limit:
            return True
        max_requests, window = limit
        now = time.time()
        if key not in self._windows:
            self._windows[key] = deque()
        q = self._windows[key]
        while q and now - q[0] >= window:
            q.popleft()
        if len(q) >= max_requests:
            return False
        q.append(now)
        return True
