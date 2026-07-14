from __future__ import annotations

import pytest


class TestClinical_foundationCapability:
    @pytest.fixture
    def capability(self):
        from backend.app.capabilities.clinical_foundation.capability import Clinical_foundationCapability
        return Clinical_foundationCapability()

    @pytest.mark.asyncio
    async def test_execute(self, capability):
        result = await capability.execute({})
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_validate(self, capability):
        result = await capability.validate({})
        assert result is True
