"""A3 — Authority boundary enforcement (ministry/directorate/facility/professional/domain).

Authorities must never silently override one another. These tests verify the
deterministic boundary classification, the explicit precedence policy, hard
conflict detection for ambiguous same-boundary claims, default-deny for
ungoverned actions, and auditable privileged enforcement.
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from app.identity.governance import (
    PRIVILEGED_ACTION_POLICY,
    AuthorityBoundary,
    AuthorityBoundaryConflict,
    AuthorityBoundaryDecision,
    AuthorityBoundaryError,
    AuthorityBoundaryService,
    AuthorityBoundaryType,
    boundary_for_authority,
    boundary_type_for,
)
from app.identity.models.audit import AuditAction


def b(
    boundary_type: AuthorityBoundaryType,
    authority_id: str = "auth-1",
    jurisdiction: str = "national",
) -> AuthorityBoundary:
    return AuthorityBoundary(
        authority_id=authority_id,
        boundary_type=boundary_type,
        jurisdiction=jurisdiction,
    )


class TestBoundaryClassification:
    def test_all_five_boundary_types_exist(self):
        values = {t.value for t in AuthorityBoundaryType}
        assert values == {
            "ministry",
            "directorate",
            "facility",
            "professional",
            "domain",
        }

    def test_classify_ministry(self):
        assert boundary_type_for("health_ministry") is AuthorityBoundaryType.ministry
        assert boundary_type_for("ministry") is AuthorityBoundaryType.ministry

    def test_classify_directorate(self):
        assert boundary_type_for("health_directorate") is AuthorityBoundaryType.directorate

    def test_classify_facility(self):
        assert boundary_type_for("hospital_authority") is AuthorityBoundaryType.facility

    def test_classify_professional(self):
        assert boundary_type_for("professional_syndicate") is AuthorityBoundaryType.professional

    def test_classify_unknown_defaults_to_domain(self):
        assert boundary_type_for("unknown_kind") is AuthorityBoundaryType.domain
        assert boundary_type_for(None) is AuthorityBoundaryType.domain

    def test_boundary_for_authority_model(self):
        authority = SimpleNamespace(
            id="A123", authority_type="professional_syndicate", jurisdiction="national"
        )
        boundary = boundary_for_authority(authority)
        assert boundary.authority_id == "A123"
        assert boundary.boundary_type is AuthorityBoundaryType.professional
        assert boundary.jurisdiction == "national"

    def test_boundary_keeps_jurisdiction_and_org(self):
        boundary = b(AuthorityBoundaryType.facility, jurisdiction="baghdad")
        assert boundary.jurisdiction == "baghdad"
        assert boundary.organization_id is None


class TestResolution:
    def test_action_not_governed_denied(self):
        decision = AuthorityBoundaryService.resolve(
            [b(AuthorityBoundaryType.ministry)], "unknown.action", "identity"
        )
        assert decision.allowed is False
        assert decision.reason == "action_not_governed"
        assert decision.boundary_type is None

    def test_no_authority_for_action_denied(self):
        decision = AuthorityBoundaryService.resolve(
            [b(AuthorityBoundaryType.domain)], "license.issue", "professional"
        )
        assert decision.allowed is False
        assert decision.reason == "no_authority_for_action"

    def test_empty_authorities_denied(self):
        decision = AuthorityBoundaryService.resolve([], "identity.revoke", "identity")
        assert decision.allowed is False
        assert decision.reason == "no_authority_for_action"

    def test_single_controlling_boundary(self):
        decision = AuthorityBoundaryService.resolve(
            [b(AuthorityBoundaryType.ministry, authority_id="M")],
            "identity.revoke",
            "identity",
        )
        assert decision.allowed is True
        assert decision.authority_id == "M"
        assert decision.boundary_type is AuthorityBoundaryType.ministry
        assert decision.reason == "controlled_by_ministry"

    def test_higher_precedence_boundary_controls_explicitly(self):
        # professional.verify allows (professional, ministry); a ministry AND a
        # professional authority both claim -> professional controls explicitly.
        decision = AuthorityBoundaryService.resolve(
            [
                b(AuthorityBoundaryType.ministry, authority_id="M"),
                b(AuthorityBoundaryType.professional, authority_id="P"),
            ],
            "professional.verify",
            "professional",
        )
        assert decision.allowed is True
        assert decision.authority_id == "P"
        assert decision.boundary_type is AuthorityBoundaryType.professional
        assert decision.reason == "controlled_by_professional"

    def test_ministry_outranks_directorate_for_org_admin(self):
        decision = AuthorityBoundaryService.resolve(
            [
                b(AuthorityBoundaryType.directorate, authority_id="D"),
                b(AuthorityBoundaryType.ministry, authority_id="M"),
            ],
            "organization.administer",
            "organization",
        )
        assert decision.allowed is True
        assert decision.authority_id == "M"
        assert decision.reason == "controlled_by_ministry"

    def test_directorate_still_controls_when_ministry_absent(self):
        decision = AuthorityBoundaryService.resolve(
            [b(AuthorityBoundaryType.directorate, authority_id="D")],
            "organization.administer",
            "organization",
        )
        assert decision.allowed is True
        assert decision.authority_id == "D"

    def test_disallowed_boundary_type_does_not_override(self):
        # facility.administer allows only facility; a ministry authority does
        # not silently override into facility administration.
        decision = AuthorityBoundaryService.resolve(
            [b(AuthorityBoundaryType.ministry, authority_id="M")],
            "facility.administer",
            "facility",
        )
        assert decision.allowed is False
        assert decision.reason == "no_authority_for_action"

    def test_same_boundary_claim_is_conflict_not_silent(self):
        with pytest.raises(AuthorityBoundaryConflict) as excinfo:
            AuthorityBoundaryService.resolve(
                [
                    b(AuthorityBoundaryType.professional, authority_id="P1"),
                    b(AuthorityBoundaryType.professional, authority_id="P2"),
                ],
                "license.issue",
                "professional",
            )
        assert "P1" in str(excinfo.value)
        assert "P2" in str(excinfo.value)

    def test_domain_boundary_authorizes_domain_actions(self):
        decision = AuthorityBoundaryService.resolve(
            [b(AuthorityBoundaryType.domain, authority_id="DG")],
            "domain.authorize",
            "domain",
        )
        assert decision.allowed is True
        assert decision.authority_id == "DG"

    def test_all_boundary_types_covered_by_policy(self):
        covered = {t for types in PRIVILEGED_ACTION_POLICY.values() for t in types}
        assert covered == set(AuthorityBoundaryType)


class TestEnforcement:
    async def test_enforce_allowed_returns_decision(self):
        audit = AsyncMock()
        audit.record = AsyncMock()
        service = AuthorityBoundaryService(audit=audit)
        decision = await service.enforce(
            "identity.revoke",
            [b(AuthorityBoundaryType.ministry, authority_id="M")],
            "identity",
            subject_id="ident-1",
            actor_id="actor-1",
        )
        assert decision.allowed is True
        audit.record.assert_awaited_once()
        args = audit.record.await_args
        assert args.args[0] is AuditAction.authority_boundary_enforced
        assert args.kwargs["actor_id"] == "actor-1"
        assert args.kwargs["target_type"] == "identity"
        assert args.kwargs["target_id"] == "ident-1"

    async def test_enforce_denied_raises_and_audits_denial(self):
        audit = AsyncMock()
        audit.record = AsyncMock()
        service = AuthorityBoundaryService(audit=audit)
        with pytest.raises(AuthorityBoundaryError) as excinfo:
            await service.enforce(
                "identity.revoke",
                [b(AuthorityBoundaryType.professional)],
                "identity",
                subject_id="ident-1",
                actor_id="actor-1",
            )
        assert "identity.revoke denied" in str(excinfo.value)
        audit.record.assert_awaited_once()
        args = audit.record.await_args
        assert args.args[0] is AuditAction.authority_boundary_denied
        assert args.kwargs["outcome"] == "denied"

    async def test_enforce_conflict_raises_and_audits_conflict(self):
        audit = AsyncMock()
        audit.record = AsyncMock()
        service = AuthorityBoundaryService(audit=audit)
        with pytest.raises(AuthorityBoundaryConflict):
            await service.enforce(
                "license.issue",
                [
                    b(AuthorityBoundaryType.professional, authority_id="P1"),
                    b(AuthorityBoundaryType.professional, authority_id="P2"),
                ],
                "professional",
                subject_id="prof-1",
            )
        audit.record.assert_awaited_once()
        args = audit.record.await_args
        assert args.args[0] is AuditAction.authority_boundary_denied
        assert args.kwargs["outcome"] == "conflict"

    async def test_enforce_without_audit_still_raises_on_denial(self):
        service = AuthorityBoundaryService(audit=None)
        with pytest.raises(AuthorityBoundaryError):
            await service.enforce("unknown.action", [b(AuthorityBoundaryType.ministry)], "x")

    async def test_enforce_records_organization_context(self):
        audit = AsyncMock()
        audit.record = AsyncMock()
        service = AuthorityBoundaryService(audit=audit)
        await service.enforce(
            "facility.administer",
            [b(AuthorityBoundaryType.facility, authority_id="F")],
            "facility",
            organization_id="org-9",
        )
        assert audit.record.await_args.kwargs["organization_id"] == "org-9"
