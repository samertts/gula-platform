from uuid import uuid4

import pytest
from app.clinical_gateway.contracts import (
    CONTRACT_VERSION,
    ClinicalPageRequest,
    ClinicalReadEnvelope,
    ClinicalWorkspaceContext,
    OrderRead,
    PatientRead,
    ResultRead,
)
from pydantic import ValidationError


def _context() -> ClinicalWorkspaceContext:
    return ClinicalWorkspaceContext(
        organization_id="org-1",
        facility_id="facility-1",
        workspace_id="workspace-1",
    )


def test_page_request_defaults_and_hard_limit() -> None:
    request = ClinicalPageRequest()

    assert request.limit == 50
    with pytest.raises(ValidationError):
        ClinicalPageRequest(limit=101)


def test_page_request_rejects_identifier_and_phone_enumeration() -> None:
    for value in ("123456", "+964 700 000 0000", "07-000-000-000"):
        with pytest.raises(ValidationError):
            ClinicalPageRequest(search=value)


def test_page_request_normalizes_safe_name_search() -> None:
    request = ClinicalPageRequest(search="  Ali   Hassan ")

    assert request.search == "Ali Hassan"


def test_result_read_excludes_sensitive_legacy_fields() -> None:
    result = ResultRead(
        id="result-1",
        order_id="order-1",
        test_name="Glucose",
        value=5.2,
        unit="mmol/L",
        interpretation="normal",
    )

    assert "token" not in result.model_dump()
    assert "result_link" not in result.model_dump()
    assert "patient_phone" not in result.model_dump()
    with pytest.raises(ValidationError):
        ResultRead(id="result-1", order_id="order-1", test_name="Glucose", result_token="secret")


def test_response_shapes_exclude_sensitive_legacy_fields() -> None:
    patient = PatientRead(id="patient-1", display_name="Ali Hassan")
    order = OrderRead(id="order-1", status="pending")

    assert "national_id" not in patient.model_dump()
    assert "phone" not in patient.model_dump()
    assert "lab_id" not in patient.model_dump()
    assert "results" not in order.model_dump()
    assert "patient_phone" not in order.model_dump()


def test_envelope_is_versioned_and_rejects_extra_fields() -> None:
    envelope = ClinicalReadEnvelope[PatientRead](
        request_id=uuid4(),
        correlation_id=uuid4(),
        workspace_context=_context(),
        items=[PatientRead(id="patient-1", display_name="Ali Hassan")],
        limit=50,
    )

    assert envelope.contract_version == CONTRACT_VERSION
    with pytest.raises(ValidationError):
        ClinicalReadEnvelope[PatientRead](
            request_id=uuid4(),
            correlation_id=uuid4(),
            workspace_context=_context(),
            items=[],
            limit=50,
            unauthorized_scope="facility-2",
        )
