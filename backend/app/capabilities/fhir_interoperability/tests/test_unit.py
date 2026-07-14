from __future__ import annotations

import pytest


class TestFhir_interoperabilityCapability:
    @pytest.fixture
    def capability(self):
        from backend.app.capabilities.fhir_interoperability.capability import Fhir_interoperabilityCapability
        return Fhir_interoperabilityCapability()

    @pytest.mark.asyncio
    async def test_execute(self, capability):
        result = await capability.execute({})
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_validate(self, capability):
        result = await capability.validate({})
        assert result is True
