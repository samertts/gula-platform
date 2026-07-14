from __future__ import annotations

import pytest


class TestProvider_managementCapability:
    @pytest.fixture
    def capability(self):
        from backend.app.capabilities.provider_management.capability import Provider_managementCapability
        return Provider_managementCapability()

    @pytest.mark.asyncio
    async def test_execute(self, capability):
        result = await capability.execute({})
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_validate(self, capability):
        result = await capability.validate({})
        assert result is True
