from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

from security.modules.compliance.asvs import ASVSValidator
from security.modules.compliance.gdpr import GDPRValidator
from security.modules.compliance.hipaa import HIPAAValidator
from security.modules.compliance.iso27001 import ISO27001Validator
from security.modules.compliance.mapper import ComplianceMapper
from security.modules.compliance.models import (
    ComplianceFramework,
    ComplianceReport,
    ControlStatus,
)
from security.modules.compliance.nist import NISTCSFValidator

logger = logging.getLogger(__name__)


class ScheduledCheck(BaseModel):
    check_id: str
    framework: ComplianceFramework
    interval_hours: int = 24
    last_run: datetime | None = None
    enabled: bool = True


class RemediationPlan(BaseModel):
    plan_id: str
    framework: ComplianceFramework
    created_at: datetime = Field(default_factory=datetime.utcnow)
    actions: list[dict[str, Any]] = Field(default_factory=list)
    target_date: datetime | None = None
    status: str = "ACTIVE"


class ComplianceEngine:
    def __init__(self):
        self._validators: dict[ComplianceFramework, Any] = {
            ComplianceFramework.OWASP_ASVS: ASVSValidator(),
            ComplianceFramework.NIST_CSF: NISTCSFValidator(),
            ComplianceFramework.ISO_27001: ISO27001Validator(),
            ComplianceFramework.HIPAA: HIPAAValidator(),
            ComplianceFramework.GDPR: GDPRValidator(),
        }
        self._mapper = ComplianceMapper()
        self._scheduled_checks: dict[str, ScheduledCheck] = {}
        self._reports: list[ComplianceReport] = []
        self._remediation_plans: list[RemediationPlan] = []
        self._evidence_store: dict[str, list[str]] = {}

    def register_framework(self, framework: ComplianceFramework, validator: Any) -> None:
        self._validators[framework] = validator

    def get_validator(self, framework: ComplianceFramework) -> Any:
        validator = self._validators.get(framework)
        if not validator:
            raise ValueError(f"Validator not registered for framework: {framework}")
        return validator

    def update_control(self, framework: ComplianceFramework, control_id: str,
                        status: ControlStatus, evidence: list[str] | None = None) -> bool:
        validator = self.get_validator(framework)
        if hasattr(validator, "update_control"):
            result = validator.update_control(control_id, status, evidence)
            if result and evidence:
                self._store_evidence(f"{framework.value}:{control_id}", evidence)
            return result
        if hasattr(validator, "update_control_status"):
            return validator.update_control_status(control_id, status, evidence)
        if hasattr(validator, "update_control_set"):
            return validator.update_control_set("all", control_id, status, evidence)
        return False

    def generate_report(self, framework: ComplianceFramework) -> ComplianceReport:
        validator = self.get_validator(framework)
        if hasattr(validator, "generate_report") or hasattr(validator, "generate_report"):
            report = validator.generate_report()
        else:
            raise ValueError(f"Validator for {framework} does not support report generation")

        self._reports.append(report)
        self._generate_remediation(report)
        return report

    def generate_all_reports(self) -> dict[ComplianceFramework, ComplianceReport]:
        reports = {}
        for framework in self._validators:
            try:
                reports[framework] = self.generate_report(framework)
            except Exception as e:
                logger.error(f"Failed to generate report for {framework}: {e}")
        return reports

    def _generate_remediation(self, report: ComplianceReport) -> None:
        failing_controls = report.findings
        if not failing_controls:
            return

        plan = RemediationPlan(
            plan_id=f"PLAN-{report.framework.value}-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}",
            framework=report.framework,
            actions=[
                {
                    "control_id": c.control_id,
                    "action": f"Implement compliance for {c.control_id}",
                    "description": c.description[:100],
                    "status": "PENDING",
                }
                for c in failing_controls[:20]
            ],
        )

        self._remediation_plans.append(plan)

    def schedule_automated_check(self, framework: ComplianceFramework,
                                   interval_hours: int = 24) -> ScheduledCheck:
        check = ScheduledCheck(
            check_id=f"CHECK-{framework.value}-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}",
            framework=framework,
            interval_hours=interval_hours,
        )
        self._scheduled_checks[check.check_id] = check
        return check

    def run_scheduled_checks(self) -> list[ComplianceReport]:
        reports: list[ComplianceReport] = []
        now = datetime.now(UTC)

        for check_id, check in list(self._scheduled_checks.items()):
            if not check.enabled:
                continue
            if check.last_run and (now - check.last_run).total_seconds() < check.interval_hours * 3600:
                continue

            try:
                report = self.generate_report(check.framework)
                reports.append(report)
                check.last_run = now
            except Exception as e:
                logger.error(f"Scheduled check {check_id} failed: {e}")

        return reports

    def collect_evidence(self, control_key: str) -> list[str]:
        return self._evidence_store.get(control_key, [])

    def _store_evidence(self, key: str, evidence: list[str]) -> None:
        if key not in self._evidence_store:
            self._evidence_store[key] = []
        self._evidence_store[key].extend(evidence)

    def generate_export(self, framework: ComplianceFramework, format: str = "json") -> str:
        report = self.generate_report(framework)

        if format == "json":
            return json.dumps(report.model_dump(mode="json"), indent=2, default=str)

        if format == "html":
            controls_html = ""
            for ctrl in report.findings[:30]:
                controls_html += (
                    f"<tr><td>{ctrl.control_id}</td><td>{ctrl.framework.value}</td>"
                    f"<td>{ctrl.category}</td><td>{ctrl.implementation_status.value}</td>"
                    f"<td>{ctrl.description[:80]}...</td></tr>"
                )

            return f"""<!DOCTYPE html><html><head><title>Compliance Report</title>
<style>body{{font-family:sans-serif;margin:20px}}table{{border-collapse:collapse;width:100%}}
th,td{{border:1px solid #ddd;padding:8px;text-align:left}}th{{background-color:#f2f2f2}}
tr:nth-child(even){{background-color:#f9f9f9}}.status{{font-weight:bold}}</style>
</head><body>
<h1>Compliance Report</h1>
<p>Framework: {report.framework.value} | Status: {report.overall_status.value}</p>
<p>Passed: {report.passed}/{report.control_count} | Failed: {report.failed}</p>
<h2>Controls</h2>
<table><tr><th>ID</th><th>Framework</th><th>Category</th><th>Status</th><th>Description</th></tr>
{controls_html}</table></body></html>"""

        if format == "xlsx":
            return json.dumps({"message": "XLSX export requires openpyxl library"}, indent=2)

        if format == "pdf":
            return json.dumps({"message": "PDF export requires reportlab library"}, indent=2)

        return json.dumps({"error": f"Unsupported format: {format}"}, indent=2)

    def get_dashboard_data(self) -> dict[str, Any]:
        all_reports = self.generate_all_reports()
        reports_list = list(all_reports.values())
        composite = self._mapper.calculate_composite_score(reports_list)

        return {
            "composite_score": composite,
            "framework_reports": {
                fw.value: {
                    "overall_status": r.overall_status.value,
                    "passed": r.passed,
                    "failed": r.failed,
                    "total": r.control_count,
                    "compliance_percentage": round(r.passed / max(r.control_count, 1) * 100, 1),
                }
                for fw, r in all_reports.items()
            },
            "remediation_plans": len(self._remediation_plans),
            "active_checks": sum(1 for c in self._scheduled_checks.values() if c.enabled),
            "evidence_count": sum(len(v) for v in self._evidence_store.values()),
        }

    def get_remediation_status(self) -> dict[str, Any]:
        status = {"active_plans": 0, "completed_plans": 0, "pending_actions": 0, "completed_actions": 0}
        for plan in self._remediation_plans:
            if plan.status == "ACTIVE":
                status["active_plans"] += 1
                for action in plan.actions:
                    if action.get("status") == "PENDING":
                        status["pending_actions"] += 1
                    else:
                        status["completed_actions"] += 1
            elif plan.status == "COMPLETED":
                status["completed_plans"] += 1

        return status

    def get_dashboard_integration(self) -> dict[str, Any]:
        return {
            "module": "compliance",
            "available_validators": [fw.value for fw in self._validators],
            "cross_framework_mappings": len(self._mapper._mappings) if hasattr(self._mapper, "_mappings") else 0,
            "evidence_store_size": sum(len(v) for v in self._evidence_store.values()),
            "last_report_generated": self._reports[-1].generated_at.isoformat() if self._reports else None,
        }
