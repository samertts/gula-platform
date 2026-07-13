from __future__ import annotations

import time

import pytest

from backend.app.kernel.background.distributed_locks import DistributedLock, DistributedLockManager


class TestDistributedLocks:
    def test_acquire_and_release(self):
        dlm = DistributedLockManager()
        assert dlm.acquire("resource_1", "worker_1")
        assert not dlm.acquire("resource_1", "worker_2")
        assert dlm.release("resource_1", "worker_1")
        assert dlm.acquire("resource_1", "worker_2")

    def test_lock_expiry(self):
        lock = DistributedLock(name="test", owner="worker", ttl=0.01)
        time.sleep(0.02)
        assert lock.expired

    def test_manager_expiry(self):
        dlm = DistributedLockManager()
        dlm.acquire("test", "worker_1", ttl=0.01)
        time.sleep(0.02)
        assert dlm.acquire("test", "worker_2")
