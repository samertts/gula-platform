from __future__ import annotations

from types import SimpleNamespace

import pytest
from app.routes import clinical_documentation, clinical_orders
from app.security.legacy_clinical import block_legacy_clinical_route
from fastapi import HTTPException
from starlette.requests import Request


def _request(path: str, method: str = "POST") -> Request:
    return Request(
        {
            "type": "http",
            "method": method,
            "path": path,
            "raw_path": path.encode(),
            "query_string": b"",
            "headers": [],
            "client": ("test", 1234),
            "server": ("test", 80),
            "scheme": "http",
        }
    )


def test_legacy_documentation_router_is_fail_closed():
    dependency_calls = [dependency.dependency for dependency in clinical_documentation.router.dependencies]
    assert block_legacy_clinical_route in dependency_calls


def test_legacy_orders_router_is_fail_closed():
    dependency_calls = [dependency.dependency for dependency in clinical_orders.router.dependencies]
    assert block_legacy_clinical_route in dependency_calls


def test_legacy_guard_returns_explicit_deprecation_response():
    with pytest.raises(HTTPException) as captured:
        block_legacy_clinical_route(
            _request("/clinical/documentation/soap-notes"),
            SimpleNamespace(id=7, role="doctor"),
        )

    error = captured.value
    assert error.status_code == 410
    assert error.headers["Deprecation"] == "true"
    assert error.headers["Cache-Control"] == "no-store"
    assert "/api/v1/clinical" in error.headers["Link"]
