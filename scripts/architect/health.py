"""Phase 9 — Architecture Health.

Measure architecture health across six dimensions using the evidence
produced by earlier phases: layer discipline and dependency governance
(from the dependency scan), context cohesion (from the system model),
decision coverage (from the ADR phase), risk exposure (from the risk
register), and national compliance (from the audit). Produces a bounded
overall score. Persisted under state/health/.
"""

from __future__ import annotations

from pathlib import Path

from scripts.architect.audit import audit_system
from scripts.architect.core import (
    HEALTH_DIMENSIONS,
    HEALTH_DIR,
    HealthScore,
    maturity_level,
    write_json,
)
from scripts.architect.decisions import build_decisions
from scripts.architect.dependencies import detect_dependencies
from scripts.architect.model import build_model
from scripts.architect.risk import build_risks
from scripts.kernel.core import REPO_ROOT, utcnow


def _layer_discipline(findings: list) -> int:
    skip = [f for f in findings if f.kind == "skip-layer"]
    if not skip:
        return 100
    return max(0, 100 - len(skip) * 5)


def _dependency_governance(findings: list) -> int:
    circular = [f for f in findings if f.kind == "circular"]
    if not circular:
        return 100
    return max(0, 100 - len(circular) * 3)


def _context_cohesion(contexts: list) -> int:
    if not contexts:
        return 0
    with_entities = sum(1 for c in contexts if c.entities)
    return round(with_entities / len(contexts) * 100)


def _decision_coverage(decisions: list) -> int:
    if not decisions:
        return 0
    accepted = sum(1 for d in decisions if d.status == "accepted")
    return round(accepted / len(decisions) * 100)


def _risk_exposure(risks: list) -> int:
    if not risks:
        return 100
    total_exposure = sum(r.exposure for r in risks)
    open_risks = sum(1 for r in risks if r.status == "open")
    return max(0, 100 - total_exposure - open_risks * 2)


def _national_compliance(items: list) -> int:
    present = sum(
        1 for item in items
        if item.title in {"fhir-hl7", "multi-tenancy", "offline-first", "identity"}
        and item.status == "measured"
    )
    return round(present / 4 * 100)


def _maturity_score(root: Path, dimensions: dict[str, int], risks: list) -> int:
    """Score architecture maturity: how institutionalized the practices are.

    Combines decision coverage (ADR practice), dependency governance
    (enforced analysis), layer discipline, knowledge coverage (Learner
    present), and automation (AI engines present).
    """
    knowledge = 100 if (root / "scripts" / "learner").exists() else 0
    automation = 100 if (root / "scripts" / "kernel").exists() else 0
    governance = dimensions.get("dependency-governance", 0)
    decisions = dimensions.get("decision-coverage", 0)
    layers = dimensions.get("layer-discipline", 0)
    components = [
        knowledge,
        automation,
        governance,
        decisions,
        layers,
        max(0, 100 - len(risks) * 4),
    ]
    return round(sum(components) / len(components))


def measure_health(root: Path | None = None) -> HealthScore:
    """Compute the architecture health and maturity scores deterministically."""
    root = root or REPO_ROOT
    findings = detect_dependencies(root)
    contexts = build_model(root)
    decisions = build_decisions(root)
    risks = build_risks(root)
    items = audit_system()

    dimensions = {
        "layer-discipline": _layer_discipline(findings),
        "dependency-governance": _dependency_governance(findings),
        "context-cohesion": _context_cohesion(contexts),
        "decision-coverage": _decision_coverage(decisions),
        "risk-exposure": _risk_exposure(risks),
        "national-compliance": _national_compliance(items),
    }
    overall = round(sum(dimensions.values()) / len(dimensions))
    maturity = _maturity_score(root, dimensions, risks)
    summary = (
        f"{overall}/100 — {len(findings)} dependency findings, "
        f"{len(contexts)} bounded contexts, {len(decisions)} decisions, "
        f"{len(risks)} risks."
    )
    return HealthScore(
        dimensions=dimensions,
        overall=overall,
        maturity=maturity,
        maturity_level=maturity_level(maturity),
        summary=summary,
    )


def persist_health(root: Path | None = None) -> Path:
    """Persist the health score under state/health/."""
    root = root or REPO_ROOT
    health = measure_health(root)
    path = HEALTH_DIR / "score.json"
    write_json(path, {
        "discovered_at": utcnow(),
        "dimensions": health.dimensions,
        "overall": health.overall,
        "maturity": health.maturity,
        "maturity_level": health.maturity_level,
        "summary": health.summary,
    })
    return path


def render_markdown(health: HealthScore) -> str:
    lines = [
        "# GULA-ARCHITECT-001 — Architecture Health",
        "",
        f"Generated: **{utcnow()}**",
        "",
        f"Overall health: **{health.overall}/100**",
        "",
        f"Maturity score: **{health.maturity}/100** "
        f"(level: {health.maturity_level})",
        "",
        f"Summary: {health.summary}",
        "",
        "| Dimension | Score |",
        "|---|---|",
    ]
    for dimension in HEALTH_DIMENSIONS:
        lines.append(f"| {dimension} | {health.dimensions.get(dimension, 0)}/100 |")
    lines.append("")
    return "\n".join(lines)
