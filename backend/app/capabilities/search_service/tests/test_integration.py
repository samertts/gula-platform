from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


class TestSearch_serviceAPI:
    @pytest.mark.asyncio
    async def test_health(self, client: TestClient):
        response = client.get("/search-service/health/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
