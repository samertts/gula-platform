from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app._compat import UTC
from app.identity.base import _ulid
from app.identity.compliance.models import ComplianceCheck, ComplianceFramework, ComplianceReport
from app.identity.services.canonical_audit import AuditEventInput, CanonicalAuditService


class ComplianceService:

    def __init__(self, session: Session) -> None:
        self.session = session
        self.audit = CanonicalAuditService(session)

    # --- Frameworks ---

    def register_framework(
        self,
        name: str,
        framework_type: str,
        version: str | None = None,
        requirements: list[dict[str, Any]] | None = None,
    ) -> ComplianceFramework:
        framework = ComplianceFramework(
            uuid=_ulid(),
            framework_id=_ulid(),
            name=name,
            framework_type=framework_type,
            version=version,
            requirements=requirements,
            status="active",
            is_active=True,
        )
        self.session.add(framework)
        self.session.flush()
        self.audit.record(
            AuditEventInput(
                event_type="COMPLIANCE_FRAMEWORK_REGISTERED",
                category="COMPLIANCE",
                action="compliance.framework.register",
                actor_type="service",
                target_type="compliance_framework",
                target_id=framework.id,
                decision="ALLOW",
                reason_code="FRAMEWORK_REGISTERED",
                data_classification="INTERNAL",
            ),
        )
        return framework

    def get_framework(self, framework_id: str) -> ComplianceFramework | None:
        stmt = select(ComplianceFramework).where(
            ComplianceFramework.framework_id == framework_id,
            ComplianceFramework.is_active.is_(True),
        )
        result = self.session.execute(stmt)
        return result.scalar_one_or_none()

    def list_frameworks(self) -> list[ComplianceFramework]:
        stmt = (
            select(ComplianceFramework)
            .where(ComplianceFramework.is_active.is_(True))
            .order_by(ComplianceFramework.name)
        )
        result = self.session.execute(stmt)
        return list(result.scalars().all())

    # --- Checks ---

    def run_check(
        self,
        framework_id: str,
        requirement_id: str,
        target_type: str,
        target_id: str,
        organization_id: str,
        checked_by: str,
        check_type: str = "automated",
    ) -> ComplianceCheck:
        stmt = select(ComplianceFramework).where(
            ComplianceFramework.id == framework_id,
            ComplianceFramework.is_active.is_(True),
        )
        result = self.session.execute(stmt)
        framework = result.scalar_one_or_none()
        if not framework:
            raise ValueError(f"Framework with id {framework_id} not found")

        check = ComplianceCheck(
            uuid=_ulid(),
            check_id=_ulid(),
            framework_id=framework_id,
            organization_id=organization_id,
            requirement_id=requirement_id,
            target_type=target_type,
            target_id=target_id,
            check_type=check_type,
            status="passed",
            checked_by=checked_by,
            checked_at=datetime.now(UTC),
            is_active=True,
        )
        self.session.add(check)
        self.session.flush()
        self.audit.record(
            AuditEventInput(
                event_type="COMPLIANCE_CHECK_EXECUTED",
                category="COMPLIANCE",
                action="compliance.check.run",
                actor_id=checked_by,
                organization_id=organization_id,
                target_type=target_type,
                target_id=target_id,
                decision="ALLOW",
                reason_code="CHECK_RECORDED",
                data_classification="INTERNAL",
                metadata={"check_type": check_type, "requirement_id": requirement_id},
            ),
        )
        return check

    def get_checks(self, target_type: str, target_id: str, organization_id: str | None = None) -> list[ComplianceCheck]:
        stmt = (
            select(ComplianceCheck)
            .where(
                ComplianceCheck.target_type == target_type,
                ComplianceCheck.target_id == target_id,
                ComplianceCheck.is_active.is_(True),
                ComplianceCheck.organization_id == organization_id if organization_id is not None else ComplianceCheck.organization_id.is_(None),
            )
            .order_by(ComplianceCheck.checked_at.desc())
        )
        result = self.session.execute(stmt)
        return list(result.scalars().all())

    # --- Reports ---

    def generate_report(
        self,
        org_id: str | None,
        framework_id: str,
        generated_by: str,
        report_type: str = "self_assessment",
    ) -> ComplianceReport:
        checks_stmt = select(ComplianceCheck).where(
            ComplianceCheck.framework_id == framework_id,
            ComplianceCheck.organization_id == org_id if org_id is not None else ComplianceCheck.organization_id.is_(None),
            ComplianceCheck.is_active.is_(True),
        )
        checks_result = self.session.execute(checks_stmt)
        checks = list(checks_result.scalars().all())

        passed = sum(1 for c in checks if c.status == "passed")
        failed = sum(1 for c in checks if c.status == "failed")
        warned = sum(1 for c in checks if c.status == "warning")
        na = sum(1 for c in checks if c.status == "not_applicable")
        total = len(checks)

        overall_score = int((passed / total) * 100) if total > 0 else 0

        findings_list = [
            {"check_id": c.check_id, "requirement_id": c.requirement_id, "status": c.status, "finding": c.finding}
            for c in checks
        ]

        report = ComplianceReport(
            uuid=_ulid(),
            report_id=_ulid(),
            organization_id=org_id,
            framework_id=framework_id,
            report_type=report_type,
            overall_score=overall_score,
            passed_count=passed,
            failed_count=failed,
            warning_count=warned,
            not_applicable_count=na,
            findings=findings_list,
            generated_by=generated_by,
            generated_at=datetime.now(UTC),
            status="final",
            is_active=True,
        )
        self.session.add(report)
        self.session.flush()
        self.audit.record(
            AuditEventInput(
                event_type="COMPLIANCE_REPORT_GENERATED",
                category="COMPLIANCE",
                action="compliance.report.generate",
                actor_id=generated_by,
                organization_id=org_id,
                target_type="compliance_report",
                target_id=report.id,
                decision="ALLOW",
                reason_code="REPORT_GENERATED",
                data_classification="CONFIDENTIAL",
                metadata={"framework_id": framework_id, "report_type": report_type},
            ),
        )
        return report

    def get_report(self, report_id: str) -> ComplianceReport | None:
        stmt = select(ComplianceReport).where(
            ComplianceReport.report_id == report_id,
            ComplianceReport.is_active.is_(True),
        )
        result = self.session.execute(stmt)
        return result.scalar_one_or_none()

    def get_org_compliance_status(self, org_id: str) -> list[dict[str, Any]]:
        stmt = (
            select(
                ComplianceFramework.framework_id,
                ComplianceFramework.name,
                ComplianceFramework.framework_type,
                func.count(ComplianceCheck.id).label("total_checks"),
                func.sum(
                    func.case((ComplianceCheck.status == "passed", 1), else_=0),
                ).label("passed_checks"),
            )
            .join(ComplianceCheck, ComplianceCheck.framework_id == ComplianceFramework.id)
            .where(
                ComplianceFramework.is_active.is_(True),
                ComplianceCheck.organization_id == org_id,
                ComplianceCheck.is_active.is_(True),
            )
            .group_by(ComplianceFramework.id)
        )
        result = self.session.execute(stmt)
        rows = result.all()

        statuses: list[dict[str, Any]] = []
        for row in rows:
            total = row.total_checks or 0
            passed = row.passed_checks or 0
            score = int((passed / total) * 100) if total > 0 else 0
            statuses.append({
                "framework_id": row.framework_id,
                "framework_name": row.name,
                "framework_type": row.framework_type,
                "total_checks": total,
                "passed_checks": passed,
                "compliance_score": score,
            })
        return statuses
