"""Wave 04 — terminated/expired workforce access enforcement.

Every assertion goes through the existing canonical AuthorizationDecisionService.
No parallel authorization engine, cache or policy source is introduced. Synthetic
fixtures only; no PHI, PII, credential or production data is used.
"""

from __future__ import annotations

from datetime import date, timedelta
from types import SimpleNamespace

import pytest
from app._compat import UTC
from app.identity.services.authorization_decision import (
    AuthorizationActor,
    AuthorizationDecisionService,
    AuthorizationReason,
    AuthorizationRequest,
)


class _Result:
    def __init__(self, values):
        self.values = values

    def scalars(self):
        return self

    def all(self):
        return self.values


class _WorkforceSession:
    """Table-name routed scripted session mirroring the canonical Phase 8 harness."""

    def __init__(self, *, identity=None, employments=None, memberships=None, assignments=None, permissions=None):
        self.identity = identity
        self.employments = employments or []
        self.memberships = memberships or []
        self.assignments = assignments or []
        self.permissions = permissions or []

    async def execute(self, statement):
        sql = str(statement)
        if "niam_identities" in sql:
            return _Result([self.identity] if self.identity is not None else [])
        if "niam_employments" in sql:
            return _Result(list(self.employments))
        if "niam_memberships" in sql:
            matches = list(self.memberships)
            if "revoked_at IS NULL" in sql:
                matches = [item for item in matches if getattr(item, "revoked_at", None) is None]
            return _Result(matches)
        if "niam_assignments" in sql:
            return _Result(list(self.assignments))
        if "niam_role_assignments" in sql:
            return _Result(list(self.permissions))
        if "niam_policies" in sql:
            return _Result([])
        return _Result([])

    async def scalar(self, _statement):
        return "permission-id"

    def add(self, _entry):
        return None

    async def flush(self):
        return None


def _actor(*, session_active=True, mfa=False):
    account = SimpleNamespace(
        id="ACCOUNT-W04",
        identity_id="IDENTITY-W04",
        status="active",
        is_active=True,
        is_locked=False,
    )
    session = SimpleNamespace(
        id="SESSION-W04",
        account_id="ACCOUNT-W04",
        is_active=session_active,
        expires_at=datetime_now() + timedelta(hours=1),
        mfa_used=mfa,
    )
    return AuthorizationActor(account=account, session=session)


def datetime_now():
    from datetime import datetime

    return datetime.now(UTC)


def _request(**overrides):
    values = dict(
        subject_account_id="ACCOUNT-W04",
        action="read",
        resource_type="patient_record",
        resource_id="PATIENT-SYN-W04",
        permission_key="patient_record.read",
        organization_id="ORG-A",
        facility_id="FACILITY-A",
        department_id=None,
        unit_id=None,
        workspace_id=None,
        resource_context={
            "exists": True,
            "organization_id": "ORG-A",
            "facility_id": "FACILITY-A",
        },
    )
    values.update(overrides)
    return AuthorizationRequest(**values)


def _identity():
    return SimpleNamespace(id="IDENTITY-W04", person_id="PERSON-W04")


def _employment(*, status="active", person_id="PERSON-W04", end_date=None, termination_date=None, is_active=True):
    return SimpleNamespace(
        id="EMPLOYMENT-W04",
        person_id=person_id,
        organization_id="ORG-A",
        status=status,
        is_active=is_active,
        start_date=date.today() - timedelta(days=30),
        end_date=end_date,
        termination_date=termination_date,
    )


def _membership(*, organization_id="ORG-A", facility_id="FACILITY-A", status="active", expires_at=None, revoked_at=None):
    return SimpleNamespace(
        id="MEMBERSHIP-W04",
        account_id="ACCOUNT-W04",
        organization_id=organization_id,
        facility_id=facility_id,
        department_id=None,
        unit_id=None,
        workspace_id=None,
        status=status,
        is_active=True,
        expires_at=expires_at,
        revoked_at=revoked_at,
    )


def _assignment(*, status="active", end_date=None, expected_end_date=None, facility_id="FACILITY-A"):
    return SimpleNamespace(
        id="ASSIGNMENT-W04",
        person_id="PERSON-W04",
        facility_id=facility_id,
        status=status,
        is_active=True,
        start_date=date.today() - timedelta(days=5),
        end_date=end_date,
        expected_end_date=expected_end_date,
    )


def _service(**kwargs):
    return AuthorizationDecisionService(_WorkforceSession(**kwargs))


