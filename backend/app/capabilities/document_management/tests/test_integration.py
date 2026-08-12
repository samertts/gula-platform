from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


class TestDocument_managementAPI:
    @pytest.mark.asyncio
    async def test_health(self, client: TestClient):
        response = client.get("/document-management/health/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
