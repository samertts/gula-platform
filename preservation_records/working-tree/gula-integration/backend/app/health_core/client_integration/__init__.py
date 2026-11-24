"""Client integration READINESS contracts — per-platform manifests and validators.

This package is a **contract/inspection layer only**. It never imports a client
application, never modifies one, and does not activate a route, a production
service, a database, a broker or any real patient identity. It turns read-only
observations of the client trees in this checkout into structured, fail-closed
manifests that are checked against the WS-C operation catalogue and the WS-D
readiness contracts.

A validated manifest means *the declaration is complete and truthful about what
was observed*. It never means a client is end-to-end integrated.
"""

from app.health_core.client_integration.manifests import (
    DEFAULT_MANIFESTS,
    AuthDeclaration,
    ClientManifest,
    ErrorDeclaration,
    OfflineDeclaration,
    RtlA11yDeclaration,
    SyncDeclaration,
    derive_implementation_status,
    manifest_for,
)
from app.health_core.client_integration.observations import (
    OBSERVED_CLIENTS,
    ClientObservation,
    ObservationVerification,
    ObservedLayer,
    observation_for,
    verify_observation,
)
from app.health_core.client_integration.platforms import (
    IMPLEMENTED,
    REQUIRED_LAYERS,
    ImplementationStatus,
    LayerKey,
    LayerStatus,
    Platform,
)
from app.health_core.client_integration.report import (
    PlatformCoverage,
    build_coverage_report,
    render_coverage_report,
)
from app.health_core.client_integration.validators import (
    ManifestValidation,
    canonical_operations,
    validate_all_manifests,
    validate_manifest,
)

__all__ = [
    "DEFAULT_MANIFESTS",
    "IMPLEMENTED",
    "OBSERVED_CLIENTS",
    "REQUIRED_LAYERS",
    "AuthDeclaration",
    "ClientManifest",
    "ClientObservation",
    "ErrorDeclaration",
    "ImplementationStatus",
    "LayerKey",
    "LayerStatus",
    "ManifestValidation",
    "ObservationVerification",
    "ObservedLayer",
    "OfflineDeclaration",
    "Platform",
    "PlatformCoverage",
    "RtlA11yDeclaration",
    "SyncDeclaration",
    "build_coverage_report",
    "canonical_operations",
    "derive_implementation_status",
    "manifest_for",
    "observation_for",
    "render_coverage_report",
    "validate_all_manifests",
    "validate_manifest",
    "verify_observation",
]
