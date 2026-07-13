from __future__ import annotations

import pytest

from backend.app.kernel import Kernel
from backend.app.kernel.runtime.context import ApplicationContext


class TestApplicationContext:
    def test_key_value_operations(self, kernel: Kernel):
        ctx = ApplicationContext(kernel)
        ctx.set("key1", "value1")
        assert ctx.get("key1") == "value1"
        assert ctx.get("nonexistent") is None
        ctx.clear()
        assert ctx.get("key1") is None

    def test_request_id(self, kernel: Kernel):
        ctx = ApplicationContext(kernel)
        ctx.set_request_id("req-123")
        assert ctx.get_request_id() == "req-123"

    def test_tenant_id(self, kernel: Kernel):
        ctx = ApplicationContext(kernel)
        ctx.set_tenant_id("tenant-1")
        assert ctx.get_tenant_id() == "tenant-1"

    def test_correlation_id(self, kernel: Kernel):
        ctx = ApplicationContext(kernel)
        ctx.set_correlation_id("corr-123")
        assert ctx.get_correlation_id() == "corr-123"
