from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


class TestClinical_foundationAPI:
    @pytest.mark.asyncio
    async def test_health(self, client: TestClient):
        response = client.get("/clinical-foundation/health/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
