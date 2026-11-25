"""Wave 05.1 — canonical authorization and consent boundary characterization.

Synthetic fixtures only. No NIAM role, policy, permission, route, consent
record, schema or production behavior is created. Tests use the existing
canonical ``AuthorizationDecisionService`` core, PHI action map, verified
guardian policy and NIAM consent model.

Known owner-gated gaps are characterized as current behavior, not approved:
canonical consent enforcement is absent, guardian purposes are outside the
engine purpose allowlist, break-glass enum/workflow checks remain shallow,
public deny reasons can collapse to membership_unresolved, and unknown PHI
actions use the generic permission_unknown reason. Break-glass expiry is
strictly parsed and enforced as a future, timezone-aware timestamp.
"""

from __future__ import annotations

from dataclasses import fields
from datetime import date, datetime, timedelta
from types import SimpleNamespace

import pytest
from app._compat import UTC
from app.identity.models.account import Account, AccountStatus
from app.identity.models.consent import NiamConsent, NiamConsentStatus
from app.identity.models.membership import Membership, MembershipStatus
from app.identity.models.session import UserSession
from app.identity.services.authorization_decision import (
    AuthorizationActor,
    AuthorizationDecisionService,
    AuthorizationReason,
    AuthorizationRequest,
)
from app.identity.services.phi_permission_map import resolve_phi_permission
from app.identity.services.verified_guardian_guard import evaluate_guardian_access

ACCOUNT = "ACCOUNT-W51"
IDENTITY = "IDENTITY-W51"
PERSON = "PERSON-W51"
ORG = "ORG-W51"
ORG_OTHER = "ORG-W51-OTHER"
FACILITY_A = "FACILITY-W51-A"
FACILITY_B = "FACILITY-W51-B"
WORKSPACE_A = "WORKSPACE-W51-A"
WORKSPACE_B = "WORKSPACE-W51-B"
MEMBERSHIP = "MEMBERSHIP-W51"
PATIENT = "PATIENT-W51"

_TODAY = date(2026, 11, 19)


class _Result:
    def __init__(self, values=None, scalar=None):
        self.values = list(values or [])
        self.scalar_value = scalar

    def scalars(self):
        return self

    def all(self):
        return list(self.values)

    def scalar_one_or_none(self):
        return self.scalar_value

    def first(self):
        return self.values[0] if self.values else None


class _ClosureSession:
    """Table-routed fake AsyncSession for canonical decision evaluation."""

    def __init__(
        self,
        *,
        identity=None,
        employments=None,
        memberships=None,
        assignments=None,
        permissions=None,
        policies=None,
        relationships=None,
        subject=None,
        permission_exists=True,
    ):
        self.identity = identity
        self.employments = employments if employments is not None else []
        self.memberships = memberships if memberships is not None else []
        self.assignments = assignments if assignments is not None else []
        self.permissions = permissions if permissions is not None else []
        self.policies = policies or []
        self.relationships = relationships or []
        self.subject = subject
        self.permission_exists = permission_exists

    async def execute(self, statement):
        sql = str(statement)
        if "niam_identities" in sql:
            return _Result([self.identity] if self.identity else [])
        if "niam_employments" in sql:
            return _Result(self.employments)
        if "niam_memberships" in sql:
            memberships = [
                item for item in self.memberships
                if getattr(item, "revoked_at", None) is None
            ]
            return _Result(memberships)
        if "niam_assignments" in sql:
            return _Result(self.assignments)
        if "niam_role_assignments" in sql:
            return _Result(self.permissions)
        if "niam_policies" in sql:
            return _Result(self.policies)
        if "niam_citizen_relationships" in sql:
            return _Result(self.relationships)
        if "niam_audit_entries" in sql:
            return _Result([])
        return _Result([])

    async def scalar(self, _statement):
        return "permission-id" if self.permission_exists else None

    def add(self, _entry):
        return None

    async def flush(self):
        return None


def _actor(*, mfa: bool = False, active: bool = True) -> AuthorizationActor:
    return AuthorizationActor(
        account=Account(
            id=ACCOUNT,
            identity_id=IDENTITY,
            status=AccountStatus.active.value if active else AccountStatus.suspended.value,
            is_active=active,
            is_locked=False,
        ),
        session=UserSession(
            id="SESSION-W51",
            account_id=ACCOUNT,
            is_active=True,
            expires_at=datetime.now(UTC) + timedelta(hours=1),
            started_at=datetime.now(UTC) - timedelta(minutes=5),
            mfa_used=mfa,
        ),
    )


