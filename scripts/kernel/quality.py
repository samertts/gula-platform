"""Phase 12 — Quality Engine.

Every mission must pass: architecture, security, testing, knowledge,
deployment, performance, documentation, governance, and constitution. No
bypass is allowed. Builds on the Governor's quality gates (Phase 8) and adds
the governance gate.
"""

from __future__ import annotations

from scripts.governor.quality_gates import (
    GateResult,
    all_gates_pass,
    failed_gates,
    run_all_gates,
)

GATE_NAMES = (
    "architecture",
    "security",
    "testing",
    "knowledge",
    "deployment",
    "performance",
    "documentation",
    "governance",
    "constitution",
)


def evaluate_governance_gate(
    decisions_approved: bool = True,
    authority_respected: bool = True,
) -> GateResult:
    """Governance gate: decisions approved and authority chain respected."""
    ok = decisions_approved and authority_respected
    detail = "Governance compliant" if ok else "Governance gate FAILED"
    return GateResult("governance", ok, detail=detail)


def run_quality_gates(
    architecture_approved: bool = True,
    adr_present: bool = True,
    no_security_violations: bool = True,
    tests_present: bool = True,
    tests_pass: bool = True,
    knowledge_updated: bool = True,
    registry_updated: bool = True,
    deployable: bool = True,
    reviewer_approved: bool = True,
    benchmarks_pass: bool = True,
    docs_updated: bool = True,
    decisions_approved: bool = True,
    authority_respected: bool = True,
    constitution_compliant: bool = True,
) -> list[GateResult]:
    """Run the nine mandatory Kernel quality gates."""
    results = run_all_gates(
        architecture_approved=architecture_approved,
        adr_present=adr_present,
        no_security_violations=no_security_violations,
        tests_present=tests_present,
        tests_pass=tests_pass,
        benchmarks_pass=benchmarks_pass,
        docs_updated=docs_updated,
        knowledge_updated=knowledge_updated,
        registry_updated=registry_updated,
        deployable=deployable,
        reviewer_approved=reviewer_approved,
        constitution_compliant=constitution_compliant,
    )
    results.append(evaluate_governance_gate(decisions_approved, authority_respected))
    return results


def all_pass(results: list[GateResult]) -> bool:
    return all_gates_pass(results)


def failed(results: list[GateResult]) -> list[str]:
    return failed_gates(results)


def require_pass(results: list[GateResult]) -> None:
    """Raise when any mandatory gate fails — no bypass allowed."""
    failing = failed(results)
    if failing:
        raise RuntimeError(f"Quality gates failed: {', '.join(failing)}")
