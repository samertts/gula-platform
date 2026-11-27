"""B5 — scoped, revocable, depth-limited delegation into canonical authority.

Owner directive GULA-MASTER-AUTH-2026-11-19 §5/B5 (AUD-SEC-008).

Disposable in-memory SQLite + synthetic NIAM accounts/roles only. No operational
database, no real identity, no second authorization engine, no new role or
permission catalog entry. The tests exercise both the grant validation and the
canonical ``RolePermissionService.effective_permissions`` consumer.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest
from app._compat import UTC
from app.identity.base import IdentityBase
from app.identity.models.account import Account
from app.identity.models.administrative_structure import (
    OrganizationOwnership,
    OrganizationRepresentative,
)
from app.identity.models.audit import AuditAction, IdentityAuditEntry
from app.identity.models.authorization import (
    CatalogStatus,
    Permission,
    Role,
    RoleAssignment,
    RolePermission,
)
from app.identity.models.delegation import DelegationStatus, NiamDelegation
from app.identity.services.authorization_service_v2 import RolePermissionService
from app.identity.services.delegation_service import (
    MAX_DELEGATION_DEPTH,
    DelegationDenied,
    DelegationPolicyError,
    DelegationService,
)
from sqlalchemy import MetaData, create_engine
from sqlalchemy.orm import Session

_ORG = "ORG-000000000000000000001"
_ACTOR = "ACCOUNT-000000000000000000001"
_DELEGATE = "ACCOUNT-000000000000000000002"
_OTHER = "ACCOUNT-000000000000000000003"
_ROLE = "ROLE-0000000000000000000001"
_PERM_A = "lab_result.read"
_PERM_B = "lab_result.export"


class _AwaitableProxy:
    """Test-only bridge: a synchronous SQLAlchemy result usable with ``await``."""

    __slots__ = ("_value",)

    def __init__(self, value):
        self._value = value

    def __await__(self):
        async def _unwrap():
            return self._value

        return _unwrap().__await__()

    def __getattr__(self, name):
        return getattr(self._value, name)


class AsyncCompatSession:
    """Test-only AsyncSession-compatible view over a synchronous SQLite session."""

    _BRIDGED = frozenset({
        "execute", "flush", "commit", "rollback", "close", "delete",
        "refresh", "merge", "run_sync", "scalar", "scalars",
    })

    def __init__(self, sync_session):
        object.__setattr__(self, "_sync_session", sync_session)

    def __getattr__(self, name):
        value = getattr(self._sync_session, name)
        if callable(value) and name in self._BRIDGED:
            def bridged(*args, **kwargs):
                return _AwaitableProxy(value(*args, **kwargs))
            return bridged
        return value


def _metadata_subset() -> MetaData:
    from app.database import Base

    combined = MetaData()
    for metadata in (Base.metadata, IdentityBase.metadata):
        for table in metadata.tables.values():
            if table.name not in combined.tables:
                table.to_metadata(combined)
    roots = (
        "niam_delegations",
        "niam_role_assignments",
        "niam_role_permissions",
        "niam_permissions",
        "niam_memberships",
        "niam_audit_entries",
        "niam_organization_ownerships",
        "niam_organization_representatives",
    )
    needed: set[str] = set()

    def visit(name: str) -> None:
        if name in needed or name not in combined.tables:
            return
        needed.add(name)
        for fk in combined.tables[name].foreign_keys:
            visit(fk.target_fullname.split(".", 1)[0])

    for root in roots:
        visit(root)
    subset = MetaData()
    for name in sorted(needed):
        combined.tables[name].to_metadata(subset)
    return subset


@pytest.fixture()
def b5db():
    engine = create_engine("sqlite://")
    _metadata_subset().create_all(engine)
    sync = Session(engine)
    try:
        yield AsyncCompatSession(sync)
    finally:
        sync.close()
        engine.dispose()


def _account(db, account_id: str, *, active: bool = True):
    account = Account(
        id=account_id,
        uuid=f"uuid-{account_id}",
        identity_id=f"IDENTITY-{account_id[-4:]}",
        account_type="human",
        status="active" if active else "suspended",
        is_active=active,
        is_locked=False,
        mfa_enabled=False,
    )
    db.add(account)
    db.flush()
    return account


def _catalog(db):
    role = Role(
        id=_ROLE, uuid="uuid-role-1", role_key="b5_test_role", name="B5 Test Role",
        scope_type="organization", status=CatalogStatus.active.value,
        is_system=False, version=1,
    )
    db.add(role)
    for idx, key in enumerate((_PERM_A, _PERM_B), start=1):
        perm = Permission(
            id=f"PERM-{idx:026d}", uuid=f"uuid-perm-{idx}", permission_key=key,
            name=key, resource="lab_result", action=key.split(".")[1],
            sensitivity="high", status=CatalogStatus.active.value, version=1,
        )
        db.add(perm)
        db.flush()
        db.add(RolePermission(
            id=f"RP-{idx:026d}", role_id=_ROLE, permission_id=perm.id,
            status=CatalogStatus.active.value,
        ))
    db.flush()


def _assignment(db, account_id: str = _ACTOR, *, facility_id=None, expired=False):
    assignment = RoleAssignment(
        id=f"ASSIGN-{account_id[-4:]}", uuid=f"uuid-assign-{account_id[-4:]}",
        assignment_key=f"key-{account_id}", account_id=account_id,
        membership_id="MEMBERSHIP-0000000000000001", role_id=_ROLE,
        organization_id=_ORG, facility_id=facility_id, department_id=None,
        unit_id=None, workspace_id=None, scope_type="organization",
        status="active", assigned_by=_OTHER,
        expires_at=datetime.now(UTC) - timedelta(hours=1) if expired
        else datetime.now(UTC) + timedelta(days=30),
        version=1,
    )
    db.add(assignment)
    db.flush()
    return assignment


def _setup(db):
    for account_id in (_ACTOR, _DELEGATE, _OTHER):
        _account(db, account_id)
    _catalog(db)
    _assignment(db)


def _grant(**overrides):
    params = {
        "actor_id": _ACTOR,
        "delegate_account_id": _DELEGATE,
        "role_id": _ROLE,
        "organization_id": _ORG,
        "permission_keys": [_PERM_A],
        "duration_hours": 24,
        "reason": "cover for approved clinical leave",
    }
    params.update(overrides)
    return params


def _run(coro):
    return asyncio.run(coro)


# ── Structural / single-authority invariants ────────────────────────────────


def test_delegation_is_canonical_metadata_only():
    assert "niam_delegations" in IdentityBase.metadata.tables
    assert MAX_DELEGATION_DEPTH == 3


def test_no_second_engine_import():
    # The Health Core synthetic engine must remain synthetic-only; B5 is wired
    # into the canonical RolePermissionService, not into a parallel engine.
    from pathlib import Path

    import app.identity.services.authorization_service_v2 as authority

    src = Path(authority.__file__).read_text(encoding="utf-8")
    assert "health_core" not in src
    assert "NiamDelegation" in src


@pytest.mark.xfail(
    strict=True,
    reason="Wave 04 excludes migrations; niam_delegations DDL remains owner-gated",
)
def test_delegation_migration_is_pending_owner_authorization():
    from pathlib import Path

    path = (
        Path(__file__).resolve().parents[2]
        / "migrations/versions/20261119_0002_niam_delegations.py"
    )
    assert path.exists()
    src = path.read_text(encoding="utf-8")
    assert 'down_revision: str | None = "20261119_0001"' in src
    assert "op.create_table(" in src
    assert 'op.drop_table("niam_delegations")' in src
    assert "alter_column" not in src


# ── Grant validation (fail-closed) ──────────────────────────────────────────


def test_delegate_role_happy_path_and_audit(b5db):
    _setup(b5db)
    delegation = _run(DelegationService(b5db).delegate_role(**_grant()))
    assert delegation.status == DelegationStatus.active
    assert delegation.depth == 1
    assert delegation.permission_keys == [_PERM_A]
    assert delegation.delegator_account_id == _ACTOR
    assert delegation.delegate_account_id == _DELEGATE
    entries = b5db.query(IdentityAuditEntry).filter_by(
        action=AuditAction.delegation_granted.value
    ).all()
    assert len(entries) == 1
    assert entries[0].target_id == delegation.id
    assert entries[0].actor_id == _ACTOR


@pytest.mark.parametrize(
    ("overrides", "exc", "match"),
    [
        ({"delegate_account_id": _ACTOR}, DelegationDenied, "Self-delegation"),
        ({"actor_id": _OTHER}, DelegationDenied, "does not hold"),
        ({"duration_hours": 0}, DelegationPolicyError, "duration"),
        ({"duration_hours": 721}, DelegationPolicyError, "duration"),
        ({"permission_keys": []}, DelegationPolicyError, "non-empty"),
        ({"permission_keys": [_PERM_A, _PERM_A]}, DelegationPolicyError, "Duplicate"),
        ({"permission_keys": ["bogus.permission"]}, DelegationDenied, "not part of"),
        ({"reason": "short"}, DelegationPolicyError, "reason"),
    ],
)
def test_delegate_role_rejects_invalid_requests(b5db, overrides, exc, match):
    _setup(b5db)
    with pytest.raises(exc, match=match):
        _run(DelegationService(b5db).delegate_role(**_grant(**overrides)))


def test_delegate_role_rejects_inactive_delegate(b5db):
    _setup(b5db)
    account = b5db.query(Account).filter_by(id=_DELEGATE).one()
    account.is_active = False
    b5db.flush()
    with pytest.raises(DelegationPolicyError, match="active"):
        _run(DelegationService(b5db).delegate_role(**_grant()))


def test_scope_cannot_exceed_holding_scope(b5db):
    _setup(b5db)
    # Actor holds organization-wide authority; a facility-scoped delegation is
    # narrower and therefore allowed.
    narrow = _run(DelegationService(b5db).delegate_role(
        **_grant(facility_id="FACILITY-0000000000000001")
    ))
    assert narrow.facility_id == "FACILITY-0000000000000001"


def test_depth_cap_blocks_redelegation(b5db):
    _setup(b5db)
    # The actor holds the role ONLY through a depth-3 delegation (no direct
    # assignment), so any further delegation would be depth 4 and must fail.
    direct = b5db.query(RoleAssignment).filter_by(account_id=_ACTOR).one()
    b5db.delete(direct)
    b5db.flush()
    b5db.add(NiamDelegation(
        id="DELEGATION-00000000000000001", uuid="uuid-deleg-depth3",
        delegator_account_id=_OTHER, delegate_account_id=_ACTOR,
        role_id=_ROLE, organization_id=_ORG, facility_id=None,
        department_id=None, unit_id=None, workspace_id=None,
        scope_type="organization", permission_keys=[_PERM_A], depth=3,
        status=DelegationStatus.active, reason="prior delegation",
        starts_at=datetime.now(UTC) - timedelta(hours=1),
        expires_at=datetime.now(UTC) + timedelta(days=1), version=1,
    ))
    b5db.flush()
    with pytest.raises(DelegationDenied, match="Maximum delegation depth"):
        _run(DelegationService(b5db).delegate_role(**_grant(
            delegate_account_id=_DELEGATE
        )))


def test_database_enforces_depth_cap(b5db):
    """Defense in depth: even a direct writer cannot persist depth > 3."""
    _setup(b5db)
    delegation = _run(DelegationService(b5db).delegate_role(**_grant()))
    delegation.depth = MAX_DELEGATION_DEPTH + 1
    with pytest.raises(Exception, match="CHECK constraint"):
        b5db.flush()
    b5db.rollback()


# ── Canonical authority consumer ────────────────────────────────────────────


def _effective(db, account_id=_DELEGATE):
    return _run(RolePermissionService(db).effective_permissions(
        account_id, _ORG
    ))


def test_delegated_permission_flows_through_canonical_authority(b5db):
    _setup(b5db)
    _run(DelegationService(b5db).delegate_role(**_grant()))
    permissions = _effective(b5db)
    assert _PERM_A in permissions
    assert _PERM_B not in permissions  # verified subset, not the whole role


def test_delegated_permission_denied_for_wrong_scope(b5db):
    _setup(b5db)
    _run(DelegationService(b5db).delegate_role(**_grant(
        facility_id="FACILITY-0000000000000001"
    )))
    service = RolePermissionService(b5db)
    # Request without the delegated facility -> no permission.
    assert _PERM_A not in _run(service.effective_permissions(_DELEGATE, _ORG))
    # Request with the matching facility -> granted.
    assert _PERM_A in _run(service.effective_permissions(
        _DELEGATE, _ORG, facility_id="FACILITY-0000000000000001"
    ))


@pytest.mark.parametrize(
    ("mutation", "expected"),
    [
        ("expired", False),
        ("revoked", False),
        ("future_start", False),
        ("disabled_role_permission", False),
    ],
)
def test_delegated_permission_fail_closed(b5db, mutation, expected):
    _setup(b5db)
    delegation = _run(DelegationService(b5db).delegate_role(**_grant()))
    if mutation == "expired":
        delegation.expires_at = datetime.now(UTC) - timedelta(minutes=1)
    elif mutation == "revoked":
        delegation.status = DelegationStatus.revoked
        delegation.revoked_at = datetime.now(UTC)
    elif mutation == "future_start":
        delegation.starts_at = datetime.now(UTC) + timedelta(hours=1)
    elif mutation == "disabled_role_permission":
        rp = b5db.query(RolePermission).filter_by(role_id=_ROLE).first()
        rp.status = CatalogStatus.disabled.value
    b5db.flush()
    assert (_PERM_A in _effective(b5db)) is expected


# ── Revocation ──────────────────────────────────────────────────────────────


def test_delegator_can_revoke_and_effect_is_immediate(b5db):
    _setup(b5db)
    delegation = _run(DelegationService(b5db).delegate_role(**_grant()))
    assert _PERM_A in _effective(b5db)
    revoked = _run(DelegationService(b5db).revoke_delegation(
        delegation_id=delegation.id, actor_id=_ACTOR,
        reason="clinical leave ended unexpectedly",
    ))
    assert revoked.status == DelegationStatus.revoked
    assert revoked.revoked_by == _ACTOR
    assert _PERM_A not in _effective(b5db)
    entries = b5db.query(IdentityAuditEntry).filter_by(
        action=AuditAction.delegation_revoked.value
    ).all()
    assert len(entries) == 1


def test_unauthorized_actor_cannot_revoke(b5db):
    _setup(b5db)
    delegation = _run(DelegationService(b5db).delegate_role(**_grant()))
    with pytest.raises(DelegationDenied, match="cannot revoke"):
        _run(DelegationService(b5db).revoke_delegation(
            delegation_id=delegation.id, actor_id=_OTHER,
            reason="unauthorized revocation attempt",
        ))
    assert _PERM_A in _effective(b5db)


def test_organization_owner_can_revoke(b5db):
    _setup(b5db)
    delegation = _run(DelegationService(b5db).delegate_role(**_grant()))
    b5db.add(OrganizationOwnership(
        id="OWNERSHIP-000000000000001", uuid="uuid-ownership-1",
        account_id=_OTHER, organization_id=_ORG, status="active",
    ))
    b5db.flush()
    revoked = _run(DelegationService(b5db).revoke_delegation(
        delegation_id=delegation.id, actor_id=_OTHER,
        reason="security incident revokes all delegations",
    ))
    assert revoked.status == DelegationStatus.revoked


def test_revocation_preserves_delegation_history(b5db):
    _setup(b5db)
    delegation = _run(DelegationService(b5db).delegate_role(**_grant()))
    original_id = delegation.id
    _run(DelegationService(b5db).revoke_delegation(
        delegation_id=original_id, actor_id=_ACTOR,
        reason="planned delegation period has concluded",
    ))
    assert b5db.query(NiamDelegation).filter_by(id=original_id).count() == 1
    with pytest.raises(DelegationDenied, match="already terminal"):
        _run(DelegationService(b5db).revoke_delegation(
            delegation_id=original_id, actor_id=_ACTOR,
            reason="second revocation attempt on terminal record",
        ))
