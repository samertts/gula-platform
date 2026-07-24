from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app._compat import UTC
from app.identity.base import _ulid
from app.identity.compliance.models import ComplianceCheck, ComplianceFramework, ComplianceReport


class ComplianceService:

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # --- Frameworks ---

    async def register_framework(
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
        await self.session.flush()
        return framework

    async def get_framework(self, framework_id: str) -> ComplianceFramework | None:
        stmt = select(ComplianceFramework).where(
            ComplianceFramework.framework_id == framework_id,
            ComplianceFramework.is_active.is_(True),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_frameworks(self) -> list[ComplianceFramework]:
        stmt = (
            select(ComplianceFramework)
            .where(ComplianceFramework.is_active.is_(True))
            .order_by(ComplianceFramework.name)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    # --- Checks ---

    async def run_check(
        self,
        framework_id: str,
        requirement_id: str,
        target_type: str,
        target_id: str,
        checked_by: str,
        check_type: str = "automated",
    ) -> ComplianceCheck:
        stmt = select(ComplianceFramework).where(
            ComplianceFramework.id == framework_id,
            ComplianceFramework.is_active.is_(True),
        )
        result = await self.session.execute(stmt)
        framework = result.scalar_one_or_none()
        if not framework:
            raise ValueError(f"Framework with id {framework_id} not found")

        check = ComplianceCheck(
            uuid=_ulid(),
            check_id=_ulid(),
            framework_id=framework_id,
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
        await self.session.flush()
        return check

    async def get_checks(self, target_type: str, target_id: str) -> list[ComplianceCheck]:
        stmt = (
            select(ComplianceCheck)
            .where(
                ComplianceCheck.target_type == target_type,
                ComplianceCheck.target_id == target_id,
                ComplianceCheck.is_active.is_(True),
            )
            .order_by(ComplianceCheck.checked_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    # --- Reports ---

    async def generate_report(
        self,
        org_id: str | None,
        framework_id: str,
        generated_by: str,
        report_type: str = "self_assessment",
    ) -> ComplianceReport:
        checks_stmt = select(ComplianceCheck).where(
            ComplianceCheck.framework_id == framework_id,
            ComplianceCheck.is_active.is_(True),
        )
        checks_result = await self.session.execute(checks_stmt)
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
        await self.session.flush()
        return report

    async def get_report(self, report_id: str) -> ComplianceReport | None:
        stmt = select(ComplianceReport).where(
            ComplianceReport.report_id == report_id,
            ComplianceReport.is_active.is_(True),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_org_compliance_status(self, org_id: str) -> list[dict[str, Any]]:
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
                ComplianceCheck.is_active.is_(True),
            )
            .group_by(ComplianceFramework.id)
        )
        result = await self.session.execute(stmt)
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
