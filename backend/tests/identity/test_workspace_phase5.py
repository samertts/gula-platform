from types import SimpleNamespace

import pytest
from app.identity.models.workspace import WorkspaceStatus, WorkspaceType
from app.identity.services.workspace_service import (
    LEGAL_WORKSPACE_TRANSITIONS,
    WorkspaceService,
    WorkspaceStateError,
)


def workspace(status: str = WorkspaceStatus.provisioning.value):
    return SimpleNamespace(status=status, version=1)


def test_workspace_types_are_extensible_concepts_not_authorization_roles():
    assert WorkspaceType.citizen.value == "citizen"
    assert WorkspaceType.professional.value == "professional"
    assert WorkspaceType.organization.value == "organization"
    assert WorkspaceType.administrative.value == "administrative"


def test_citizen_provisioning_key_is_one_per_account():
    assert WorkspaceService.citizen_key("account-1") == "citizen:account-1"
    assert WorkspaceService.citizen_key("account-1") == WorkspaceService.citizen_key("account-1")
    assert WorkspaceService.citizen_key("account-1") != WorkspaceService.citizen_key("account-2")


def test_professional_key_is_scoped_to_account_and_profession():
    assert WorkspaceService.professional_key("account-1", "physician") == "professional:account-1:physician"
    assert WorkspaceService.professional_key("account-1", "physician") != WorkspaceService.professional_key("account-1", "nurse")


def test_workspace_lifecycle_requires_backend_transition():
    item = workspace()
    WorkspaceService.transition(item, WorkspaceStatus.active)
    assert item.status == WorkspaceStatus.active.value
    assert item.version == 2


def test_workspace_cannot_skip_provisioning_or_reactivate_archived():
    with pytest.raises(WorkspaceStateError):
        WorkspaceService.transition(workspace(WorkspaceStatus.provisioning.value), WorkspaceStatus.suspended)
    with pytest.raises(WorkspaceStateError):
        WorkspaceService.transition(workspace(WorkspaceStatus.archived.value), WorkspaceStatus.active)


def test_suspended_workspace_can_be_restricted_only_by_explicit_policy():
    item = workspace(WorkspaceStatus.active.value)
    WorkspaceService.transition(item, WorkspaceStatus.suspended)
    assert item.status == WorkspaceStatus.suspended.value
    assert WorkspaceStatus.active.value in LEGAL_WORKSPACE_TRANSITIONS[item.status]


def test_deactivated_workspace_is_terminal():
    assert LEGAL_WORKSPACE_TRANSITIONS[WorkspaceStatus.deactivated.value] == frozenset()
