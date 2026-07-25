from __future__ import annotations

import pytest


class TestStorage_serviceCapability:
    @pytest.fixture
    def capability(self):
        from app.capabilities.storage_service.capability import Storage_serviceCapability

        return Storage_serviceCapability()

    @pytest.mark.asyncio
    async def test_execute(self, capability):
        result = await capability.execute({})
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_validate(self, capability):
        result = await capability.validate({})
        assert result is True
