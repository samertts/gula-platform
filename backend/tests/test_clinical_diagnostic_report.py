from __future__ import annotations

from unittest.mock import Mock

import pytest
from pydantic import ValidationError

from app.clinical_gateway.context import ClinicalGatewayBlocked
from app.clinical_gateway.diagnostic_report_routes import (
    DiagnosticReportAmendRequest,
    DiagnosticReportFinalizeRequest,
)
from app.clinical_gateway.diagnostic_report_service import DiagnosticReportService
from app.models.clinical_diagnostic_report import ClinicalDiagnosticReport
from app.models.lab_result import LabResult


def _report(**overrides: object) -> ClinicalDiagnosticReport:
    values: dict[str, object] = {
        "id": "DIAGREPORT00000000000000001",
        "source_type": "LAB_ORDER",
        "source_id": "100",
        "patient_id": "200",
        "report_name": "CBC",
        "status": "PRELIMINARY",
        "result_refs": ["300"],
        "organization_id": "org-1",
        "facility_id": "facility-1",
        "workspace_id": "workspace-1",
        "tenant_id": 10,
        "legacy_lab_id": 20,
        "version": 1,
        "created_by": "account-1",
    }
    values.update(overrides)
    return ClinicalDiagnosticReport(**values)


def test_diagnostic_report_finalize_contract_forbids_client_authority_fields() -> None:
    with pytest.raises(ValidationError):
        DiagnosticReportFinalizeRequest(
            expected_version=1,
            patient_id="client-controlled",  # type: ignore[call-arg]
            organization_id="client-controlled",  # type: ignore[call-arg]
        )


def test_diagnostic_report_amend_contract_forbids_client_authority_fields() -> None:
    with pytest.raises(ValidationError):
        DiagnosticReportAmendRequest(
            expected_version=1,
            reason="correction",
            practitioner_id="client-controlled",  # type: ignore[call-arg]
        )


def test_diagnostic_report_safe_dict_excludes_sensitive_scope_and_correlation_fields() -> None:
    report = _report(
        legacy_lab_id=999,
        tenant_id=777,
        correlation_id="private-correlation-id",
        source_metadata={"raw_token": "must-not-leak"},
    )

    safe = DiagnosticReportService.to_safe_dict(report)

    assert safe["id"] == "DIAGREPORT00000000000000001"
    assert safe["source_type"] == "LAB_ORDER"
    assert safe["workspace_id"] == "workspace-1"
    assert "legacy_lab_id" not in safe
    assert "tenant_id" not in safe
    assert "correlation_id" not in safe
    assert "source_metadata" not in safe


def test_diagnostic_report_finalize_denied_when_lab_results_are_not_accepted() -> None:
    report = _report(status="PRELIMINARY", version=1)
    service = DiagnosticReportService(Mock())
    access = Mock()
    service._report = Mock(return_value=report)  # type: ignore[method-assign]
    service._access_for_report = Mock(return_value=access)  # type: ignore[method-assign]
    service.db.query.return_value.filter.return_value.all.return_value = [
        LabResult(id=300, order_id=100, review_status="UNREVIEWED")
    ]

    with pytest.raises(ClinicalGatewayBlocked, match="diagnostic_report_results_not_reviewed"):
        service.finalize(actor=Mock(), report_id=report.id, expected_version=1)

    assert report.status == "PRELIMINARY"
    assert report.version == 1


def test_diagnostic_report_amend_denied_from_preliminary_status() -> None:
    report = _report(status="PRELIMINARY", version=1)
    service = DiagnosticReportService(Mock())
    access = Mock()
    service._report = Mock(return_value=report)  # type: ignore[method-assign]
    service._access_for_report = Mock(return_value=access)  # type: ignore[method-assign]

    with pytest.raises(ClinicalGatewayBlocked, match="diagnostic_report_amendment_denied"):
        service.amend(
            actor=Mock(),
            report_id=report.id,
            expected_version=1,
            conclusion="corrected conclusion",
            reason="correction",
        )

    assert report.status == "PRELIMINARY"
    assert report.version == 1


def test_diagnostic_report_scope_mismatch_is_denied() -> None:
    report = _report(organization_id="org-1")
    service = DiagnosticReportService(Mock())
    access = Mock(
        organization_id="org-2",
        facility_id="facility-1",
        workspace_id="workspace-1",
        tenant_id=10,
    )
    service._access_for_legacy_patient = Mock(return_value=access)  # type: ignore[method-assign]

    with pytest.raises(ClinicalGatewayBlocked, match="diagnostic_report_scope_mismatch"):
        service._access_for_report(
            Mock(),
            report,
            purpose="diagnostic_report.read",
            permissions=frozenset({"read"}),
        )
