"""AUD-ARCH-003 — pin the synthetic Health Core authorization engine to the
canonical NIAM authority by decision equivalence on a shared corpus.

Root cause: ``app/health_core/authorization/engine.py`` described itself as "the
only authority for permissions", while the ONE cataloged, production-facing
authority is ``app/identity/services/authorization_service.py`` (decision engine
``identity/services/authorization_decision.py``). Two engines with the same name
and overlapping responsibility invite drift: a future change could weaken one
of them (e.g. allow on missing permission) without touching the other.

Remediation (engineering scope; owner ratification still required):
  * the synthetic engine is explicitly scoped to the non-activated Health Core
    slice (opaque ``SYN-`` ids, no real identity/DB);
  * the canonical authority is recorded as the single source of truth in
    ``app/domain_platform/shared_core.py``;
  * THIS test feeds a neutral corpus of authorization situations into BOTH
    engines through real evaluation calls and asserts the same ALLOW/DENY
    verdict. Any divergence — in either direction — fails the build.

This is a deterministic differential test on a curated corpus, not a formal
proof of full semantic equivalence; the two engines intentionally differ in
reason codes and internal policy language. It pins the *decision contract*:
deny-by-default, authentication grants nothing, tenant isolation, and explicit
revocation/deny-policy override.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest
from app._compat import UTC
from app.health_core.authorization import (
    AuthorizationEngine,
    Decision,
    Principal,
    ResourceContext,
)
from app.health_core.contracts.authorization import Role
from app.health_core.contracts.catalogue import ContractOperation as Op
from app.identity.models.account import Account, AccountStatus
from app.identity.models.membership import Membership, MembershipStatus
from app.identity.models.policy import IdentityPolicy
from app.identity.models.session import UserSession
from app.identity.services.authorization_decision import (
    AuthorizationActor,
    AuthorizationDecisionService,
    AuthorizationRequest,
)

# ── Neutral corpus: (situation, expected verdict) ──────────────────────────────
# "allow" / "deny" are the shared semantic verdict; each adapter maps a
# situation into its engine's native inputs and returns that verdict.
CORPUS: tuple[tuple[str, str], ...] = (
    ("authenticated_principal_with_required_permission_in_scope", "allow"),
    ("unauthenticated_or_inactive_actor", "deny"),
    ("authenticated_but_permission_missing", "deny"),
    ("cross_tenant_request", "deny"),
    ("explicit_revocation_or_deny_policy", "deny"),
)

_TENANT = "SYN-LAB-0001"
_OTHER_TENANT = "SYN-LAB-0002"
_PRINCIPAL = "SYN-PRC-0001"

# Canonical-side opaque ids (the canonical authority uses free-form strings).
_ACCOUNT = "account-equivalence-1"
_SESSION = "session-equivalence-1"
_ORG = "org-equivalence-1"
_OTHER_ORG = "org-equivalence-2"
_PERMISSION = "practitioner.read"


# ── Health Core (synthetic) adapter ────────────────────────────────────────────


class _HealthCoreResult:
    def __init__(self, verdict: str, policy_id: str) -> None:
        self.verdict = verdict
        self.policy_id = policy_id


def _health_core_principal(*, authenticated: bool = True):
    return Principal(
        principal_id=_PRINCIPAL,
        tenant_id=_TENANT,
        roles=frozenset({Role.VIEWER}),
        authenticated=authenticated,
    )


def _health_core_verdict(situation: str) -> _HealthCoreResult:
    engine = AuthorizationEngine()
    if situation == "authenticated_principal_with_required_permission_in_scope":
        who = _health_core_principal()
        what = ResourceContext(tenant_id=_TENANT, resource_id="SYN-RES-0001", action=Op.PRACTITIONER_READ)
    elif situation == "unauthenticated_or_inactive_actor":
        who = _health_core_principal(authenticated=True).without_authentication()
        what = ResourceContext(tenant_id=_TENANT, resource_id="SYN-RES-0001", action=Op.PRACTITIONER_READ)
    elif situation == "authenticated_but_permission_missing":
        who = Principal(principal_id=_PRINCIPAL, tenant_id=_TENANT)  # no role, no grant
        what = ResourceContext(tenant_id=_TENANT, resource_id="SYN-RES-0001", action=Op.PRACTITIONER_READ)
    elif situation == "cross_tenant_request":
        who = _health_core_principal()
        what = ResourceContext(tenant_id=_OTHER_TENANT, resource_id="SYN-RES-0001", action=Op.PRACTITIONER_READ)
    elif situation == "explicit_revocation_or_deny_policy":
        who = _health_core_principal()
        engine.revoke_principal(_PRINCIPAL, reason="equivalence corpus")
        what = ResourceContext(tenant_id=_TENANT, resource_id="SYN-RES-0001", action=Op.PRACTITIONER_READ)
    else:
        raise AssertionError(f"unmapped corpus situation: {situation}")

    decision = engine.evaluate(who, what)
    verdict = "allow" if decision.decision is Decision.ALLOW else "deny"
    return _HealthCoreResult(verdict, decision.policy_id.value)


# ── Canonical NIAM adapter ─────────────────────────────────────────────────────


class _Result:
    def __init__(self, values: list[object]) -> None:
        self.values = values

    def scalars(self) -> _Result:
        return self

    def all(self) -> list[object]:
        return self.values


class _Session:
    """Minimal in-memory stand-in for the canonical decision engine's stores."""

    def __init__(
        self,
        *,
        membership: Membership | None = None,
        effective_permissions: list[str] | None = None,
        policies: list[IdentityPolicy] | None = None,
    ) -> None:
        self.membership = membership
        self.effective_permissions = effective_permissions or []
        self.policies = policies or []

    async def execute(self, statement):
        sql = str(statement)
        if "niam_memberships" in sql:
            return _Result([self.membership] if self.membership else [])
        if "niam_role_assignments" in sql:
            return _Result(self.effective_permissions)
        if "niam_policies" in sql:
            return _Result(self.policies)
        return _Result([])

    async def scalar(self, statement):
        # Permission catalog lookup: always active for this corpus.
        return "permission-id"

    def add(self, entry) -> None:
        del entry

    async def flush(self) -> None:
        return None


