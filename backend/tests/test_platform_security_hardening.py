from __future__ import annotations

from collections.abc import Callable, Iterator
from types import SimpleNamespace
from typing import cast

import pytest
from app.database import get_db
from app.models.audit_log import AuditLog
from app.main import app
from app.security.dependencies import get_current_user
from app.security.policy import (
    normalize_collection_name,
    sanitize_request_id,
    tenant_collection_key,
)
from fastapi import HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.testclient import TestClient
from app.security.auth import create_token


def _typed_fixture(
    function: Callable[..., Iterator[TestClient]],
) -> Callable[..., Iterator[TestClient]]:
    return cast(Callable[..., Iterator[TestClient]], pytest.fixture()(function))


@_typed_fixture
def client() -> Iterator[TestClient]:
    app.dependency_overrides[get_db] = object
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


def test_jwt_lab_scope_must_match_authoritative_user(db, make_lab, make_lab_user) -> None:
    lab = make_lab(name="JWT Scope Lab")
    user = make_lab_user(lab_id=lab.id, role="doctor", email="jwt-scope@example.com")
    db.commit()
    token = create_token({"user_id": user.id, "lab_id": lab.id + 1000, "role": user.role})
    request = Request({"type": "http", "method": "GET", "path": "/", "headers": []})
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    with pytest.raises(HTTPException) as exc:
        get_current_user(request, credentials, db)
    assert exc.value.status_code == 401


def test_jwt_permission_version_must_be_positive_integer(db, make_lab, make_lab_user) -> None:
    lab = make_lab(name="JWT Version Lab")
    user = make_lab_user(lab_id=lab.id, role="doctor", email="jwt-version@example.com")
    db.commit()
    token = create_token({"user_id": user.id, "lab_id": lab.id, "role": user.role, "perm_ver": "invalid"})
    request = Request({"type": "http", "method": "GET", "path": "/", "headers": []})
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    with pytest.raises(HTTPException) as exc:
        get_current_user(request, credentials, db)
    assert exc.value.status_code == 401


def test_security_headers_cover_api_and_static_responses(client: TestClient) -> None:
    for path in ("/health", "/assets/not-present.js"):
        response = client.get(path)
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-Frame-Options"] == "DENY"
        assert response.headers["X-Permitted-Cross-Domain-Policies"] == "none"
        assert "Content-Security-Policy" in response.headers


def test_audit_log_is_tenant_scoped_for_institutional_auditor(db, make_lab, make_lab_user) -> None:
    lab_a = make_lab(name="Audit Lab A")
    lab_b = make_lab(name="Audit Lab B")
    auditor = make_lab_user(lab_id=lab_a.id, role="admin", email="auditor@example.com")
    db.add_all([
        AuditLog(user_id=auditor.id, user_role="admin", lab_id=lab_a.id, action="read", resource_type="Patient", resource_id=7, details="same lab"),
        AuditLog(user_id=auditor.id, user_role="admin", lab_id=lab_b.id, action="read", resource_type="Patient", resource_id=7, details="other lab"),
    ])
    db.commit()
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: auditor
    try:
        with TestClient(app, raise_server_exceptions=False) as test_client:
            response = test_client.get("/national/security/audit/Patient/7")
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_current_user, None)
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["details"] == "same lab"


def test_cors_preflight_allows_device_session_header(client: TestClient) -> None:
    response = client.options(
        "/national/sync/status",
        headers={
            "Origin": "https://gula-platform.org",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "X-Device-Session",
        },
    )
    assert response.status_code in {200, 204}
    assert "X-Device-Session" in response.headers.get("access-control-allow-headers", "")


def test_doctor_cannot_activate_break_glass_without_critical_permission(client: TestClient) -> None:
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        id=7,
        lab_id=3,
        role="doctor",
        perm_version=1,
        is_active=True,
        is_verified=True,
    )
    try:
        response = client.post(
            "/national/security/break-glass",
            json={"citizen_id": "citizen-1", "reason": "routine review"},
        )
    finally:
        app.dependency_overrides.pop(get_current_user, None)
    assert response.status_code == 403


def test_doctor_cannot_read_audit_log_without_audit_permission(client: TestClient) -> None:
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        id=7,
        lab_id=3,
        role="doctor",
        perm_version=1,
        is_active=True,
        is_verified=True,
    )
    try:
        response = client.get("/national/security/audit/Patient/7")
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
