from app.main import app
from app.security.auth import API_KEY_ENV, verify_api_key
from _test_support import TEST_API_KEY
from fastapi import HTTPException
from fastapi.testclient import TestClient
import pytest


def test_auth_required() -> None:
    client = TestClient(app)
    response = client.get("/devices")
    assert response.status_code == 401


def test_auth_missing_configuration_is_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(API_KEY_ENV, raising=False)
    with pytest.raises(HTTPException) as error:
        verify_api_key(None)
    assert error.value.status_code == 503


def test_mode_and_sync_endpoints() -> None:
    client = TestClient(app)
    headers = {"x-api-key": TEST_API_KEY}

    response = client.post("/mode", json={"mode": "hybrid"}, headers=headers)
    assert response.status_code == 200

    response = client.get("/mode", headers=headers)
    assert response.status_code == 200
    assert response.json()["mode"] == "hybrid"

    response = client.post("/edge/sync", headers=headers)
    assert response.status_code == 200
    assert "sent" in response.json()
