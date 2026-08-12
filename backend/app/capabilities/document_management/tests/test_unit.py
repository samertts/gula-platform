from __future__ import annotations

import pytest


class TestDocument_managementCapability:
    @pytest.fixture
    def capability(self):
        from app.capabilities.document_management.capability import (
            Document_managementCapability,
        )
        return Document_managementCapability()

    @pytest.mark.asyncio
    async def test_execute(self, capability):
        result = await capability.execute({})
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_validate(self, capability):
        result = await capability.validate({})
        assert result is True
