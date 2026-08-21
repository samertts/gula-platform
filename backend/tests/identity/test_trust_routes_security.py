from __future__ import annotations

import pytest
from app.identity.trust import routes
from fastapi import HTTPException


def test_trust_workflow_gate_fails_closed() -> None:
    with pytest.raises(HTTPException) as error:
        routes._reject_unscoped_trust_workflow()

    assert error.value.status_code == 410


def test_every_trust_route_inherits_fail_closed_gate() -> None:
    for route in routes.router.routes:
        dependency_calls = {dependency.call for dependency in route.dependant.dependencies}
        assert routes._reject_unscoped_trust_workflow in dependency_calls, route.path
