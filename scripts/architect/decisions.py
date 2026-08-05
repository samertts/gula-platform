"""Phase 2 — Architectural Decisions.

Discover the platform's existing ADR corpus (docs/adr/) and record the
strategic architectural decisions that define the national GULA platform.
Every decision captures the reason, alternatives considered, trade-offs,
risk, cost, rollback strategy, and review status — and links to an ADR
when one exists. Records persist under state/decisions/.
"""

from __future__ import annotations

from pathlib import Path

from scripts.architect.core import (
    DECISION_DIR,
    ArchitectureDecision,
    DecisionStatus,
    write_json,
)
from scripts.kernel.core import REPO_ROOT, utcnow

# Canonical strategic decisions of the national platform.
# Each record: id, title, context, reason, decision, alternatives,
#              trade_offs, risk, cost, rollback, consequences, adr_ref.
STRATEGIC_DECISIONS: tuple[dict[str, object], ...] = (
    {
        "decision_id": "modular-monolith-first",
        "title": "Modular monolith first, service extraction when evidence demands",
        "context": "A national healthcare platform must ship as one deployable "
        "before splitting services; premature microservices multiply operational "
        "cost across governorates without evidence.",
        "reason": "One deployable unit minimizes governance, deployment, and "
        "rollback complexity during national pilot while preserving clear module "
        "boundaries for later extraction.",
        "decision": "Adopt a modular monolith. Extract services only when "
        "measurement shows a real boundary (load, team, regulatory).",
        "alternatives": [
            "Distributed microservices from day one",
            "Layered single module with no boundaries",
        ],
        "trade_offs": [
            "Deployment blast radius spans the whole platform",
            "Module boundaries must be enforced by review, not by process isolation",
        ],
        "risk": "Monolith grows into a ball of mud without boundary enforcement.",
        "cost": "Low — no extra infrastructure; requires review discipline.",
        "rollback": "Full revert of the module; extraction path remains open.",
        "consequences": [
            "One deployable unit, clear module boundaries",
            "Services extracted only when measured",
        ],
        "adr_ref": "ADR-002-monolith-first.md",
    },
    {
        "decision_id": "fhir-r4",
        "title": "FHIR R4 as the interoperability backbone",
        "context": "National health data must interoperate across ministries, "
        "directorates, hospitals, and laboratories.",
        "reason": "FHIR R4 is the national-standard clinical contract; HL7 "
        "messaging is preserved for legacy analyzer and hospital bridges.",
        "decision": "Adopt FHIR R4 resources as the canonical clinical contract, "
        "with HL7 adapters at the boundaries.",
        "alternatives": ["Proprietary clinical data model", "HL7 v2 only"],
        "trade_offs": [
            "FHIR profiles require national conformance effort",
            "HL7 v2 adapters add translation complexity",
        ],
        "risk": "Specification drift between national FHIR profiles and platform.",
        "cost": "Medium — conformance testing and profile management.",
        "rollback": "FHIR layer is additive; legacy data model retained.",
        "consequences": [
            "FHIR R4 resources as the canonical clinical contract",
            "HL7 messaging preserved at device and hospital boundaries",
        ],
        "adr_ref": "docs/adr/ADR-024-Platform-Constitution.md",
    },
    {
        "decision_id": "multi-tenant-isolation",
        "title": "Multi-tenancy with tenant isolation at the data layer",
        "context": "Every governorate, directorate, hospital, and laboratory must "
        "operate independently without cross-tenant leakage.",
        "reason": "Regulatory and clinical safety require tenant-scoped access "
        "enforced in every query, not just at the UI.",
        "decision": "Enforce tenant isolation at the data layer: lab_id scoping "
        "through services and models, verified by the Reviewer.",
        "alternatives": ["Single shared database without scoping", "Database-per-tenant"],
        "trade_offs": [
            "Single schema requires disciplined scoping everywhere",
            "Database-per-tenant multiplies operational cost",
        ],
        "risk": "A missing scoping filter leaks data across tenants.",
        "cost": "Low-to-medium — discipline enforced by tests and review.",
        "rollback": "Restore row-level scoping; no schema change.",
        "consequences": [
            "Tenant-scoped access control",
            "Lab-level isolation enforced in every query",
        ],
        "adr_ref": "docs/adr/ADR-003-multi-tenant-isolation.md",
    },
    {
        "decision_id": "postgresql-redis",
        "title": "PostgreSQL + Redis as the platform data stack",
        "context": "Free, self-hosted, and operationally boring primitives support "
        "national deployment without vendor lock-in.",
        "reason": "PostgreSQL and Redis are self-hosted, replaceable, and meet the "
        "Free/Open-Source/Self-Hosted-first constitution.",
        "decision": "Use PostgreSQL as the primary store and Redis for caching and "
        "the task queue; both replaceable behind interfaces.",
        "alternatives": ["Managed cloud databases", "NoSQL primary store"],
        "trade_offs": [
            "PostgreSQL requires migration discipline",
            "Redis is memory-bound and needs eviction policy",
        ],
        "risk": "Operational tuning burden grows at national scale.",
        "cost": "Low — self-hosted OSS; operational expertise required.",
        "rollback": "Swap the cache/client behind existing interfaces.",
        "consequences": [
            "PostgreSQL primary store",
            "Redis caching and task queue",
        ],
        "adr_ref": "docs/adr/ADR-005-postgresql-redis-stack.md",
    },
    {
        "decision_id": "immutable-audit-log",
        "title": "Immutable audit log for clinical and administrative actions",
        "context": "Regulatory compliance (ISO 15189, CAP, CLSI) and national "
        "accountability require tamper-evident audit trails.",
        "reason": "Clinical safety and regulatory certification demand "
        "append-only, verifiable records of every significant action.",
        "decision": "Maintain an immutable, append-only audit log with "
        "verification capability for every clinical and administrative action.",
        "alternatives": ["Mutable audit tables", "Third-party audit SaaS"],
        "trade_offs": [
            "Append-only storage grows unboundedly",
            "Verification adds a small write-path cost",
        ],
        "risk": "Audit records could be tampered with if the store is compromised.",
        "cost": "Low — storage; requires retention policy.",
        "rollback": "Immutable by design; no rollback, retention pruning only.",
        "consequences": [
            "Append-only audit records",
            "Verification capability on every record",
        ],
        "adr_ref": "docs/adr/ADR-024-Platform-Constitution.md",
    },
    {
        "decision_id": "offline-first",
        "title": "Offline-first operations for laboratory continuity",
        "context": "Laboratories in underserved governorates cannot depend on "
        "continuous connectivity.",
        "reason": "Clinical continuity requires local-first data capture with "
        "reliable synchronization when connectivity returns.",
        "decision": "Design offline-first: local data capture, outbox-pattern "
        "synchronization, conflict-resolution policies.",
        "alternatives": ["Online-only operation", "Local terminals with nightly batch sync"],
        "trade_offs": [
            "Conflict resolution policies are complex",
            "Offline capture adds validation latency",
        ],
        "risk": "Synchronization conflicts across governorate partitions.",
        "cost": "Medium — sync engine and conflict policies.",
        "rollback": "Disable offline mode; revert to online-only.",
        "consequences": [
            "Local-first data capture",
            "Synchronization via outbox/event bus",
        ],
        "adr_ref": "docs/adr/ADR-024-Platform-Constitution.md",
    },
    {
        "decision_id": "arabic-first",
        "title": "Arabic-first user experience with RTL layout",
        "context": "The national platform serves Arabic-speaking clinical staff and "
        "citizens across Iraq.",
        "reason": "Usability and national mandate require Arabic as the primary "
        "interface language with correct RTL rendering.",
        "decision": 'Deliver Arabic-first UI with dir="rtl" in frontend-v3, '
        "with internationalization for every user-facing string.",
        "alternatives": ["English-first with Arabic later", "Bilingual from day one"],
        "trade_offs": [
            "RTL layout requires careful component design",
            "Translation keys add UI overhead",
        ],
        "risk": "Incomplete translation coverage for inactive contexts.",
        "cost": "Low-to-medium — i18n keying and RTL testing.",
        "rollback": "Flip locale preference; no schema change.",
        "consequences": [
            "Arabic as primary language",
            "RTL layout throughout frontend-v3",
        ],
        "adr_ref": "docs/adr/ADR-024-Platform-Constitution.md",
    },
    {
        "decision_id": "identity-platform",
        "title": "Centralized identity platform for all platform roles",
        "context": "Ministry, directorate, hospital, and laboratory hierarchies need "
        "a single identity authority with RBAC/ABAC.",
        "reason": "A single identity authority keeps authorization consistent "
        "across the national hierarchy and avoids credential fragmentation.",
        "decision": "Adopt the centralized identity platform (NIAM) as the single "
        "authority with RBAC and ABAC authorization.",
        "alternatives": ["Per-context identity stores", "Third-party identity SaaS"],
        "trade_offs": [
            "Single authority is a high-value target",
            "Federation adapters are required for national integration",
        ],
        "risk": "Identity coupling to the national federation roadmap.",
        "cost": "Medium — identity platform hardening and federation.",
        "rollback": "Adapter-based federation allows swapping the authority.",
        "consequences": [
            "Central identity authority",
            "RBAC and ABAC authorization",
        ],
        "adr_ref": "docs/adr/ADR-012-identity-platform.md",
    },
    {
        "decision_id": "event-bus",
        "title": "Event-driven integration between platform modules",
        "context": "Orders, results, notifications, and offline sync must react to "
        "domain events without hard coupling.",
        "reason": "Domain events decouple contexts and enable the outbox pattern "
        "for reliable publishing.",
        "decision": "Use a domain event bus with the outbox pattern for reliable "
        "event publishing across contexts.",
        "alternatives": ["Synchronous service calls everywhere", "Shared database integration"],
        "trade_offs": [
            "Eventual consistency across consumers",
            "Event schema versioning is required",
        ],
        "risk": "Event schema drift breaks consumers.",
        "cost": "Low-to-medium — bus + outbox infrastructure.",
        "rollback": "Revert to synchronous calls for affected flows.",
        "consequences": [
            "Domain events on a shared bus",
            "Outbox pattern for reliable publishing",
        ],
        "adr_ref": "docs/adr/ADR-024-Platform-Constitution.md",
    },
    {
        "decision_id": "national-ehr",
        "title": "National EHR compatibility (FHIR R4, SNDHS integration)",
        "context": "The platform must remain mergeable into future national health "
        "releases across all Iraqi governorates.",
        "reason": "National compatibility is a core mission requirement; "
        "government integration gateways keep the platform sovereign.",
        "decision": "Keep national EHR and SNDHS government integration on the "
        "roadmap with FHIR R4 contracts and gateway adapters.",
        "alternatives": ["Closed platform with no national integration", "Single national vendor stack"],
        "trade_offs": [
            "Gateway adapters add surface area",
            "National spec changes require adaptation",
        ],
        "risk": "Specification drift with national standards.",
        "cost": "High over 5 years — federation and compliance.",
        "rollback": "Gateway adapters isolate national dependencies.",
        "consequences": [
            "FHIR R4 national contracts",
            "Government integration gateways",
        ],
        "adr_ref": "docs/adr/ADR-010-sndhs-government-integration.md",
    },
)


