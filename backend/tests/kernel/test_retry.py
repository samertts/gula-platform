from __future__ import annotations

import pytest

from app.kernel.background.job_retry import JobRetry


class TestJobRetry:
    def test_retry_limit(self):
        jr = JobRetry()
        assert jr.should_retry("task_1")
        jr.increment("task_1")
        jr.increment("task_1")
        jr.increment("task_1")
        assert not jr.should_retry("task_1")

    def test_backoff(self):
        jr = JobRetry()
        jr.increment("task_1")
        backoff = jr.get_backoff("task_1")
        assert backoff == 2.0
        jr.increment("task_1")
        backoff = jr.get_backoff("task_1")
        assert backoff == 4.0
