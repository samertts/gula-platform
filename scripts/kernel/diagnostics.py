"""Phase 17 — Self Diagnostics.

Continuously audit the Kernel, Governor, Architect, Builder, Reviewer,
Learner, Optimizer, Deployer, Knowledge, Registry, Memory, and
Infrastructure, then generate improvement proposals. Proposals are advisory
and never applied automatically.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from scripts.governor.self_governance import ImprovementProposal, generate_proposals

from .contract import contract_violations
from .core import ENGINE_REGISTRY, Finding, Severity, utcnow
from .registry import health_matrix, version_matrix


@dataclass
class ComponentAudit:
    """An audit result for a single platform component."""

    component: str
    present: bool
    findings: list[Finding] = field(default_factory=list)
    health: str = "healthy"


def _component_present(component: str) -> bool:
    markers = {
        "kernel": ["scripts/kernel"],
        "governor": ["scripts/governor"],
        "architect": ["scripts/architecture_compliance_engine.py", "scripts/architecture_guardian.py"],
        "builder": ["backend/app", "frontend-v3/src"],
        "reviewer": ["scripts/self_audit_agent.py", "scripts/quality_gate.py"],
        "learner": ["scripts/auto_learning_proposal.py"],
        "optimizer": ["scripts/generate_performance_report.py", "scripts/repository_scorecard.py"],
        "deployer": ["deploy.sh", ".github/workflows"],
        "knowledge": [".ai/core/index", ".ai/core/registry"],
        "registry": [".ai/core/registry", "scripts/auto_registry.py"],
        "memory": [".ai/core/memory", "docs/brain/PROJECT_BRAIN.md"],
        "infrastructure": ["docker-compose.yml", ".github/workflows", "Makefile"],
    }[component]
    from pathlib import Path

    return any(Path(marker).exists() for marker in markers)


def audit_components(registry: dict | None = None) -> list[ComponentAudit]:
    """Audit every platform component and return per-component findings."""
    registry = registry or ENGINE_REGISTRY
    audits: list[ComponentAudit] = []
    components = [
        "kernel", "governor", "architect", "builder", "reviewer", "learner",
        "optimizer", "deployer", "knowledge", "registry", "memory", "infrastructure",
    ]
    for component in components:
        present = _component_present(component)
        findings: list[Finding] = []
        if not present:
            findings.append(Finding(
                id=f"DIAG-{component.upper()}-0001",
                title=f"{component} component missing",
                severity=Severity.MEDIUM,
                category="self-diagnostics",
                detail=f"No implementation evidence found for {component}",
            ))
        audits.append(ComponentAudit(
            component=component,
            present=present,
            findings=findings,
            health="healthy" if present and not findings else "degraded",
        ))
    return audits


def audit_engine_contract(registry: dict | None = None) -> list[Finding]:
    """Find engine contract violations (Phase 3 conformance)."""
    registry = registry or ENGINE_REGISTRY
    findings: list[Finding] = []
    for violation in contract_violations(registry):
        findings.append(Finding(
            id=f"DIAG-CONTRACT-{len(findings) + 1:04d}",
            title="Engine contract violation",
            severity=Severity.MEDIUM,
            category="engine-communication",
            detail=violation,
        ))
    return findings


def audit_registry_health(registry: dict | None = None) -> list[Finding]:
    """Find engines with missing versions or unhealthy status."""
    registry = registry or ENGINE_REGISTRY
    findings: list[Finding] = []
    versions = version_matrix(registry)
    health = health_matrix(registry)
    for engine in registry:
        if versions.get(engine) in (None, "", "0.0.0"):
            findings.append(Finding(
                id=f"DIAG-VER-{engine.upper()}",
                title=f"{engine} engine missing version",
                severity=Severity.LOW,
                category="registry",
                detail="Engine has no declared version",
            ))
        if health.get(engine) == "unhealthy":
            findings.append(Finding(
                id=f"DIAG-HEALTH-{engine.upper()}",
                title=f"{engine} engine unhealthy",
                severity=Severity.HIGH,
                category="registry",
                detail="Engine reports unhealthy status",
            ))
    return findings


def run_diagnostics(registry: dict | None = None) -> list[Finding]:
    """Run the full self-diagnostics pass over all components and engines."""
    registry = registry or ENGINE_REGISTRY
    findings: list[Finding] = []
    for audit in audit_components(registry):
        findings.extend(audit.findings)
    findings.extend(audit_engine_contract(registry))
    findings.extend(audit_registry_health(registry))
    return findings


def diagnose_and_propose(registry: dict | None = None) -> list[ImprovementProposal]:
    """Audit everything and generate advisory improvement proposals."""
    findings = run_diagnostics(registry)
    return generate_proposals(findings)


def save_diagnostics_report(path, findings: list[Finding], proposals: list[ImprovementProposal]) -> None:
    """Persist a machine-readable diagnostics report."""
    from .core import write_json

    write_json(path, {
        "generated_at": utcnow(),
        "findings": [vars(f) for f in findings],
        "proposals": [vars(p) for p in proposals],
    })
