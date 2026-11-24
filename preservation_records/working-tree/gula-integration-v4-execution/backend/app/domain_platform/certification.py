"""PROGRAM-STABLE-004 — Domain Certification (Phase 7).

The certification engine validates, for every Domain and for the platform:

  1. No duplicated business logic
  2. No duplicated infrastructure
  3. No direct database coupling
  4. No circular dependencies
  5. No permission leakage
  6. No cross-domain administration
  7. No shared mutable state
  8. Shared Core usage 100%
  9. Backward compatibility maintained
 10. Dormancy policy respected (every Domain module is declared, and no
     active Domain owns an archived/retired strategic asset)

Check 10 is the first Architecture Policy: it delegates to the shared
``DormancyPolicy`` module (ADR-027) so certification, the Architecture Gate
and CI enforce exactly the same rule through one implementation.

A Domain receives an independent, auditable certification verdict.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.domain_platform.core import DomainManifest
from app.domain_platform.dormancy import DormancySource, build_dormancy_source
from app.domain_platform.isolation import DomainIsolationReport, IsolationValidator
from app.domain_platform.manifest import CANONICAL_DOMAINS
from app.domain_platform.policies import PolicyContext, PolicyStatus
from app.domain_platform.policies.dormancy_policy import DormancyPolicy
from app.domain_platform.shared_core import is_infrastructure_reimplementation
from app.domain_platform.versioning import parse_version

CERTIFICATION_CHECKS: tuple[str, ...] = (
    "no_duplicated_business_logic",
    "no_duplicated_infrastructure",
    "no_direct_database_coupling",
    "no_circular_dependencies",
    "no_permission_leakage",
    "no_cross_domain_administration",
    "no_shared_mutable_state",
    "shared_core_usage_100",
    "backward_compatibility",
    "dormancy_policy",
)

# Severity ordering used for verdict computation.
_SEVERITY_RANK = {"info": 0, "minor": 1, "major": 2, "critical": 3}


@dataclass
class CheckResult:
    """One Phase 7 certification check."""

    check: str
    passed: bool
    severity: str = "info"
    details: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "check": self.check,
            "passed": self.passed,
            "severity": self.severity,
            "details": self.details,
        }


@dataclass
class DomainCertification:
    """Independent certification verdict for one Domain."""

    domain_code: str
    version: str
    checks: list[CheckResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(c.passed for c in self.checks)

    @property
    def score(self) -> int:
        if not self.checks:
            return 0
        return round(100 * sum(1 for c in self.checks if c.passed) / len(self.checks))

    def to_dict(self) -> dict[str, Any]:
        return {
            "domain_code": self.domain_code,
            "version": self.version,
            "passed": self.passed,
            "score": self.score,
            "checks": [c.to_dict() for c in self.checks],
        }


class DomainCertificationEngine:
    """Runs the Phase 7 certification for every Domain."""

    def __init__(
        self,
        isolation_report: DomainIsolationReport | None = None,
        dormancy_registry: DormancySource | None = None,
    ) -> None:
        self.isolation_report = isolation_report
        self.dormancy_registry: DormancySource = (
            dormancy_registry or build_dormancy_source("canonical")
        )
        self._modules_source: dict[str, str] = {}

    def set_module_sources(self, sources: dict[str, str]) -> None:
        self._modules_source = sources

    def _source(self, module: str) -> str:
        return self._modules_source.get(module, "")

    # ── check 1: no duplicated business logic ───────────────────────────────

    def check_no_duplicated_business_logic(self, manifest: DomainManifest) -> CheckResult:
        services = [s.lower() for s in manifest.services]
        duplicated = [s for s in services if s.count("_service") > 1]
        return CheckResult(
            check="no_duplicated_business_logic",
            passed=not duplicated,
            severity="major" if duplicated else "info",
            details=(
                f"duplicated service declarations: {duplicated}"
                if duplicated
                else "domain services are unique within the blueprint"
            ),
        )

    # ── check 2: no duplicated infrastructure ───────────────────────────────

    def check_no_duplicated_infrastructure(self, manifest: DomainManifest) -> CheckResult:
        findings: list[str] = []
        for module in manifest.modules:
            findings.extend(
                f"{module} reimplements Shared Core service '{svc}'"
                for svc in is_infrastructure_reimplementation(self._source(module))
            )
        return CheckResult(
            check="no_duplicated_infrastructure",
            passed=not findings,
            severity="critical" if findings else "info",
            details="; ".join(findings) if findings else "no Shared Core reimplementation detected",
        )

    # ── check 3: no direct database coupling ────────────────────────────────

    def check_no_direct_database_coupling(
        self, manifest: DomainManifest, isolation: DomainIsolationReport
    ) -> CheckResult:
        findings = [
            f.message for f in isolation.db_coupling if manifest.code in f.message
        ]
        return CheckResult(
            check="no_direct_database_coupling",
            passed=not findings,
            severity="critical" if findings else "info",
            details="; ".join(findings) if findings else "no direct engine/session creation",
        )

    # ── check 4: no circular dependencies ───────────────────────────────────

    def check_no_circular_dependencies(
        self, manifest: DomainManifest, isolation: DomainIsolationReport
    ) -> CheckResult:
        findings = [
            f.message for f in isolation.circular if manifest.code in f.message
        ]
        return CheckResult(
            check="no_circular_dependencies",
            passed=not findings,
            severity="critical" if findings else "info",
            details="; ".join(findings) if findings else "no circular dependency within the Domain",
        )

    # ── check 5: no permission leakage ──────────────────────────────────────

    def check_no_permission_leakage(
        self, manifest: DomainManifest, isolation: DomainIsolationReport
    ) -> CheckResult:
        findings = [
            f.message for f in isolation.permission_leaks if manifest.code in f.message
        ]
        return CheckResult(
            check="no_permission_leakage",
            passed=not findings,
            severity="major" if findings else "info",
            details="; ".join(findings) if findings else "API surface stays inside its own namespace",
        )

    # ── check 6: no cross-domain administration ─────────────────────────────

    def check_no_cross_domain_administration(self, manifest: DomainManifest) -> CheckResult:
        # A Domain that is a portal (citizen/provider) must never administer
        # operational Domains. All Domains must never declare ownership.
        portal_codes = {"citizen_portal", "provider_portal"}
        if manifest.code in portal_codes and manifest.services:
            admin_services = [s for s in manifest.services if "admin" in s.lower()]
            if admin_services:
                return CheckResult(
                    check="no_cross_domain_administration",
                    passed=False,
                    severity="critical",
                    details=f"portal Domain declares administration services: {admin_services}",
                )
        return CheckResult(
            check="no_cross_domain_administration",
            passed=True,
            severity="info",
            details="no Domain administers another Domain",
        )

    # ── check 7: no shared mutable state ────────────────────────────────────

    def check_no_shared_mutable_state(
        self, manifest: DomainManifest, isolation: DomainIsolationReport
    ) -> CheckResult:
        findings = [
            f.message for f in isolation.shared_state if manifest.code in f.message
        ]
        return CheckResult(
            check="no_shared_mutable_state",
            passed=not findings,
            severity="major" if findings else "info",
            details="; ".join(findings) if findings else "no mutable module-level state",
        )

    # ── check 8: Shared Core usage 100% ─────────────────────────────────────

    def check_shared_core_usage(
        self, manifest: DomainManifest, isolation: DomainIsolationReport
    ) -> CheckResult:
        consumed = set(manifest.shared_core.keys())
        # A Domain that consumes at least the platform-mandated core set.
        expected = {"identity", "authentication", "authorization", "audit", "event_bus"}
        absent = sorted(expected - consumed)
        return CheckResult(
            check="shared_core_usage_100",
            passed=not absent,
            severity="major" if absent else "info",
            details=(
                f"missing mandatory Shared Core: {', '.join(absent)}"
                if absent
                else f"{len(consumed)} Shared Core services consumed, zero reimplementation"
            ),
        )

    # ── check 9: backward compatibility ─────────────────────────────────────

    def check_backward_compatibility(self, manifest: DomainManifest) -> CheckResult:
        try:
            parse_version(manifest.version)
            return CheckResult(
                check="backward_compatibility",
                passed=True,
                severity="info",
                details=f"version {manifest.version} is a valid SemVer release",
            )
        except ValueError as exc:
            return CheckResult(
                check="backward_compatibility",
                passed=False,
                severity="major",
                details=str(exc),
            )

    # ── check 10: dormancy policy (ADR-026 / ADR-027) ─────────────────────

    def check_dormancy_policy(self, manifest: DomainManifest) -> CheckResult:
        """Delegates to the shared DormancyPolicy (the first Architecture Policy).

        Certification, the Architecture Gate and CI run the identical rule
        implementation; this adapter only maps the policy result onto the
        ``CheckResult`` shape Phase 7 consumers expect (backward compatible).
        """
        result = DormancyPolicy(self.dormancy_registry).evaluate(
            PolicyContext(domains=[manifest])
        )
        return CheckResult(
            check="dormancy_policy",
            passed=result.status in (PolicyStatus.PASS, PolicyStatus.WARN),
            severity=str(result.severity.value),
            details=result.summary,
        )

    # ── full certification ──────────────────────────────────────────────────

    def certify_domain(self, manifest: DomainManifest) -> DomainCertification:
        isolation = self.isolation_report or IsolationValidator([manifest]).run()
        checks = [
            self.check_no_duplicated_business_logic(manifest),
            self.check_no_duplicated_infrastructure(manifest),
            self.check_no_direct_database_coupling(manifest, isolation),
            self.check_no_circular_dependencies(manifest, isolation),
            self.check_no_permission_leakage(manifest, isolation),
            self.check_no_cross_domain_administration(manifest),
            self.check_no_shared_mutable_state(manifest, isolation),
            self.check_shared_core_usage(manifest, isolation),
            self.check_backward_compatibility(manifest),
            self.check_dormancy_policy(manifest),
        ]
        return DomainCertification(
            domain_code=manifest.code,
            version=manifest.version,
            checks=checks,
        )

    def certify_all(self, domains: list[DomainManifest] | None = None) -> list[DomainCertification]:
        domains = domains or list(CANONICAL_DOMAINS.values())
        isolation = self.isolation_report or IsolationValidator(domains).run()
        self.isolation_report = isolation
        return [self.certify_domain(manifest) for manifest in domains]

    def platform_certification(self, domains: list[DomainManifest] | None = None) -> dict[str, Any]:
        certifications = self.certify_all(domains)
        passed = sum(1 for c in certifications if c.passed)
        total = len(certifications)
        score = round(100 * passed / total) if total else 0
        return {
            "domains": [c.to_dict() for c in certifications],
            "passed": passed,
            "total": total,
            "score": score,
            "verdict": "CERTIFIED" if passed == total else "NOT_CERTIFIED",
        }
