"""NIAM Platform Authority foundation (Phase 10).

Focused tests for the new assignment-bound Platform Authority axis and its
wiring into the two Phase 6 findings (federation.update_provider,
trust.update_framework). Follows this repo's own established pattern for
testing NIAM's async layer: there is no real async SQLAlchemy engine
anywhere in this codebase (confirmed by grep for create_async_engine --
zero hits), and existing NIAM route/service tests (e.g.
test_workspace_api_hardening_phase5.py, test_authorization_phase8.py) all
call the async route/service functions directly with hand-built fake
session/actor objects rather than a real FastAPI TestClient + real DB. This
file does the same, not as a shortcut, but because that is the only pattern
this test suite has for this layer.

AUTH-002 through AUTH-005 (cited in the Phase 10 directive as a regression
check) are commits on origin/claude/p0-2-pharmacy-reconciliation, not on
this branch (confirmed via git log --all / git merge-base in Phase 6-8A).
There is nothing of theirs on this branch to regress. The regression check
this file can actually make is that get_current_niam_actor and the
adaptive_auth/admin/RBAC machinery this new code deliberately does NOT
touch keep working -- covered by running the existing identity suite
unchanged (see the session's final report), not re-tested here.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from app.identity.federation import routes as federation_routes
from app.identity.federation.models import FederatedProvider
from app.identity.platform_authority.authorization import require_platform_capability
from app.identity.platform_authority.models import (
    PlatformAuthorityAssignment,
    PlatformCapability,
)
from app.identity.platform_authority.services import (
    PlatformAuthorityService,
    UnknownPlatformCapability,
)
from app.identity.trust import routes as trust_routes
from app.identity.trust.models import TrustFramework
from fastapi import HTTPException

# ── Fakes (mirrors test_workspace_api_hardening_phase5.py's established shape) ──


class _Result:
    def __init__(self, row):
        self._row = row

    def scalar_one_or_none(self):
        return self._row


class _FakeDb:
    """Answers exactly the query shapes this phase's code issues.

    Dispatches by target table name (Select.get_final_froms()) rather than
    by parsing SQL text, so it stays correct regardless of filter order.
    Unmatched tables (e.g. the audit hash-chain lookup) return None, which
    is harmless for every assertion in this file.
    """

    def __init__(self, *, active_assignment=None, entity=None):
        self.active_assignment = active_assignment
        self.entity = entity
        self.added: list = []
        self.flush_count = 0

    def add(self, obj):
        self.added.append(obj)

    async def flush(self):
        self.flush_count += 1
        for obj in self.added:
            if getattr(obj, "id", None) is None:
                obj.id = f"GENERATED-{len(self.added)}"

    async def execute(self, stmt):
        table = stmt.get_final_froms()[0].name
        if table == "niam_platform_authority_assignments":
            return _Result(self._matching_active_assignment(stmt))
        if table in ("niam_trust_frameworks", "niam_fed_providers"):
            return _Result(self.entity)
        return _Result(None)

    def _matching_active_assignment(self, stmt) -> PlatformAuthorityAssignment | None:
        """Actually honors the query's identity_id/capability filter (unlike a
        blanket canned response) so a wrong-capability/wrong-identity lookup
        correctly misses even when *some* assignment is configured."""
        if self.active_assignment is None:
            return None
        params = {k.rsplit("_", 1)[0]: v for k, v in stmt.compile().params.items()}
        if params.get("identity_id") != self.active_assignment.identity_id:
            return None
        if params.get("capability") != self.active_assignment.capability:
            return None
        return self.active_assignment


def _actor(identity_id="IDENTITY0000000000000001", account_id="ACCOUNT0000000000000001"):
    return SimpleNamespace(account=SimpleNamespace(id=account_id, identity_id=identity_id))


def _assignment(
    identity_id="IDENTITY0000000000000001", capability=PlatformCapability.trust_manage.value
):
    return PlatformAuthorityAssignment(
        id="PA0000000000000000000001",
        uuid="pa-uuid-1",
        identity_id=identity_id,
        capability=capability,
        status="active",
    )


def _framework():
    return TrustFramework(
        id="TF0000000000000000000001",
        framework_id="fw-1",
        name_en="Old Name",
        name_ar="اسم قديم",
        version="1.0",
        status="draft",
        scope=None,
        assurance_policies=None,
        authority_id=None,
        supersedes_framework_id=None,
        is_active=True,
    )


def _provider():
    return FederatedProvider(
        id="FP0000000000000000000001",
        provider_id="prov-1",
        name_en="Old",
        name_ar=None,
        provider_type="oauth2",
        issuer_url="https://issuer.example",
        client_secret_encrypted="old-secret",
        status="active",
        is_active=True,
    )


# ── A/B/C/D/F: PlatformAuthorityService.has_capability -- fail-closed matrix ─


@pytest.mark.asyncio
async def test_has_capability_denies_with_no_assignment():
    db = _FakeDb(active_assignment=None)
    allowed = await PlatformAuthorityService(db).has_capability(
        "IDENTITY0000000000000001",
        PlatformCapability.trust_manage.value,
    )
    assert allowed is False


@pytest.mark.asyncio
async def test_has_capability_allows_with_matching_active_assignment():
    db = _FakeDb(active_assignment=_assignment())
    allowed = await PlatformAuthorityService(db).has_capability(
        "IDENTITY0000000000000001",
        PlatformCapability.trust_manage.value,
    )
    assert allowed is True


@pytest.mark.asyncio
async def test_has_capability_denies_unknown_capability_string():
    db = _FakeDb(active_assignment=_assignment())  # even with a row present
    allowed = await PlatformAuthorityService(db).has_capability(
        "IDENTITY0000000000000001",
        "platform.made_up.manage",
    )
    assert allowed is False


@pytest.mark.asyncio
async def test_has_capability_denies_missing_identity():
    db = _FakeDb(active_assignment=_assignment())
    assert (
        await PlatformAuthorityService(db).has_capability(
            None, PlatformCapability.trust_manage.value
        )
        is False
    )
    assert (
        await PlatformAuthorityService(db).has_capability("", PlatformCapability.trust_manage.value)
        is False
    )


# ── Grant / revoke lifecycle, including H: duplicate-active-assignment ──────


@pytest.mark.asyncio
async def test_grant_creates_a_new_active_assignment_and_audits_it():
    db = _FakeDb(active_assignment=None)
    assignment = await PlatformAuthorityService(db).grant(
        identity_id="IDENTITY0000000000000001",
        capability=PlatformCapability.trust_manage.value,
        granted_by_account_id="ACCOUNT0000000000000001",
    )
    assert assignment.status == "active"
    assert assignment.identity_id == "IDENTITY0000000000000001"
    added_types = [type(o).__name__ for o in db.added]
    assert "PlatformAuthorityAssignment" in added_types
    assert "IdentityAuditEntry" in added_types  # canonical audit, reused not duplicated


@pytest.mark.asyncio
async def test_grant_is_idempotent_when_already_active():
    """H. Assignment uniqueness: a duplicate active grant is a deterministic no-op."""
    existing = _assignment()
    db = _FakeDb(active_assignment=existing)
    result = await PlatformAuthorityService(db).grant(
        identity_id="IDENTITY0000000000000001",
        capability=PlatformCapability.trust_manage.value,
        granted_by_account_id="ACCOUNT0000000000000001",
    )
    assert result is existing
    assert db.added == []  # no new row, no new audit entry


@pytest.mark.asyncio
async def test_grant_rejects_unknown_capability_before_touching_the_session():
    db = _FakeDb(active_assignment=None)
    with pytest.raises(UnknownPlatformCapability):
        await PlatformAuthorityService(db).grant(
            identity_id="IDENTITY0000000000000001",
            capability="platform.made_up.manage",
            granted_by_account_id="ACCOUNT0000000000000001",
        )
    assert db.added == []


@pytest.mark.asyncio
async def test_revoke_marks_the_active_assignment_revoked_and_audits_it():
    existing = _assignment()
    db = _FakeDb(active_assignment=existing)
    result = await PlatformAuthorityService(db).revoke(
        identity_id="IDENTITY0000000000000001",
        capability=PlatformCapability.trust_manage.value,
        revoked_by_account_id="ACCOUNT0000000000000001",
        reason="no longer needed",
    )
    assert result is existing
    assert existing.status == "revoked"
    assert existing.revoked_at is not None
    assert any(type(o).__name__ == "IdentityAuditEntry" for o in db.added)


@pytest.mark.asyncio
async def test_revoke_with_nothing_active_is_a_clean_no_op():
    db = _FakeDb(active_assignment=None)
    result = await PlatformAuthorityService(db).revoke(
        identity_id="IDENTITY0000000000000001",
        capability=PlatformCapability.trust_manage.value,
        revoked_by_account_id="ACCOUNT0000000000000001",
    )
    assert result is None
    assert db.added == []  # nothing to revoke -> nothing audited


# ── require_platform_capability resolver: A/B/D/E/F/G ────────────────────────


@pytest.mark.asyncio
async def test_resolver_denies_authenticated_actor_with_no_assignment():
    """A. Authentication vs authorization: being logged in is not enough."""
    db = _FakeDb(active_assignment=None)
    with pytest.raises(HTTPException) as exc:
        await require_platform_capability(_actor(), db, PlatformCapability.trust_manage.value)
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_resolver_allows_matching_active_assignment():
    db = _FakeDb(active_assignment=_assignment())
    await require_platform_capability(
        _actor(), db, PlatformCapability.trust_manage.value
    )  # no raise


@pytest.mark.asyncio
async def test_resolver_denies_wrong_capability():
    """D. Wrong capability: federation grant must not satisfy a trust check."""
    db = _FakeDb(
        active_assignment=_assignment(capability=PlatformCapability.federation_manage.value)
    )
    with pytest.raises(HTTPException) as exc:
        await require_platform_capability(_actor(), db, PlatformCapability.trust_manage.value)
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_resolver_denies_after_revocation():
    """E. A previously-authorized identity is denied once nothing is active
    (the fake models "revoked" the same way the real DB would: the active-
    only query simply stops returning a row)."""
    db = _FakeDb(active_assignment=None)
    with pytest.raises(HTTPException) as exc:
        await require_platform_capability(_actor(), db, PlatformCapability.trust_manage.value)
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_resolver_denies_unknown_capability():
    """F. Unknown capability denies, even if some row happens to exist."""
    db = _FakeDb(active_assignment=_assignment())
    with pytest.raises(HTTPException):
        await require_platform_capability(_actor(), db, "platform.made_up.manage")


@pytest.mark.asyncio
async def test_resolver_denies_missing_or_malformed_actor():
    db = _FakeDb(active_assignment=_assignment())
    with pytest.raises(HTTPException):
        await require_platform_capability(None, db, PlatformCapability.trust_manage.value)
    with pytest.raises(HTTPException):
        await require_platform_capability(
            SimpleNamespace(account=None), db, PlatformCapability.trust_manage.value
        )


@pytest.mark.asyncio
async def test_resolver_never_treats_org_membership_as_platform_authority():
    """G. Cross-boundary: an actor shaped like an org admin (has organization-
    scoped attributes an org-RBAC check would look at) is still denied,
    because the resolver never reads them -- it only ever queries
    niam_platform_authority_assignments."""
    org_admin_actor = SimpleNamespace(
        account=SimpleNamespace(
            id="ACCOUNT0000000000000002",
            identity_id="IDENTITY0000000000000002",
            # shaped like it might carry org-role context; resolver must ignore this
            organization_role="organization_manager",
        ),
    )
    db = _FakeDb(active_assignment=None)  # no platform grant exists
    with pytest.raises(HTTPException) as exc:
        await require_platform_capability(
            org_admin_actor, db, PlatformCapability.trust_manage.value
        )
    assert exc.value.status_code == 403


# ── B: organization admin vs Platform Authority, at the route level ─────────


@pytest.mark.asyncio
async def test_update_framework_denies_ordinary_authenticated_actor():
    db = _FakeDb(active_assignment=None, entity=_framework())
    with pytest.raises(HTTPException) as exc:
        await trust_routes.update_framework(
            framework_id="fw-1",
            body={"name_en": "New Name"},
            db=db,
            actor=_actor(),
        )
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_update_framework_denies_wrong_capability():
    db = _FakeDb(
        active_assignment=_assignment(capability=PlatformCapability.federation_manage.value),
        entity=_framework(),
    )
    with pytest.raises(HTTPException) as exc:
        await trust_routes.update_framework(
            framework_id="fw-1",
            body={"name_en": "New Name"},
            db=db,
            actor=_actor(),
        )
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_update_framework_succeeds_for_authorized_platform_actor_and_enforces_field_boundary():
    """C + Section 9: authorized actor may proceed, but status/assurance_policies/
    scope (security-sensitive, no dedicated-operation precedent to route them
    through) never move through the generic path, exactly mirroring Hospital's
    already-proven allow-list pattern."""
    framework = _framework()
    db = _FakeDb(
        active_assignment=_assignment(capability=PlatformCapability.trust_manage.value),
        entity=framework,
    )
    result = await trust_routes.update_framework(
        framework_id="fw-1",
        body={
            "name_en": "New Name",
            "status": "active",  # security-sensitive: must be ignored
            "assurance_policies": {"hijacked": True},  # security-sensitive: must be ignored
            "framework_id": "hijacked-id",  # immutable: must be ignored
        },
        db=db,
        actor=_actor(),
    )
    assert result["name_en"] == "New Name"  # allowed field applied
    assert framework.status == "draft"  # protected: unchanged
    assert framework.assurance_policies is None  # protected: unchanged
    assert framework.framework_id == "fw-1"  # protected: unchanged
    assert any(type(o).__name__ == "IdentityAuditEntry" for o in db.added)


@pytest.mark.asyncio
async def test_update_provider_denies_ordinary_authenticated_actor():
    db = _FakeDb(active_assignment=None, entity=_provider())
    with pytest.raises(HTTPException) as exc:
        await federation_routes.update_provider(
            provider_id="prov-1",
            body={"name_en": "New"},
            db=db,
            actor=_actor(),
        )
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_update_provider_denies_wrong_capability():
    db = _FakeDb(
        active_assignment=_assignment(capability=PlatformCapability.trust_manage.value),
        entity=_provider(),
    )
    with pytest.raises(HTTPException) as exc:
        await federation_routes.update_provider(
            provider_id="prov-1",
            body={"name_en": "New"},
            db=db,
            actor=_actor(),
        )
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_update_provider_succeeds_for_authorized_platform_actor_and_enforces_field_boundary():
    provider = _provider()
    db = _FakeDb(
        active_assignment=_assignment(capability=PlatformCapability.federation_manage.value),
        entity=provider,
    )
    result = await federation_routes.update_provider(
        provider_id="prov-1",
        body={
            "name_en": "New Name",
            "client_secret_encrypted": "attacker-supplied-secret",  # security-sensitive
            "status": "compromised",  # security-sensitive
            "provider_id": "hijacked-id",  # immutable
        },
        db=db,
        actor=_actor(),
    )
    assert result["name_en"] == "New Name"
    assert provider.client_secret_encrypted == "old-secret"  # protected: unchanged
    assert provider.status == "active"  # protected: unchanged
    assert provider.provider_id == "prov-1"  # protected: unchanged
    assert any(type(o).__name__ == "IdentityAuditEntry" for o in db.added)


# ── I: audit ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_grant_and_revoke_produce_real_audit_entries_with_expected_shape():
    db = _FakeDb(active_assignment=None)
    svc = PlatformAuthorityService(db)
    await svc.grant(
        identity_id="IDENTITY0000000000000001",
        capability=PlatformCapability.trust_manage.value,
        granted_by_account_id="ACCOUNT0000000000000001",
    )
    grant_entries = [o for o in db.added if type(o).__name__ == "IdentityAuditEntry"]
    assert len(grant_entries) == 1
    assert grant_entries[0].action == "platform_authority.grant"
    assert grant_entries[0].actor_id == "ACCOUNT0000000000000001"
    assert grant_entries[0].decision == "ALLOW"

    db2 = _FakeDb(active_assignment=_assignment())
    await PlatformAuthorityService(db2).revoke(
        identity_id="IDENTITY0000000000000001",
        capability=PlatformCapability.trust_manage.value,
        revoked_by_account_id="ACCOUNT0000000000000001",
        reason="test revoke",
    )
    revoke_entries = [o for o in db2.added if type(o).__name__ == "IdentityAuditEntry"]
    assert len(revoke_entries) == 1
    assert revoke_entries[0].action == "platform_authority.revoke"


# ── Negative proof: the capability check is load-bearing, not incidental ────
#
# Proves the 403s above come from require_platform_capability actually being
# called and actually denying -- not from some unrelated exception that
# happens to look like a 403. Monkeypatches the check to a no-op (in this
# test process only; no source file is modified) for an ordinary,
# unauthorized actor and confirms the mutation that was denied everywhere
# above now goes through -- i.e. removing the gate is exactly what turns the
# deny into an allow.


@pytest.mark.asyncio
async def test_negative_proof_removing_the_gate_reopens_the_vulnerability():
    framework = _framework()
    db = _FakeDb(active_assignment=None, entity=framework)  # ordinary actor, no grant
    with patch.object(
        trust_routes, "require_platform_capability", new=AsyncMock(return_value=None)
    ):
        result = await trust_routes.update_framework(
            framework_id="fw-1",
            body={"name_en": "Hijacked"},
            db=db,
            actor=_actor(),
        )
    assert result["name_en"] == "Hijacked"  # confirms the gate, not something else, was denying it

    provider = _provider()
    db2 = _FakeDb(active_assignment=None, entity=provider)
    with patch.object(
        federation_routes, "require_platform_capability", new=AsyncMock(return_value=None)
    ):
        result2 = await federation_routes.update_provider(
            provider_id="prov-1",
            body={"name_en": "Hijacked"},
            db=db2,
            actor=_actor(),
        )
    assert result2["name_en"] == "Hijacked"
