from __future__ import annotations

import asyncio
import inspect

from fastapi.responses import PlainTextResponse
from starlette.requests import Request

from app import middleware as middleware_module
from app.middleware import DemoReadOnlyMiddleware
from app.routes import demo as demo_module


def _request(method: str, path: str) -> Request:
    return Request(
        {
            "type": "http",
            "http_version": "1.1",
            "method": method,
            "scheme": "https",
            "path": path,
            "raw_path": path.encode(),
            "query_string": b"",
            "headers": [],
            "client": ("127.0.0.1", 12345),
            "server": ("demo.local", 443),
        },
    )


async def _ok_next(_request: Request):
    return PlainTextResponse("ok")


def test_public_demo_exposes_safe_personas():
    personas = demo_module.__dict__["_DEMO_PERSONAS"]
    assert set(personas) == {"doctor", "technician", "lab_admin", "citizen"}
    assert personas["doctor"]["role"] == "doctor"
    assert personas["technician"]["role"] == "technician"
    assert personas["lab_admin"]["role"] == "lab_admin"
    assert personas["citizen"]["role"] == "citizen"
    assert demo_module.__dict__["_DEFAULT_DEMO_PERSONA"] == "doctor"
    assert "DEMO_MODE" in inspect.getsource(demo_module._demo_unavailable)


def test_demo_access_creates_each_persona_in_isolated_lab(client, db, monkeypatch):
    monkeypatch.setattr(demo_module, "DEMO_MODE", True)
    monkeypatch.setattr(demo_module, "IS_PRODUCTION", False)
    monkeypatch.setattr(demo_module, "rate_limit_auth", lambda _request: None)

    for persona_id, expected_role in (("doctor", "doctor"), ("technician", "technician"), ("lab_admin", "lab_admin"), ("citizen", "citizen")):
        response = client.post(f"/demo/access?persona={persona_id}")
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["demo_mode"] is True
        assert body["demo_persona"] == persona_id
        assert body["user"]["role"] == expected_role
        assert body["user"]["lab_name"] == "GULA Synthetic Demo Lab"

    users = db.query(demo_module.LabUser).filter(demo_module.LabUser.email.like("demo.%@gula-demo.iq")).all()
    assert {user.role for user in users} == {"doctor", "technician", "lab_admin", "citizen"}
    assert len({user.email for user in users}) == 4

    doctor = db.query(demo_module.LabUser).filter(demo_module.LabUser.email == "demo.doctor@gula-demo.iq").one()
    doctor.role = "master_admin"
    db.commit()
    rejected = client.post("/demo/access?persona=doctor")
    assert rejected.status_code == 503


def test_demo_read_only_blocks_mutations(monkeypatch):
    monkeypatch.setattr(middleware_module, "DEMO_MODE", True)
    middleware = DemoReadOnlyMiddleware(lambda _scope: None)

    blocked = asyncio.run(middleware.dispatch(_request("POST", "/patients"), _ok_next))
    assert blocked.status_code == 405

    allowed = asyncio.run(middleware.dispatch(_request("POST", "/demo/access"), _ok_next))
    assert allowed.status_code == 200

    refresh = asyncio.run(middleware.dispatch(_request("POST", "/auth/refresh"), _ok_next))
    assert refresh.status_code == 200


def test_demo_read_only_is_inactive_outside_demo(monkeypatch):
    monkeypatch.setattr(middleware_module, "DEMO_MODE", False)
    middleware = DemoReadOnlyMiddleware(lambda _scope: None)

    response = asyncio.run(middleware.dispatch(_request("POST", "/patients"), _ok_next))
    assert response.status_code == 200
