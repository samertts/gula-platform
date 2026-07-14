from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


class TestWorkflow_engineAPI:
    @pytest.mark.asyncio
    async def test_health(self, client: TestClient):
        response = client.get("/workflow-engine/health/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
