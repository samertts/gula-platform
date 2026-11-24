"""Adversarial tests for the deny-by-default authorization policy engine.

Every test makes a real evaluation through ``AuthorizationEngine.evaluate`` and
asserts on the returned decision and the append-only audit record. No test is
skipped and no assertion is weakened to accommodate a failure.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import cast

import pytest
from app.health_core.authorization import (
    PUBLIC_DENIAL_REASON,
    AuthorizationEngine,
    Decision,
    PolicyId,
    Principal,
    ResourceContext,
    RevocationScope,
)
from app.health_core.authorization.models import Action
from app.health_core.common.errors import InvalidSyntheticReferenceError
from app.health_core.contracts.authorization import Permission, Role
from app.health_core.contracts.catalogue import ContractOperation as Op

TENANT = "SYN-LAB-0001"
OTHER_TENANT = "SYN-LAB-0002"
PATIENT = "SYN-PAT-0001"
OTHER_PATIENT = "SYN-PAT-0002"
ORG = "SYN-ORG-0001"
OTHER_ORG = "SYN-ORG-0002"
FACILITY = "SYN-FAC-0001"
OTHER_FACILITY = "SYN-FAC-0002"
PRINCIPAL = "SYN-PRC-0001"
OTHER_PRINCIPAL = "SYN-PRC-0002"


def principal(**overrides: object) -> Principal:
    values: dict[str, object] = {
        "principal_id": PRINCIPAL,
        "tenant_id": TENANT,
        "roles": frozenset({Role.VIEWER}),
        "patient_scopes": frozenset({PATIENT}),
    }
    values.update(overrides)
    return Principal(**values)  # type: ignore[arg-type]


def resource(action: Action, **overrides: object) -> ResourceContext:
    values: dict[str, object] = {
        "tenant_id": TENANT,
        "resource_id": "SYN-RES-0001",
        "action": action,
    }
    values.update(overrides)
    return ResourceContext(**values)  # type: ignore[arg-type]


def denied_policy(engine: AuthorizationEngine, who: Principal, what: ResourceContext) -> PolicyId:
    decision = engine.evaluate(who, what)
    assert decision.decision is Decision.DENY
    return decision.policy_id


# ------------------------------------------------------- deny-by-default / auth


def test_authenticated_principal_with_no_role_or_grant_is_denied():
    engine = AuthorizationEngine()
    who = Principal(principal_id=PRINCIPAL, tenant_id=TENANT)
    decision = engine.evaluate(who, resource(Op.ENCOUNTER_READ))
    assert decision.decision is Decision.DENY
    assert decision.policy_id is PolicyId.DENY_MISSING_PERMISSION


def test_authentication_alone_never_creates_a_policy():
    engine = AuthorizationEngine()
    who = Principal(principal_id=PRINCIPAL, tenant_id=TENANT)
    for action in Op:
        decision = engine.evaluate(who, resource(action))
        assert decision.decision is Decision.DENY


def test_unknown_injected_action_is_denied_with_no_policy():
    engine = AuthorizationEngine()
    who = principal(roles=frozenset({Role.ADMIN}))
    injected = cast(Action, "health_core:secret.admin_operation")
    assert denied_policy(engine, who, resource(injected)) is PolicyId.DENY_NO_POLICY


def test_unauthenticated_principal_denied_even_with_valid_role_and_scope():
    engine = AuthorizationEngine()
    who = principal().without_authentication()
    assert denied_policy(engine, who, resource(Op.ENCOUNTER_READ)) is PolicyId.DENY_UNAUTHENTICATED


# ------------------------------------------------------------------ tenant rule


def test_cross_tenant_access_is_denied():
    engine = AuthorizationEngine()
    who = principal()
    assert (
        denied_policy(engine, who, resource(Op.ENCOUNTER_READ, tenant_id=OTHER_TENANT))
        is PolicyId.DENY_TENANT
    )


def test_cross_tenant_denial_reason_is_generic_and_discloses_nothing():
    engine = AuthorizationEngine()
    who = principal()
    decision = engine.evaluate(who, resource(Op.ENCOUNTER_READ, tenant_id=OTHER_TENANT))
    assert decision.reason == PUBLIC_DENIAL_REASON
    lowered = decision.reason.lower()
    assert "exist" not in lowered
    assert "tenant" not in lowered
    assert "found" not in lowered


def test_tenant_denial_is_audited_with_the_resource_tenant():
    """The guard relies on this path after it substitutes the indexed tenant."""
    engine = AuthorizationEngine()
    who = principal()
    decision = engine.evaluate(who, resource(Op.ENCOUNTER_READ, tenant_id=OTHER_TENANT))
    assert decision.policy_id is PolicyId.DENY_TENANT
    assert decision.tenant_id == OTHER_TENANT
    records = engine.audit.records()
    assert len(records) == 1
    assert records[0].decision == Decision.DENY.value
    assert records[0].policy_id == PolicyId.DENY_TENANT.value
    assert records[0].tenant_id == OTHER_TENANT
    assert engine.audit.verify().is_valid is True


# -------------------------------------------------------------- RBAC exactness


def test_viewer_role_grants_its_declared_read_permission():
    engine = AuthorizationEngine()
    decision = engine.evaluate(principal(), resource(Op.ENCOUNTER_READ, patient_ref=PATIENT))
    assert decision.decision is Decision.ALLOW
    assert decision.policy_id is PolicyId.ALLOW_EXPLICIT


def test_viewer_role_cannot_escalate_to_a_write():
    engine = AuthorizationEngine()
    assert (
        denied_policy(engine, principal(), resource(Op.ENCOUNTER_CREATE, patient_ref=PATIENT))
        is PolicyId.DENY_MISSING_PERMISSION
    )


def test_admin_role_does_not_implicitly_inherit_every_permission():
    engine = AuthorizationEngine()
    who = principal(roles=frozenset({Role.ADMIN}))
    assert (
        denied_policy(engine, who, resource(Op.LAB_RESULT_CREATE, patient_ref=PATIENT))
        is PolicyId.DENY_MISSING_PERMISSION
    )


def test_lab_technician_role_cannot_perform_clinical_write():
    engine = AuthorizationEngine()
    who = principal(roles=frozenset({Role.LAB_TECHNICIAN}))
    assert (
        denied_policy(engine, who, resource(Op.DIAGNOSIS_CREATE, patient_ref=PATIENT))
        is PolicyId.DENY_MISSING_PERMISSION
    )


def test_adding_a_second_role_does_not_inherit_unrelated_permissions():
    engine = AuthorizationEngine()
    who = principal(roles=frozenset({Role.VIEWER, Role.CLINICIAN}))
    assert (
        denied_policy(engine, who, resource(Op.SPECIMEN_CREATE, patient_ref=PATIENT))
        is PolicyId.DENY_MISSING_PERMISSION
    )


def test_forged_role_string_is_rejected_when_building_principal():
    with pytest.raises(ValueError, match="Role enum"):
        principal(roles=frozenset({"admin"}))  # type: ignore[arg-type]


def test_forged_role_string_is_rejected_by_with_role():
    with pytest.raises(ValueError, match="Role enum"):
        principal().with_role("admin")  # type: ignore[arg-type]


def test_forged_permission_string_is_rejected_by_grant_registry():
    engine = AuthorizationEngine()
    with pytest.raises(ValueError, match="Permission enum"):
        engine.grant(PRINCIPAL, "health_core:lab_result.create", reason="forged")  # type: ignore[arg-type]


# ------------------------------------------------------------- direct grants


def test_practitioner_specific_grant_enables_an_otherwise_denied_write():
    engine = AuthorizationEngine()
    engine.grant(PRINCIPAL, Permission.ENCOUNTER_CREATE, reason="attending clinician")
    who = principal()
    decision = engine.evaluate(who, resource(Op.ENCOUNTER_CREATE, patient_ref=PATIENT))
    assert decision.decision is Decision.ALLOW


def test_grant_to_another_principal_does_not_apply():
    engine = AuthorizationEngine()
    engine.grant(OTHER_PRINCIPAL, Permission.ENCOUNTER_CREATE, reason="someone else")
    assert (
        denied_policy(
            engine, principal(), resource(Op.ENCOUNTER_CREATE, patient_ref=PATIENT)
        )
        is PolicyId.DENY_MISSING_PERMISSION
    )


def test_empty_grant_reason_is_rejected():
    engine = AuthorizationEngine()
    with pytest.raises(ValueError, match="non-empty reason"):
        engine.grant(PRINCIPAL, Permission.ENCOUNTER_CREATE, reason="  ")


def test_expired_grant_no_longer_allows():
    engine = AuthorizationEngine()
    past = (datetime.now(UTC) - timedelta(days=1)).isoformat()
    engine.grant(
        PRINCIPAL,
        Permission.ENCOUNTER_CREATE,
        reason="temporary",
        expires_at=past,
    )
    assert engine.active_grants(PRINCIPAL) == ()
    assert (
        denied_policy(engine, principal(), resource(Op.ENCOUNTER_CREATE, patient_ref=PATIENT))
        is PolicyId.DENY_MISSING_PERMISSION
    )


# ------------------------------------------------------------------ revocation


def test_principal_revocation_overrides_an_existing_grant():
    engine = AuthorizationEngine()
    engine.grant(PRINCIPAL, Permission.ENCOUNTER_CREATE, reason="attending")
    engine.revoke_principal(PRINCIPAL, reason="suspended")
    assert (
        denied_policy(engine, principal(), resource(Op.ENCOUNTER_CREATE, patient_ref=PATIENT))
        is PolicyId.DENY_REVOKED_PRINCIPAL
    )


def test_principal_revocation_registered_before_grant_still_denies():
    engine = AuthorizationEngine()
    engine.revoke_principal(PRINCIPAL, reason="pre-emptive suspension")
    engine.grant(PRINCIPAL, Permission.ENCOUNTER_CREATE, reason="late grant")
    assert (
        denied_policy(engine, principal(), resource(Op.ENCOUNTER_CREATE, patient_ref=PATIENT))
        is PolicyId.DENY_REVOKED_PRINCIPAL
    )


def test_permission_revocation_overrides_a_direct_grant():
    engine = AuthorizationEngine()
    engine.grant(PRINCIPAL, Permission.ENCOUNTER_CREATE, reason="attending")
    engine.revoke_permission(Permission.ENCOUNTER_CREATE, reason="policy withdrawn")
    assert (
        denied_policy(engine, principal(), resource(Op.ENCOUNTER_CREATE, patient_ref=PATIENT))
        is PolicyId.DENY_REVOKED_PERMISSION
    )


def test_role_revocation_blocks_role_granted_permission():
    engine = AuthorizationEngine()
    engine.revoke_role(Role.CLINICIAN, reason="role withdrawn", permission=Permission.ENCOUNTER_CREATE)
    who = principal(roles=frozenset({Role.CLINICIAN}))
    assert (
        denied_policy(engine, who, resource(Op.ENCOUNTER_CREATE, patient_ref=PATIENT))
        is PolicyId.DENY_REVOKED_ROLE
    )


def test_expired_revocation_no_longer_denies():
    engine = AuthorizationEngine()
    past = (datetime.now(UTC) - timedelta(days=1)).isoformat()
    engine.grant(PRINCIPAL, Permission.ENCOUNTER_CREATE, reason="attending")
    engine.revoke_principal(PRINCIPAL, reason="one-day suspension", expires_at=past)
    assert engine.active_revocations() == ()
    decision = engine.evaluate(principal(), resource(Op.ENCOUNTER_CREATE, patient_ref=PATIENT))
    assert decision.decision is Decision.ALLOW


def test_revocation_registry_records_reason_and_scope():
    engine = AuthorizationEngine()
    record = engine.revoke_role(Role.VIEWER, reason="read access withdrawn")
    assert record.scope is RevocationScope.ROLE
    assert record.role is Role.VIEWER
    assert record.reason == "read access withdrawn"
    assert record.revoked_at


# ------------------------------------------------------- org / facility scoping


def test_missing_organization_attribute_is_denied():
    engine = AuthorizationEngine()
    who = principal(roles=frozenset({Role.VIEWER, Role.CLINICIAN}))
    assert (
        denied_policy(engine, who, resource(Op.ORGANIZATION_READ)) is PolicyId.DENY_MISSING_ATTRIBUTE
    )


def test_out_of_scope_organization_is_denied():
    engine = AuthorizationEngine()
    who = principal(roles=frozenset({Role.VIEWER, Role.CLINICIAN}))
    assert (
        denied_policy(engine, who, resource(Op.FACILITY_READ, organization_id=OTHER_ORG, facility_id=FACILITY))
        is PolicyId.DENY_ORG_SCOPE
    )


def test_out_of_scope_facility_is_denied_even_with_matching_organization():
    engine = AuthorizationEngine()
    who = principal(roles=frozenset({Role.VIEWER, Role.CLINICIAN}), organization_ids=frozenset({ORG}))
    assert (
        denied_policy(
            engine,
            who,
            resource(Op.FACILITY_READ, organization_id=ORG, facility_id=OTHER_FACILITY),
        )
        is PolicyId.DENY_FACILITY_SCOPE
    )


# ----------------------------------------------------------- patient scoping


def test_patient_scoped_action_denied_without_any_patient_scope():
    engine = AuthorizationEngine()
    who = principal(roles=frozenset({Role.VIEWER}), patient_scopes=frozenset())
    assert (
        denied_policy(engine, who, resource(Op.ENCOUNTER_READ, patient_ref=PATIENT))
        is PolicyId.DENY_PATIENT_SCOPE
    )


def test_patient_scope_mismatch_is_denied():
    engine = AuthorizationEngine()
    who = principal(patient_scopes=frozenset({OTHER_PATIENT}))
    assert (
        denied_policy(engine, who, resource(Op.ENCOUNTER_READ, patient_ref=PATIENT))
        is PolicyId.DENY_PATIENT_SCOPE
    )


def test_patient_attribute_on_non_patient_action_still_requires_scope():
    engine = AuthorizationEngine()
    who = principal(patient_scopes=frozenset({OTHER_PATIENT}))
    assert (
        denied_policy(engine, who, resource(Op.PRACTITIONER_READ, patient_ref=PATIENT))
        is PolicyId.DENY_PATIENT_SCOPE
    )


def test_wildcard_patient_scope_is_not_representable():
    with pytest.raises(InvalidSyntheticReferenceError):
        principal(patient_scopes=frozenset({"*"}))


def test_explicit_patient_scope_utility_only_accepts_synthetic_references():
    who = principal(patient_scopes=frozenset())
    with pytest.raises(InvalidSyntheticReferenceError):
        who.with_patient_scope("12345678901")


# ------------------------------------------------------------------ audit record


def test_every_evaluation_appends_exactly_one_audit_record():
    engine = AuthorizationEngine()
    assert len(engine.audit) == 0
    engine.evaluate(principal(), resource(Op.ENCOUNTER_READ, patient_ref=PATIENT))
    assert len(engine.audit) == 1
    denied_policy(engine, principal(roles=frozenset()), resource(Op.ENCOUNTER_CREATE))
    assert len(engine.audit) == 2


def test_audit_record_captures_every_required_dimension():
    engine = AuthorizationEngine()
    engine.evaluate(principal(), resource(Op.ENCOUNTER_READ, patient_ref=PATIENT))
    record = engine.audit.records()[0]
    assert record.principal_id == PRINCIPAL
    assert record.tenant_id == TENANT
    assert record.action == Op.ENCOUNTER_READ.value
    assert record.resource_id == "SYN-RES-0001"
    assert record.decision == Decision.ALLOW.value
    assert record.policy_id == PolicyId.ALLOW_EXPLICIT.value
    assert record.occurred_at
    assert record.record_id.startswith("SYN-AUD-")


def test_all_denial_types_use_the_same_generic_public_reason():
    engine = AuthorizationEngine()
    who = principal(roles=frozenset())
    cases = (
        resource(Op.ENCOUNTER_CREATE, patient_ref=PATIENT),
        resource(Op.ENCOUNTER_READ, tenant_id=OTHER_TENANT),
        resource(Op.ORGANIZATION_READ),
    )
    reasons = [engine.evaluate(who, case).reason for case in cases]
    assert reasons == [PUBLIC_DENIAL_REASON] * len(cases)
    assert len(set(reasons)) == 1
