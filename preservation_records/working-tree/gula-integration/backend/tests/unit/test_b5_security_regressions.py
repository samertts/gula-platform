"""B5 security regressions — Team C HIGH findings (GULA-MASTER-AUTH-2026-11-19).

Locks in the three fixes for the later, adversarial Team C pass
(``INDEPENDENT_VERIFICATION_TEAM_C_TIER_B.md`` §4, timestamp 2026-11-19T09:38:19Z):

1. Authority laundering — a narrow-delegation holder must NOT be able to
   re-delegate a permission from the role catalog that it does not itself hold.
2. Transitive revocation — a delegation must stop conferring authority as soon
   as the delegator's live holding chain is broken.
3. Integration gap — the canonical ``/niam/delegations`` route writes the
   governed ``niam_delegations`` table consumed by ``effective_permissions()``;
   the legacy ``/authz/delegations`` surface is failed closed (HTTP 410).

Disposable in-memory SQLite + synthetic NIAM accounts only. No operational DB,
no real identity, no second authorization engine.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest
from app._compat import UTC
from app.database import AsyncCompatSession, get_db
from app.identity.base import IdentityBase
from app.identity.models.account import Account
from app.identity.models.authorization import (
    CatalogStatus,
    Permission,
    Role,
    RoleAssignment,
    RolePermission,
)
from app.identity.models.delegation import DelegationStatus, NiamDelegation
from app.identity.services.authorization_service_v2 import RolePermissionService
from app.identity.services.delegation_service import DelegationDenied, DelegationService
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import MetaData, create_engine, text
from sqlalchemy.orm import Session


def _id(prefix: str, number: int) -> str:
    """Canonical NIAM identifiers are exactly 26 characters."""
    return f"{prefix}{number:0{26 - len(prefix)}d}"


_ORG = _id("ORG", 1)
_ACTOR = _id("ACT", 1)
_DELEGATE = _id("ACT", 2)
_OTHER = _id("ACT", 3)
_NARROW = _id("ACT", 4)
_ROLE = _id("ROLE", 1)
_PERM_A = "lab_result.read"
_PERM_B = "lab_result.export"


def _metadata_subset() -> MetaData:
    from app.database import Base

    combined = MetaData()
    for metadata in (Base.metadata, IdentityBase.metadata):
        for table in metadata.tables.values():
            if table.name not in combined.tables:
                table.to_metadata(combined)
    roots = (
        "niam_delegations", "niam_role_assignments", "niam_role_permissions",
        "niam_permissions", "niam_memberships", "niam_audit_entries",
        "niam_organization_ownerships", "niam_organization_representatives",
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
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    _metadata_subset().create_all(engine)
    sync = Session(engine)
    try:
        yield AsyncCompatSession(sync)
    finally:
        sync.close()
        engine.dispose()


def _run(coro):
    import asyncio

    return asyncio.run(coro)


def _account(db, account_id: str):
    db.add(Account(
        id=account_id, uuid=f"uuid-{account_id}",
        identity_id=f"IDENTITY-{account_id[-4:]}", account_type="human",
        status="active", is_active=True, is_locked=False, mfa_enabled=False,
    ))
    db.flush()


def _catalog(db):
    db.add(Role(
        id=_ROLE, uuid="uuid-role-1", role_key="b5_regression_role", name="B5 Role",
        scope_type="organization", status=CatalogStatus.active.value,
        is_system=False, version=1,
    ))
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


def _assignment(db, account_id: str = _ACTOR):
    assignment = RoleAssignment(
        id=f"ASSIGN-{account_id[-4:]}", uuid=f"uuid-assign-{account_id[-4:]}",
        assignment_key=f"key-{account_id}", account_id=account_id,
        membership_id="MEMBERSHIP-0000000000000001", role_id=_ROLE,
        organization_id=_ORG, facility_id=None, department_id=None, unit_id=None,
        workspace_id=None, scope_type="organization", status="active",
        assigned_by=_OTHER, expires_at=datetime.now(UTC) + timedelta(days=30), version=1,
    )
    db.add(assignment)
    db.flush()
    return assignment


def _setup(db):
    for account_id in (_ACTOR, _DELEGATE, _OTHER, _NARROW):
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


def _effective(db, account_id: str) -> set[str]:
    return _run(RolePermissionService(db).effective_permissions(account_id, _ORG))


# ── Finding 1: authority laundering ──────────────────────────────────────────


def test_narrow_delegate_cannot_redelegate_unheld_permission(b5db):
    """A holder of only lab_result.read cannot delegate lab_result.export."""
    _setup(b5db)
    # _ACTOR holds the full role; grant _NARROW only the read permission.
    _run(DelegationService(b5db).delegate_role(**_grant(
        delegate_account_id=_NARROW, permission_keys=[_PERM_A]
    )))
    assert _PERM_A in _effective(b5db, _NARROW)
    assert _PERM_B not in _effective(b5db, _NARROW)

    # _NARROW tries to launder an unheld sibling permission from the same role.
    with pytest.raises(DelegationDenied, match="holding authority"):
        _run(DelegationService(b5db).delegate_role(**_grant(
            actor_id=_NARROW,
            delegate_account_id=_DELEGATE,
            permission_keys=[_PERM_A, _PERM_B],
        )))

    # No governed row was created for the laundering attempt.
    assert b5db.query(NiamDelegation).filter_by(
        delegator_account_id=_NARROW
    ).count() == 0
    entries = b5db.execute(text(
        "SELECT count(*) FROM niam_audit_entries WHERE outcome='denied'"
    )).scalar()
    assert entries >= 1


# ── Finding 2: transitive revocation ─────────────────────────────────────────


def test_revoking_delegator_direct_role_revokes_delegate_authority(b5db):
    """Broken holding chain removes the delegate's authority immediately."""
    _setup(b5db)
    _run(DelegationService(b5db).delegate_role(**_grant()))
    assert _PERM_A in _effective(b5db, _DELEGATE)

    # Revoke _ACTOR's direct role assignment; the chain no longer has a live root.
    assignment = b5db.query(RoleAssignment).filter_by(account_id=_ACTOR).one()
    assignment.status = "revoked"
    assignment.revoked_at = datetime.now(UTC)
    b5db.flush()

    assert _PERM_A not in _effective(b5db, _DELEGATE)


