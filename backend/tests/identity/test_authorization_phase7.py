from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from app.identity.api.roles import RoleAssignmentRequest
from app.identity.models.authorization import RoleAssignment, RoleAssignmentStatus
from app.identity.services.authorization_service_v2 import (
    LEGAL_ROLE_ASSIGNMENT_TRANSITIONS,
    RoleAssignmentStateError,
    RoleAuthorizationDenied,
    RolePermissionService,
)


def test_role_assignment_transition_matrix_rejects_terminal_reactivation() -> None:
    for current, targets in LEGAL_ROLE_ASSIGNMENT_TRANSITIONS.items():
        for target in targets:
            assignment = RoleAssignment(status=current, version=1)
            RolePermissionService.transition_assignment(assignment, RoleAssignmentStatus(target))
            assert assignment.status == target
            assert assignment.version == 2

    revoked = RoleAssignment(status=RoleAssignmentStatus.revoked.value, version=3)
    with pytest.raises(RoleAssignmentStateError):
        RolePermissionService.transition_assignment(revoked, RoleAssignmentStatus.active)


def test_role_assignment_key_is_scope_specific() -> None:
    first = RolePermissionService.assignment_key("account", "membership", "role", "organization")
    second = RolePermissionService.assignment_key("account", "membership", "role", "organization", facility_id="facility")
    assert first != second
    assert first == RolePermissionService.assignment_key("account", "membership", "role", "organization")


def test_role_scope_match_requires_exact_context() -> None:
    membership = SimpleNamespace(
        scope_type="facility",
        facility_id="facility",
        department_id=None,
        unit_id=None,
        workspace_id=None,
    )
    assert RolePermissionService._scope_matches_membership(membership, "facility", "facility", None, None, None)
    assert not RolePermissionService._scope_matches_membership(membership, "facility", "other", None, None, None)
    assert not RolePermissionService._scope_matches_membership(membership, "organization", None, None, None, None)


@pytest.mark.asyncio
async def test_grant_role_rejects_self_escalation_before_database_mutation() -> None:
    service = RolePermissionService(SimpleNamespace())
    service._audit = AsyncMock()
    with pytest.raises(RoleAuthorizationDenied):
        await service.grant_role(
            actor_id="same-account",
            account_id="same-account",
            membership_id="membership",
            role_id="role",
        )
    service._audit.assert_awaited_once()


def test_role_assignment_request_does_not_accept_status_or_assigned_by() -> None:
    fields = set(RoleAssignmentRequest.model_fields)
    assert "status" not in fields
    assert "assigned_by" not in fields
    assert "actor_id" not in fields
