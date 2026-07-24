from __future__ import annotations

import pytest
from app.kernel.background.worker_pool import WorkerPool


class TestWorkerPool:
    def test_custom_size(self):
        wp = WorkerPool(size=4)
        assert wp.size == 4
        wp.start()
        wp.stop()

    def test_default_size(self):
        wp = WorkerPool()
        assert wp.size == 4
