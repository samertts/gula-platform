"""NIAM Lifecycle Category-F closure, class 4 of 5: GovernmentHRService.

Same shape as WorkforceService: no self-service angle anywhere, no
existing PlatformCapability that fits "government HR appointing
authority" -- and unlike WorkforceService, this class has no read route
at all. All 9 routes fail closed. See
docs/security/NIAM_SYNC_ASYNC_LIFECYCLE_F4_GOVERNMENT_HR_STATUS.md.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from app.identity.lifecycle import routes as lifecycle_routes
from fastapi import HTTPException

_MUTATING_ROUTES = [
    (lifecycle_routes.create_government_appointment, {
        "appointment_id": "a1", "person_id": "p1", "organization_id": "org1",
        "hr_reference": "hr-ref-1", "appointment_type": "civil_servant",
    }),
    (lifecycle_routes.approve_government_appointment, {"appointment_id": "a1", "approved_by": "hr1"}),
    (lifecycle_routes.create_government_identity, {"appointment_id": "a1"}),
    (lifecycle_routes.issue_government_credential, {"appointment_id": "a1"}),
    (lifecycle_routes.activate_government_account, {"appointment_id": "a1"}),
    (lifecycle_routes.assign_government_permissions, {"appointment_id": "a1"}),
    (lifecycle_routes.promote_government_employee, {"appointment_id": "a1", "new_position": "p2", "new_grade": "g2"}),
    (lifecycle_routes.transfer_government_employee, {"appointment_id": "a1"}),
    (lifecycle_routes.retire_government_employee, {"appointment_id": "a1", "retirement_date": None}),
]


def _actor():
    return SimpleNamespace(account=SimpleNamespace(id="ACCOUNT-1", identity_id="IDENTITY-1"))


@pytest.mark.asyncio
@pytest.mark.parametrize("route_fn,kwargs", _MUTATING_ROUTES, ids=[fn.__name__ for fn, _ in _MUTATING_ROUTES])
async def test_every_government_hr_route_fails_closed_for_any_actor(monkeypatch, route_fn, kwargs):
    db = object()
    monkeypatch.setattr(lifecycle_routes, "GovernmentHRService", lambda _db: SimpleNamespace(**{
        name: AsyncMock(side_effect=AssertionError(f"must not reach service.{name}"))
        for name in (
            "create_appointment", "approve_appointment", "create_identity", "issue_credential",
            "activate_account", "assign_permissions", "promote", "transfer", "retire",
        )
    }))
    with pytest.raises(HTTPException) as exc:
        await route_fn(db=db, actor=_actor(), **kwargs)
    assert exc.value.status_code == 403
    assert "administrative authority" in exc.value.detail
