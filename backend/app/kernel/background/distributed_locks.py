from __future__ import annotations

import logging
import time

logger = logging.getLogger("gula.kernel.background.locks")


class DistributedLock:
    def __init__(self, name: str, owner: str, ttl: float = 30.0):
        self.name = name
        self.owner = owner
        self.ttl = ttl
        self.acquired_at: float = time.time()

    @property
    def expired(self) -> bool:
        return time.time() - self.acquired_at > self.ttl


class DistributedLockManager:
    def __init__(self):
        self._locks: dict[str, DistributedLock] = {}

    def acquire(self, name: str, owner: str, ttl: float = 30.0) -> bool:
        if name in self._locks:
            existing = self._locks[name]
            if existing.expired:
                del self._locks[name]
            else:
                return False
        self._locks[name] = DistributedLock(name, owner, ttl)
        return True

    def release(self, name: str, owner: str) -> bool:
        lock = self._locks.get(name)
        if lock and lock.owner == owner:
            del self._locks[name]
            return True
        return False

    def is_locked(self, name: str) -> bool:
        lock = self._locks.get(name)
        if lock and lock.expired:
            del self._locks[name]
            return False
        return lock is not None
