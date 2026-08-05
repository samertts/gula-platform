"""Phase 5 — Risk Engine.

Maintain the architectural risk register of the GULA platform across
technical, business, operational, security, infrastructure, AI, and
knowledge categories. Risks are derived deterministically: fixed strategic
risks plus risks that surface from dependency-governance and
architecture-health evidence. Each risk carries category, probability,
impact, exposure, priority, status, and mitigation.
"""

from __future__ import annotations

from pathlib import Path

from scripts.architect.core import (
    RISK_DIR,
    RISK_LEVELS,
    RiskItem,
    RiskStatus,
    make_id,
    write_json,
)
from scripts.architect.dependencies import detect_dependencies
from scripts.kernel.core import REPO_ROOT, utcnow

_PROBABILITY_WEIGHT = {"low": 1, "medium": 2, "high": 3, "critical": 4}
_IMPACT_WEIGHT = {"low": 1, "medium": 2, "high": 3, "critical": 4}


def exposure(probability: str, impact: str) -> int:
    """Compute a bounded exposure score from probability and impact."""
    return (
        _PROBABILITY_WEIGHT.get(probability, 1)
        * _IMPACT_WEIGHT.get(impact, 1)
    )


def _priority(probability: str, impact: str) -> str:
    value = exposure(probability, impact)
    if value >= 9:
        return "critical"
    if value >= 6:
        return "high"
    if value >= 3:
        return "medium"
    return "low"


# Fixed strategic risks of the national platform.
# (category, area, title, probability, impact, mitigation)
STRATEGIC_RISKS: tuple[tuple[str, str, str, str, str, str], ...] = (
    (
        "security",
        "identity",
        "Identity platform coupling to national federation roadmap",
        "high",
        "high",
        "Adopt the identity platform as the single authority; keep "
        "federation adapters behind interfaces.",
    ),
    (
        "technical",
        "offline",
        "Offline-first sync conflicts across governorate partitions",
        "high",
        "high",
        "Outbox pattern + conflict-resolution policies exercised in pilot.",
    ),
    (
        "business",
        "compliance",
        "ISO 15189 / CAP / CLSI audit evidence drift",
        "medium",
        "high",
        "Automate evidence packs in quality gates; continuous validation.",
    ),
    (
        "business",
        "data-residency",
        "Governorate data residency and national aggregation conflict",
        "medium",
        "critical",
        "Tenant-aware routing and regional data stores planned for "
        "3-year horizon.",
    ),
    (
        "security",
        "encryption",
        "ENCRYPTION_KEY rotation without bulk re-encryption",
        "medium",
        "high",
        "Design key rotation with per-record key versioning and lazy "
        "re-encryption.",
    ),
    (
        "operational",
        "recovery",
        "Cloud snapshot restore path is not rehearsed",
        "medium",
        "high",
        "Rehearse restore runbook; verify PITR + WAL recovery end-to-end.",
    ),
    (
        "technical",
        "analyzer",
        "Analyzer protocol fragmentation across laboratory hardware",
        "high",
        "medium",
        "Standardize ASTM/HL7 device bridge with validation per result.",
    ),
    (
        "operational",
        "capacity",
        "Database and storage growth at national scale",
        "medium",
        "high",
        "Partition data stores, add read replicas, and archive per "
        "retention policy before hitting capacity limits.",
    ),
    (
        "ai",
        "ai-governance",
        "AI engines drift from the single architectural vision",
        "medium",
        "medium",
        "The Architect coordinates all six engines; contracts and "
        "registers are the single source of truth.",
    ),
    (
        "knowledge",
        "knowledge-drift",
        "Knowledge coverage lags behind architectural change",
        "medium",
        "medium",
        "Learner records knowledge per mission; brain freshness is a "
        "hard CI gate.",
    ),
)


def _dependency_risk(root: Path) -> RiskItem | None:
    """Surface a risk when circular dependencies exist in the backend."""
    findings = detect_dependencies(root)
    circular = [f for f in findings if f.kind == "circular"]
    if not circular:
        return None
    probability = "high" if len(circular) > 15 else "medium"
    impact = "high"
    return RiskItem(
        risk_id=make_id("RISK"),
        area="architecture",
        category="technical",
        title=f"Circular dependencies in the backend ({len(circular)} found)",
        probability=probability,
        impact=impact,
        exposure=exposure(probability, impact),
        priority=_priority(probability, impact),
        status=RiskStatus.OPEN.value,
        mitigation="Extract shared modules and introduce domain events to "
        "break the detected cycles.",
    )


def build_risks(root: Path | None = None) -> list[RiskItem]:
    """Build the architectural risk register deterministically."""
    root = root or REPO_ROOT
    risks: list[RiskItem] = []
    for category, area, title, probability, impact, mitigation in STRATEGIC_RISKS:
        risks.append(RiskItem(
            risk_id=make_id("RISK"),
            area=area,
            title=title,
            category=category,
            probability=probability,
            impact=impact,
            exposure=exposure(probability, impact),
            priority=_priority(probability, impact),
            status=RiskStatus.OPEN.value,
            mitigation=mitigation,
        ))
    dependency_risk = _dependency_risk(root)
    if dependency_risk:
        risks.append(dependency_risk)
    return sorted(risks, key=lambda r: (-r.exposure, r.area, r.title))


def persist_risks(root: Path | None = None) -> Path:
    """Persist the risk register under state/risks/."""
    root = root or REPO_ROOT
    risks = build_risks(root)
    path = RISK_DIR / "register.json"
    write_json(path, {
        "discovered_at": utcnow(),
        "levels": list(RISK_LEVELS),
        "categories": ["technical", "business", "operational", "security",
                       "infrastructure", "ai", "knowledge"],
        "risks": [r.to_dict() for r in risks],
    })
    return path


def render_markdown(risks: list[RiskItem]) -> str:
    lines = [
        "# GULA-ARCHITECT-001 — Architectural Risk Register",
        "",
        f"Generated: **{utcnow()}**",
        "",
        f"**{len(risks)} risks** ranked by exposure.",
        "",
        "| Risk | Category | Area | Probability | Impact | Exposure | Priority | Status |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for risk in risks:
        lines.append(
            f"| {risk.title} | {risk.category} | {risk.area} | "
            f"{risk.probability} | {risk.impact} | {risk.exposure} | "
            f"{risk.priority} | {risk.status} |"
        )
    lines.extend(["", "## Mitigations", ""])
    for risk in risks:
        lines.append(f"- `{risk.risk_id}` **{risk.title}**: {risk.mitigation}")
    lines.append("")
    return "\n".join(lines)
