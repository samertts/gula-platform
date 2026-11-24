"""B1 — centralized per-action PHI permission map (owner directive §5/B1).

Proves that eight distinct PHI actions have distinct permission keys, that
unmapped actions fail closed, and that the canonical authorization engine
rejects a caller-supplied broad/substitute key for a PHI resource.

Disposable synthetic objects only; no database, Redis, or real data.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest
from app._compat import UTC
from app.identity.models.account import Account, AccountStatus
from app.identity.models.membership import Membership, MembershipStatus
from app.identity.models.session import UserSession
from app.identity.services.authorization_decision import (
    AuthorizationActor,
    AuthorizationDecisionService,
    AuthorizationReason,
    AuthorizationRequest,
)
from app.identity.services.phi_permission_map import (
    PHI_ACTIONS,
    PHI_RESOURCE_TYPES,
    PhiPermissionUnresolved,
    canonical_phi_action,
    require_phi_permission,
    resolve_phi_permission,
)

# ── pure map ──────────────────────────────────────────────────────────────────


def test_eight_distinct_phi_actions():
    assert {
        "read", "create", "update", "delete", "export", "print", "share", "administrative",
    } == PHI_ACTIONS


def test_per_resource_actions_are_distinct_and_explicit():
    keys = [resolve_phi_permission("lab_result", action) for action in sorted(PHI_ACTIONS)]
    assert len(keys) == len(set(keys))
    assert set(keys) == {
        f"lab_result.{action}" for action in sorted(PHI_ACTIONS)
    }


def test_alias_administer_maps_to_administrative():
    assert canonical_phi_action("administer") == "administrative"
    assert resolve_phi_permission("lab_result", "administer") == "lab_result.administrative"


def test_unmapped_action_and_non_phi_resource_fail_closed():
    assert resolve_phi_permission("lab_result", "delete_everything") is None
    assert resolve_phi_permission("public_announcement", "read") is None
    assert canonical_phi_action(123) is None  # type: ignore[arg-type]
    with pytest.raises(PhiPermissionUnresolved):
        require_phi_permission("lab_result", "delete_everything")


def test_phi_resource_registry_contains_canonical_types():
    assert {"patient_record", "lab_result", "lab_order", "sample"} <= PHI_RESOURCE_TYPES


# ── canonical engine enforcement ──────────────────────────────────────────────


class _Result:
    def __init__(self, values: list[object]) -> None:
        self.values = values

    def scalars(self) -> _Result:
        return self

    def all(self) -> list[object]:
        return self.values


class _Db:
    def __init__(self, permissions: list[str]) -> None:
        self.permissions = permissions
        self.membership = Membership(
            id="membership-1", account_id="account-1", organization_id="org-1",
            facility_id=None, department_id=None, unit_id=None, workspace_id=None,
            status=MembershipStatus.active.value, is_active=True, expires_at=None,
        )

    async def execute(self, statement):
        sql = str(statement)
        if "niam_memberships" in sql:
            return _Result([self.membership])
        if "niam_role_assignments" in sql:
            return _Result(self.permissions)
        return _Result([])

    async def scalar(self, statement):
        return "permission-id"

    def add(self, entry) -> None:
        return None

    async def flush(self) -> None:
        return None


def _actor() -> AuthorizationActor:
    account = Account(
        id="account-1", identity_id="identity-1", status=AccountStatus.active.value,
        is_active=True, is_locked=False,
    )
    session = UserSession(
        id="session-1", account_id="account-1", is_active=True, mfa_used=False,
        started_at=datetime.now(UTC) - timedelta(minutes=5),
        expires_at=datetime.now(UTC) + timedelta(hours=1),
    )
    return AuthorizationActor(account=account, session=session)


def _request(resource_type: str, action: str, permission_key: str | None) -> AuthorizationRequest:
    return AuthorizationRequest(
        subject_account_id="account-1",
        action=action,
        resource_type=resource_type,
        resource_id="resource-1",
        permission_key=permission_key,
        organization_id="org-1",
        resource_context={"exists": True, "organization_id": "org-1"},
    )


async def _decide(permissions: list[str], request: AuthorizationRequest):
    return await AuthorizationDecisionService(_Db(permissions))._evaluate(_actor(), request)


@pytest.mark.asyncio
async def test_broad_substitute_key_is_rejected_for_phi_action():
    decision = await _decide(
        ["lab_result.all"],
        _request("lab_result", "read", "lab_result.all"),
    )
    assert decision.reason_code is AuthorizationReason.phi_permission_conflict
    assert decision.allowed is False


@pytest.mark.asyncio
async def test_exact_key_from_map_is_authoritative_and_allows():
    decision = await _decide(
        ["lab_result.read"],
        _request("lab_result", "read", None),  # no client key: map supplies it
    )
    assert decision.allowed is True


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("held", "resource", "action", "expected"),
    [
        (["lab_result.read"], "patient_record", "read", AuthorizationReason.permission_missing),
        (["lab_result.read"], "lab_result", "delete", AuthorizationReason.permission_missing),
        (["lab_result.read"], "lab_result", "export", AuthorizationReason.permission_missing),
        (["lab_result.read"], "lab_result", "print", AuthorizationReason.permission_missing),
        (["lab_result.read"], "lab_result", "share", AuthorizationReason.permission_missing),
        (["lab_result.read"], "lab_result", "administrative", AuthorizationReason.permission_missing),
    ],
)
async def test_horizontal_and_vertical_escalation_denied(held, resource, action, expected):
    decision = await _decide(held, _request(resource, action, None))
    assert decision.reason_code is expected
    assert decision.allowed is False
