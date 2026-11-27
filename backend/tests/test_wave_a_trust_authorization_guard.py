from __future__ import annotations

import ast
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest
from app._compat import UTC
from app.identity.api.authorization_guard import (
    AuthorizationGuardSpec,
    require_authorized_action,
)
from app.identity.api.workspaces import NiamActor
from app.identity.federation import routes as federation_routes
from app.identity.models.account import Account, AccountStatus
from app.identity.models.membership import Membership, MembershipStatus
from app.identity.models.session import UserSession
from app.identity.services.authorization_decision import (
    AuthorizationDecision,
    AuthorizationDecisionService,
    AuthorizationReason,
    AuthorizationRequest,
)
from app.identity.services.canonical_audit import AuditEventInput, CanonicalAuditService
from app.identity.trust import routes as trust_routes
from fastapi import HTTPException

REPO_ROOT = Path(__file__).resolve().parents[2]


class _Result:
    def __init__(self, values: list[object]) -> None:
        self.values = values

    def scalars(self) -> _Result:
        return self

    def all(self) -> list[object]:
        return self.values


class _FakeDB:
    def __init__(self, memberships: list[Membership] | None = None) -> None:
        self.memberships = memberships or []
        self.commits = 0

    async def execute(self, statement):
        del statement
        return _Result(list(self.memberships))

    async def commit(self) -> None:
        self.commits += 1


def _actor() -> NiamActor:
    account = Account(
        id="account-1",
        identity_id="identity-1",
        status=AccountStatus.active.value,
        is_active=True,
        is_locked=False,
    )
    session = UserSession(
        id="session-1",
        account_id="account-1",
        is_active=True,
        mfa_used=True,
        started_at=datetime.now(UTC) - timedelta(minutes=5),
        expires_at=datetime.now(UTC) + timedelta(hours=1),
    )
    return NiamActor(account=account, session=session)


def _membership(organization_id: str = "org-1") -> Membership:
    return Membership(
        id="membership-1",
        account_id="account-1",
        organization_id=organization_id,
        status=MembershipStatus.active.value,
        is_active=True,
        expires_at=None,
        revoked_at=None,
    )


def _spec(**overrides: object) -> AuthorizationGuardSpec:
    values: dict[str, object] = {
        "action": "establish",
        "resource_type": "federation_trust",
        "permission_key": "federation_trust.establish",
        "organization_id": "org-1",
    }
    values.update(overrides)
    return AuthorizationGuardSpec(**values)  # type: ignore[arg-type]


