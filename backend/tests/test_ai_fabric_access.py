from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.database import get_db
from app.main import app
from app.security.dependencies import get_current_user


@pytest.fixture()
def client():
    # Anonymous requests fail before the DB object is used; this keeps the test
    # isolated from the production database configuration.
    app.dependency_overrides[get_db] = lambda: object()
    try:
        with TestClient(app, raise_server_exceptions=False) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


def test_ai_fabric_requires_authentication(client):
    response = client.get("/ai/fabric/health")
    assert response.status_code == 401


def test_radiology_requires_authentication(client):
    response = client.get("/radiology/orders")
    assert response.status_code == 401


def test_decision_support_requires_authentication(client):
    response = client.post(
        "/api/ai/v2/decision-support/query",
        json={"patient_id": "1", "query": "clinical question"},
    )
    assert response.status_code == 401


def test_ai_fabric_admin_operations_require_system_permission(client):
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        id=7,
        lab_id=3,
        role="doctor",
    )
    try:
        response = client.post(
            "/ai/fabric/rag/index",
            params={"collection": "test", "texts": "should-not-index"},
        )
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 403
