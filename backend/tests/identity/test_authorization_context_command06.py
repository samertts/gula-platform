from __future__ import annotations

from types import SimpleNamespace
from typing import Any, cast

import pytest
from app.identity.api.roles import _resolve_trusted_scope
from app.identity.models.audit import IdentityAuditEntry
from app.identity.models.workspace import WorkspaceStatus
from app.identity.services.access_revocation import revoke_account_access
from app.identity.services.audit_service import AuditService
from app.identity.services.authorization_decision import AuthorizationRequest


class _Result:
    def __init__(
        self,
        *,
        rowcount: int = 0,
        scalar: Any = None,
        rows: list[Any] | None = None,
    ) -> None:
        self.rowcount = rowcount
        self._scalar = scalar
        self._rows = list(rows or [])

    def scalar_one_or_none(self) -> Any:
        return self._scalar

    def scalars(self) -> _Result:
        return self

    def all(self) -> list[Any]:
        return self._rows


class _AuditSession:
    def __init__(self) -> None:
        self.entries: list[IdentityAuditEntry] = []
        self.calls = 0

    async def execute(self, _statement: Any) -> _Result:
        self.calls += 1
        return _Result(scalar=None, rows=self.entries if self.calls > 1 else [])

    def add(self, entry: IdentityAuditEntry) -> None:
        self.entries.append(entry)

    async def flush(self) -> None:
        return None


class _RevocationSession(_AuditSession):
    async def execute(self, _statement: Any) -> _Result:
        self.calls += 1
        if self.calls == 1:
            return _Result(rowcount=2)
        if self.calls == 2:
            return _Result(rowcount=1)
        return _Result(scalar=None)


@pytest.mark.asyncio
async def test_audit_context_is_first_class_and_chain_hashes_it() -> None:
    session = _AuditSession()
    entry = await AuditService(cast(Any, session)).record_event(
        action="AUTHZ_DENY",
        actor_id="account-a",
        target_type="patient",
        target_id="patient-a",
        organization_id="org-a",
        facility_id="facility-a",
        workspace_id="workspace-a",
        decision="deny",
        reason_code="CROSS_TENANT_DENIED",
        request_id="request-a",
        correlation_id="correlation-a",
        source="niam_authorization",
        metadata={"bounded": True},
        outcome="denied",
    )
    assert entry.organization_id == "org-a"
    assert entry.facility_id == "facility-a"
    assert entry.workspace_id == "workspace-a"
    assert entry.decision == "deny"
    assert entry.reason_code == "CROSS_TENANT_DENIED"
    assert entry.request_id == "request-a"
    assert entry.correlation_id == "correlation-a"
    assert await AuditService(cast(Any, session)).verify_chain_integrity() == []


@pytest.mark.asyncio
async def test_access_revocation_invalidates_sessions_and_workspace_contexts() -> None:
    session = _RevocationSession()
    counts = await revoke_account_access(
        cast(Any, session),
        account_id="account-a",
        actor_id="admin-a",
        organization_id="org-a",
        facility_id="facility-a",
        workspace_id="workspace-a",
        reason_code="membership_revoked",
    )
    assert counts == (2, 1)
    assert session.calls == 3
    assert len(session.entries) == 1
    audit = session.entries[0]
    assert audit.action == "session_revoked"
    assert audit.organization_id == "org-a"
    assert audit.facility_id == "facility-a"
    assert audit.workspace_id == "workspace-a"


class _ScopeSession:
    def __init__(self, workspace: Any) -> None:
        self.workspace = workspace

    async def scalar(self, _statement: Any) -> Any:
        return SimpleNamespace(is_active=True, workspace_id=self.workspace.id)

    async def get(self, _model: Any, _workspace_id: Any) -> Any:
        return self.workspace


@pytest.mark.asyncio
async def test_trusted_scope_rejects_cross_workspace_request() -> None:
    workspace = SimpleNamespace(
        id="workspace-a",
        organization_id="org-a",
        facility_id="facility-a",
        department_id="department-a",
        status=WorkspaceStatus.active.value,
    )
    actor = SimpleNamespace(
        account=SimpleNamespace(id="account-a"),
        session=SimpleNamespace(id="session-a"),
    )
    with pytest.raises(Exception, match="Authorization scope mismatch"):
        await _resolve_trusted_scope(
            actor,
            cast(Any, _ScopeSession(workspace)),
            organization_id="org-a",
            facility_id="facility-a",
            department_id="department-a",
            unit_id=None,
            workspace_id="workspace-b",
        )


@pytest.mark.asyncio
async def test_trusted_scope_rejects_cross_organization_request() -> None:
    workspace = SimpleNamespace(
        id="workspace-a",
        organization_id="org-a",
        facility_id=None,
        department_id=None,
        status=WorkspaceStatus.active.value,
    )
    actor = SimpleNamespace(
        account=SimpleNamespace(id="account-a"),
        session=SimpleNamespace(id="session-a"),
    )
    with pytest.raises(Exception, match="Organization context mismatch"):
        await _resolve_trusted_scope(
            actor,
            cast(Any, _ScopeSession(workspace)),
            organization_id="org-b",
            facility_id=None,
            department_id=None,
            unit_id=None,
            workspace_id=None,
        )


def test_authorization_request_carries_request_and_correlation_context() -> None:
    request = AuthorizationRequest(
        subject_account_id="account-a",
        action="read",
        resource_type="patient",
        organization_id="org-a",
        request_id="request-a",
        correlation_id="correlation-a",
    )
    assert request.request_id == "request-a"
    assert request.correlation_id == "correlation-a"
