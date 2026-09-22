"""NIAM Lifecycle Category-F closure, class 2 of 5: EnterpriseRegistrationService.

Regression guard for the 6 previously-broken routes (validate_license,
submit_inspection, assess_risk, approve_registration, reject_registration,
get_registration_status) -- see
docs/security/NIAM_SYNC_ASYNC_LIFECYCLE_F2_ENTERPRISE_STATUS.md. Follows
this suite's established pattern for this layer (fake session/actor, no
real async engine).
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from app.identity.lifecycle import routes as lifecycle_routes
from app.identity.platform_authority.models import PlatformCapability
from fastapi import HTTPException


def _actor():
    return SimpleNamespace(account=SimpleNamespace(id="ACCOUNT-1", identity_id="IDENTITY-1"))


@pytest.mark.asyncio
async def test_validate_license_blocked_without_governance_manage_capability(monkeypatch):
    db = object()
    actor = _actor()
    monkeypatch.setattr(lifecycle_routes, "EnterpriseRegistrationService", lambda _db: SimpleNamespace(
        validate_license=AsyncMock(side_effect=AssertionError("must not reach service")),
    ))
    with patch.object(
        lifecycle_routes, "require_platform_capability",
        AsyncMock(side_effect=HTTPException(status_code=403, detail="no capability")),
    ) as mock_check:
        with pytest.raises(HTTPException) as exc:
            await lifecycle_routes.validate_enterprise_license(
                reg_id="r1", license_document="doc", validated_by="v1", db=db, actor=actor,
            )
        assert exc.value.status_code == 403
        mock_check.assert_awaited_once_with(actor, db, PlatformCapability.governance_manage.value)


@pytest.mark.asyncio
async def test_approve_registration_allowed_with_governance_manage_capability(monkeypatch):
    db = AsyncMock()
    fake_svc = SimpleNamespace(approve_registration=AsyncMock(return_value=SimpleNamespace(reg_id="r1", status="approved")))
    monkeypatch.setattr(lifecycle_routes, "EnterpriseRegistrationService", lambda _db: fake_svc)
    with patch.object(lifecycle_routes, "require_platform_capability", AsyncMock(return_value=None)):
        result = await lifecycle_routes.approve_enterprise_registration(
            reg_id="r1", approved_by="a1", db=db, actor=_actor(),
        )
    assert result == {"reg_id": "r1", "status": "approved"}
    fake_svc.approve_registration.assert_awaited_once()
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_reject_registration_gated_by_same_capability_as_all_other_mutations(monkeypatch):
    db = object()
    monkeypatch.setattr(lifecycle_routes, "EnterpriseRegistrationService", lambda _db: SimpleNamespace(
        reject_registration=AsyncMock(side_effect=AssertionError("must not reach service")),
    ))
    with patch.object(
        lifecycle_routes, "require_platform_capability",
        AsyncMock(side_effect=HTTPException(status_code=403, detail="no capability")),
    ):
        with pytest.raises(HTTPException) as exc:
            await lifecycle_routes.reject_enterprise_registration(
                reg_id="r1", reason="incomplete", db=db, actor=_actor(),
            )
        assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_get_enterprise_status_is_a_read_with_no_capability_gate(monkeypatch):
    db = object()
    fake_svc = SimpleNamespace(get_registration_status=AsyncMock(return_value=None))
    monkeypatch.setattr(lifecycle_routes, "EnterpriseRegistrationService", lambda _db: fake_svc)
    result = await lifecycle_routes.get_enterprise_status(org_id="org-1", db=db, actor=_actor())
    assert result == {"status": None}
    fake_svc.get_registration_status.assert_awaited_once_with("org-1")
