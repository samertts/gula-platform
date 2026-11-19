"""NIAM Lifecycle Category-F closure, class 3 of 5: WorkforceService.

WorkforceService has no self-service angle anywhere (organization/HR-side
onboarding actions performed on a person, never by them), and none of the
4 existing PlatformCapability values model "workforce onboarding
authority" -- so every mutation fails closed for everyone, deterministic
403, until a real capability is designed. See
docs/security/NIAM_SYNC_ASYNC_LIFECYCLE_F3_WORKFORCE_STATUS.md.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from app.identity.lifecycle import routes as lifecycle_routes
from fastapi import HTTPException

_MUTATING_ROUTES = [
    (lifecycle_routes.request_employee, {
        "request_id": "r1", "request_type": "hire", "requesting_org_id": "org1", "requested_by": "hr1",
    }),
    (lifecycle_routes.validate_workforce_national_id, {"request_id": "r1", "national_id_hash": "h"}),
    (lifecycle_routes.validate_workforce_license, {"request_id": "r1", "license_number": "L1"}),
    (lifecycle_routes.check_workforce_conflicts, {"request_id": "r1"}),
    (lifecycle_routes.approve_workforce_request, {"request_id": "r1", "approved_by": "hr1"}),
    (lifecycle_routes.activate_workforce_account, {"request_id": "r1"}),
    (lifecycle_routes.terminate_workforce_employment, {"request_id": "r1", "reason": "x"}),
    (lifecycle_routes.preserve_workforce_history, {"person_id": "p1"}),
]


def _actor():
    return SimpleNamespace(account=SimpleNamespace(id="ACCOUNT-1", identity_id="IDENTITY-1"))


@pytest.mark.asyncio
@pytest.mark.parametrize("route_fn,kwargs", _MUTATING_ROUTES, ids=[fn.__name__ for fn, _ in _MUTATING_ROUTES])
async def test_every_workforce_mutation_fails_closed_for_any_actor(monkeypatch, route_fn, kwargs):
    db = object()
    monkeypatch.setattr(lifecycle_routes, "WorkforceService", lambda _db: SimpleNamespace(**{
        name: AsyncMock(side_effect=AssertionError(f"must not reach service.{name}"))
        for name in (
            "request_employee", "validate_national_id", "validate_license", "check_conflicts",
            "approve_request", "activate_account", "terminate_employment", "preserve_history",
        )
    }))
    with pytest.raises(HTTPException) as exc:
        await route_fn(db=db, actor=_actor(), **kwargs)
    assert exc.value.status_code == 403
    assert "administrative authority" in exc.value.detail


@pytest.mark.asyncio
async def test_get_request_status_is_a_read_with_no_gate(monkeypatch):
    db = object()
    fake_svc = SimpleNamespace(get_request_status=AsyncMock(return_value=None))
    monkeypatch.setattr(lifecycle_routes, "WorkforceService", lambda _db: fake_svc)
    result = await lifecycle_routes.get_workforce_request_status(request_id="r1", db=db, actor=_actor())
    assert result == {"request": None}
    fake_svc.get_request_status.assert_awaited_once_with("r1")
