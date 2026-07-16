from __future__ import annotations

import pytest


class TestReporting_serviceCapability:
    @pytest.fixture
    def capability(self):
        from app.capabilities.reporting_service.capability import (
            Reporting_serviceCapability,
        )
        return Reporting_serviceCapability()

    @pytest.mark.asyncio
    async def test_execute(self, capability):
        result = await capability.execute({})
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_validate(self, capability):
        result = await capability.validate({})
        assert result is True
