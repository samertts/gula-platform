from __future__ import annotations

import pytest


class TestSearch_serviceCapability:
    @pytest.fixture
    def capability(self):
        from app.capabilities.search_service.capability import Search_serviceCapability
        return Search_serviceCapability()

    @pytest.mark.asyncio
    async def test_execute_is_not_implemented(self, capability):
        """Pins the honest state. Asserting success here certified a stub (NR-089)."""
        with pytest.raises(NotImplementedError, match="must not report success"):
            await capability.execute({})

    @pytest.mark.asyncio
    async def test_validate_is_not_implemented(self, capability):
        with pytest.raises(NotImplementedError, match="no validation rules"):
            await capability.validate({})

    @pytest.mark.asyncio
    async def test_health_reports_scaffolding_not_ok(self, capability):
        """A health probe answers, but it must not answer "ok" for a stub."""
        report = await capability.health()
        assert report["status"] == "not_implemented"
