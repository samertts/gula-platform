from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.clinical_gateway.access_context import ClinicalAccessContext
from app.clinical_gateway.context import ClinicalGatewayBlocked, ClinicalGatewayContextResolver
from app.identity.api.workspaces import NiamActor
from app.models.clinical_diagnostic_report import ClinicalDiagnosticReport
from app.models.lab_order import LabOrder
from app.models.lab_result import LabResult
from app.models.patient import Patient
from app.radiology.models import RadiologyReport


class DiagnosticReportConflict(RuntimeError):
    """The report cannot transition without a safe source/version proof."""


class DiagnosticReportService:
    def __init__(self, db: Session) -> None:
        self.db = db

    @staticmethod
    def _now() -> datetime:
        return datetime.now(UTC)

    @staticmethod
    def _as_utc(value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)

    def _access_for_legacy_patient(
        self,
        actor: NiamActor,
        patient_id: int,
        *,
        purpose: str,
        permissions: frozenset[str],
    ) -> ClinicalAccessContext:
        if patient_id <= 0:
            raise ClinicalGatewayBlocked("invalid_patient_scope")
        gateway = ClinicalGatewayContextResolver(self.db).resolve(actor)
        patient = (
            self.db.query(Patient)
            .filter(
                Patient.id == patient_id,
                Patient.lab_id == gateway.legacy_user.lab_id,
                Patient.is_active.is_(True),
            )
            .one_or_none()
        )
        if patient is None:
            raise ClinicalGatewayBlocked("legacy_patient_scope_denied")
        return ClinicalAccessContext.from_gateway_for_patient(
            self.db,
            gateway,
            patient_id=patient_id,
            purpose=purpose,
            permissions=permissions,
        )

    def _report(self, report_id: str) -> ClinicalDiagnosticReport:
        report = (
            self.db.query(ClinicalDiagnosticReport)
            .filter(
                ClinicalDiagnosticReport.id == report_id,
                ClinicalDiagnosticReport.is_deleted.is_(False),
            )
            .one_or_none()
        )
        if report is None:
            raise DiagnosticReportConflict("diagnostic_report_not_found")
        return report

    def _access_for_report(
        self,
        actor: NiamActor,
        report: ClinicalDiagnosticReport,
        *,
        purpose: str,
        permissions: frozenset[str],
    ) -> ClinicalAccessContext:
        try:
            patient_id = int(report.patient_id)
        except (TypeError, ValueError) as exc:
            raise ClinicalGatewayBlocked("diagnostic_report_patient_mapping_missing") from exc
        access = self._access_for_legacy_patient(
            actor,
            patient_id,
            purpose=purpose,
            permissions=permissions,
        )
        if (
            report.organization_id != access.organization_id
            or report.facility_id != access.facility_id
            or report.workspace_id != access.workspace_id
            or report.tenant_id != access.tenant_id
        ):
            raise ClinicalGatewayBlocked("diagnostic_report_scope_mismatch")
        return access

    def _existing_source(self, source_type: str, source_id: str) -> ClinicalDiagnosticReport | None:
        return (
            self.db.query(ClinicalDiagnosticReport)
            .filter(
                ClinicalDiagnosticReport.source_type == source_type,
                ClinicalDiagnosticReport.source_id == source_id,
                ClinicalDiagnosticReport.is_deleted.is_(False),
            )
            .one_or_none()
        )

    @staticmethod
    def to_safe_dict(report: ClinicalDiagnosticReport) -> dict[str, Any]:
        return {
            "id": report.id,
            "source_type": report.source_type,
            "source_id": report.source_id,
            "patient_id": report.patient_id,
            "encounter_id": report.encounter_id,
            "report_code": report.report_code,
            "report_name": report.report_name,
            "status": report.status,
            "conclusion": report.conclusion,
            "result_refs": list(report.result_refs or []),
            "version": report.version,
            "issued_at": report.issued_at.isoformat() if report.issued_at else None,
            "released_at": report.released_at.isoformat() if report.released_at else None,
            "amended_at": report.amended_at.isoformat() if report.amended_at else None,
            "amendment_reason": report.amendment_reason,
            "organization_id": report.organization_id,
            "facility_id": report.facility_id,
            "department_id": report.department_id,
            "workspace_id": report.workspace_id,
        }

    def _new_report(
        self,
        *,
        access: ClinicalAccessContext,
        source_type: str,
        source_id: str,
        patient_id: str,
        report_name: str,
        report_code: str | None,
        conclusion: str | None,
        result_refs: list[str],
        source_metadata: dict[str, Any] | None = None,
        encounter_id: str | None = None,
    ) -> ClinicalDiagnosticReport:
        report = ClinicalDiagnosticReport(
            source_type=source_type,
            source_id=source_id,
            patient_id=patient_id,
            encounter_id=encounter_id,
            report_code=report_code,
            report_name=report_name,
            status="PRELIMINARY",
            conclusion=conclusion,
            result_refs=result_refs,
            source_metadata=source_metadata or {},
            organization_id=access.organization_id,
            facility_id=access.facility_id,
            department_id=access.department_id,
            workspace_id=access.workspace_id,
            tenant_id=access.tenant_id,
            legacy_lab_id=access.legacy_lab_id,
            version=1,
            correlation_id=str(access.correlation_id),
            created_by=str(access.account_id),
            updated_by=str(access.account_id),
        )
        self.db.add(report)
        self.db.flush()
        return report

    def create_from_lab_order(self, *, actor: NiamActor, order_id: int) -> ClinicalDiagnosticReport:
        order = self.db.get(LabOrder, order_id)
        if order is None:
            raise DiagnosticReportConflict("lab_order_not_found")
        access = self._access_for_legacy_patient(
            actor,
            int(order.patient_id),
            purpose="diagnostic_report.create",
            permissions=frozenset({"create"}),
        )
        access.require_operation("create")
        if (
            order.lab_id != access.legacy_lab_id
            or str(order.tenant_id) != str(access.tenant_id)
            or str(order.organization_id) != str(access.operational_organization_id)
            or str(order.facility_id) != str(access.operational_facility_id)
            or str(order.workspace_id) != str(access.workspace_id)
        ):
            raise ClinicalGatewayBlocked("lab_order_scope_denied")
        existing = self._existing_source("LAB_ORDER", str(order.id))
        if existing is not None:
            return existing
        results = self.db.query(LabResult).filter(LabResult.order_id == order.id).order_by(LabResult.id.asc()).all()
        return self._new_report(
            access=access,
            source_type="LAB_ORDER",
            source_id=str(order.id),
            patient_id=str(order.patient_id),
            encounter_id=order.encounter_id,
            report_name=order.service or "Laboratory Diagnostic Report",
            report_code=order.service,
            conclusion=None,
            result_refs=[str(result.id) for result in results],
            source_metadata={"clinical_status": order.clinical_status, "legacy_status": order.status},
        )

    def create_from_radiology_report(self, *, actor: NiamActor, report_id: str) -> ClinicalDiagnosticReport:
        source = (
            self.db.query(RadiologyReport)
            .filter(RadiologyReport.id == report_id, RadiologyReport.is_deleted.is_(False))
            .one_or_none()
        )
        if source is None:
            raise DiagnosticReportConflict("radiology_report_not_found")
        try:
            legacy_patient_id = int(source.patient_id)
        except (TypeError, ValueError) as exc:
            raise ClinicalGatewayBlocked("radiology_patient_mapping_missing") from exc
        access = self._access_for_legacy_patient(
            actor,
            legacy_patient_id,
            purpose="diagnostic_report.create",
            permissions=frozenset({"create"}),
        )
        access.require_operation("create")
        existing = self._existing_source("RADIOLOGY_REPORT", str(source.id))
        if existing is not None:
            return existing
        return self._new_report(
            access=access,
            source_type="RADIOLOGY_REPORT",
            source_id=str(source.id),
            patient_id=str(source.patient_id),
            report_name="Radiology Diagnostic Report",
            report_code=source.accession_number,
            conclusion=source.impression or source.conclusion,
            result_refs=[],
            encounter_id=None,
            source_metadata={"exam_id": source.exam_id, "source_status": str(source.status)},
        )

    def get(self, *, actor: NiamActor, report_id: str) -> ClinicalDiagnosticReport:
        report = self._report(report_id)
        self._access_for_report(actor, report, purpose="diagnostic_report.read", permissions=frozenset({"read"}))
        return report

    def finalize(self, *, actor: NiamActor, report_id: str, expected_version: int) -> ClinicalDiagnosticReport:
        report = self._report(report_id)
        access = self._access_for_report(actor, report, purpose="diagnostic_report.finalize", permissions=frozenset({"validate"}))
        access.require_operation("validate")
        if report.version != expected_version:
            raise DiagnosticReportConflict("diagnostic_report_version_conflict")
        if report.status not in {"PRELIMINARY", "AMENDED"}:
            raise ClinicalGatewayBlocked("diagnostic_report_status_not_publishable")
        if report.source_type == "LAB_ORDER":
            results = self.db.query(LabResult).filter(LabResult.order_id == int(report.source_id)).all()
            if not results or any(result.review_status != "ACCEPTED" for result in results):
                raise ClinicalGatewayBlocked("diagnostic_report_results_not_reviewed")
        elif report.source_type == "RADIOLOGY_REPORT":
            source = self.db.get(RadiologyReport, report.source_id)
            if source is None or str(source.status).upper() not in {"FINAL", "AMENDED"}:
                raise ClinicalGatewayBlocked("radiology_source_not_final")
        now = self._now()
        report.status = "FINAL"
        report.version += 1
        report.issued_at = now
        report.released_at = now
        report.released_by = str(access.account_id)
        report.updated_by = str(access.account_id)
        self.db.flush()
        return report

    def amend(
        self,
        *,
        actor: NiamActor,
        report_id: str,
        expected_version: int,
        conclusion: str | None,
        reason: str,
    ) -> ClinicalDiagnosticReport:
        report = self._report(report_id)
        access = self._access_for_report(actor, report, purpose="diagnostic_report.amend", permissions=frozenset({"update"}))
        access.require_operation("update")
        if report.version != expected_version:
            raise DiagnosticReportConflict("diagnostic_report_version_conflict")
        if report.status not in {"FINAL", "AMENDED"} or not reason.strip():
            raise ClinicalGatewayBlocked("diagnostic_report_amendment_denied")
        report.status = "AMENDED"
        report.version += 1
        report.conclusion = conclusion
        report.amended_at = self._now()
        report.amendment_reason = reason.strip()
        report.updated_by = str(access.account_id)
        self.db.flush()
        return report