def _request(**overrides):
    values = {
        "subject_account_id": ACCOUNT,
        "action": "read",
        "resource_type": "patient_record",
        "resource_id": PATIENT,
        "permission_key": "patient_record.read",
        "organization_id": ORG,
        "facility_id": FACILITY_A,
        "resource_context": {
            "exists": True,
            "organization_id": ORG,
            "facility_id": FACILITY_A,
            "patient_id": PATIENT,
        },
    }
    values.update(overrides)
    return AuthorizationRequest(**values)


def _identity():
    return SimpleNamespace(id=IDENTITY, person_id=PERSON)


def _employment(*, status="active", end_date=None, termination_date=None):
    today = datetime.now(UTC).date()
    return SimpleNamespace(
        id="EMPLOYMENT-W51",
        person_id=PERSON,
        organization_id=ORG,
        status=status,
        is_active=True,
        start_date=today - timedelta(days=30),
        end_date=end_date,
        termination_date=termination_date,
    )


def _membership(*, facility_id=FACILITY_A, workspace_id=None, expires_at=None, revoked_at=None):
    return Membership(
        id=MEMBERSHIP,
        account_id=ACCOUNT,
        identity_id=IDENTITY,
        organization_id=ORG,
        facility_id=facility_id,
        department_id=None,
        unit_id=None,
        workspace_id=workspace_id,
        status=MembershipStatus.active.value,
        is_active=True,
        expires_at=expires_at,
        revoked_at=revoked_at,
    )


def _session(**overrides):
    values = {
        "identity": _identity(),
        "employments": [_employment()],
        "memberships": [_membership()],
        "permissions": ["patient_record.read"],
    }
    values.update(overrides)
    return _ClosureSession(**values)


async def _decide(session, *, mfa=False, **request_overrides):
    service = AuthorizationDecisionService(session)
    return await service._evaluate(_actor(mfa=mfa), _request(**request_overrides))


@pytest.mark.asyncio
async def test_in_scope_phi_read_is_allowed_by_canonical_engine():
    decision = await _decide(_session())
    assert decision.allowed is True
    assert decision.reason_code is AuthorizationReason.allowed


@pytest.mark.asyncio
async def test_cross_tenant_request_is_not_resolved_to_a_membership():
    decision = await _decide(
        _session(),
        organization_id=ORG_OTHER,
        resource_context={
            "exists": True,
            "organization_id": ORG_OTHER,
            "facility_id": FACILITY_A,
        },
    )
    assert decision.allowed is False
    assert decision.reason_code is AuthorizationReason.membership_unresolved


@pytest.mark.asyncio
async def test_cross_facility_request_is_not_resolved_to_a_membership():
    decision = await _decide(
        _session(),
        facility_id=FACILITY_B,
        resource_context={
            "exists": True,
            "organization_id": ORG,
            "facility_id": FACILITY_B,
        },
    )
    assert decision.allowed is False
    assert decision.reason_code is AuthorizationReason.membership_unresolved


def test_public_authorization_scope_denial_collapses_to_membership_unresolved_characterized_gap():
    """Specific helper reasons are not observable at the public decision boundary."""
    assert (
        AuthorizationDecisionService._check_scope(
            _request(
                organization_id=ORG_OTHER,
                resource_context={
                    "exists": True,
                    "organization_id": ORG_OTHER,
                    "facility_id": FACILITY_A,
                },
            ),
            _membership(),
        )
        is AuthorizationReason.cross_tenant_denied
    )
    assert (
        AuthorizationDecisionService._check_scope(
            _request(
                facility_id=FACILITY_B,
                resource_context={
                    "exists": True,
                    "organization_id": ORG,
                    "facility_id": FACILITY_B,
                },
            ),
            _membership(),
        )
        is AuthorizationReason.scope_mismatch
    )
    assert (
        AuthorizationDecisionService._check_scope(
            _request(workspace_id=WORKSPACE_B),
            _membership(workspace_id=WORKSPACE_A),
        )
        is AuthorizationReason.workspace_boundary_denied
    )
    assert (
        AuthorizationDecisionService._check_resource_context(
            _request(resource_context={"exists": False})
        )
        is AuthorizationReason.resource_unresolved
    )


@pytest.mark.asyncio
async def test_expired_membership_is_not_resolved():
    session = _session(
        memberships=[
            _membership(expires_at=datetime.now(UTC) - timedelta(seconds=1))
        ]
    )
    decision = await _decide(session)
    assert decision.allowed is False
    assert decision.reason_code is AuthorizationReason.membership_unresolved


@pytest.mark.asyncio
async def test_revoked_membership_is_not_resolved():
    membership = _membership(revoked_at=datetime.now(UTC) - timedelta(seconds=1))
    membership.status = MembershipStatus.revoked.value
    decision = await _decide(_session(memberships=[membership]))
    assert decision.allowed is False
    assert decision.reason_code is AuthorizationReason.membership_unresolved


