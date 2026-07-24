from __future__ import annotations

import asyncio

import pytest
from app.kernel.config.registry import ConfigurationRegistry
from app.kernel.config.reload import RuntimeReloader


class TestRuntimeReloader:
    def test_on_reload_hook(self):
        cr = ConfigurationRegistry()
        reloader = RuntimeReloader(cr)
        called = []

        async def hook():
            called.append(True)

        reloader.on_reload(hook)
        asyncio.run(reloader.reload())
        assert len(called) == 1