def discover_adrs(root: Path | None = None) -> list[Path]:
    """Return existing ADR files from docs/adr/."""
    root = root or REPO_ROOT
    adr_dir = root / "docs" / "adr"
    if not adr_dir.exists():
        return []
    return sorted(adr_dir.glob("ADR-*.md"))


def _resolve_adr(root: Path, reference: str) -> str:
    """Map a decision reference to an existing ADR path or report missing."""
    if reference.startswith("docs/adr/"):
        candidate = root / reference
        return reference if candidate.exists() else f"{reference} (missing)"
    candidate = root / "docs" / "adr" / reference
    return f"docs/adr/{reference}" if candidate.exists() else f"docs/adr/{reference} (missing)"


def build_decisions(root: Path | None = None) -> list[ArchitectureDecision]:
    """Record the strategic decisions with their ADR linkage."""
    root = root or REPO_ROOT
    decisions: list[ArchitectureDecision] = []
    for record in STRATEGIC_DECISIONS:
        decision_id = str(record["decision_id"])
        adr_ref = str(record["adr_ref"])
        linked = _resolve_adr(root, adr_ref)
        if " (missing)" in linked:
            status = DecisionStatus.PROPOSED.value
        else:
            status = DecisionStatus.ACCEPTED.value
        decisions.append(ArchitectureDecision(
            decision_id=f"AD-{decision_id}",
            title=str(record["title"]),
            status=status,
            context=str(record["context"]),
            decision=str(record["decision"]),
            reason=str(record["reason"]),
            alternatives=[str(a) for a in record["alternatives"]],
            trade_offs=[str(t) for t in record["trade_offs"]],
            risk=str(record["risk"]),
            cost=str(record["cost"]),
            rollback=str(record["rollback"]),
            review_status="reviewed" if status == DecisionStatus.ACCEPTED.value
            else "pending-review",
            consequences=[str(c) for c in record["consequences"]],
        ))
    return decisions