@pytest.mark.asyncio
async def test_terminated_workforce_is_denied_despite_active_membership():
    session = _session(
        employments=[_employment(status="terminated", termination_date=datetime.now(UTC).date())]
    )
    decision = await _decide(session)
    assert decision.allowed is False
    assert decision.reason_code is AuthorizationReason.employment_terminated


@pytest.mark.asyncio
async def test_break_glass_cannot_rescue_terminated_workforce():
    session = _session(
        employments=[_employment(status="terminated", termination_date=datetime.now(UTC).date())]
    )
    decision = await _decide(
        session,
        break_glass=True,
        break_glass_authorized=True,
        environment={
            "break_glass_reason": "synthetic-emergency",
            "break_glass_expires_at": (datetime.now(UTC) + timedelta(minutes=10)).isoformat(),
        },
    )
    assert decision.allowed is False
    assert decision.reason_code is AuthorizationReason.employment_terminated


@pytest.mark.asyncio
async def test_break_glass_requires_workflow_authorization_and_environment_fields():
    unauthorized = await _decide(_session(), break_glass=True, break_glass_authorized=False)
    assert unauthorized.reason_code is AuthorizationReason.break_glass_workflow_required

    missing_environment = await _decide(
        _session(), break_glass=True, break_glass_authorized=True, environment={}
    )
    assert missing_environment.reason_code is AuthorizationReason.break_glass_workflow_required


@pytest.mark.asyncio
async def test_break_glass_invalid_expiry_is_denied():
    decision = await _decide(
        _session(),
        mfa=True,
        break_glass=True,
        break_glass_authorized=True,
        environment={
            "break_glass_reason": "synthetic-emergency",
            "break_glass_expires_at": "not-a-timestamp",
        },
    )
    assert decision.allowed is False
    assert decision.reason_code is AuthorizationReason.break_glass_workflow_required


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "expiry",
    [
        (datetime.now(UTC) - timedelta(minutes=1)).isoformat(),
        (datetime.now(UTC) + timedelta(minutes=10)).replace(tzinfo=None).isoformat(),
    ],
)
async def test_break_glass_expired_or_naive_expiry_is_denied(expiry):
    decision = await _decide(
        _session(),
        mfa=True,
        break_glass=True,
        break_glass_authorized=True,
        environment={
            "break_glass_reason": "synthetic-emergency",
            "break_glass_expires_at": expiry,
        },
    )
    assert decision.allowed is False
    assert decision.reason_code is AuthorizationReason.break_glass_workflow_required


@pytest.mark.asyncio
async def test_break_glass_valid_future_expiry_is_allowed():
    decision = await _decide(
        _session(),
        mfa=True,
        break_glass=True,
        break_glass_authorized=True,
        environment={
            "break_glass_reason": "synthetic-emergency",
            "break_glass_expires_at": (datetime.now(UTC) + timedelta(minutes=10)).isoformat(),
        },
    )
    assert decision.allowed is True


@pytest.mark.asyncio
async def test_break_glass_requires_mfa_even_when_authorized():
    service = AuthorizationDecisionService(_session())
    decision = await service._evaluate(
        _actor(mfa=False),
        _request(
            break_glass=True,
            break_glass_authorized=True,
            environment={
                "break_glass_reason": "synthetic-emergency",
                "break_glass_expires_at": (datetime.now(UTC) + timedelta(minutes=10)).isoformat(),
            },
        ),
    )
    assert decision.allowed is False
    assert decision.reason_code is AuthorizationReason.step_up_required
    assert decision.required_assurance == "MFA"


@pytest.mark.asyncio
async def test_valid_break_glass_does_not_replace_membership_or_rbac():
    environment = {
        "break_glass_reason": "synthetic-emergency",
        "break_glass_expires_at": (datetime.now(UTC) + timedelta(minutes=10)).isoformat(),
    }
    no_membership = await _decide(
        _session(memberships=[]),
        mfa=True,
        break_glass=True,
        break_glass_authorized=True,
        environment=environment,
    )
    assert no_membership.reason_code is AuthorizationReason.membership_unresolved

    no_permission = await _decide(
        _session(permissions=[]),
        mfa=True,
        break_glass=True,
        break_glass_authorized=True,
        environment=environment,
    )
    assert no_permission.reason_code is AuthorizationReason.permission_missing


@pytest.mark.asyncio
async def test_valid_break_glass_with_mfa_still_requires_normal_rbac_allow():
    service = AuthorizationDecisionService(_session())
    decision = await service._evaluate(
        _actor(mfa=True),
        _request(
            break_glass=True,
            break_glass_authorized=True,
            environment={
                "break_glass_reason": "synthetic-emergency",
                "break_glass_expires_at": (datetime.now(UTC) + timedelta(minutes=10)).isoformat(),
            },
        ),
    )
    assert decision.allowed is True
    assert decision.reason_code is AuthorizationReason.allowed


