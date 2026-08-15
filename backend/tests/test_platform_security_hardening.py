from __future__ import annotations

from collections.abc import Iterator
from types import SimpleNamespace

import pytest
from app.database import get_db
from app.main import app
from app.security.dependencies import get_current_user
from app.security.policy import (
    normalize_collection_name,
    sanitize_request_id,
    tenant_collection_key,
)
from fastapi.testclient import TestClient


@pytest.fixture()  # type: ignore[misc,unused-ignore]
def client() -> Iterator[TestClient]:
    app.dependency_overrides[get_db] = lambda: object()
    try:
        with TestClient(app, raise_server_exceptions=False) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


def test_request_id_is_bounded_and_log_safe() -> None:
    assert sanitize_request_id("req-123:abc") == "req-123:abc"
    assert sanitize_request_id("bad\\nX-Trace: forged") != "bad\\nX-Trace: forged"
    assert len(sanitize_request_id("x" * 500)) == 36


def test_rag_collection_is_tenant_namespaced() -> None:
    user = SimpleNamespace(id=7, lab_id=42, role="doctor")
    assert tenant_collection_key(user, "clinical") == "lab:42:clinical"


def test_rag_collection_rejects_path_like_names() -> None:
    with pytest.raises(ValueError):
        normalize_collection_name("../shared")


def test_citizen_cannot_reach_internal_ai_fabric(client: TestClient) -> None:
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        id=9,
        lab_id=None,
        role="citizen",
        perm_version=1,
        is_active=True,
        is_verified=True,
    )
    try:
        response = client.get("/ai/fabric/health")
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 403


def test_doctor_cannot_read_ai_provider_inventory(client: TestClient) -> None:
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        id=7,
        lab_id=3,
        role="doctor",
        perm_version=1,
        is_active=True,
        is_verified=True,
    )
    try:
        response = client.get("/ai/fabric/gateway/providers")
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 403
