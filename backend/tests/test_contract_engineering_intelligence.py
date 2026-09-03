from app.contracts.clinical_core import APPOINTMENT, ContractEvidence, ReadinessState
from app.contracts.engineering_intelligence import evaluate_contract


def test_report_explains_missing_evidence_instead_of_only_returning_blocked() -> None:
    report = evaluate_contract(
        APPOINTMENT,
        ContractEvidence(domain_model=True, state_machine=True, frontend_states=True),
    )

    assert report.readiness is ReadinessState.BUILDING
    assert report.score_percent == 13
    assert "backend_contract" in report.missing
    assert "object_authorization" in report.missing
    assert report.findings[0].suggested_fix
    assert not report.can_be_marked_complete


def test_report_reaches_review_only_after_backend_and_safety_evidence() -> None:
    report = evaluate_contract(
        APPOINTMENT,
        ContractEvidence(
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
        ),
    )

    assert report.readiness is ReadinessState.READY_FOR_REVIEW
    assert report.score_percent == 87
    assert "remote_ci" in report.missing
    assert "staging" in report.missing
    assert "rollback" in report.missing
    assert not report.can_be_marked_complete
