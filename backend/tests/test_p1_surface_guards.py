from __future__ import annotations

from fastapi.routing import APIRoute

from app.certification.routes import _require_certification_admin, router as certification_router
from app.contracts.routes import _require_contract_export_admin, router as contracts_router


def _route(router, path: str, method: str) -> APIRoute:
    return next(
        route
        for route in router.routes
        if isinstance(route, APIRoute)
        and route.path == path
        and method.upper() in (route.methods or set())
    )


def _dependency_calls(route: APIRoute) -> set[object]:
    return {dependency.call for dependency in route.dependant.dependencies}


def test_certification_routes_require_system_admin():
    routes = [route for route in certification_router.routes if isinstance(route, APIRoute)]
    assert routes
    for route in routes:
        assert _require_certification_admin in _dependency_calls(route), route.path


def test_contract_export_requires_system_admin():
    route = _route(contracts_router, "/contracts/export", "POST")
    assert _require_contract_export_admin in _dependency_calls(route)


def test_read_only_contract_routes_remain_available_for_public_contract_consumers():
    route = _route(contracts_router, "/contracts/openapi.json", "GET")
    assert _require_contract_export_admin not in _dependency_calls(route)
