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


def test_public_demo_uses_read_only_doctor_role():
    assert demo_module.__dict__["_DEMO_EMAIL"] == "demo.viewer@gula-demo.iq"
    assert 'role="doctor"' in inspect.getsource(demo_module.start_demo_session)


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
