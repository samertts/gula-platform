from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


class TestReporting_serviceAPI:
    @pytest.mark.asyncio
    async def test_health(self, client: TestClient):
        response = client.get("/reporting-service/health/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
