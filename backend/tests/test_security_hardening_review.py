from __future__ import annotations

from collections.abc import Iterator, Sequence
from types import SimpleNamespace
from unittest.mock import Mock

from app.routes import metrics
from app.security import rate_limit


def test_prometheus_metrics_fails_closed_without_production_bearer(monkeypatch) -> None:
    monkeypatch.setattr(metrics, "IS_PRODUCTION", True)
    monkeypatch.delenv("METRICS_BEARER_TOKEN", raising=False)

    request = SimpleNamespace(headers={})
    response = metrics.prometheus_metrics(request, db=Mock())

    assert response.status_code == 503
    assert response.body == b"Metrics authentication is not configured"


def test_auth_identifier_rate_limit_key_is_hmac_and_does_not_contain_identifier(monkeypatch) -> None:
    seen_keys: list[str] = []

    def allow(key: str, max_requests: int, window_seconds: int, request=None):
        seen_keys.append(key)
        return True, max_requests, 0

    monkeypatch.setattr(rate_limit, "_check", allow)
    monkeypatch.setenv("NID_HMAC_KEY", "n" * 64)
    request = SimpleNamespace(
        client=SimpleNamespace(host="198.51.100.10"),
        headers={},
    )

    rate_limit.rate_limit_auth(request, identifier="Person@example.com")

    assert len(seen_keys) == 2
    assert seen_keys[0].startswith("auth:")
    assert seen_keys[1].startswith("auth-id:")
    assert all("person@example.com" not in key for key in seen_keys)
    assert all("@" not in key for key in seen_keys)
    assert len(seen_keys[1].split(":", 1)[1]) == 64


def test_public_health_diagnostics_do_not_format_raw_exception_text() -> None:
    from pathlib import Path

    source = (Path(__file__).parents[1] / "app" / "main.py").read_text()

    assert "db_error = str(e)" not in source
    assert "redis_error = str(e)" not in source
    assert "db_err = str(e)" not in source
    assert "red_err = str(e)" not in source
    assert "queue_err = str(e)" not in source


def test_openapi_generation_has_unique_operation_ids_and_canonical_security_routes() -> None:
    from app.main import app

    schema = app.openapi()
    operations: list[str] = []
    for path_item in schema.get("paths", {}).values():
        for method, operation in path_item.items():
            if method.lower() in {"get", "post", "put", "patch", "delete", "options", "head"}:
                operation_id = operation.get("operationId")
                if operation_id:
                    operations.append(operation_id)

    assert len(operations) == len(set(operations))
    assert "/auth/change-password" in schema["paths"]
    assert "/integration/connectors" in schema["paths"]
    for path in ("/register", "/register/citizen", "/register/doctor"):
        operation = schema["paths"][path]["post"]
        assert operation.get("deprecated") is True, path
        assert "410" in operation["responses"], path
    history_operation = schema["paths"]["/history/{phone}"]["get"]
    assert history_operation.get("deprecated") is True
    assert "410" in history_operation["responses"]
    assert "/lims/orders/{order_id}/fhir-bundle" in schema["paths"]
    assert "application/fhir+json" in str(schema["paths"]["/lims/orders/{order_id}/fhir-bundle"])


def test_canonical_quality_and_connector_routes_are_unique() -> None:
    from app.main import app
    from fastapi.routing import APIRoute

    target_paths = {
        "/clinical/quality/benchmarks",
        "/clinical/quality/measurements",
        "/integration/connectors",
    }
    seen: dict[tuple[str, str], int] = {}

    def iter_routes(routes: Sequence[object], prefix: str = "") -> Iterator[APIRoute]:
        for route in routes:
            if isinstance(route, APIRoute):
                yield route
                continue
            original_router = getattr(route, "original_router", None)
            if original_router is not None:
                include_context = getattr(route, "include_context", None)
                included_prefix = getattr(include_context, "prefix", None) or prefix
                yield from iter_routes(original_router.routes, included_prefix)

    for route in iter_routes(app.routes):
        if route.path not in target_paths:
            continue
        for method in route.methods or set():
            key = (method, route.path)
            seen[key] = seen.get(key, 0) + 1

    assert seen
    assert all(count == 1 for count in seen.values()), seen


def test_citizen_family_and_notifications_routes_require_relationship_guard() -> None:
    from app.citizen_platform.routes import require_citizen_relationship
    from app.main import app
    from fastapi.routing import APIRoute

    expected = {"/citizen-platform/me/family", "/citizen-platform/me/notifications"}
    found: dict[str, APIRoute] = {}

    def iter_routes(routes: Sequence[object]) -> Iterator[APIRoute]:
        for route in routes:
            if isinstance(route, APIRoute):
                yield route
                continue
            original_router = getattr(route, "original_router", None)
            if original_router is not None:
                yield from iter_routes(original_router.routes)

    for route in iter_routes(app.routes):
        if route.path in expected:
            found[route.path] = route
    assert set(found) == expected
    for path, route in found.items():
        dependency_calls = {getattr(dependency.call, "__name__", "") for dependency in route.dependant.dependencies}
        assert require_citizen_relationship.__name__ in dependency_calls, path


def test_person_and_device_routes_require_server_side_actor() -> None:
    from app.identity.api.workspaces import get_current_niam_actor
    from app.main import app
    from fastapi.routing import APIRoute

    def iter_routes(
        routes: Sequence[object], prefix: str = ""
    ) -> Iterator[tuple[APIRoute, str]]:
        for route in routes:
            if isinstance(route, APIRoute):
                path = f"{prefix.rstrip('/')}{route.path or '/'}"
                yield route, path
                continue
            original_router = getattr(route, "original_router", None)
            if original_router is not None:
                include_context = getattr(route, "include_context", None)
                included_prefix = getattr(include_context, "prefix", None) or prefix
                yield from iter_routes(original_router.routes, included_prefix)

    protected_paths = [
        (route, path)
        for route, path in iter_routes(app.routes)
        if path.startswith(("/niam/persons", "/niam/devices"))
    ]
    assert protected_paths
    for route, path in protected_paths:
        dependency_calls = {getattr(dependency.call, "__name__", "") for dependency in route.dependant.dependencies}
        assert get_current_niam_actor.__name__ in dependency_calls, path
