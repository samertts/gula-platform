"""Phase 1 — System Model.

Build a deterministic system model of the GULA platform: bounded contexts
discovered from the backend (services, routes, models), entities from the
model layer, relationships between contexts, and trust boundaries. The
model is persisted under state/model/ and feeds every later phase.
"""

from __future__ import annotations

from pathlib import Path

from scripts.architect.core import (
    BOUNDED_CONTEXT_SEEDS,
    MODEL_DIR,
    BoundedContext,
    ContextRelationship,
    write_json,
)
from scripts.kernel.core import REPO_ROOT, utcnow

# Context -> trust boundary mapping (mirrors the platform's security model).
CONTEXT_TRUST: dict[str, str] = {
    "identity": "authenticated",
    "patient": "authenticated",
    "consent": "authenticated",
    "lab": "internal",
    "sample": "internal",
    "order": "internal",
    "result": "internal",
    "quality-control": "internal",
    "claim": "internal",
    "communication": "external",
    "dashboard": "authenticated",
    "admin": "internal",
}

# Context -> subdomains (core/supporting/generic classification).
CONTEXT_SUBDOMAINS: dict[str, tuple[str, ...]] = {
    "identity": ("core", "authentication", "authorization", "hierarchy"),
    "patient": ("core", "registration", "demographics", "mpi"),
    "consent": ("core", "privacy", "authorization"),
    "lab": ("core", "catalog", "tiering", "management"),
    "sample": ("supporting", "collection", "tracking", "chain-of-custody"),
    "order": ("supporting", "ordering", "requisition"),
    "result": ("core", "verification", "validation", "critical-alerting"),
    "quality-control": ("supporting", "westgard", "qc-rules", "audit"),
    "claim": ("supporting", "billing", "idempotency", "outbox"),
    "communication": ("generic", "notifications", "providers"),
    "dashboard": ("supporting", "analytics", "summary"),
    "admin": ("supporting", "platform-admin", "audit-log"),
}

# Per-context data-flow and control-flow descriptions (Phase 1).
CONTEXT_FLOWS: dict[str, tuple[str, str]] = {
    "identity": (
        "Authenticated identity, RBAC/ABAC decisions, hierarchy scopes",
        "Token issuance, permission checks, hierarchical delegation",
    ),
    "patient": (
        "Demographics, MPI resolution, family memberships",
        "Patient creation/update events over the event bus",
    ),
    "consent": (
        "Consent policies governing data access",
        "Consent grants/revocations published for downstream consumers",
    ),
    "lab": (
        "Lab catalog, tiers, employees, equipment",
        "Lab CRUD operations and capability registration",
    ),
    "sample": (
        "Sample records, collection metadata, chain of custody",
        "Sample lifecycle transitions (collected, in-transit, received)",
    ),
    "order": (
        "Orders, requisitions, order status",
        "Order placement and status events",
    ),
    "result": (
        "Results, verification, critical flags",
        "Result verification, Westgard flagging, critical alerting",
    ),
    "quality-control": (
        "QC measurements, rules, flags",
        "QC evaluation events and rule violations",
    ),
    "claim": (
        "Claims, line items, idempotency keys",
        "Claim submission to the outbox / national gateway",
    ),
    "communication": (
        "Notification templates and delivery state",
        "Provider dispatch (email, sms, push, webhook)",
    ),
    "dashboard": (
        "Aggregated statistics and summaries",
        "Read-only analytics queries with Redis caching",
    ),
    "admin": (
        "Platform-wide configuration and audit records",
        "Admin CRUD with immutable audit trail",
    ),
}


def _scan_packages(root: Path) -> dict[str, list[str]]:
    """Map bounded-context seed -> backend modules that implement it."""
    service_dir = root / "backend" / "app" / "services"
    model_dir = root / "backend" / "app" / "models"
    route_dir = root / "backend" / "app" / "routes"
    mapping: dict[str, list[str]] = {}
    for seed in BOUNDED_CONTEXT_SEEDS:
        parts: list[str] = []
        for directory in (service_dir, model_dir, route_dir):
            if not directory.exists():
                continue
            for path in sorted(directory.rglob("*.py")):
                if path.name == "__init__.py":
                    continue
                if seed.replace("-", "_") in path.name:
                    parts.append(path.relative_to(root).as_posix())
        if parts:
            mapping[seed] = parts
    return mapping


def _entities(root: Path) -> dict[str, list[str]]:
    """Map bounded-context seed -> entity class names from the model layer."""
    model_dir = root / "backend" / "app" / "models"
    entities: dict[str, list[str]] = {}
    if not model_dir.exists():
        return entities
    for seed in BOUNDED_CONTEXT_SEEDS:
        names: list[str] = []
        needle = seed.replace("-", "_")
        for path in sorted(model_dir.rglob("*.py")):
            if path.name == "__init__.py":
                continue
            if needle in path.name:
                for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
                    stripped = line.strip()
                    if stripped.startswith("class ") and "(" in stripped:
                        class_name = (
                            stripped.split("class ")[1].split("(")[0].strip().rstrip(":")
                        )
                        names.append(class_name)
        if names:
            entities[seed] = names
    return entities


