"""End-to-end adversarial tests of the authorizing facade over real services.

These tests prove that authorization is enforced at runtime: a denial happens
before the wrapped clinical/lab service is called, and no caller-supplied
attribute can forge a patient, organization or facility scope on a read.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from app.health_core.authorization import (
    PUBLIC_DENIAL_REASON,
    AuthorizationDenied,
    AuthorizationEngine,
    AuthorizedHealthCore,
    Decision,
    PolicyId,
    Principal,
    build_authorized_context,
)
from app.health_core.clinical import ClinicalContext, EncounterStatus, UnknownClinicalEntityError
from app.health_core.common import TenantMismatchError
from app.health_core.common.ids import new_synthetic_id
from app.health_core.contracts.authorization import Permission, Role
from app.health_core.identity.synthetic import SyntheticPatientRegistry
from app.health_core.lab import LabWorkflowService, SpecimenStatus, VerificationDecision

TENANT = "SYN-LAB-0001"
OTHER_TENANT = "SYN-LAB-0002"
PRACTITIONER = "SYN-PRC-0001"
ORG = "SYN-ORG-0001"
OTHER_ORG = "SYN-ORG-0002"
FACILITY = "SYN-FAC-0001"
OTHER_FACILITY = "SYN-FAC-0002"
ACTOR = "SYN-ACT-0001"
FOREIGN_PRACTITIONER = "SYN-PRC-0002"
FOREIGN_ORG = "SYN-ORG-0003"
FOREIGN_FACILITY = "SYN-FAC-0003"
FOREIGN_ENCOUNTER = "SYN-ENC-0101"


@pytest.fixture
def guard() -> AuthorizedHealthCore:
    return build_authorized_context(SyntheticPatientRegistry())


@pytest.fixture
def patient(guard: AuthorizedHealthCore):
    return guard._clinical.identity.register_patient(tenant_id=TENANT, label="guard-fixture")


@pytest.fixture
def privileged() -> Principal:
    return Principal(
        principal_id=PRACTITIONER,
        tenant_id=TENANT,
        roles=frozenset({Role.VIEWER, Role.CLINICIAN, Role.LAB_TECHNICIAN}),
        organization_ids=frozenset({ORG}),
        facility_ids=frozenset({FACILITY}),
    )


def scoped(principal: Principal, patient_ref: str) -> Principal:
    return principal.with_patient_scope(patient_ref)


def seed(
    guard: AuthorizedHealthCore,
    principal: Principal,
    *,
    tenant_id: str = TENANT,
) -> None:
    guard.register_practitioner(
        principal,
        tenant_id=tenant_id,
        idempotency_key=PRACTITIONER,
        role="physician",
        qualification="MBBS",
    )
    guard.register_organization(
        principal,
        tenant_id=tenant_id,
        idempotency_key=ORG,
        label="synthetic-hospital",
    )
    guard.register_facility(
        principal,
        tenant_id=tenant_id,
        idempotency_key=FACILITY,
        organization_id=ORG,
        label="synthetic-ward",
        facility_type="hospital",
    )


def create_encounter(
    guard: AuthorizedHealthCore, principal: Principal, patient_ref: str, key: str = "SYN-ENC-0001"
):
    return guard.create_encounter(
        principal,
        tenant_id=TENANT,
        idempotency_key=key,
        patient_ref=patient_ref,
        practitioner_id=PRACTITIONER,
        facility_id=FACILITY,
        reason="synthetic consultation",
    )


def last_policy(engine: AuthorizationEngine) -> PolicyId:
    records = engine.audit.records()
    assert records
    return PolicyId(records[-1].policy_id)


def foreign_tenant_resource(guard: AuthorizedHealthCore):
    """Store one encounter under OTHER_TENANT through the guarded write path."""
    owner = Principal(
        principal_id=FOREIGN_PRACTITIONER,
        tenant_id=OTHER_TENANT,
        roles=frozenset({Role.VIEWER, Role.CLINICIAN, Role.LAB_TECHNICIAN}),
        organization_ids=frozenset({FOREIGN_ORG}),
        facility_ids=frozenset({FOREIGN_FACILITY}),
    )
    foreign_patient = guard._clinical.identity.register_patient(
        tenant_id=OTHER_TENANT, label="tenant-b-guard-fixture"
    )
    guard.register_practitioner(
        owner,
        tenant_id=OTHER_TENANT,
        idempotency_key=FOREIGN_PRACTITIONER,
        role="physician",
        qualification="MBBS",
    )
    guard.register_organization(
        owner,
        tenant_id=OTHER_TENANT,
        idempotency_key=FOREIGN_ORG,
        label="tenant-b-hospital",
    )
    guard.register_facility(
        owner,
        tenant_id=OTHER_TENANT,
        idempotency_key=FOREIGN_FACILITY,
        organization_id=FOREIGN_ORG,
        label="tenant-b-ward",
        facility_type="hospital",
    )
    scoped_owner = owner.with_patient_scope(foreign_patient.ref)
    encounter = guard.create_encounter(
        scoped_owner,
        tenant_id=OTHER_TENANT,
        idempotency_key=FOREIGN_ENCOUNTER,
        patient_ref=foreign_patient.ref,
        practitioner_id=FOREIGN_PRACTITIONER,
        facility_id=FOREIGN_FACILITY,
        reason="tenant-b synthetic consultation",
    )
    return scoped_owner, foreign_patient, encounter


# ---------------------------------------------------------------- happy path


def test_guard_allows_real_clinical_and_lab_workflow(
    guard: AuthorizedHealthCore, privileged: Principal, patient
):
    who = scoped(privileged, patient.ref)
    seed(guard, privileged)
    encounter = create_encounter(guard, who, patient.ref)
    assert encounter.status is EncounterStatus.PLANNED
    assert guard.get_encounter(who, tenant_id=TENANT, encounter_id=encounter.encounter_id) == encounter

    order = guard.place_order(
        who,
        tenant_id=TENANT,
        patient_ref=patient.ref,
        test_codes=("GLU",),
        idempotency_key="SYN-KEY-0001",
        actor_id=ACTOR,
    )
    specimen = guard.register_specimen(
        who,
        tenant_id=TENANT,
        order_id=order.order_id,
        barcode="SYN-BAR-0001",
        actor_id=ACTOR,
    )
    for status in (SpecimenStatus.COLLECTED, SpecimenStatus.RECEIVED):
        specimen = guard.transition_specimen(
            who,
            tenant_id=TENANT,
            specimen_id=specimen.specimen_id,
            to_status=status,
            actor_id=ACTOR,
        )
    assert specimen.status is SpecimenStatus.RECEIVED
    result = guard.record_result(
        who,
        tenant_id=TENANT,
        order_id=order.order_id,
        specimen_id=specimen.specimen_id,
        patient_ref=patient.ref,
        test_code="GLU",
        value=92.0,
        unit="mg/dL",
        idempotency_key="SYN-KEY-0002",
        actor_id=ACTOR,
    )
    verification = guard.verify_result(
        who,
        tenant_id=TENANT,
        result_id=result.result_id,
        reviewer_id=ACTOR,
        decision=VerificationDecision.VERIFIED,
        idempotency_key="SYN-KEY-0003",
    )
    assert verification.status.value == "verified"
    assert guard.engine.audit.verify().is_valid is True
    assert all(record.decision == Decision.ALLOW.value for record in guard.engine.audit.records())


def test_wrapped_services_are_private_and_guarded_methods_still_work(
    guard: AuthorizedHealthCore, privileged: Principal, patient
):
    assert isinstance(guard._clinical, ClinicalContext)
    assert isinstance(guard._lab, LabWorkflowService)
    assert not hasattr(guard, "clinical")
    assert not hasattr(guard, "lab")
    assert hasattr(guard, "engine")
    for name, value in vars(guard).items():
        if name.startswith("_"):
            continue
        assert not isinstance(value, ClinicalContext), name
        assert not isinstance(value, LabWorkflowService), name

    who = scoped(privileged, patient.ref)
    seed(guard, privileged)
    encounter = create_encounter(guard, who, patient.ref)
    assert (
        guard.get_encounter(who, tenant_id=TENANT, encounter_id=encounter.encounter_id)
        == encounter
    )
    assert guard.engine.audit.verify().is_valid is True


# -------------------------------------------------------------- denied writes


def test_unauthorized_create_never_reaches_wrapped_service(
    guard: AuthorizedHealthCore, privileged: Principal, patient
):
    seed(guard, privileged)
    viewer = Principal(
        principal_id=PRACTITIONER,
        tenant_id=TENANT,
        roles=frozenset({Role.VIEWER}),
        facility_ids=frozenset({FACILITY}),
    )
    with pytest.raises(AuthorizationDenied) as exc:
        create_encounter(guard, scoped(viewer, patient.ref), patient.ref)
    assert exc.value.decision.policy_id is PolicyId.DENY_MISSING_PERMISSION
    with pytest.raises(UnknownClinicalEntityError):
        guard._clinical.encounters.get_encounter(tenant_id=TENANT, encounter_id="SYN-ENC-0001")


def test_role_hierarchy_bypass_is_denied_on_lab_write(
    guard: AuthorizedHealthCore, privileged: Principal, patient
):
    who = scoped(privileged, patient.ref)
    seed(guard, privileged)
    order = guard.place_order(
        who,
        tenant_id=TENANT,
        patient_ref=patient.ref,
        test_codes=("GLU",),
        idempotency_key="SYN-KEY-0001",
        actor_id=ACTOR,
    )
    clinician_only = Principal(
        principal_id=PRACTITIONER,
        tenant_id=TENANT,
        roles=frozenset({Role.CLINICIAN}),
        facility_ids=frozenset({FACILITY}),
    ).with_patient_scope(patient.ref)
    with pytest.raises(AuthorizationDenied) as exc:
        guard.register_specimen(
            clinician_only,
            tenant_id=TENANT,
            order_id=order.order_id,
            barcode="SYN-BAR-0001",
            actor_id=ACTOR,
        )
    assert exc.value.decision.policy_id is PolicyId.DENY_MISSING_PERMISSION
    assert last_policy(guard.engine) is PolicyId.DENY_MISSING_PERMISSION


def test_direct_grant_enables_write_without_role_escalation(
    guard: AuthorizedHealthCore, privileged: Principal, patient
):
    seed(guard, privileged)
    viewer = Principal(
        principal_id=PRACTITIONER,
        tenant_id=TENANT,
        roles=frozenset({Role.VIEWER}),
        facility_ids=frozenset({FACILITY}),
    ).with_patient_scope(patient.ref)
    with pytest.raises(AuthorizationDenied):
        create_encounter(guard, viewer, patient.ref)
    guard.engine.grant(PRACTITIONER, Permission.ENCOUNTER_CREATE, reason="attending override")
    encounter = create_encounter(guard, viewer, patient.ref)
    assert encounter.patient_ref == patient.ref


def test_revoked_principal_cannot_reuse_an_existing_grant(
    guard: AuthorizedHealthCore, privileged: Principal, patient
):
    who = scoped(privileged, patient.ref)
    seed(guard, privileged)
    encounter = create_encounter(guard, who, patient.ref)
    guard.engine.grant(PRACTITIONER, Permission.ENCOUNTER_READ, reason="temporary read")
    guard.engine.revoke_principal(PRACTITIONER, reason="suspended")
    with pytest.raises(AuthorizationDenied) as exc:
        guard.get_encounter(who, tenant_id=TENANT, encounter_id=encounter.encounter_id)
    assert exc.value.decision.policy_id is PolicyId.DENY_REVOKED_PRINCIPAL


def test_no_authentication_grants_zero_permissions_at_the_facade(
    guard: AuthorizedHealthCore, privileged: Principal, patient
):
    seed(guard, privileged)
    anonymous = Principal(principal_id=PRACTITIONER, tenant_id=TENANT).without_authentication()
    with pytest.raises(AuthorizationDenied) as exc:
        guard.list_orders(anonymous, tenant_id=TENANT)
    assert exc.value.decision.policy_id is PolicyId.DENY_UNAUTHENTICATED


def test_unauthenticated_with_valid_role_and_scope_still_denied(
    guard: AuthorizedHealthCore, privileged: Principal, patient
):
    seed(guard, privileged)
    who = scoped(privileged, patient.ref).without_authentication()
    with pytest.raises(AuthorizationDenied) as exc:
        create_encounter(guard, who, patient.ref)
    assert exc.value.decision.policy_id is PolicyId.DENY_UNAUTHENTICATED


# ------------------------------------------------------------ tenant / scoping


def test_cross_tenant_probe_cannot_discover_existence(
    guard: AuthorizedHealthCore, privileged: Principal, patient
):
    _owner, _foreign_patient, encounter = foreign_tenant_resource(guard)
    who = scoped(privileged, patient.ref)  # tenant A
    random_id = new_synthetic_id("ENC")

    with pytest.raises(AuthorizationDenied) as existing:
        guard.get_encounter(who, tenant_id=OTHER_TENANT, encounter_id=encounter.encounter_id)
    with pytest.raises(AuthorizationDenied) as unknown:
        guard.get_encounter(who, tenant_id=OTHER_TENANT, encounter_id=random_id)

    assert existing.value.decision.policy_id is PolicyId.DENY_TENANT
    assert unknown.value.decision.policy_id is PolicyId.DENY_TENANT
    assert existing.value.decision.reason == unknown.value.decision.reason == PUBLIC_DENIAL_REASON
    # The stored tenant B (not the caller's claim) is what the engine evaluated.
    assert existing.value.decision.tenant_id == OTHER_TENANT
    # The unwrapped service still refuses a direct cross-tenant address.
    with pytest.raises(TenantMismatchError):
        guard._clinical.encounters.get_encounter(
            tenant_id=TENANT, encounter_id=encounter.encounter_id
        )


def test_indexed_read_ignores_caller_tenant_and_denies_cross_tenant(
    guard: AuthorizedHealthCore, privileged: Principal, patient
):
    owner, _foreign_patient, encounter = foreign_tenant_resource(guard)
    intruder = scoped(privileged, patient.ref)  # tenant A, claiming its own tenant
    stored = guard.attributes.get(encounter.encounter_id)
    assert stored is not None
    assert stored.tenant_id == OTHER_TENANT

    baseline = len(guard.engine.audit.records())
    with pytest.raises(AuthorizationDenied) as exc:
        guard.get_encounter(
            intruder, tenant_id=TENANT, encounter_id=encounter.encounter_id
        )

    assert exc.value.decision.policy_id is PolicyId.DENY_TENANT
    assert exc.value.decision.tenant_id == OTHER_TENANT
    assert exc.value.to_dict()["details"] == {}
    records = guard.engine.audit.records()
    assert len(records) == baseline + 1
    denial = records[-1]
    assert denial.decision == Decision.DENY.value
    assert denial.policy_id == PolicyId.DENY_TENANT.value
    assert denial.tenant_id == OTHER_TENANT
    assert denial.resource_id == encounter.encounter_id
    assert guard.engine.audit.verify().is_valid is True

    # A legitimate tenant-B read of the same indexed resource still ALLOWs.
    allowed = guard.get_encounter(
        owner, tenant_id=OTHER_TENANT, encounter_id=encounter.encounter_id
    )
    assert allowed == encounter
    assert last_policy(guard.engine) is PolicyId.ALLOW_EXPLICIT


def test_organization_scope_violation_prevents_facility_creation(
    guard: AuthorizedHealthCore, privileged: Principal, patient
):
    who = scoped(privileged, patient.ref)
    seed(guard, privileged)
    other_org_admin = Principal(
        principal_id=PRACTITIONER,
        tenant_id=TENANT,
        roles=frozenset({Role.CLINICIAN}),
        organization_ids=frozenset({OTHER_ORG}),
    )
    guard.register_organization(
        other_org_admin, tenant_id=TENANT, idempotency_key=OTHER_ORG, label="other-org"
    )
    with pytest.raises(AuthorizationDenied) as exc:
        guard.register_facility(
            who,
            tenant_id=TENANT,
            idempotency_key="SYN-FAC-0002",
            organization_id=OTHER_ORG,
            label="other-ward",
            facility_type="clinic",
        )
    assert exc.value.decision.policy_id is PolicyId.DENY_ORG_SCOPE
    assert guard.attributes.get("SYN-FAC-0002") is None


def test_facility_scope_violation_prevents_encounter_creation(
    guard: AuthorizedHealthCore, privileged: Principal, patient
):
    who = scoped(privileged, patient.ref)
    seed(guard, privileged)
    with pytest.raises(AuthorizationDenied) as exc:
        guard.create_encounter(
            who,
            tenant_id=TENANT,
            idempotency_key="SYN-ENC-0002",
            patient_ref=patient.ref,
            practitioner_id=PRACTITIONER,
            facility_id=OTHER_FACILITY,
            reason="outside scope",
        )
    assert exc.value.decision.policy_id is PolicyId.DENY_FACILITY_SCOPE


def test_patient_scope_violation_prevents_observation_recording(
    guard: AuthorizedHealthCore, privileged: Principal, patient
):
    who = scoped(privileged, patient.ref)
    seed(guard, privileged)
    encounter = create_encounter(guard, who, patient.ref)
    other_patient = guard._clinical.identity.register_patient(
        tenant_id=TENANT, label="other-patient"
    )
    with pytest.raises(AuthorizationDenied) as exc:
        guard.record_observation(
            who,
            tenant_id=TENANT,
            idempotency_key="SYN-OBS-0001",
            patient_ref=other_patient.ref,
            encounter_id=encounter.encounter_id,
            code="8867-4",
            display="heart rate",
            value=80.0,
            unit="/min",
            recorded_at=datetime.now(UTC),
        )
    assert exc.value.decision.policy_id is PolicyId.DENY_PATIENT_SCOPE


def test_patient_scope_violation_prevents_reading_another_patients_encounter(
    guard: AuthorizedHealthCore, privileged: Principal, patient
):
    who = scoped(privileged, patient.ref)
    seed(guard, privileged)
    encounter = create_encounter(guard, who, patient.ref)
    other_patient = guard._clinical.identity.register_patient(
        tenant_id=TENANT, label="other-patient"
    )
    intruder = Principal(
        principal_id=PRACTITIONER,
        tenant_id=TENANT,
        roles=frozenset({Role.VIEWER}),
        facility_ids=frozenset({FACILITY}),
    ).with_patient_scope(other_patient.ref)
    with pytest.raises(AuthorizationDenied) as exc:
        guard.get_encounter(intruder, tenant_id=TENANT, encounter_id=encounter.encounter_id)
    assert exc.value.decision.policy_id is PolicyId.DENY_PATIENT_SCOPE


def test_reads_use_authoritative_attributes_not_caller_claims(
    guard: AuthorizedHealthCore, privileged: Principal, patient
):
    who = scoped(privileged, patient.ref)
    seed(guard, privileged)
    encounter = create_encounter(guard, who, patient.ref)
    stored = guard.attributes.get(encounter.encounter_id)
    assert stored is not None
    assert stored.patient_ref == patient.ref
    assert stored.facility_id == FACILITY
    # The facade deliberately has no read API parameter for scope claims.
    import inspect

    signature = inspect.signature(AuthorizedHealthCore.get_encounter)
    assert set(signature.parameters) == {"self", "principal", "tenant_id", "encounter_id"}


def test_direct_service_write_is_not_indexed_and_cannot_be_read_via_guard(
    guard: AuthorizedHealthCore, privileged: Principal, patient
):
    seed(guard, privileged)
    who = scoped(privileged, patient.ref)
    unguarded = guard._clinical.encounters.create(
        tenant_id=TENANT,
        idempotency_key="SYN-ENC-0009",
        patient_ref=patient.ref,
        practitioner_id=PRACTITIONER,
        facility_id=FACILITY,
        reason="bypassing the guard",
    )
    assert guard.attributes.get(unguarded.encounter_id) is None
    with pytest.raises(AuthorizationDenied) as exc:
        guard.get_encounter(who, tenant_id=TENANT, encounter_id=unguarded.encounter_id)
    assert exc.value.decision.policy_id is PolicyId.DENY_PATIENT_SCOPE


# ------------------------------------------------------------------ audit/error


def test_every_guard_denial_is_audited_and_chain_stays_valid(
    guard: AuthorizedHealthCore, privileged: Principal, patient
):
    seed(guard, privileged)
    baseline = len(guard.engine.audit.records())
    unprivileged = Principal(principal_id=PRACTITIONER, tenant_id=TENANT)
    for _ in range(3):
        with pytest.raises(AuthorizationDenied):
            guard.list_orders(unprivileged, tenant_id=TENANT)
    records = guard.engine.audit.records()
    assert len(records) == baseline + 3
    assert all(record.decision == Decision.DENY.value for record in records[baseline:])
    assert guard.engine.audit.verify().is_valid is True


def test_authorization_denied_public_error_body_is_generic(
    guard: AuthorizedHealthCore, privileged: Principal, patient
):
    unprivileged = Principal(principal_id=PRACTITIONER, tenant_id=TENANT)
    with pytest.raises(AuthorizationDenied) as exc:
        guard.list_orders(unprivileged, tenant_id=TENANT)
    body = exc.value.to_dict()
    assert body["code"] == "AUTHORIZATION_DENIED"
    assert body["message"] == PUBLIC_DENIAL_REASON
    assert body["details"] == {}
    assert "policy_id" not in body