@pytest.mark.asyncio
async def test_active_employee_with_valid_membership_allowed_in_scope():
    service = _service(
        identity=_identity(),
        employments=[_employment()],
        memberships=[_membership()],
        permissions=["patient_record.read"],
    )
    decision = await service.authorize(_actor(), _request())
    assert decision.allowed is True


@pytest.mark.asyncio
async def test_expired_membership_denied():
    service = _service(
        identity=_identity(),
        employments=[_employment()],
        memberships=[_membership(expires_at=datetime_now() - timedelta(seconds=1))],
        permissions=["patient_record.read"],
    )
    decision = await service.authorize(_actor(), _request())
    assert decision.allowed is False
    assert decision.reason_code is AuthorizationReason.membership_unresolved


@pytest.mark.asyncio
async def test_revoked_membership_denied():
    service = _service(
        identity=_identity(),
        employments=[_employment()],
        memberships=[_membership(revoked_at=datetime_now() - timedelta(seconds=1))],
        permissions=["patient_record.read"],
    )
    decision = await service.authorize(_actor(), _request())
    assert decision.allowed is False


@pytest.mark.asyncio
async def test_terminated_employment_denied_despite_live_membership():
    service = _service(
        identity=_identity(),
        employments=[_employment(status="terminated", termination_date=date.today() - timedelta(days=1))],
        memberships=[_membership()],
        permissions=["patient_record.read"],
    )
    decision = await service.authorize(_actor(), _request())
    assert decision.allowed is False
    assert decision.reason_code is AuthorizationReason.employment_terminated


@pytest.mark.asyncio
async def test_expired_temporary_assignment_denied():
    service = _service(
        identity=_identity(),
        employments=[_employment()],
        memberships=[_membership(facility_id=None)],
        assignments=[_assignment(end_date=date.today() - timedelta(days=1))],
        permissions=["patient_record.read"],
    )
    decision = await service.authorize(_actor(), _request())
    assert decision.allowed is False
    assert decision.reason_code is AuthorizationReason.assignment_expired


@pytest.mark.asyncio
async def test_second_valid_membership_allows_only_own_scope():
    # A second valid membership at another facility must not lend access here.
    service = _service(
        identity=_identity(),
        employments=[_employment()],
        memberships=[
            _membership(facility_id="FACILITY-B"),
            _membership(facility_id="FACILITY-A"),
        ],
        permissions=["patient_record.read"],
    )
    decision = await service.authorize(_actor(), _request())
    assert decision.allowed is True

    # The other facility's scope is denied even though its membership is active.
    cross = _service(
        identity=_identity(),
        employments=[_employment()],
        memberships=[_membership(facility_id="FACILITY-B")],
        permissions=["patient_record.read"],
    )
    denied = await cross.authorize(
        _actor(),
        _request(facility_id="FACILITY-A", resource_context={"exists": True, "organization_id": "ORG-A", "facility_id": "FACILITY-A"}),
    )
    assert denied.allowed is False


@pytest.mark.asyncio
async def test_cached_authorization_does_not_survive_termination():
    """The engine re-resolves state on every decision; there is no auth cache."""
    session = _WorkforceSession(
        identity=_identity(),
        employments=[_employment()],
        memberships=[_membership()],
        permissions=["patient_record.read"],
    )
    service = AuthorizationDecisionService(session)
    first = await service.authorize(_actor(), _request())
    assert first.allowed is True

    session.employments = [
        _employment(status="terminated", termination_date=date.today() - timedelta(days=1))
    ]
    second = await service.authorize(_actor(), _request())
    assert second.allowed is False
    assert second.reason_code is AuthorizationReason.employment_terminated


@pytest.mark.asyncio
async def test_inactive_clinical_session_denied():
    service = _service(
        identity=_identity(),
        employments=[_employment()],
        memberships=[_membership()],
        permissions=["patient_record.read"],
    )
    decision = await service.authorize(_actor(session_active=False), _request())
    assert decision.allowed is False
    assert decision.reason_code is AuthorizationReason.session_invalid


@pytest.mark.asyncio
async def test_break_glass_cannot_rescue_terminated_workforce():
    service = _service(
        identity=_identity(),
        employments=[_employment(status="terminated")],
        memberships=[_membership()],
        permissions=["patient_record.read"],
    )
    decision = await service.authorize(
        _actor(mfa=True),
        _request(break_glass=True, break_glass_authorized=True, environment={"break_glass_reason": "test", "break_glass_expires_at": "soon"}),
    )
    assert decision.allowed is False
    assert decision.reason_code is AuthorizationReason.employment_terminated