def _relationships(mapping: dict[str, list[str]]) -> list[ContextRelationship]:
    """Infer relationships between contexts from module co-location evidence."""
    relationships: list[ContextRelationship] = []
    for source in BOUNDED_CONTEXT_SEEDS:
        source_files = {Path(p).name for p in mapping.get(source, [])}
        for target in BOUNDED_CONTEXT_SEEDS:
            if source == target:
                continue
            target_files = {Path(p).name for p in mapping.get(target, [])}
            overlap = source_files & target_files
            if overlap:
                data_flow, control_flow = CONTEXT_FLOWS.get(target, ("", ""))
                relationships.append(ContextRelationship(
                    source=source,
                    target=target,
                    kind="shares-data",
                    note="co-located modules: " + ", ".join(sorted(overlap)[:3]),
                    data_flow=data_flow,
                    control_flow=control_flow,
                ))
    return relationships


def build_model(root: Path | None = None) -> list[BoundedContext]:
    """Discover bounded contexts and return them deterministically."""
    root = root or REPO_ROOT
    mapping = _scan_packages(root)
    entities = _entities(root)
    contexts: list[BoundedContext] = []
    for seed in BOUNDED_CONTEXT_SEEDS:
        modules = mapping.get(seed, [])
        if not modules:
            continue
        data_flow, control_flow = CONTEXT_FLOWS.get(seed, ("", ""))
        contexts.append(BoundedContext(
            name=seed,
            description=f"Bounded context governing the {seed} domain.",
            modules=modules,
            entities=entities.get(seed, []),
            subdomains=list(CONTEXT_SUBDOMAINS.get(seed, ())),
            data_flow=data_flow,
            control_flow=control_flow,
            trust_boundary=CONTEXT_TRUST.get(seed, "internal"),
            discovered_at=utcnow(),
        ))
    return contexts


def build_relationships(root: Path | None = None) -> list[ContextRelationship]:
    """Infer cross-context relationships deterministically."""
    root = root or REPO_ROOT
    mapping = _scan_packages(root)
    return _relationships(mapping)


def persist_model(root: Path | None = None) -> tuple[Path, Path]:
    """Persist contexts and relationships under state/model/."""
    root = root or REPO_ROOT
    contexts = build_model(root)
    relationships = build_relationships(root)
    contexts_path = MODEL_DIR / "contexts.json"
    relationships_path = MODEL_DIR / "relationships.json"
    write_json(contexts_path, {
        "discovered_at": utcnow(),
        "contexts": [c.to_dict() for c in contexts],
    })
    write_json(relationships_path, {
        "discovered_at": utcnow(),
        "relationships": [r.to_dict() for r in relationships],
    })
    return contexts_path, relationships_path


def render_markdown(contexts: list[BoundedContext], relationships: list[ContextRelationship]) -> str:
    lines = [
        "# GULA-ARCHITECT-001 — System Model",
        "",
        f"Generated: **{utcnow()}**",
        "",
        f"**{len(contexts)} bounded contexts** detected in the backend.",
        "",
        "## Bounded Contexts",
        "",
        "| Context | Trust boundary | Subdomains | Entities | Modules |",
        "|---|---|---|---|---|",
    ]
    for context in contexts:
        lines.append(
            f"| {context.name} | {context.trust_boundary} | "
            f"{', '.join(context.subdomains)} | "
            f"{len(context.entities)} | {len(context.modules)} |"
        )
    lines.extend([
        "",
        "## Data Flow",
        "",
        "| Context | Data flow | Control flow |",
        "|---|---|---|",
    ])
    for context in contexts:
        data_flow, control_flow = CONTEXT_FLOWS.get(context.name, ("", ""))
        lines.append(f"| {context.name} | {data_flow} | {control_flow} |")
    lines.extend([
        "",
        "## Trust Boundaries",
        "",
        "| Boundary | Purpose |",
        "|---|---|",
        "| public | Unauthenticated entry points (login, public catalog) |",
        "| authenticated | Requires verified user identity (patient-facing) |",
        "| internal | Internal service-to-service (lab, orders, results) |",
        "| data-store | Database, cache, object storage access |",
        "| external | Outbound integrations (analyzer, messaging, national) |",
        "",
        "## Cross-Context Relationships",
        "",
    ])
    if relationships:
        for relationship in relationships:
            lines.append(
                f"- `{relationship.source}` {relationship.kind} `{relationship.target}`"
            )
    else:
        lines.append("- No shared-module relationships detected.")
    lines.append("")
    return "\n".join(lines)
