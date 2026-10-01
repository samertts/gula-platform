from app.main import app
from app.security.auth import API_KEY_ENV
from fastapi.testclient import TestClient


def test_auth_required() -> None:
    client = TestClient(app)
    response = client.get("/devices")
    assert response.status_code == 503


def test_mode_and_sync_endpoints(monkeypatch) -> None:
    monkeypatch.setenv(API_KEY_ENV, "synthetic-device-test-key")
    client = TestClient(app)
    headers = {"x-api-key": "synthetic-device-test-key"}

    response = client.post("/mode", json={"mode": "hybrid"}, headers=headers)
    assert response.status_code == 200

    response = client.get("/mode", headers=headers)
    assert response.status_code == 200
    assert response.json()["mode"] == "hybrid"

    response = client.post("/edge/sync", headers=headers)
    assert response.status_code == 200
    assert "sent" in response.json()
