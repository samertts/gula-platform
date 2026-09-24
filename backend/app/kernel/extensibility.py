"""PROGRAM-EXT-001 — the normative contract a new capability is measured against.

This module adds no registry. GULA already has one that loads at boot
(`app.kernel.runtime.capability_registry.CapabilityRegistry`, populated by
`app.kernel.capabilities_registry_populator` with 52 descriptors), and a second
one would be the exact failure this programme exists to prevent. What was
missing was not storage but a *rule*: nothing said which metadata a capability
must declare, so descriptors could be registered with no owner, no tenancy
statement, no audit obligation and no test path, and nothing noticed.

So this module is three small things:

* `REQUIRED_FIELDS` — the normative set, one place, referenced by the guards.
* `validate_descriptor` — returns the violations for one descriptor. It returns
  them rather than raising, because the interesting question at this stage is
  "how far is the estate from the contract", and an exception answers only the
  first instance.
* `GlobalIntelligenceEntry` / `load_global_intelligence` — the structure
  PROGRAM-GLOBAL-001 will fill. The structure is established here; the research
  sweep is not done and the registry ships deliberately empty rather than
  pre-seeded with guesses.

A descriptor that predates the contract is not silently exempt. It is
*grandfathered explicitly*: `GRANDFATHERED` names the 52 that existed when the
contract was written, the guard asserts that the set never grows, and each one
is a debt with a name rather than an absence nobody is counting.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.kernel.types import (
    CapabilityDescriptor,
    CapabilityMaturity,
    FeatureFlagClass,
    TenantScope,
)

# ── The normative contract ────────────────────────────────────────────────────

#: Fields a capability registered after PROGRAM-EXT-001 must populate.
#: Deliberately short. Every entry here is something a reviewer cannot derive
#: from the code, so requiring it buys information rather than ceremony.
REQUIRED_FIELDS: tuple[str, ...] = (
    "capability_id",
    "name",
    "version",
    "owner",
    "description",
    "domain",
    "maturity",
    "tenant_scope",
    "documentation",
    "test_paths",
    "module_path",
)

#: Maturities that may not be reached without a populated deprecation notice.
_DEPRECATING = frozenset({CapabilityMaturity.DEPRECATED, CapabilityMaturity.RETIRED})

#: Data classifications that oblige a capability to write audit.
SENSITIVE_CLASSIFICATIONS = frozenset({"CLINICAL_SENSITIVE", "PII", "RESTRICTED"})

#: Maturities a feature flag class may legitimately accompany. A PRODUCTION
#: capability behind an EXPERIMENTAL flag is either mislabelled or a rollout
#: nobody finished; either way it should be visible.
_FLAG_FOR_MATURITY: dict[CapabilityMaturity, frozenset[FeatureFlagClass]] = {
    CapabilityMaturity.EXPERIMENTAL: frozenset({FeatureFlagClass.EXPERIMENTAL, FeatureFlagClass.INTERNAL}),
    CapabilityMaturity.INTERNAL: frozenset({FeatureFlagClass.INTERNAL, FeatureFlagClass.EXPERIMENTAL}),
    CapabilityMaturity.PILOT: frozenset({FeatureFlagClass.PILOT, FeatureFlagClass.INTERNAL}),
    CapabilityMaturity.VALIDATED: frozenset({FeatureFlagClass.PILOT, FeatureFlagClass.PRODUCTION}),
    CapabilityMaturity.PRODUCTION: frozenset({FeatureFlagClass.PRODUCTION, FeatureFlagClass.NATIONAL}),
    CapabilityMaturity.NATIONAL: frozenset({FeatureFlagClass.NATIONAL, FeatureFlagClass.PRODUCTION}),
    CapabilityMaturity.DEPRECATED: frozenset({FeatureFlagClass.DEPRECATED, FeatureFlagClass.PRODUCTION}),
}


#: The 52 capabilities that were already registered when this contract was
#: written. Each fails it on the same four fields — `capability_id`,
#: `documentation`, `test_paths` and `module_path` — which is itself the
#: finding: nothing in the registry points at the code, the tests or the docs
#: that implement it, so a descriptor cannot currently be checked against
#: reality. Backfilling them is a separate piece of work with an owner per
#: domain. What this set does is stop the debt growing: the guard asserts that
#: no capability outside it is registered incomplete, and that the set itself
#: never gains a member.
GRANDFATHERED: frozenset[str] = frozenset({
    "admin_console", "analytics", "audit_logging", "authentication", "authorization_rbac",
    "background_processing", "claims_processing", "clinical_foundation",
    "clinical_intelligence", "compliance", "consent_management", "critical_alerting",
    "device_integration", "document_management", "edge_platform", "ehr_integration",
    "encounter_management", "encryption_service", "event_bus", "feature_flags",
    "fhir_interoperability", "health_checks", "healthcare_consent", "id_scanning",
    "insurance_integration", "intrusion_detection", "lab_management",
    "master_patient_index", "metrics_collection", "multi_tenant", "national_identity",
    "notification_service", "order_management", "outbox_pattern", "patient_card",
    "patient_management", "pdf_reporting", "prometheus_integration", "provider_management",
    "quality_control", "rate_limiting", "redis_cache", "reporting_service",
    "result_management", "sample_tracking", "search_service", "self_healing",
    "session_management", "sndhs_integration", "storage_service", "subscription_tiers",
    "workflow_engine"
})


def validate_descriptor(descriptor: CapabilityDescriptor) -> list[str]:
    """Return every way `descriptor` fails the contract. Empty means it passes."""
    violations: list[str] = []

    for field_name in REQUIRED_FIELDS:
        value = getattr(descriptor, field_name, None)
        if value in (None, "", [], {}):
            violations.append(f"{field_name} is not declared")

    if not isinstance(descriptor.maturity, CapabilityMaturity):
        violations.append("maturity is not a CapabilityMaturity")
    if not isinstance(descriptor.tenant_scope, TenantScope):
        violations.append("tenant_scope is not a TenantScope")

    # A capability on its way out owes its consumers a destination and a date.
    if descriptor.maturity in _DEPRECATING and not descriptor.deprecation.is_declared():
        violations.append(
            f"maturity is {descriptor.maturity.value} but no deprecation "
            "(since_version, removal_version, replacement) is declared",
        )

    # Sensitive data obliges an audit trail. This is the one rule here that is
    # a safety property rather than a documentation property.
    if (
        descriptor.audit.data_classification in SENSITIVE_CLASSIFICATIONS
        and not descriptor.audit.writes_audit
    ):
        violations.append(
            f"data_classification is {descriptor.audit.data_classification} "
            "but the capability does not declare that it writes audit",
        )

    # A capability that names permissions but no tenancy, or claims PLATFORM
    # scope while naming tenant permissions, is ambiguous at the boundary that
    # matters most.
    if descriptor.required_permissions and descriptor.tenant_scope is TenantScope.NATIONAL_REFERENCE:
        violations.append(
            "tenant_scope is national_reference (no tenant) yet required_permissions "
            "are declared; state the scope the permissions are evaluated in",
        )

    allowed_flags = _FLAG_FOR_MATURITY.get(descriptor.maturity)
    if allowed_flags is not None and descriptor.flag_class not in allowed_flags:
        violations.append(
            f"flag_class {descriptor.flag_class.value} does not match maturity "
            f"{descriptor.maturity.value}",
        )

    return violations


def validate_registry(descriptors: list[CapabilityDescriptor]) -> dict[str, list[str]]:
    """Validate many, returning only those with violations."""
    report: dict[str, list[str]] = {}
    for descriptor in descriptors:
        violations = validate_descriptor(descriptor)
        if violations:
            report[descriptor.name] = violations
    return report


# ── PROGRAM-GLOBAL-001 foundation ─────────────────────────────────────────────

GLOBAL_INTELLIGENCE_PATH = (
    Path(__file__).resolve().parents[3]
    / "docs"
    / "architecture"
    / "extensibility"
    / "global-intelligence-registry.json"
)

#: The only four verdicts an entry may carry. ADOPT means take it as-is; ADAPT
#: means the idea holds but the implementation must change for Iraq; INSPIRE
#: means read it and design our own; REJECT means recorded so nobody proposes
#: it again without reading why.
RECOMMENDATIONS = ("ADOPT", "ADAPT", "INSPIRE", "REJECT")

#: How confident we are in the *evidence*, separately from the recommendation.
#: A strong recommendation on weak evidence is the failure mode this prevents.
EVIDENCE_QUALITY = ("PEER_REVIEWED", "OFFICIAL_REPORT", "VENDOR_CLAIM", "ANECDOTAL", "UNKNOWN")


@dataclass
class GlobalIntelligenceEntry:
    """One studied health system, standard or implementation."""

    entry_id: str
    source: str
    country: str
    system: str
    domain: str
    architecture: str = ""
    scale: str = ""
    standards: list[str] = field(default_factory=list)
    interoperability: str = ""
    security: str = ""
    privacy: str = ""
    governance: str = ""
    success_factors: list[str] = field(default_factory=list)
    failure_modes: list[str] = field(default_factory=list)
    evidence_quality: str = "UNKNOWN"
    licence: str = ""
    gula_relevance: str = ""
    recommendation: str = "INSPIRE"

    def violations(self) -> list[str]:
        problems: list[str] = []
        for required in ("entry_id", "source", "country", "system", "domain"):
            if not getattr(self, required):
                problems.append(f"{required} is not declared")
        if self.recommendation not in RECOMMENDATIONS:
            problems.append(f"recommendation {self.recommendation!r} is not one of {RECOMMENDATIONS}")
        if self.evidence_quality not in EVIDENCE_QUALITY:
            problems.append(f"evidence_quality {self.evidence_quality!r} is not one of {EVIDENCE_QUALITY}")
        # A verdict of ADOPT on unknown evidence is how a rumour becomes a
        # roadmap item. Recorded as a violation rather than a warning.
        if self.recommendation == "ADOPT" and self.evidence_quality in ("ANECDOTAL", "UNKNOWN"):
            problems.append("recommendation is ADOPT but the evidence is anecdotal or unknown")
        if not self.licence:
            problems.append("licence is not declared (Free/Open Source First needs it stated)")
        return problems


def load_global_intelligence(path: Path | None = None) -> list[GlobalIntelligenceEntry]:
    """Read the registry. An absent or empty registry is a valid, honest state."""
    source = path or GLOBAL_INTELLIGENCE_PATH
    if not source.exists():
        return []
    payload: dict[str, Any] = json.loads(source.read_text(encoding="utf-8"))
    return [GlobalIntelligenceEntry(**entry) for entry in payload.get("entries", [])]
