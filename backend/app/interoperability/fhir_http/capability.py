"""FHIR R4 CapabilityStatement for the local T6 evidence surface.

The statement is deliberately honest: it lists only the resource types and
interactions that this router actually implements, is marked experimental, and
names the synthetic local namespace. It is a conformance *statement* for local
evidence only, not a claim of external interoperability validation.
"""

from __future__ import annotations

from typing import Final

__all__ = ["CAPABILITY_DATE", "SUPPORTED_INTERACTIONS", "build_capability_statement"]

CAPABILITY_DATE: Final[str] = "2026-11-18"

# Must stay in lockstep with the routes in router.py.
SUPPORTED_INTERACTIONS: Final[dict[str, tuple[str, ...]]] = {
    "Patient": ("read", "vread", "search-type"),
    "Observation": ("read", "vread", "search-type", "create", "update"),
}


def build_capability_statement() -> dict[str, object]:
    """Return a deterministic FHIR R4 CapabilityStatement dictionary."""
    resources: list[dict[str, object]] = []
    for resource_type, interactions in SUPPORTED_INTERACTIONS.items():
        resources.append(
            {
                "type": resource_type,
                "interaction": [{"code": code} for code in interactions],
                "searchParam": (
                    [{"name": "identifier", "type": "token"}, {"name": "name", "type": "string"}]
                    if resource_type == "Patient"
                    else [{"name": "identifier", "type": "token"}]
                ),
                "versioning": "versioned",
                "readHistory": True,
            }
        )
    return {
        "resourceType": "CapabilityStatement",
        "id": "gula-phase-b-t6-synthetic",
        "status": "active",
        "experimental": True,
        "date": CAPABILITY_DATE,
        "publisher": "GULA National Integration Program / Phase B / T6 (local evidence only)",
        "kind": "instance",
        "software": {
            "name": "gula-fhir-http-local-evidence",
            "version": "0.1.0",
            "releaseDescription": "Synthetic in-memory FHIR R4 HTTP surface; not production-activated",
        },
        "fhirVersion": "4.0.1",
        "format": ["json", "application/fhir+json"],
        "rest": [
            {
                "mode": "server",
                "documentation": (
                    "Local, non-activated evidence surface. Synthetic data only. "
                    "Header-based principal is a test fixture, not an identity provider."
                ),
                "resource": resources,
            }
        ],
    }
