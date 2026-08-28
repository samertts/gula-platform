from app.contracts.clinical_core import (
    APPOINTMENT,
    CLINICAL_NOTE,
    CORE_CONTRACTS,
    ContractEvidence,
    ReadinessState,
    get_contract,
    require_transition,
)


def test_core_contract_registry_contains_the_safe_golden_path_domains() -> None:
    domains = [contract.domain for contract in CORE_CONTRACTS]

    assert domains == [
        "appointment",
        "session",
        "device",
        "patient-access",
        "consent-sharing",
        "access-history",
        "delegation",
        "task",
        "encounter",
        "clinical-note",
        "lab-order",
        "specimen",
        "result",
        "critical-result",
        "notification",
        "prescription",
        "dispense",
        "imaging-order",
        "imaging-study",
        "imaging-report",
        "clinical-record",
        "hospital-admission",
        "hospital-task",
        "hospital-emar",
        "hospital-transfer",
        "hospital-discharge",
        "emergency-incident",
        "emergency-dispatch",
        "lis-analyzer",
        "lis-qc",
        "financial-coverage",
        "financial-eligibility",
        "financial-preauthorization",
        "financial-claim",
        "financial-payment",
        "financial-refund",
        "financial-settlement",
        "pharmacy-controlled-policy",
        "pharmacy-recall",
    ]
    assert get_contract("appointment") is APPOINTMENT
    assert get_contract("financial-payment").allows("PENDING", "CAPTURED")
    assert not get_contract("financial-payment").allows("CAPTURED", "PAID")
    assert get_contract("lis-analyzer").allows("ACTIVE", "QUARANTINED")
    assert not get_contract("lis-analyzer").allows("QUARANTINED", "ACTIVE")
    assert get_contract("pharmacy-controlled-policy").allows("PENDING_POLICY_REVIEW", "APPROVED_BY_POLICY")


def test_state_machine_rejects_invalid_transitions() -> None:
    assert APPOINTMENT.allows("REQUESTED", "CONFIRMED")
    assert APPOINTMENT.allows("CONFIRMED", "CHECKED_IN")
    assert not APPOINTMENT.allows("CONFIRMED", "COMPLETED")

    require_transition("appointment", "REQUESTED", "CONFIRMED")

    try:
        require_transition("appointment", "CONFIRMED", "COMPLETED")
    except ValueError as exc:
        assert str(exc) == "INVALID_STATE_TRANSITION:CONTRACT-001:CONFIRMED->COMPLETED"
    else:
        raise AssertionError("invalid transition must fail closed")


def test_readiness_requires_evidence_and_never_infers_production_from_frontend_types() -> None:
    partial = ContractEvidence(domain_model=True, state_machine=True, frontend_states=True)
    assert partial.readiness(APPOINTMENT) is ReadinessState.BUILDING
    assert partial.missing()

    review = ContractEvidence(
        domain_model=True,
        state_machine=True,
        backend_contract=True,
        authorization=True,
        object_authorization=True,
        tenant_isolation=True,
        audit=True,
        idempotency=True,
        concurrency=True,
        rate_limits=True,
        error_contract=True,
        frontend_states=True,
        rtl_accessibility=True,
        offline_policy=True,
        unit_tests=True,
        integration_tests=True,
        contract_tests=True,
        security_tests=True,
        e2e_tests=True,
        performance_tests=True,
    )
    assert review.readiness(APPOINTMENT) is ReadinessState.READY_FOR_REVIEW
    assert review.readiness(CLINICAL_NOTE) is ReadinessState.READY_FOR_REVIEW
    assert review.readiness(get_contract("financial-payment")) is ReadinessState.EXTERNAL_DEPENDENCY
