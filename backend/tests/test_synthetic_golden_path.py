from __future__ import annotations

from itertools import pairwise

from app.contracts.clinical_core import require_transition
from app.gateways.national_integration_gateway import NationalIntegrationGateway


def _advance(domain: str, states: tuple[str, ...]) -> None:
    for current, requested in pairwise(states):
        require_transition(domain, current, requested)


def test_synthetic_golden_path_is_cross_domain_and_fail_closed() -> None:
    _advance("appointment", ("REQUESTED", "CONFIRMED", "CHECKED_IN", "IN_PROGRESS", "COMPLETED"))
    _advance("encounter", ("PLANNED", "CHECKED_IN", "IN_PROGRESS", "COMPLETED", "SIGNED"))
    _advance("lab-order", ("DRAFT", "PLACED", "ACCEPTED", "IN_PROGRESS", "COMPLETED"))
    _advance("specimen", ("ORDERED", "COLLECTED", "RECEIVED", "PROCESSING", "ANALYZING", "VALIDATED"))
    _advance("result", ("DRAFT", "TECHNICALLY_VALIDATED", "CLINICALLY_VALIDATED", "RELEASED"))
    _advance("financial-claim", ("DRAFT", "SUBMITTED", "RECEIVED", "UNDER_REVIEW", "APPROVED", "PAID"))

    result = NationalIntegrationGateway().submit(
        operation="eligibility.check",
        payload={"citizen_ref": "synthetic-citizen-001", "coverage_ref": "synthetic-policy-001"},
        idempotency_key="golden-path-001",
    )

    assert result.data["synthetic"] is True
    assert result.requires_verification is False
