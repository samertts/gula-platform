from __future__ import annotations

import logging
import time
from collections import deque
from typing import Dict, Optional

from backend.app.kernel.exceptions import RateLimitExceededError

logger = logging.getLogger("gula.kernel.gateway.rate_limiting")


class RateLimiter:
    def __init__(self):
        self._limits: dict[str, tuple[int, int]] = {}
        self._windows: dict[str, list[float]] = {}

    def set_limit(self, key: str, max_requests: int, window_seconds: int) -> None:
        self._limits[key] = (max_requests, window_seconds)

    def check(self, key: str) -> bool:
        import time
        limit = self._limits.get(key)
        if not limit:
            return True
        max_requests, window = limit
        now = time.time()
        if key not in self._windows:
            self._windows[key] = []
        self._windows[key] = [t for t in self._windows[key] if now - t < window]
        if len(self._windows[key]) >= max_requests:
            return False
        self._windows[key].append(now)
        return True
