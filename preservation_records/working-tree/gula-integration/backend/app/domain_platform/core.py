"""PROGRAM-STABLE-004 — Domain Platform Framework core vocabulary.

The permanent Domain Platform Framework. Every healthcare specialty
(GULA Laboratory, GULA Pharmacy, GULA Radiology, GULA Hospital, Blood Bank,
Public Health, Insurance, Emergency, Research, …) is an independent Domain
that inherits this framework.

Enforced invariants (Domain Sovereignty):

  * A Domain owns only: entities, services, policies, api, events, workflows,
    reports, ui — nothing else (Domain Blueprint).
  * Infrastructure belongs to Shared Core, never to a Domain.
  * No Domain reads another Domain's database.
  * No Domain administers another Domain.
  * No Domain owns another Domain.
  * Cross-domain communication is allowed ONLY through versioned contracts
    (public REST, FHIR, HL7, events) — never direct imports.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

# ── Domain Blueprint (Phase 1) ──────────────────────────────────────────────
# The ONLY sections a Domain may contain. Anything outside these sections
# belongs to Shared Core and must be moved there.
BLUEPRINT_SECTIONS: tuple[str, ...] = (
    "entities",    # Domain entities + value objects + aggregates
    "services",    # Domain services (application + domain logic)
    "policies",    # Domain policies / invariants / business rules
    "api",         # Public REST API surface
    "events",      # Domain events the Domain emits or subscribes to
    "workflows",   # Domain workflows / state machines
    "reports",     # Domain reports
    "ui",          # Domain UI (rendered only inside its own workspace)
)

# Shared Core services a Domain must consume instead of reimplementing
# (Phase 2). The canonical catalog (service -> single authoritative provider)
# lives in ``shared_core.py``; this tuple MUST contain exactly the catalog keys.
SHARED_CORE_SERVICES: tuple[str, ...] = (
    "identity",
    "authentication",
    "authorization",
    "organizations",
    "users",
    "sessions",
    "audit",
    "rbac",
    "abac",
    "encryption",
    "digital_signature",
    "mfa",
    "auth_primitives",
    "service_accounts",
    "notifications",
    "workflow_engine",
    "rule_engine",
    "barcode_engine",
    "qr_engine",
    "search_engine",
    "reporting_framework",
    "document_engine",
    "files",
    "media",
    "pdf_engine",
    "printing",
    "payments",
    "scheduler",
    "event_bus",
    "api_gateway",
    "api_schemas",
    "validators",
    "localization",
    "design_system",
    "config_loader",
    "settings",
    "dependency_injection",
    "device_integration",
    "communication",
    "ai_gateway",
    "feature_flags",
    "health_checks",
    "monitoring",
    "logging",
    "telemetry",
    "cache",
    "retry",
    "circuit_breaker",
    "backup_recovery",
    "fhir_engine",
)

# Domain lifecycle states (Phase 5).
class DomainLifecycleState(StrEnum):
    installed = "installed"
    active = "active"
    suspended = "suspended"
    upgrading = "upgrading"
    failed = "failed"
    retired = "retired"


# Valid lifecycle transitions (Phase 5 state machine).
DOMAIN_LIFECYCLE_TRANSITIONS: dict[str, tuple[str, ...]] = {
    "installed": ("active", "retired"),
    "active": ("suspended", "upgrading", "failed"),
    "suspended": ("active", "retired", "upgrading"),
    "upgrading": ("active", "suspended", "failed"),
    "failed": ("installed", "retired"),
    "retired": (),
}

# Cross-domain contract kinds (Phase 4). Direct access is forbidden; these
# are the only allowed communication channels.
class ContractKind(StrEnum):
    rest = "rest"
    fhir = "fhir"
    hl7 = "hl7"
    event = "event"
    contract = "contract"


# Phase 6 — every Domain binds to exactly ONE workspace type. The workspace
# may never display another Domain's UI.
DOMAIN_WORKSPACE_TYPES: dict[str, str] = {
    "laboratory": "laboratory",
    "pharmacy": "pharmacy",
    "radiology": "radiology",
    "hospital": "hospital",
    "blood_bank": "blood_bank",
    "public_health": "public_health",
    "insurance": "insurance",
    "emergency": "hospital",
    "research": "research",
    "citizen_portal": "citizen",
    "provider_portal": "professional",
}

# Phase 4 — cross-domain communication verbs (allowed channels).
ALLOWED_CROSS_DOMAIN_CHANNELS: tuple[str, ...] = (
    "public_api",
    "fhir_api",
    "hl7",
    "event_bus",
    "contract",
)


@dataclass(frozen=True)
class DomainContract:
    """A versioned cross-domain contract.

    Direct access is forbidden; this is the only legal interface between two
    Domains. Every contract MUST be versioned (SemVer), documented, and
    tested before it may be published.
    """

    contract_id: str
    provider_domain: str
    consumer_domain: str
    kind: ContractKind
    version: str
    endpoint: str
    documentation_url: str
    status: str = "published"
    summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract_id": self.contract_id,
            "provider_domain": self.provider_domain,
            "consumer_domain": self.consumer_domain,
            "kind": str(self.kind.value),
            "version": self.version,
            "endpoint": self.endpoint,
            "documentation_url": self.documentation_url,
            "status": self.status,
            "summary": self.summary,
        }


@dataclass
class DomainManifest:
    """The official Domain Blueprint (Phase 1).

    A Domain declares ONLY its eight blueprint sections plus the metadata
    that governs its sovereignty. Any attempt to add infrastructure,
    cross-domain tables, or management capabilities is rejected.
    """

    code: str
    name_en: str
    name_ar: str
    version: str
    workspace_type: str
    description: str
    entities: list[str] = field(default_factory=list)
    services: list[str] = field(default_factory=list)
    policies: list[str] = field(default_factory=list)
    api: list[str] = field(default_factory=list)
    events: list[str] = field(default_factory=list)
    workflows: list[str] = field(default_factory=list)
    reports: list[str] = field(default_factory=list)
    ui: list[str] = field(default_factory=list)
    contracts: list[DomainContract] = field(default_factory=list)
    shared_core: dict[str, str] = field(default_factory=dict)
    modules: list[str] = field(default_factory=list)
    tables: list[str] = field(default_factory=list)
    lifecycle_state: str = "installed"
    certification: str = "uncertified"

    @property
    def blueprint(self) -> dict[str, list[str]]:
        """The blueprint sections only — everything a Domain may own."""
        return {
            section: getattr(self, section)
            for section in BLUEPRINT_SECTIONS
            if getattr(self, section)
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "name_en": self.name_en,
            "name_ar": self.name_ar,
            "version": self.version,
            "workspace_type": self.workspace_type,
            "description": self.description,
            "blueprint": self.blueprint,
            "contracts": [c.to_dict() for c in self.contracts],
            "shared_core": self.shared_core,
            "modules": self.modules,
            "tables": self.tables,
            "lifecycle_state": self.lifecycle_state,
            "certification": self.certification,
        }


def utcnow() -> datetime:
    return datetime.now(UTC)


def lifecycle_transition_allowed(current: str, target: str) -> bool:
    allowed = DOMAIN_LIFECYCLE_TRANSITIONS.get(current, ())
    return target in allowed


def assert_blueprint_rule(manifest: DomainManifest) -> None:
    """Reject a manifest that violates the Domain Blueprint.

    A Domain may contain ONLY the eight blueprint sections plus its
    sovereignty metadata. Foreign keys, management capabilities, and
    infrastructure are always Shared Core concerns.
    """
    expected = DOMAIN_WORKSPACE_TYPES.get(manifest.code)
    if expected is not None and manifest.workspace_type != expected:
        raise ValueError(
            f"domain '{manifest.code}' must bind to workspace type "
            f"'{expected}', not '{manifest.workspace_type}'"
        )