def persist_decisions(root: Path | None = None) -> Path:
    """Persist decisions under state/decisions/ and return the path."""
    root = root or REPO_ROOT
    decisions = build_decisions(root)
    path = DECISION_DIR / "decisions.json"
    write_json(path, {
        "discovered_at": utcnow(),
        "adr_files": [p.relative_to(root).as_posix() for p in discover_adrs(root)],
        "decisions": [d.to_dict() for d in decisions],
    })
    return path


def render_markdown(decisions: list[ArchitectureDecision], adr_count: int) -> str:
    lines = [
        "# GULA-ARCHITECT-001 — Architectural Decisions",
        "",
        f"Generated: **{utcnow()}**",
        "",
        f"**{len(decisions)} strategic decisions** recorded against "
        f"**{adr_count}** existing ADR files.",
        "",
        "## Decision Records",
        "",
        "| Decision | Status | Review | Cost | Risk |",
        "|---|---|---|---|---|",
    ]
    for decision in decisions:
        lines.append(
            f"| `{decision.decision_id}` {decision.title} | {decision.status} | "
            f"{decision.review_status} | {decision.cost} | {decision.risk} |"
        )
    lines.extend(["", "## Details", ""])
    for decision in decisions:
        lines.append(f"### {decision.decision_id} — {decision.title}")
        lines.append("")
        lines.append(f"**Reason:** {decision.reason}")
        lines.append("")
        lines.append(f"**Decision:** {decision.decision}")
        lines.append("")
        lines.append(f"**Alternatives considered:** {', '.join(decision.alternatives)}")
        lines.append("")
        lines.append(f"**Trade-offs:** {', '.join(decision.trade_offs)}")
        lines.append("")
        lines.append(f"**Rollback strategy:** {decision.rollback}")
        lines.append("")
        for consequence in decision.consequences:
            lines.append(f"- Consequence: {consequence}")
        lines.append("")
    lines.append(f"**{sum(1 for d in decisions if d.status == 'accepted')} accepted, "
                 f"{sum(1 for d in decisions if d.status == 'proposed')} proposed.**")
    lines.append("")
    return "\n".join(lines)
