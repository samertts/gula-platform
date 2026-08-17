"""Safe, synthetic-only FHIR R4 exchange contracts for GULA staging.

This module deliberately contains no persistence and no write operation. It is a
contract boundary for conformance tests and synthetic integration demos while the
clinical gateway remains blocked by P4/P5 governance.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

FHIR_R4 = "4.0.1"
FHIR_JSON = "application/fhir+json"
SYNTHETIC_TAG_SYSTEM = "urn:gula:dataset"
SYNTHETIC_TAG_CODE = "synthetic"

READ_ONLY_RESOURCE_TYPES = (
    "Patient",
    "Organization",
    "Practitioner",
    "PractitionerRole",
    "ServiceRequest",
    "Specimen",
    "Observation",
    "DiagnosticReport",
    "DocumentReference",
    "Provenance",
    "AuditEvent",
)


class FHIRExchangeBlocked(PermissionError):
    """Raised when the server-side rollout gate denies an exchange."""


class FHIRContractError(ValueError):
    """Raised when a synthetic FHIR payload violates the exchange contract."""


class AuditRecorder(Protocol):
    def record(self, *, action: str, outcome: str, resource_type: str, resource_id: str) -> None:
        """Record an allow/deny decision without storing clinical values."""


@dataclass(frozen=True)
class AuditDecision:
    action: str
    outcome: str
    resource_type: str
    resource_id: str


@dataclass
class InMemoryAuditRecorder:
    decisions: list[AuditDecision] = field(default_factory=list)

    def record(self, *, action: str, outcome: str, resource_type: str, resource_id: str) -> None:
        self.decisions.append(AuditDecision(action, outcome, resource_type, resource_id))


def _synthetic_meta() -> dict[str, Any]:
    return {
        "tag": [{"system": SYNTHETIC_TAG_SYSTEM, "code": SYNTHETIC_TAG_CODE}],
    }


def synthetic_bundle() -> dict[str, Any]:
    """Return deterministic, non-identifying data for staging conformance tests."""
    patient = {
        "resourceType": "Patient",
        "id": "synthetic-patient-001",
        "meta": _synthetic_meta(),
        "name": [{"text": "Synthetic Test Patient"}],
        "gender": "unknown",
    }
    organization = {
        "resourceType": "Organization",
        "id": "synthetic-facility-001",
        "meta": _synthetic_meta(),
        "active": True,
        "name": "Synthetic GULA Facility",
    }
    request = {
        "resourceType": "ServiceRequest",
        "id": "synthetic-request-001",
        "meta": _synthetic_meta(),
        "status": "active",
        "intent": "order",
        "subject": {"reference": "Patient/synthetic-patient-001"},
        "requester": {"reference": "Practitioner/synthetic-practitioner-001"},
        "code": {"text": "Synthetic laboratory panel"},
    }
    specimen = {
        "resourceType": "Specimen",
        "id": "synthetic-specimen-001",
        "meta": _synthetic_meta(),
        "status": "available",
        "subject": {"reference": "Patient/synthetic-patient-001"},
        "request": [{"reference": "ServiceRequest/synthetic-request-001"}],
    }
    observation = {
        "resourceType": "Observation",
        "id": "synthetic-observation-001",
        "meta": _synthetic_meta(),
        "status": "final",
        "code": {"text": "Synthetic observation"},
        "subject": {"reference": "Patient/synthetic-patient-001"},
        "specimen": {"reference": "Specimen/synthetic-specimen-001"},
        "valueString": "synthetic-result",
    }
    report = {
        "resourceType": "DiagnosticReport",
        "id": "synthetic-report-001",
        "meta": _synthetic_meta(),
        "status": "final",
        "code": {"text": "Synthetic laboratory report"},
        "subject": {"reference": "Patient/synthetic-patient-001"},
        "result": [{"reference": "Observation/synthetic-observation-001"}],
    }
    return {
        "resourceType": "Bundle",
        "id": "synthetic-bundle-001",
        "type": "collection",
        "meta": _synthetic_meta(),
        "entry": [{"resource": resource} for resource in (patient, organization, request, specimen, observation, report)],
    }


def _is_synthetic(resource: dict[str, Any]) -> bool:
    tags = resource.get("meta", {}).get("tag", [])
    return any(tag.get("system") == SYNTHETIC_TAG_SYSTEM and tag.get("code") == SYNTHETIC_TAG_CODE for tag in tags)


def validate_synthetic_bundle(bundle: dict[str, Any]) -> list[str]:
    """Validate the intentionally small, synthetic-only staging contract."""
    errors: list[str] = []
    if bundle.get("resourceType") != "Bundle":
        errors.append("resourceType must be Bundle")
    if bundle.get("type") != "collection":
        errors.append("bundle type must be collection")
    if not _is_synthetic(bundle):
        errors.append("bundle must be explicitly tagged as synthetic")
    entries = bundle.get("entry")
    if not isinstance(entries, list) or not entries:
        errors.append("bundle must contain entries")
        return errors
    for index, entry in enumerate(entries):
        resource = entry.get("resource") if isinstance(entry, dict) else None
        if not isinstance(resource, dict):
            errors.append(f"entry[{index}] must contain a resource")
            continue
        resource_type = resource.get("resourceType")
        if resource_type not in READ_ONLY_RESOURCE_TYPES:
            errors.append(f"entry[{index}] resource type is not allowed: {resource_type}")
        if not resource.get("id"):
            errors.append(f"entry[{index}] resource id is required")
        if not _is_synthetic(resource):
            errors.append(f"entry[{index}] resource must be explicitly tagged as synthetic")
    return errors


def capability_statement() -> dict[str, Any]:
    """Return the public contract: read/search only, with no clinical writes."""
    return {
        "resourceType": "CapabilityStatement",
        "id": "gula-national-staging-r4",
        "status": "draft",
        "fhirVersion": FHIR_R4,
        "format": ["json"],
        "rest": [{
            "mode": "server",
            "resource": [
                {"type": resource_type, "interaction": [{"code": "read"}, {"code": "search"}]}
                for resource_type in READ_ONLY_RESOURCE_TYPES
            ],
        }],
    }


@dataclass
class SyntheticFHIRReadOnlyExchange:
    """Read-only exchange used only with explicit server-side enablement."""

    enabled: bool = False
    audit: AuditRecorder = field(default_factory=InMemoryAuditRecorder)
    _bundle: dict[str, Any] = field(default_factory=synthetic_bundle)

    def read_bundle(self, *, resource_type: str = "Bundle", resource_id: str = "synthetic-bundle-001") -> dict[str, Any]:
        if not self.enabled:
            self.audit.record(action="fhir.synthetic.read", outcome="denied", resource_type=resource_type, resource_id=resource_id)
            raise FHIRExchangeBlocked("synthetic FHIR exchange is disabled by server policy")
        errors = validate_synthetic_bundle(self._bundle)
        if errors:
            self.audit.record(action="fhir.synthetic.read", outcome="rejected", resource_type=resource_type, resource_id=resource_id)
            raise FHIRContractError("; ".join(errors))
        if resource_type != "Bundle" or resource_id != self._bundle["id"]:
            self.audit.record(action="fhir.synthetic.read", outcome="not_found", resource_type=resource_type, resource_id=resource_id)
            raise KeyError(f"synthetic resource not found: {resource_type}/{resource_id}")
        self.audit.record(action="fhir.synthetic.read", outcome="allowed", resource_type=resource_type, resource_id=resource_id)
        return self._bundle

    def write(self, *_: Any, **__: Any) -> None:
        self.audit.record(action="fhir.synthetic.write", outcome="denied", resource_type="unknown", resource_id="unknown")
        raise FHIRExchangeBlocked("synthetic exchange is read-only")
