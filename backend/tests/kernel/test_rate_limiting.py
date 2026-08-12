from __future__ import annotations

import time

import pytest

from app.kernel.gateway.rate_limiting import RateLimiter


class TestRateLimiter:
    def test_limit_enforcement(self):
        rl = RateLimiter()
        rl.set_limit("test_key", 2, 60)
        assert rl.check("test_key")
        assert rl.check("test_key")
        assert not rl.check("test_key")

    def test_no_limit(self):
        rl = RateLimiter()
        assert rl.check("unlimited_key")

    def test_window_cleanup(self):
        rl = RateLimiter()
        rl.set_limit("key", 5, 0.01)
        assert rl.check("key")
        time.sleep(0.02)
        assert rl.check("key")