async def test_guard_records_denied_decision_in_canonical_v2_audit(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    async def fake_authorize(self, actor, request: AuthorizationRequest):
        del self, actor
        captured["request"] = request
        return AuthorizationDecision.deny(AuthorizationReason.permission_missing)

    async def fake_record(self, event: AuditEventInput):
        del self
        captured["event"] = event
        return SimpleNamespace(id="audit-1")

    monkeypatch.setattr(AuthorizationDecisionService, "authorize", fake_authorize)
    monkeypatch.setattr(CanonicalAuditService, "record", fake_record)
    db = _FakeDB()

    with pytest.raises(HTTPException) as exc:
        await require_authorized_action(
            _actor(),
            db,  # type: ignore[arg-type]
            spec=_spec(),
        )

    assert exc.value.status_code == 403
    assert "PERMISSION_MISSING" in exc.value.detail
    assert db.commits == 1
    request = captured["request"]
    assert isinstance(request, AuthorizationRequest)
    assert request.permission_key == "federation_trust.establish"
    assert request.organization_id == "org-1"
    event = captured["event"]
    assert isinstance(event, AuditEventInput)
    assert event.decision == "deny"
    assert event.outcome == "denied"
    assert event.target_type == "federation_trust"
    assert event.source == "niam_authorization_guard"


async def test_guard_allows_explicit_action_without_committing_business_transaction(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_authorize(self, actor, request):
        del self, actor, request
        return AuthorizationDecision.allow()

    async def fake_record(self, event):
        del self, event
        return SimpleNamespace(id="audit-2")

    monkeypatch.setattr(AuthorizationDecisionService, "authorize", fake_authorize)
    monkeypatch.setattr(CanonicalAuditService, "record", fake_record)
    db = _FakeDB()

    await require_authorized_action(
        _actor(),
        db,  # type: ignore[arg-type]
        spec=_spec(resource_id="trust-1"),
    )

    assert db.commits == 0


async def test_ambiguous_membership_scope_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    async def fake_authorize(self, actor, request):
        del self, actor
        captured["request"] = request
        return AuthorizationDecision.deny(AuthorizationReason.membership_unresolved)

    async def fake_record(self, event):
        del self, event
        return SimpleNamespace(id="audit-3")

    monkeypatch.setattr(AuthorizationDecisionService, "authorize", fake_authorize)
    monkeypatch.setattr(CanonicalAuditService, "record", fake_record)
    db = _FakeDB([_membership("org-1"), _membership("org-2")])

    with pytest.raises(HTTPException) as exc:
        await require_authorized_action(
            _actor(),
            db,  # type: ignore[arg-type]
            spec=_spec(organization_id=None),
        )

    assert exc.value.status_code == 403
    request = captured["request"]
    assert isinstance(request, AuthorizationRequest)
    assert request.organization_id is None


async def test_federation_mutation_denied_before_service_call(monkeypatch: pytest.MonkeyPatch) -> None:
    async def deny(actor, db, *, spec):
        del actor, db, spec
        raise HTTPException(status_code=403, detail="guard denied")

    async def unexpected(self, **kwargs):
        del self, kwargs
        raise AssertionError("service must not run after authorization denial")

    monkeypatch.setattr(federation_routes, "require_authorized_action", deny)
    monkeypatch.setattr(federation_routes.CrossOrgTrustService, "establish_trust", unexpected)

    with pytest.raises(HTTPException) as exc:
        await federation_routes.establish_trust(
            source_org_id="org-1",
            target_org_id="org-2",
            trust_level="limited",
            trust_type="bilateral",
            agreement=None,
            established_by=None,
            actor=_actor(),
            db=_FakeDB(),  # type: ignore[arg-type]
        )

    assert exc.value.status_code == 403


async def test_trust_mutation_denied_before_service_call(monkeypatch: pytest.MonkeyPatch) -> None:
    async def deny(actor, db, *, spec):
        del actor, db, spec
        raise HTTPException(status_code=403, detail="guard denied")

    async def unexpected(self, trust_id):
        del self, trust_id
        raise AssertionError("service must not run after authorization denial")

    monkeypatch.setattr(trust_routes, "require_authorized_action", deny)
    monkeypatch.setattr(trust_routes.FederationTrustService, "suspend_trust", unexpected)

    with pytest.raises(HTTPException) as exc:
        await trust_routes.suspend_federation_trust(
            trust_id="trust-1",
            actor=_actor(),
            db=_FakeDB(),  # type: ignore[arg-type]
        )

    assert exc.value.status_code == 403


def _mutation_functions(path: Path) -> list[ast.AsyncFunctionDef]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    methods = {"post", "put", "patch", "delete"}
    functions: list[ast.AsyncFunctionDef] = []
    for node in tree.body:
        if not isinstance(node, ast.AsyncFunctionDef):
            continue
        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call):
                continue
            if isinstance(decorator.func, ast.Attribute) and decorator.func.attr in methods:
                functions.append(node)
                break
    return functions


@pytest.mark.parametrize(
    "relative_path",
    [
        "backend/app/identity/federation/routes.py",
        "backend/app/identity/trust/routes.py",
    ],
)
def test_every_mutation_route_uses_trusted_actor_and_canonical_guard(relative_path: str) -> None:
    functions = _mutation_functions(REPO_ROOT / relative_path)
    assert functions, f"no mutation routes discovered in {relative_path}"
    for function in functions:
        actor_arguments = [
            argument
            for argument in function.args.args
            if isinstance(argument.annotation, ast.Name) and argument.annotation.id == "NiamActor"
        ]
        guard_calls = [
            node
            for node in ast.walk(function)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "require_authorized_action"
        ]
        assert actor_arguments, f"{function.name} lacks trusted NiamActor dependency"
        assert guard_calls, f"{function.name} lacks canonical authorization guard"


def test_factory_does_not_register_weaker_duplicate_trust_router() -> None:
    source = (REPO_ROOT / "backend/app/factory.py").read_text(encoding="utf-8")
    assert "app.include_router(trust_router)" not in source
    assert "mounted only through ``get_niam_router()``" in source