def _actor(*, active: bool = True) -> AuthorizationActor:
    account = Account(
        id=_ACCOUNT,
        identity_id="identity-equivalence-1",
        status=AccountStatus.active.value if active else AccountStatus.suspended.value,
        is_active=active,
        is_locked=False,
    )
    session = UserSession(
        id=_SESSION,
        account_id=_ACCOUNT,
        is_active=active,
        mfa_used=False,
        started_at=datetime.now(UTC) - timedelta(minutes=5),
        expires_at=datetime.now(UTC) + timedelta(hours=1),
    )
    return AuthorizationActor(account=account, session=session)


def _membership(organization_id: str = _ORG) -> Membership:
    return Membership(
        id="membership-equivalence-1",
        account_id=_ACCOUNT,
        organization_id=organization_id,
        facility_id=None,
        department_id=None,
        unit_id=None,
        workspace_id=None,
        status=MembershipStatus.active.value,
        is_active=True,
        expires_at=None,
    )


def _request(*, organization_id: str = _ORG) -> AuthorizationRequest:
    return AuthorizationRequest(
        subject_account_id=_ACCOUNT,
        action="read",
        resource_type="practitioner",
        resource_id=None,
        permission_key=_PERMISSION,
        organization_id=organization_id,
        resource_context={"organization_id": organization_id},
    )


async def _canonical_verdict(situation: str) -> tuple[str, str]:
    if situation == "authenticated_principal_with_required_permission_in_scope":
        actor, request = _actor(), _request()
        session = _Session(membership=_membership(), effective_permissions=[_PERMISSION])
    elif situation == "unauthenticated_or_inactive_actor":
        actor, request = _actor(active=False), _request()
        session = _Session(membership=_membership(), effective_permissions=[_PERMISSION])
    elif situation == "authenticated_but_permission_missing":
        actor, request = _actor(), _request()
        session = _Session(membership=_membership(), effective_permissions=[])
    elif situation == "cross_tenant_request":
        actor, request = _actor(), _request(organization_id=_OTHER_ORG)
        # Membership belongs to _ORG; the resolver filters by requested org and
        # yields no usable membership -> fail closed.
        session = _Session(membership=_membership(_ORG), effective_permissions=[_PERMISSION])
    elif situation == "explicit_revocation_or_deny_policy":
        actor, request = _actor(), _request()
        deny = IdentityPolicy(
            policy_id="equivalence-deny-v1",
            effect="deny",
            actions=["read"],
            resources=["practitioner"],
            priority=10,
            version="1.0",
            is_active=True,
            is_enabled=True,
        )
        session = _Session(
            membership=_membership(), effective_permissions=[_PERMISSION], policies=[deny]
        )
    else:
        raise AssertionError(f"unmapped corpus situation: {situation}")

    decision = await AuthorizationDecisionService(session)._evaluate(actor, request)
    verdict = "allow" if decision.allowed else "deny"
    return verdict, decision.reason_code.value


# ── The equivalence contract ───────────────────────────────────────────────────


@pytest.mark.asyncio
@pytest.mark.parametrize(("situation", "expected"), CORPUS, ids=[s for s, _ in CORPUS])
async def test_synthetic_engine_and_canonical_authority_agree(situation: str, expected: str):
    synthetic = _health_core_verdict(situation)
    canonical_verdict, canonical_reason = await _canonical_verdict(situation)

    assert synthetic.verdict == expected, (
        f"synthetic engine diverged for {situation}: {synthetic.verdict} ({synthetic.policy_id})"
    )
    assert canonical_verdict == expected, (
        f"canonical authority diverged for {situation}: {canonical_verdict} ({canonical_reason})"
    )
    # Both real evaluation calls must have produced a verdict (no vacuous pass).
    assert synthetic.policy_id
    assert canonical_reason


def test_corpus_covers_allow_and_all_core_deny_boundaries():
    """Guard against someone shrinking the corpus into a vacuous test."""
    verdicts = {expected for _, expected in CORPUS}
    assert verdicts == {"allow", "deny"}
    assert len(CORPUS) == 5


def test_synthetic_engine_is_scoped_and_catalog_points_to_canonical_authority():
    """AUD-ARCH-003: the single authority is documented in code, not just docs."""
    import inspect

    from app.domain_platform.shared_core import SHARED_CORE_CATALOG
    from app.health_core.authorization import engine as synthetic_engine

    catalog_entry = SHARED_CORE_CATALOG["authorization"]["provider"]
    assert catalog_entry.endswith("identity/services/authorization_service.py"), catalog_entry

    doc = inspect.getdoc(synthetic_engine) or ""
    assert "SYNTHETIC ONLY" in doc
    assert "identity/services/authorization_service.py" in doc
    assert "NOT the platform-wide" in doc
