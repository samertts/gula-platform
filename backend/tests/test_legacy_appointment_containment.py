from __future__ import annotations

from unittest.mock import Mock

import pytest
from fastapi import HTTPException

from app.national.scheduling_platform.api.routes import router as scheduling_router
from app.security.legacy_appointment import block_legacy_appointment_write


_MUTATION_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


def test_legacy_appointment_write_blocker_returns_gone_successor() -> None:
    request = Mock()
    request.url.path = "/national/scheduling/appointments"
    request.method = "POST"
    user = Mock(id=7, lab_id=11)

    with pytest.raises(HTTPException) as exc_info:
        block_legacy_appointment_write(request, user)

    assert exc_info.value.status_code == 410
    assert exc_info.value.headers["Deprecation"] == "true"
    assert exc_info.value.headers["Cache-Control"] == "no-store"
    assert "/api/v1/clinical/appointments" in exc_info.value.headers["Link"]


def test_legacy_appointment_mutations_are_contained_but_reads_remain_compatibility_only() -> None:
    appointment_routes = [
        route
        for route in scheduling_router.routes
        if getattr(route, "path", "").startswith("/national/scheduling/appointments")
    ]
    guarded_mutations = [
        route
        for route in appointment_routes
        if any(method in _MUTATION_METHODS for method in route.methods)
    ]
    assert guarded_mutations
    assert all(
        any(
            getattr(getattr(dependency, "dependency", None), "__name__", "") == "block_legacy_appointment_write"
            for dependency in route.dependencies
        )
        for route in guarded_mutations
    )
    assert any(route.methods == {"GET"} for route in appointment_routes)
