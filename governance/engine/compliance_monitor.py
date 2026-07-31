from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from governance.catalogs.dependency_registry import DependencyRegistry
from governance.catalogs.technology_catalog import TechnologyCatalog
from governance.constitution_engine import ConstitutionEngine


class ContinuousComplianceMonitor:
    def __init__(self) -> None:
        self.engine = ConstitutionEngine()
        self.catalog = TechnologyCatalog()
        self.registry = DependencyRegistry()
        self.repo_root = Path(__file__).resolve().parent.parent.parent
        self.alerts: list[dict[str, Any]] = []

    def run_check(self) -> dict[str, Any]:
        self.alerts = []
        self._check_dependencies()
        self._check_licenses()
        self._check_cves()
        self._check_adr_compliance()
        self._check_costs()
        self._check_constitution()
        self._check_architecture()

        return {
            "checked_at": datetime.now(UTC).isoformat(),
            "total_alerts": len(self.alerts),
            "blocker_alerts": sum(1 for a in self.alerts if a["severity"] == "BLOCKER"),
            "high_alerts": sum(1 for a in self.alerts if a["severity"] == "HIGH"),
            "medium_alerts": sum(1 for a in self.alerts if a["severity"] == "MEDIUM"),
            "low_alerts": sum(1 for a in self.alerts if a["severity"] == "LOW"),
            "alerts": self.alerts,
            "status": "COMPLIANT" if not any(a["severity"] in ("BLOCKER", "HIGH") for a in self.alerts) else "NON_COMPLIANT",
        }

    def _check_dependencies(self) -> None:
        self.registry.load()
        for dep in self.registry.get_high_risk():
            self.alerts.append({
                "type": "high_risk_dependency",
                "severity": "HIGH",
                "source": "dependency_registry",
                "message": f"Dependency {dep.name} v{dep.version} has HIGH risk: {dep.risk}",
                "remediation": f"Review and replace {dep.name} — check {dep.replacement}",
            })

        for dep in self.registry.get_outdated():
            self.alerts.append({
                "type": "outdated_dependency",
                "severity": "MEDIUM",
                "source": "dependency_registry",
                "message": f"Dependency {dep.name} has stale maintenance status: {dep.maintenance_status}",
                "remediation": f"Plan replacement for {dep.name} — suggested: {dep.replacement}",
            })

    def _check_licenses(self) -> None:
        self.catalog.load()
        for tech in self.catalog.get_forbidden():
            self.alerts.append({
                "type": "forbidden_technology",
                "severity": "HIGH",
                "source": "technology_catalog",
                "message": f"Forbidden technology detected: {tech.name} ({tech.license_type})",
                "remediation": f"Replace with: {tech.open_source_alternative}",
            })

    def _check_cves(self) -> None:
        self.registry.load()
        for dep in self.registry.dependencies:
            if dep.cves > 0:
                self.alerts.append({
                    "type": "cve_found",
                    "severity": "HIGH" if dep.cves > 2 else "MEDIUM",
                    "source": "dependency_registry",
                    "message": f"{dep.name} has {dep.cves} CVEs (security score: {dep.security_score})",
                    "remediation": f"Upgrade {dep.name} or replace with {dep.replacement}",
                })

    def _check_adr_compliance(self) -> None:
        adr_dir = self.repo_root / "docs" / "adr"
        if adr_dir.exists():
            adrs = list(adr_dir.glob("ADR-*.md"))
            if len(adrs) < 5:
                self.alerts.append({
                    "type": "adr_compliance",
                    "severity": "MEDIUM",
                    "source": "architecture",
                    "message": f"Only {len(adrs)} ADRs found — expected minimum for this codebase size",
                    "remediation": "Create ADRs for major architectural decisions",
                })

    def _check_costs(self) -> None:
        self.catalog.load()
        paid = [t for t in self.catalog.technologies if t.cost > 0]
        if paid:
            self.alerts.append({
                "type": "paid_technology",
                "severity": "MEDIUM",
                "source": "technology_catalog",
                "message": f"{len(paid)} paid technologies in catalog — verify cost governance compliance",
                "remediation": "Review cost governance policy for each paid technology",
            })

    def _check_constitution(self) -> None:
        report = self.engine.generate_compliance_report()
        if report["status"] == "NON_COMPLIANT":
            self.alerts.append({
                "type": "constitution_violation",
                "severity": "BLOCKER",
                "source": "constitution_engine",
                "message": f"Constitution compliance score: {report['compliance_score']}/100 — {report['failed_rules']} rules failed",
                "remediation": "Address all constitution violations",
            })

    def _check_architecture(self) -> None:
        from governance.engine.review_engine import AutonomousReviewEngine
        reviewer = AutonomousReviewEngine()
        findings = reviewer.review_all()
        blockers = [f for f in findings if f["severity"] == "BLOCKER"]
        for b in blockers:
            self.alerts.append({
                "type": "architecture_violation",
                "severity": "BLOCKER",
                "source": "review_engine",
                "message": b["message"],
                "remediation": f"Fix architecture violation in {b['file']}",
            })
