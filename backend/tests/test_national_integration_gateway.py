from __future__ import annotations

import pytest
from app.contracts.clinical_core import get_contract, require_transition
from app.gateways.national_integration_gateway import (
    NationalIntegrationGateway,
    SyntheticOnlyViolation,
)


def test_synthetic_submit_is_deterministic_and_idempotent() -> None:
    gateway = NationalIntegrationGateway()
    payload = {"national_id_hash": "synthetic-001", "facility_code": "FAC-001"}

    first = gateway.submit(
        operation="identity.verify",
        payload=payload,
        idempotency_key="idem-001",
    )
    second = gateway.submit(
        operation="identity.verify",
        payload=payload,
        idempotency_key="idem-001",
    )

    assert first.data == second.data
    assert first.source == "api"
    assert second.source == "idempotency_receipt"
    assert first.data["synthetic"] is True


def test_idempotency_key_cannot_change_request() -> None:
    gateway = NationalIntegrationGateway()
    gateway.submit(
        operation="facility.lookup",
        payload={"facility_code": "FAC-001"},
        idempotency_key="idem-002",
    )

    with pytest.raises(ValueError, match="IDEMPOTENCY_KEY_REUSE"):
        gateway.submit(
            operation="facility.lookup",
            payload={"facility_code": "FAC-002"},
            idempotency_key="idem-002",
        )


def test_clinical_truth_is_rejected_before_provider() -> None:
    gateway = NationalIntegrationGateway()

    with pytest.raises(SyntheticOnlyViolation):
        gateway.submit(
            operation="eligibility.check",
            payload={"clinical_truth": {"diagnosis": "synthetic"}},
            idempotency_key="idem-003",
        )


def test_live_or_shadow_request_is_hard_blocked(monkeypatch) -> None:
    monkeypatch.setenv("GULA_ADAPTER_MODE_NATIONAL_GATEWAY", "live")
    monkeypatch.setenv("NATIONAL_GATEWAY_URL", "https://synthetic.invalid")
    monkeypatch.setenv("NATIONAL_GATEWAY_API_KEY", "synthetic-only")
    gateway = NationalIntegrationGateway()

    with pytest.raises(SyntheticOnlyViolation):
        gateway._do_call("facility.lookup", payload={"facility_code": "FAC-001"})


def test_national_contracts_reject_invalid_transitions() -> None:
    message = get_contract("national-integration-message")
    reconciliation = get_contract("national-reconciliation")
    review = get_contract("national-manual-review")

    assert message.allows("RECEIVED", "VALIDATED")
    assert reconciliation.allows("CONFLICT", "RESOLVED")
    assert review.allows("IN_REVIEW", "APPROVED")
    with pytest.raises(ValueError, match="INVALID_STATE_TRANSITION"):
        require_transition("national-integration-message", "APPLIED", "ROUTED")
