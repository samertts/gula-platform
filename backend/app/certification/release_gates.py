from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path

from .enums import ReleaseGate


@dataclass
class GateCheckResult:
    name: str
    gate: ReleaseGate
    passed: bool
    score: float = 0.0
    evidence: list[str] = field(default_factory=list)
    remediations: list[str] = field(default_factory=list)
    blocking: bool = True

    @property
    def status(self) -> str:
        return "PASS" if self.passed else "FAIL"


class BaseGateChecker(ABC):
    def __init__(self, project_root: Path | str):
        self.project_root = Path(project_root)
        self.evidence: list[str] = []
        self.remediations: list[str] = []

    @abstractmethod
    def check(self) -> GateCheckResult:
        ...

    def _add_evidence(self, message: str) -> None:
        self.evidence.append(message)

    def _add_remediation(self, message: str) -> None:
        self.remediations.append(message)

    def _result(self, name: str, gate: ReleaseGate, passed: bool, score: float = 0.0) -> GateCheckResult:
        return GateCheckResult(
            name=name,
            gate=gate,
            passed=passed,
            score=score,
            evidence=self.evidence,
            remediations=self.remediations,
        )


class ArchitectureGate(BaseGateChecker):
    def check(self) -> GateCheckResult:
        from .dimensions.architecture import ArchitectureEvaluator
        evaluator = ArchitectureEvaluator(self.project_root)
        result = evaluator.evaluate()
        self._add_evidence(f"Architecture score: {result.score:.2f}")
        self._add_evidence(f"Clean arch violations: {len([e for e in result.evidence if 'arch' in e.name.lower() and not e.passed])}")
        self._add_evidence(f"Circular deps: {len([e for e in result.evidence if 'circular' in e.name.lower() and not e.passed])}")
        if not result.passed:
            for r in result.remediations:
                self._add_remediation(r.message)
        return self._result("Architecture Gate", ReleaseGate.ARCHITECTURE, result.passed, result.score)


class SecurityGate(BaseGateChecker):
    def check(self) -> GateCheckResult:
        from .dimensions.security import SecurityEvaluator
        evaluator = SecurityEvaluator(self.project_root)
        result = evaluator.evaluate()
        self._add_evidence(f"Security score: {result.score:.2f}")
        vulns = [e for e in result.evidence if "vulnerabilities" in e.name.lower()]
        secrets = [e for e in result.evidence if "secrets" in e.name.lower()]
        for v in vulns:
            self._add_evidence(f"Vulnerabilities: {v.value}")
        for s in secrets:
            self._add_evidence(f"Secrets: {s.value}")
        if not result.passed:
            for r in result.remediations:
                self._add_remediation(r.message)
        return self._result("Security Gate", ReleaseGate.SECURITY, result.passed, result.score)


class PerformanceGate(BaseGateChecker):
    def check(self) -> GateCheckResult:
        from .dimensions.performance import PerformanceEvaluator
        evaluator = PerformanceEvaluator(self.project_root)
        result = evaluator.evaluate()
        self._add_evidence(f"Performance score: {result.score:.2f}")
        startup = [e for e in result.evidence if "startup" in e.name.lower()]
        for s in startup:
            self._add_evidence(f"Startup time: {s.value}ms")
        if not result.passed:
            for r in result.remediations:
                self._add_remediation(r.message)
        return self._result("Performance Gate", ReleaseGate.PERFORMANCE, result.passed, result.score)


class ClinicalSafetyGate(BaseGateChecker):
    def check(self) -> GateCheckResult:
        score = 1.0
        for py_file in self.project_root.rglob("*.py"):
            if "test" in py_file.parts or "__pycache__" in py_file.parts:
                continue
            try:
                content = py_file.read_text()
                if "audit" in content.lower() and "log" in content.lower():
                    self._add_evidence("Audit logging found")
                    break
            except Exception:
                continue
        else:
            self._add_evidence("No audit logging detected — CRITICAL for clinical safety")
            self._add_remediation("Add audit logging for all patient data mutations")
            score -= 0.4

        for py_file in self.project_root.rglob("*.py"):
            if "model" in py_file.parts or "models" in py_file.parts:
                try:
                    content = py_file.read_text()
                    if "optimistic" in content.lower() or "version" in content.lower():
                        self._add_evidence("Optimistic locking found")
                        break
                except Exception:
                    continue
        else:
            self._add_evidence("No optimistic locking detected — data integrity risk")
            self._add_remediation("Add version column for optimistic locking on LabResult")
            score -= 0.3

        for py_file in self.project_root.rglob("*.py"):
            try:
                content = py_file.read_text()
                if "validate" in content.lower() and "result" in content.lower():
                    self._add_evidence("Clinical result validation found")
                    break
            except Exception:
                continue
        else:
            self._add_evidence("No clinical result validation detected")
            self._add_remediation("Add clinical result validation (reference ranges, panic values)")
            score -= 0.2

        tenant_isolation = False
        for py_file in self.project_root.rglob("*.py"):
            try:
                content = py_file.read_text()
                if "lab_id" in content and "filter" in content.lower():
                    tenant_isolation = True
                    self._add_evidence("Tenant isolation (lab_id filtering) found")
                    break
            except Exception:
                continue
        if not tenant_isolation:
            self._add_remediation("Ensure all patient queries filter by lab_id")
            score -= 0.1

        passed = score >= 0.7
        return self._result("Clinical Safety Gate", ReleaseGate.CLINICAL_SAFETY, passed, score)