@pytest.mark.asyncio
async def test_unknown_phi_action_is_denied_even_with_broad_permission_key():
    assert resolve_phi_permission("patient_record", "teleport") is None
    decision = await _decide(
        _session(permissions=["patient_record.all"]),
        action="teleport",
        permission_key="patient_record.all",
    )
    assert decision.allowed is False
    assert decision.reason_code is AuthorizationReason.permission_unknown


@pytest.mark.asyncio
async def test_wrong_phi_action_permission_is_denied():
    decision = await _decide(
        _session(permissions=["lab_result.read"]),
        permission_key="lab_result.read",
    )
    assert decision.allowed is False
    assert decision.reason_code is AuthorizationReason.phi_permission_conflict


def _consent(*, status=NiamConsentStatus.active.value, expires_in_hours=1):
    return NiamConsent(
        uuid="CONSENT-SYN-W51",
        subject_account_id=ACCOUNT,
        grantee_account_id="ACCOUNT-W51-GRANTEE",
        purpose="synthetic-treatment",
        scope={"resource_domain": "patient_record"},
        resource_domain="patient_record",
        status=status,
        expires_at=datetime.now(UTC) + timedelta(hours=expires_in_hours),
        version=1,
        source="USER_PORTAL",
    )


@pytest.mark.parametrize(
    "status",
    [
        NiamConsentStatus.active,
        NiamConsentStatus.withdrawn,
        NiamConsentStatus.expired,
        NiamConsentStatus.revoked,
    ],
)
def test_niam_consent_validity_requires_active_status_and_future_expiry(status):
    if status is NiamConsentStatus.active:
        assert _consent(status=status.value).is_valid_now() is True
        assert _consent(status=status.value, expires_in_hours=-1).is_valid_now() is False
    else:
        assert _consent(status=status.value).is_valid_now() is False


def test_canonical_decision_request_has_no_consent_binding_characterized_gap():
    field_names = {item.name for item in fields(AuthorizationRequest)}
    assert "consent_id" not in field_names
    assert "consent" not in field_names


def test_guardian_purposes_are_not_in_canonical_request_allowlist_characterized_gap():
    assert "guardian_access" not in AuthorizationDecisionService.ALLOWED_PURPOSES
    assert "minor_guardian" not in AuthorizationDecisionService.ALLOWED_PURPOSES


def _minor_subject():
    return SimpleNamespace(
        id="CITIZEN-W51-MINOR",
        date_of_birth=date(2015, 5, 20),
        national_id_hash=None,
        name_blocking_key="SYN2015M",
        merged_into_id=None,
        is_deceased=False,
        identity_status=SimpleNamespace(value="active"),
    )


def _adult_subject():
    subject = _minor_subject()
    subject.date_of_birth = date(1995, 5, 20)
    return subject


def _relationship(**overrides):
    values = {
        "id": "RELATIONSHIP-W51",
        "relationship_type": "guardian",
        "verified_at": datetime(2026, 1, 1, tzinfo=UTC),
        "purpose": "guardian_access",
        "scope": {"resources": ["patient_record"]},
        "metadata_": {
            "guardian_type": "parent",
            "source_verified": True,
            "guardian_verified": True,
        },
        "citizen_id": "CITIZEN-W51-MINOR",
        "is_active_at": lambda now=None: True,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_verified_guardian_read_is_allowed_by_canonical_guard():
    decision = evaluate_guardian_access(
        subject=_minor_subject(),
        relationship=_relationship(),
        action="read",
        today=_TODAY,
    )
    assert decision.allowed is True
    assert decision.reason == "verified_guardian_access"


@pytest.mark.parametrize(
    ("overrides", "expected_reason"),
    [
        ({"subject": None}, "subject_not_linkable"),
        ({"relationship": None}, "no_guardian_relationship"),
        ({"relationship": _relationship(relationship_type="self")}, "not_guardian_relationship"),
        ({"relationship": _relationship(verified_at=None)}, "guardian_relationship_unverified"),
        ({"action": "export"}, "action_not_permitted_for_guardian"),
        ({"subject": _adult_subject()}, "guardian_authority_ended"),
    ],
)
def test_guardian_overreach_is_denied_by_canonical_guard(overrides, expected_reason):
    values = {
        "subject": _minor_subject(),
        "relationship": _relationship(),
        "action": "read",
        "today": _TODAY,
    }
    values.update(overrides)
    decision = evaluate_guardian_access(**values)
    assert decision.allowed is False
    assert decision.reason == expected_reason
