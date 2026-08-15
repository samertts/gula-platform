from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client():
    from app.main import app

    with TestClient(app) as test_client:
        yield test_client


class TestFhir_interoperabilityAPI:
    def test_health(self, client: TestClient):
        response = client.get("/fhir-interoperability/health/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
