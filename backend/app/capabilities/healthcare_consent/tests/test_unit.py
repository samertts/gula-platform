from __future__ import annotations

import pytest


class TestHealthcare_consentCapability:
    @pytest.fixture
    def capability(self):
        from backend.app.capabilities.healthcare_consent.capability import Healthcare_consentCapability
        return Healthcare_consentCapability()

    @pytest.mark.asyncio
    async def test_execute(self, capability):
        result = await capability.execute({})
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_validate(self, capability):
        result = await capability.validate({})
        assert result is True
