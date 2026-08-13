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
