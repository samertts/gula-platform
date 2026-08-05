"""Phase 3 — Engineering Analyzer.

Determine the engineering surface a mission touches: affected modules, APIs,
database, frontend, tests, documentation, deployment, security, knowledge,
and registry. Deterministic keyword matching over the objective plus the
mission type and expected files.
"""

from __future__ import annotations

from scripts.builder.analyzer import normalize
from scripts.builder.core import IMPACT_AREAS, ImpactAnalysis, MissionAnalysis

# Keyword -> surface mappings for impact detection.
MODULE_SIGNALS: dict[str, tuple[str, ...]] = {
    "backend": ("backend", "api", "service", "route", "module", "model", "db"),
    "frontend": ("frontend", "page", "component", "ui", "screen", "mobile", "dashboard"),
    "infrastructure": ("docker", "k8s", "ci", "deploy", "terraform", "helm", "nginx"),
    "security": ("security", "auth", "permission", "encrypt", "audit log", "vulnerability"),
    "database": ("migration", "schema", "database", "model", "table", "query"),
    "testing": ("test", "pytest", "coverage", "regression"),
    "documentation": ("document", "docstring", "readme", "guide", "manual", "docs"),
    "knowledge": ("knowledge", "skill", "runbook", "playbook", "registry", "memory"),
    "deployment": ("deploy", "release", "provision", "rollout", "environment"),
    "apis": ("api", "endpoint", "contract", "openapi", "fhir", "graphql"),
}


def _matches(text: str, signals: tuple[str, ...]) -> list[str]:
    return [signal for signal in signals if signal in text]


def analyze_impact(analysis: MissionAnalysis) -> ImpactAnalysis:
    """Produce an ImpactAnalysis for an analyzed mission."""
    text = normalize(analysis.objective)
    mission_type = analysis.mission_type
    expected = " ".join(analysis.expected_files)

    impact = ImpactAnalysis(mission_id=analysis.mission_id)

    if "backend" in text or "api" in text or mission_type in {"feature", "bug", "refactor", "performance", "security"}:
        impact.affected_modules.append("backend/app")
    if "frontend" in text or "page" in text or "ui" in text or mission_type in {"feature", "bug"}:
        impact.affected_frontend.append("frontend-v3/src")

    impact.affected_modules.extend(_matches(text, MODULE_SIGNALS["backend"]))
    impact.affected_apis.extend(_matches(text, MODULE_SIGNALS["apis"]))
    impact.affected_database.extend(_matches(text, MODULE_SIGNALS["database"]))
    impact.affected_frontend.extend(_matches(text, MODULE_SIGNALS["frontend"]))
    impact.affected_tests.extend(_matches(text, MODULE_SIGNALS["testing"]))
    impact.affected_documentation.extend(_matches(text, MODULE_SIGNALS["documentation"]))
    impact.affected_deployment.extend(_matches(text, MODULE_SIGNALS["deployment"]))
    impact.affected_security.extend(_matches(text, MODULE_SIGNALS["security"]))
    impact.affected_knowledge.extend(_matches(text, MODULE_SIGNALS["knowledge"]))

    # Mission-type baseline surfaces.
    if mission_type == "security":
        impact.affected_security.extend(["security config", "audit trail"])
    if mission_type == "deployment":
        impact.affected_deployment.extend(["workflows", "deploy config"])
    if mission_type == "documentation":
        impact.affected_documentation.append("docs/")
    if mission_type == "testing":
        impact.affected_tests.append("test suite")
    if mission_type == "architecture":
        impact.affected_knowledge.append("ADR")
        impact.affected_modules.append("module boundaries")

    # Registry + knowledge are always impacted when files change.
    if expected:
        impact.affected_registry.append(".ai/core/registry/REGISTRY.md")
        impact.affected_knowledge.append(".ai/core/index/INDEX.md")

    return _dedupe(impact)


def _dedupe(impact: ImpactAnalysis) -> ImpactAnalysis:
    for area in IMPACT_AREAS:
        values = getattr(impact, f"affected_{area}")
        if isinstance(values, list):
            seen: list[str] = []
            for value in values:
                if value not in seen:
                    seen.append(value)
            setattr(impact, f"affected_{area}", seen)
    return impact


def impact_summary(impact: ImpactAnalysis) -> str:
    """Compact one-line summary of the impact analysis."""
    counts = {
        area: len(getattr(impact, f"affected_{area}"))
        for area in IMPACT_AREAS
    }
    touched = [area for area, count in counts.items() if count]
    return f"{impact.mission_id} touches {len(touched)} areas: {', '.join(touched)}"
