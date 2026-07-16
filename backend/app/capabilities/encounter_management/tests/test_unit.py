from __future__ import annotations

import pytest


class TestEncounter_managementCapability:
    @pytest.fixture
    def capability(self):
        from app.capabilities.encounter_management.capability import (
            Encounter_managementCapability,
        )
        return Encounter_managementCapability()

    @pytest.mark.asyncio
    async def test_execute(self, capability):
        result = await capability.execute({})
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_validate(self, capability):
        result = await capability.validate({})
        assert result is True
