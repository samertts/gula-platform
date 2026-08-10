"""Wave B unit B1 — ABAC route enforcement tests.

B1 guarantees enforced here:

1. **Route-coverage gate** — every effective HTTP route is classified; no
   route may be unprotected, and every protected ``/niam/*`` route must carry
   the ``require_abac`` guard in its flattened dependant tree.
2. **Decision-pipeline ordering** — authentication (401) precedes the ABAC
   decision (403), which precedes the route handler; an anonymous caller is
   never evaluated by ABAC, and an authenticated-but-denied caller receives a
   deterministic 403.
3. **Fail-closed** — no matching rule, an unknown resource, or an
   undecidable subject all deny (never allow).
4. **Actor-source integrity** — the ABAC subject id is always derived from the
   server-verified principal, never from a client payload.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest
from app.security.abac import ABACRequest, ABACRule, Effect
from app.security.abac_coverage import (
    PUBLIC_ROUTE_SPECS,
    RouteStatus,
    classify_route,
    has_abac_guard,
    has_authz_dependency,
    iter_effective_routes,
    route_coverage_report,
)
from app.security.abac_enforcement import (
    enforce_abac_decision,
    get_abac_engine,
    method_to_action,
    require_abac,
    reset_abac_engine,
)
from app.security.abac_policies import (
    NIAM_ABAC_RESOURCES,
    build_default_abac_rules,
    niam_path_prefixes,
)
from fastapi import Depends, HTTPException
from tests.conftest import auth_headers


@pytest.fixture(autouse=True)
def _clean_abac_engine():
    """Give every test a pristine engine with the default rule set."""
    reset_abac_engine()
    yield
    reset_abac_engine()


# ═══════════════════════════════════════════════════════════════════════════
# Registry integrity
# ═══════════════════════════════════════════════════════════════════════════


class TestAbacPolicyRegistry:
    def test_resources_all_niam_prefixed(self):
        assert NIAM_ABAC_RESOURCES
        assert all(r.startswith("niam:") for r in NIAM_ABAC_RESOURCES)
        assert len(NIAM_ABAC_RESOURCES) == len(set(NIAM_ABAC_RESOURCES))

    def test_default_rules_cover_every_resource(self):
        rules = build_default_abac_rules()
        assert len(rules) == len(NIAM_ABAC_RESOURCES)
        covered = {rule.resource for rule in rules}
        assert covered == set(NIAM_ABAC_RESOURCES)
        for rule in rules:
            assert rule.effect is Effect.ALLOW
            assert rule.is_active
            assert rule.action == "*"

    def test_default_rules_are_deterministic(self):
        first = build_default_abac_rules()
        second = build_default_abac_rules()
        assert [r.id for r in first] == [r.id for r in second]
        assert len({r.id for r in first}) == len(first)
        assert [r.resource for r in first] == list(NIAM_ABAC_RESOURCES)

    def test_default_engine_allows_authenticated_subject_on_every_resource(self):
        engine = get_abac_engine()
        for resource in NIAM_ABAC_RESOURCES:
            decision = engine.decide(
                ABACRequest(
                    resource=resource,
                    action="read",
                    subject={"subject_id": "account:server-derived"},
                )
            )
            assert decision.allowed, f"default policy must allow {resource}"

    def test_niam_path_prefixes_map_onto_resources(self):
        prefixes = niam_path_prefixes()
        assert len(prefixes) == len(NIAM_ABAC_RESOURCES)
        for resource, prefix in zip(NIAM_ABAC_RESOURCES, prefixes, strict=True):
            assert prefix == f"/niam/{resource.split(':', 1)[1]}"

    def test_method_action_mapping(self):
        assert method_to_action("GET") == "read"
        assert method_to_action("POST") == "create"
        assert method_to_action("PUT") == "update"
        assert method_to_action("PATCH") == "update"
        assert method_to_action("DELETE") == "delete"
        assert method_to_action("head") == "read"
        assert method_to_action("OPTIONS") == "options"


# ═══════════════════════════════════════════════════════════════════════════
# Fail-closed + deny-overrides engine semantics
# ═══════════════════════════════════════════════════════════════════════════


class TestFailClosedSemantics:
    def test_unknown_resource_denies_by_default(self):
        engine = get_abac_engine()
        decision = engine.decide(
            ABACRequest(
                resource="billing:invoices",
                action="read",
                subject={"subject_id": "account:1"},
            )
        )
        assert not decision.allowed
        assert decision.rule_id is None
        assert "fail-closed" in decision.reason

    def test_deny_rule_overrides_allow_rule(self):
        engine = get_abac_engine()
        engine.add_rule(
            ABACRule(
                id="test.allow.low",
                name="allow at priority 100",
                effect=Effect.ALLOW,
                resource="billing:invoices",
                action="*",
                priority=100,
            )
        )
        engine.add_rule(
            ABACRule(
                id="test.deny.high",
                name="deny at priority 10",
                effect=Effect.DENY,
                resource="billing:invoices",
                action="*",
                priority=10,
            )
        )
        decision = engine.decide(
            ABACRequest(
                resource="billing:invoices",
                action="read",
                subject={"subject_id": "account:1"},
            )
        )
        assert not decision.allowed
        assert decision.rule_id == "test.deny.high"

    def test_equal_priority_decided_by_rule_id(self):
        engine = get_abac_engine()
        engine.add_rule(
            ABACRule(
                id="zz.allow",
                name="allow",
                effect=Effect.ALLOW,
                resource="billing:invoices",
                action="*",
                priority=100,
            )
        )
        engine.add_rule(
            ABACRule(
                id="aa.deny",
                name="deny",
                effect=Effect.DENY,
                resource="billing:invoices",
                action="*",
                priority=100,
            )
        )
        decision = engine.decide(
            ABACRequest(
                resource="billing:invoices",
                action="read",
                subject={"subject_id": "account:1"},
            )
        )
        assert not decision.allowed
        assert decision.rule_id == "aa.deny"


# ═══════════════════════════════════════════════════════════════════════════
# Actor-source integrity + enforcement point
# ═══════════════════════════════════════════════════════════════════════════


class TestActorSourceIntegrity:
    def test_account_principal_derives_subject_from_server(self):
        principal = SimpleNamespace(
            uuid="account-uuid-1",
            identity_id="identity-1",
            account_type="government",
            status="active",
        )
        decision = enforce_abac_decision(principal, "niam:governance", "read", "/niam/governance")
        assert decision.allowed
        assert decision.subject_id == "account-uuid-1"

    def test_lab_principal_derives_subject_from_server(self):
        principal = SimpleNamespace(id=7, lab_id=3, role="admin", province_id=None)
        decision = enforce_abac_decision(principal, "niam:governance", "read", "/niam/governance")
        assert decision.allowed
        assert decision.subject_id == "lab-user:7"

    def test_undecidable_principal_fails_closed(self):
        principal = object()
        with pytest.raises(HTTPException) as exc:
            enforce_abac_decision(principal, "niam:governance", "read", "/niam/governance")
        assert exc.value.status_code == 403

    def test_deny_raises_403_without_leaking_rule_detail(self):
        engine = get_abac_engine()
        engine.add_rule(
            ABACRule(
                id="test.deny.governance",
                name="deny governance during maintenance",
                effect=Effect.DENY,
                resource="niam:governance",
                action="*",
                priority=10,
            )
        )
        principal = SimpleNamespace(id=7, lab_id=3, role="admin", province_id=None)
        with pytest.raises(HTTPException) as exc:
            enforce_abac_decision(principal, "niam:governance", "read", "/niam/governance")
        assert exc.value.status_code == 403
        assert exc.value.detail == "Access denied"

    def test_require_abac_factory_marks_guard(self):
        guard = require_abac("niam:persons")
        assert guard._abac_guard is True
        assert guard._abac_resource == "niam:persons"
        assert guard._abac_purpose is None
        other = require_abac("niam:persons", purpose="clinical")
        assert other is not guard
        assert other._abac_purpose == "clinical"

    def test_decisions_recorded_in_engine_log(self):
        engine = get_abac_engine()
        engine.clear_decisions()
        principal = SimpleNamespace(id=7, lab_id=3, role="admin", province_id=None)
        enforce_abac_decision(principal, "niam:domains", "read", "/niam/domains")
        decisions = engine.recent_decisions()
        assert decisions
        assert decisions[-1].resource == "niam:domains"
        assert decisions[-1].action == "read"
        assert decisions[-1].allowed is True
        assert decisions[-1].subject_id == "lab-user:7"


# ═══════════════════════════════════════════════════════════════════════════
# Route-coverage gate
# ═══════════════════════════════════════════════════════════════════════════


class TestRouteCoverageGate:
    def test_every_route_classified_and_niam_routes_guarded(self):
        from app.factory import create_app

        report = route_coverage_report(create_app())
        assert report.total_routes >= 2000
        assert report.unprotected == [], (
            "unprotected routes:\n" + "\n".join(f"{m} {p}" for p, m in report.unprotected)
        )
        assert report.missing_abac == [], (
            "protected NIAM routes missing ABAC guard:\n"
            + "\n".join(f"{m} {p}" for p, m in report.missing_abac)
        )

    def test_every_niam_prefix_has_effective_routes(self):
        from app.factory import create_app

        app = create_app()
        paths = {path for path, _methods, _dep in iter_effective_routes(app)}
        for prefix in niam_path_prefixes():
            assert any(p.startswith(prefix) for p in paths), f"no routes under {prefix}"

    def test_public_niam_routes_declared_public_and_unguarded(self):
        from app.factory import create_app

        app = create_app()
        public = {"/niam/health", "/niam/auth/login", "/niam/auth/refresh"}
        for path, methods, dependant in iter_effective_routes(app):
            if path in public:
                assert not has_authz_dependency(dependant), f"{path} must stay public"
                assert not has_abac_guard(dependant), f"{path} must stay unguarded"
                assert classify_route(path, methods, False, False) is RouteStatus.PUBLIC

    def test_public_registry_entries_are_used(self):
        """Every public declaration must actually classify at least one route."""
        from app.factory import create_app

        app = create_app()
        matched_patterns = set()
        for path, methods, dependant in iter_effective_routes(app):
            authz = has_authz_dependency(dependant)
            abac = has_abac_guard(dependant)
            if authz or abac:
                continue
            for spec in PUBLIC_ROUTE_SPECS:
                if spec.matches(path, methods):
                    matched_patterns.add(spec.path_pattern)
        assert matched_patterns == {spec.path_pattern for spec in PUBLIC_ROUTE_SPECS}, (
            "declared public specs never matched: "
            f"{sorted({spec.path_pattern for spec in PUBLIC_ROUTE_SPECS} - matched_patterns)}"
        )


# ═══════════════════════════════════════════════════════════════════════════
# HTTP request semantics (client fixture)
# ═══════════════════════════════════════════════════════════════════════════


class TestHttpSemantics:
    def test_public_niam_routes_and_anonymous_401(self, client):
        r = client.get("/niam/health")
        assert r.status_code == 200
        assert r.json()["status"] == "healthy"

        r = client.get("/niam/governance/authorities")
        assert r.status_code == 401

        r = client.post("/niam/auth/refresh", params={"refresh_token": "nope"})
        assert r.status_code in (401, 422)

    def test_authenticated_allow_deny_semantics(self, client, db, make_lab, make_lab_user):
        lab = make_lab()
        user = make_lab_user(lab_id=lab.id, role="master_admin")
        headers = auth_headers(user.id, lab.id, user.role)
        engine = get_abac_engine()
        engine.clear_decisions()

        r = client.get("/niam/governance/authorities", headers=headers)
        assert r.status_code == 200

        decisions = engine.recent_decisions()
        allow = [d for d in decisions if d.resource == "niam:governance" and d.action == "read"]
        assert allow, "ABAC decision must be recorded for the authenticated request"
        assert allow[-1].allowed is True
        assert allow[-1].subject_id == f"lab-user:{user.id}"

        engine.add_rule(
            ABACRule(
                id="test.deny.governance.http",
                name="deny governance",
                effect=Effect.DENY,
                resource="niam:governance",
                action="*",
                priority=10,
            )
        )
        try:
            engine.clear_decisions()
            r = client.get("/niam/governance/authorities", headers=headers)
            assert r.status_code == 403
            denied = [
                d for d in engine.recent_decisions()
                if d.resource == "niam:governance" and d.action == "read"
            ]
            assert denied and denied[-1].allowed is False
        finally:
            engine.remove_rule("test.deny.governance.http")

        r = client.get("/niam/governance/authorities", headers=headers)
        assert r.status_code == 200

    def test_lab_user_abac_guard_orders_before_handler(self, client, db, make_lab, make_lab_user):
        """The ABAC 403 must fire even when the handler would succeed."""
        lab = make_lab()
        user = make_lab_user(lab_id=lab.id, role="master_admin")
        headers = auth_headers(user.id, lab.id, user.role)
        engine = get_abac_engine()
        engine.add_rule(
            ABACRule(
                id="test.deny.trust.http",
                name="deny trust",
                effect=Effect.DENY,
                resource="niam:trust",
                action="*",
                priority=10,
            )
        )
        try:
            r = client.get("/niam/trust/frameworks", headers=headers)
            assert r.status_code == 403
        finally:
            engine.remove_rule("test.deny.trust.http")
