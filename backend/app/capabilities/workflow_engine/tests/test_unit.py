from __future__ import annotations

import pytest


class TestWorkflow_engineCapability:
    @pytest.fixture
    def capability(self):
        from app.capabilities.workflow_engine.capability import Workflow_engineCapability

        return Workflow_engineCapability()

    @pytest.mark.asyncio
    async def test_execute(self, capability):
        result = await capability.execute({})
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_validate(self, capability):
        result = await capability.validate({})
        assert result is True
