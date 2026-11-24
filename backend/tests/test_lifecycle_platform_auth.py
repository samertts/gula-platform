"""Regression guard: app/lifecycle_platform routes must require authentication.

Every route in app/lifecycle_platform/api/routes.py (component registry,
releases, compatibility matrix, upgrade paths, deprecation notices) had
zero authentication or authorization dependency at all -- proven with a
real HTTP request via a fully anonymous TestClient: POST /lifecycle/components
returned 201 and created a real row with no Authorization header, no
cookie, nothing. This is the same severity class as the previously-fixed
pilot-platform-no-auth P0. Fixed with a router-level
Depends(require_permission("system:admin")) gate, the same convention
already used by every sibling "National X Platform" domain
(biomedical/command_center/public_health/critical_care).
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.database as _database
from app.database import get_db
from app.national.base import NationalBase
from app.lifecycle_platform.infrastructure.models import ComponentRegistryModel
from app.security.dependencies import get_current_user

PAYLOAD = {
    "name": "regression-test-component",
    "component_type": "service",
    "current_version": "1.0.0",
    "stage": "ga",
    "owner": "nobody",
}


@pytest.fixture()
def client(monkeypatch):
    db_engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    NationalBase.metadata.create_all(db_engine, tables=[ComponentRegistryModel.__table__])
    session_factory = sessionmaker(bind=db_engine, autoflush=False)
    db = session_factory()

    monkeypatch.setattr(_database, "SessionLocal", session_factory, raising=True)
    monkeypatch.setattr(_database, "engine", db_engine, raising=True)

    from app.main import app

    def _override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    try:
        with TestClient(app, raise_server_exceptions=True) as c:
            yield c
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_current_user, None)
        try:
            db.close()
        except Exception:
            pass


def test_unauthenticated_request_is_denied(client):
    client.app.dependency_overrides.pop(get_current_user, None)
    resp = client.post("/lifecycle/components", json=PAYLOAD)
    assert resp.status_code == 401


def test_wrong_role_is_denied(client):
    client.app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=1, role="lab_tech", lab_id=1)
    resp = client.post("/lifecycle/components", json={**PAYLOAD, "name": "wrong-role"})
    assert resp.status_code == 403


def test_system_admin_succeeds(client):
    client.app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=1, role="master_admin", lab_id=1)
    resp = client.post("/lifecycle/components", json={**PAYLOAD, "name": "authorized"})
    assert resp.status_code == 201
    assert resp.json()["name"] == "authorized"