def test_multi_hop_chain_still_grants_while_live(b5db):
    """The hardening must not break legitimate depth-2 chains."""
    _setup(b5db)
    hop1 = _run(DelegationService(b5db).delegate_role(**_grant(
        delegate_account_id=_NARROW, permission_keys=[_PERM_A]
    )))
    assert hop1.depth == 1
    hop2 = _run(DelegationService(b5db).delegate_role(**_grant(
        actor_id=_NARROW, delegate_account_id=_DELEGATE, permission_keys=[_PERM_A]
    )))
    assert hop2.depth == 2
    assert _PERM_A in _effective(b5db, _DELEGATE)

    # Break the root -> first hop; both descendants must lose authority.
    assignment = b5db.query(RoleAssignment).filter_by(account_id=_ACTOR).one()
    assignment.status = "revoked"
    b5db.flush()
    assert _PERM_A not in _effective(b5db, _NARROW)
    assert _PERM_A not in _effective(b5db, _DELEGATE)


# ── Finding 3: integration gap ────────────────────────────────────────────────


def test_canonical_route_writes_governed_table_and_changes_effective_permissions(b5db):
    """POST /niam/delegations writes niam_delegations consumed by canonical authority."""
    from app.identity.api.delegations import get_current_niam_actor, router

    _setup(b5db)
    actor = b5db.query(Account).filter_by(id=_ACTOR).one()
    fake_actor = SimpleNamespace(account=actor, session=object())

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_current_niam_actor] = lambda: fake_actor
    app.dependency_overrides[get_db] = lambda: b5db

    try:
        with TestClient(app) as client:
            response = client.post("/delegations", json={
                "delegate_account_id": _DELEGATE,
                "role_id": _ROLE,
                "organization_id": _ORG,
                "permission_keys": [_PERM_A],
                "duration_hours": 24,
                "reason": "cover for approved clinical leave",
            })
            assert response.status_code == 201, response.text
            row = b5db.query(NiamDelegation).filter_by(
                delegate_account_id=_DELEGATE
            ).one()
            assert row.delegator_account_id == _ACTOR
            assert _PERM_A in _effective(b5db, _DELEGATE)
            assert _PERM_B not in _effective(b5db, _DELEGATE)

            revoke = client.post(
                f"/delegations/{row.id}/revoke",
                json={"reason": "clinical leave ended unexpectedly"},
            )
            assert revoke.status_code == 200, revoke.text
            assert row.status == DelegationStatus.revoked
            assert _PERM_A not in _effective(b5db, _DELEGATE)
    finally:
        app.dependency_overrides.clear()


def test_legacy_delegation_surface_fails_closed():
    """The ungoverned /authz/delegations handlers are disabled (HTTP 410)."""
    from app.routes.authorization import (
        create_delegation,
        list_my_delegations,
        revoke_delegation,
    )

    calls = [
        lambda: create_delegation(None, None, None),
        lambda: revoke_delegation(1, None, None),
        lambda: list_my_delegations(None, None),
    ]
    for call in calls:
        with pytest.raises(HTTPException) as excinfo:
            call()
        assert excinfo.value.status_code == 410
        assert "niam/delegations" in excinfo.value.detail


def test_canonical_route_registered_on_real_app():
    """The canonical delegation API is mounted under /niam on the real app."""
    from app.main import app

    paths = set(app.openapi()["paths"])
    assert "/niam/delegations" in paths
    assert "/niam/delegations/{delegation_id}/revoke" in paths
    assert "/authz/delegations" in paths  # retained but fails closed
