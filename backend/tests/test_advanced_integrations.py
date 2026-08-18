from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


def test_smart_app_launch_discovery(client: TestClient):
    resp = client.get("/.well-known/smart-configuration")
    assert resp.status_code == 200
    data = resp.json()
    assert "issuer" in data
    assert "authorization_endpoint" in data
    assert "token_endpoint" in data
    assert "capabilities" in data
    assert "launch-standalone" in data["capabilities"]

def test_openhim_gateway_status_unauthorized(client: TestClient):
    resp = client.get("/integrations/openhim/gateway-status")
    assert resp.status_code in {401, 403}

def test_snowstorm_terminology_status_unauthorized(client: TestClient):
    resp = client.get("/integrations/snowstorm/terminology-status")
    assert resp.status_code in {401, 403}
