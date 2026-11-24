from app.main import app
from fastapi.testclient import TestClient


def test_auth_required() -> None:
    client = TestClient(app)
    response = client.get("/devices")
    assert response.status_code == 401


def test_mode_and_sync_endpoints(api_key_headers) -> None:
    client = TestClient(app)
    headers = api_key_headers

    response = client.post("/mode", json={"mode": "hybrid"}, headers=headers)
    assert response.status_code == 200

    response = client.get("/mode", headers=headers)
    assert response.status_code == 200
    assert response.json()["mode"] == "hybrid"

    response = client.post("/edge/sync", headers=headers)
    assert response.status_code == 200
    assert "sent" in response.json()