class DocumentationGate(BaseGateChecker):
    def check(self) -> GateCheckResult:
        from .dimensions.documentation import DocumentationEvaluator
        evaluator = DocumentationEvaluator(self.project_root)
        result = evaluator.evaluate()
        self._add_evidence(f"Documentation score: {result.score:.2f}")
        for e in result.evidence:
            self._add_evidence(f"{e.name}: {e.value}")
        if not result.passed:
            for r in result.remediations:
                self._add_remediation(r.message)
        return self._result("Documentation Gate", ReleaseGate.DOCUMENTATION, result.passed, result.score)


class SBOMGate(BaseGateChecker):
    def check(self) -> GateCheckResult:
        score = 1.0
        from app.engineering.security.sbom import SBOMGenerator
        generator = SBOMGenerator(self.project_root)
        sbom = generator.generate()
        components = sbom.get("components", [])
        self._add_evidence(f"SBOM components: {len(components)}")
        if not components:
            self._add_remediation("Generate SBOM (CycloneDX format) for dependency tracking")
            score -= 0.5
        score -= max(0, 100 - len(components)) * 0.005

        from app.engineering.security.sbom import DependencyAuditor
        auditor = DependencyAuditor(self.project_root)
        outdated = auditor.audit()
        self._add_evidence(f"Outdated dependencies: {len(outdated)}")
        if outdated:
            self._add_remediation(f"Update {len(outdated)} outdated dependencies")
            score -= min(len(outdated) * 0.05, 0.3)

        passed = score >= 0.7
        return self._result("SBOM Gate", ReleaseGate.SBOM, passed, score)


class RiskAssessmentGate(BaseGateChecker):
    def check(self) -> GateCheckResult:
        score = 1.0
        risk_factors = []

        from .dimensions.security import SecurityEvaluator
        sec = SecurityEvaluator(self.project_root)
        sec_result = sec.evaluate()
        if sec_result.score < 0.7:
            risk_factors.append(f"Security score below threshold: {sec_result.score:.2f}")
            score -= 0.2

        from .dimensions.reliability import ReliabilityEvaluator
        rel = ReliabilityEvaluator(self.project_root)
        rel_result = rel.evaluate()
        if rel_result.score < 0.7:
            risk_factors.append(f"Reliability score below threshold: {rel_result.score:.2f}")
            score -= 0.15

        from .dimensions.db_integrity import DBIntegrityEvaluator
        db = DBIntegrityEvaluator(self.project_root)
        db_result = db.evaluate()
        if db_result.score < 0.7:
            risk_factors.append(f"DB integrity score below threshold: {db_result.score:.2f}")
            score -= 0.15

        for factor in risk_factors:
            self._add_evidence(f"Risk factor: {factor}")

        if risk_factors:
            self._add_remediation(f"Address {len(risk_factors)} risk factors before release")
        else:
            self._add_evidence("No significant risk factors detected")

        passed = score >= 0.7
        return self._result("Risk Assessment Gate", ReleaseGate.RISK_ASSESSMENT, passed, score)


class ReleaseGateChecker:
    GATES: dict[ReleaseGate, type[BaseGateChecker]] = {
        ReleaseGate.ARCHITECTURE: ArchitectureGate,
        ReleaseGate.SECURITY: SecurityGate,
        ReleaseGate.PERFORMANCE: PerformanceGate,
        ReleaseGate.CLINICAL_SAFETY: ClinicalSafetyGate,
        ReleaseGate.DOCUMENTATION: DocumentationGate,
        ReleaseGate.SBOM: SBOMGate,
        ReleaseGate.RISK_ASSESSMENT: RiskAssessmentGate,
    }

    def __init__(self, project_root: Path | str | None = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()

    def check_all(self) -> list[GateCheckResult]:
        results = []
        for _gate, checker_cls in self.GATES.items():
            checker = checker_cls(self.project_root)
            results.append(checker.check())
        return results

    def check_gate(self, gate: ReleaseGate) -> GateCheckResult:
        checker_cls = self.GATES.get(gate)
        if checker_cls is None:
            raise ValueError(f"Unknown release gate: {gate}")
        checker = checker_cls(self.project_root)
        return checker.check()

    def validate_release(self) -> dict:
        results = self.check_all()
        passed = [r for r in results if r.passed]
        failed = [r for r in results if not r.passed]
        blocking = [r for r in failed if r.blocking]

        return {
            "release_readiness": len(blocking) == 0,
            "total_gates": len(results),
            "passed": len(passed),
            "failed": len(failed),
            "blocking_failures": len(blocking),
            "details": [
                {
                    "gate": r.gate.value,
                    "name": r.name,
                    "status": r.status,
                    "score": r.score,
                    "blocking": r.blocking,
                    "evidence": r.evidence,
                    "remediations": r.remediations,
                }
                for r in results
            ],
        }
