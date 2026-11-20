"""NC013-C02 — NIAM person, session and device routers require authentication."""

from __future__ import annotations

import asyncio

import pytest
from app.database import get_db
from app.identity.api import persons
from app.identity.api import router as niam_router_module
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient


async def _fake_db():
    yield object()


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(niam_router_module.router)
    app.dependency_overrides[get_db] = _fake_db
    return TestClient(app)


def test_person_create_requires_authentication() -> None:
    response = _client().post(
        "/niam/persons/",
        params={"given_name": "Synthetic", "family_name": "Person"},
    )
    assert response.status_code == 401


def test_person_read_requires_authentication() -> None:
    response = _client().get("/niam/persons/unknown-uuid")
    assert response.status_code == 401


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("GET", "/niam/sessions/account/synthetic-account"),
        ("POST", "/niam/devices/register"),
    ],
)
def test_session_and_device_routers_require_authentication(method: str, path: str) -> None:
    response = _client().request(method, path)
    assert response.status_code == 401


def test_person_miss_returns_http_404(monkeypatch: pytest.MonkeyPatch) -> None:
    class EmptyService:
        async def get_person_by_uuid(self, _uuid: str) -> None:
            return None

    monkeypatch.setattr(persons, "PersonService", lambda _db: EmptyService())

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(persons.get_person("unknown-uuid", db=object(), actor=object()))

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "not_found"
