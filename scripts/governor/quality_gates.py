"""Phase 8 — Quality Gates.

Every mission must pass mandatory gates: Architecture, Security, Testing,
Performance, Documentation, Knowledge, Deployment, Constitution. Reject
missions that fail mandatory gates.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .core import Finding, Severity

GATE_NAMES = (
    "architecture",
    "security",
    "testing",
    "performance",
    "documentation",
    "knowledge",
    "deployment",
    "constitution",
)

MANDATORY_GATES = set(GATE_NAMES)


@dataclass
class GateResult:
    """Result of a single quality gate."""

    name: str
    passed: bool
    detail: str = ""
    findings: list[Finding] = field(default_factory=list)


def evaluate_architecture_gate(architecture_approved: bool = True, adr_present: bool = True) -> GateResult:
    """Architecture gate: changes follow Clean Architecture / SOLID and have ADRs."""
    findings = []
    if not adr_present:
        findings.append(Finding("ARCH-1", "Missing ADR", Severity.HIGH,
                                "architecture", "Architectural change without ADR"))
    if not architecture_approved:
        findings.append(Finding("ARCH-2", "Architecture not approved", Severity.CRITICAL,
                                "architecture", "Change not approved by Architect"))
    return GateResult("architecture", architecture_approved and adr_present,
                      detail="Clean Architecture + ADR" if architecture_approved and adr_present
                      else "Architecture gate FAILED", findings=findings)


def evaluate_security_gate(no_security_violations: bool = True) -> GateResult:
    """Security gate: no OWASP violations, no secrets exposure, least privilege."""
    detail = "No security violations" if no_security_violations else "Security gate FAILED"
    return GateResult("security", no_security_violations, detail=detail)


def evaluate_testing_gate(tests_present: bool = True, tests_pass: bool = True) -> GateResult:
    """Testing gate: tests exist and pass (regression tests for bug fixes)."""
    ok = tests_present and tests_pass
    detail = "Tests present and passing" if ok else "Testing gate FAILED"
    return GateResult("testing", ok, detail=detail)


def evaluate_performance_gate(benchmarks_pass: bool = True) -> GateResult:
    """Performance gate: benchmarks pass; no regression vs baseline."""
    detail = "Benchmarks pass" if benchmarks_pass else "Performance gate FAILED"
    return GateResult("performance", benchmarks_pass, detail=detail)


def evaluate_documentation_gate(docs_updated: bool = True) -> GateResult:
    """Documentation gate: public features documented, deployment docs present."""
    detail = "Documentation updated" if docs_updated else "Documentation gate FAILED"
    return GateResult("documentation", docs_updated, detail=detail)


def evaluate_knowledge_gate(knowledge_updated: bool = True, registry_updated: bool = True) -> GateResult:
    """Knowledge gate: skills/playbooks/registry updated when knowledge changed."""
    ok = knowledge_updated and registry_updated
    detail = "Knowledge + registry updated" if ok else "Knowledge gate FAILED"
    return GateResult("knowledge", ok, detail=detail)


def evaluate_deployment_gate(deployable: bool = True, reviewer_approved: bool = True) -> GateResult:
    """Deployment gate: deployable and approved by the Reviewer."""
    ok = deployable and reviewer_approved
    detail = "Deployment approved by Reviewer" if ok else "Deployment gate FAILED"
    return GateResult("deployment", ok, detail=detail)


def evaluate_constitution_gate(constitution_compliant: bool = True) -> GateResult:
    """Constitution gate: no violation of the supreme constitution."""
    detail = "Constitution compliant" if constitution_compliant else "Constitution gate FAILED"
    return GateResult("constitution", constitution_compliant, detail=detail)


GATE_EVALUATORS = {
    "architecture": evaluate_architecture_gate,
    "security": evaluate_security_gate,
    "testing": evaluate_testing_gate,
    "performance": evaluate_performance_gate,
    "documentation": evaluate_documentation_gate,
    "knowledge": evaluate_knowledge_gate,
    "deployment": evaluate_deployment_gate,
    "constitution": evaluate_constitution_gate,
}


def run_all_gates(
    architecture_approved: bool = True,
    adr_present: bool = True,
    no_security_violations: bool = True,
    tests_present: bool = True,
    tests_pass: bool = True,
    benchmarks_pass: bool = True,
    docs_updated: bool = True,
    knowledge_updated: bool = True,
    registry_updated: bool = True,
    deployable: bool = True,
    reviewer_approved: bool = True,
    constitution_compliant: bool = True,
) -> list[GateResult]:
    """Run the full mandatory gate suite and return results."""
    return [
        evaluate_architecture_gate(architecture_approved, adr_present),
        evaluate_security_gate(no_security_violations),
        evaluate_testing_gate(tests_present, tests_pass),
        evaluate_performance_gate(benchmarks_pass),
        evaluate_documentation_gate(docs_updated),
        evaluate_knowledge_gate(knowledge_updated, registry_updated),
        evaluate_deployment_gate(deployable, reviewer_approved),
        evaluate_constitution_gate(constitution_compliant),
    ]


def all_gates_pass(results: list[GateResult]) -> bool:
    """Reject missions failing any mandatory gate."""
    return all(gate.passed for gate in results if gate.name in MANDATORY_GATES)


def failed_gates(results: list[GateResult]) -> list[str]:
    return [gate.name for gate in results if not gate.passed]
