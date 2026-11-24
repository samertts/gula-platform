"""Application integration READINESS contracts (synthetic development only).

This subpackage contains framework-agnostic contracts and in-memory fakes for
client integration. It is deliberately not imported by ``app.factory`` or
``app.main``; no route, feature flag, or production path is activated here.

Everything depends on the shared foundation:

* :mod:`app.health_core.common` for events, ids and boundary-safe errors.
* :mod:`app.health_core.identity` for the ONLY permitted patient identity seam.

No MPI lookup, national identifier, database, HTTP library, real endpoint or
client-application source is used or modified by this subpackage.
"""

from app.health_core.integration.api_client import (
    ELIGIBLE_DOMAINS,
    ApiResult,
    DomainCode,
    InMemorySyntheticApiClient,
    SyntheticApiClient,
)
from app.health_core.integration.arabic_rtl_a11y import (
    DEFAULT_SURFACE_ANNOTATIONS,
    REQUIRED_SURFACES,
    REQUIREMENT_CATALOGUE,
    A11yRequirement,
    A11yValidation,
    Direction,
    RequirementKind,
    SurfaceAnnotation,
    UiSurfaceAnnotation,
    validate_requirement_catalogue,
    validate_surfaces,
)
from app.health_core.integration.auth_boundaries import (
    DEFAULT_BOUNDARIES,
    ELIGIBLE_OPERATIONS,
    AccessMode,
    AuthBoundary,
    BoundaryValidation,
    Operation,
    Role,
    assert_valid_boundaries,
    is_permitted,
    is_write_operation,
    validate_boundaries,
)
from app.health_core.integration.conflicts import (
    ConflictCase,
    ConflictDecision,
    ConflictStrategy,
    Disposition,
    assert_no_silent_drops,
    resolve_conflict,
)
from app.health_core.integration.offline import (
    ApplyDecision,
    ApplyStatus,
    OfflineOutbox,
    OutboxEntry,
    ReplayJournal,
    aggregate_key,
    replay,
)

__all__ = [
    "DEFAULT_BOUNDARIES",
    "DEFAULT_SURFACE_ANNOTATIONS",
    "ELIGIBLE_DOMAINS",
    "ELIGIBLE_OPERATIONS",
    "REQUIRED_SURFACES",
    "REQUIREMENT_CATALOGUE",
    "A11yRequirement",
    "A11yValidation",
    "AccessMode",
    "ApiResult",
    "ApplyDecision",
    "ApplyStatus",
    "AuthBoundary",
    "BoundaryValidation",
    "ConflictCase",
    "ConflictDecision",
    "ConflictStrategy",
    "Direction",
    "Disposition",
    "DomainCode",
    "InMemorySyntheticApiClient",
    "OfflineOutbox",
    "Operation",
    "OutboxEntry",
    "ReplayJournal",
    "RequirementKind",
    "Role",
    "SurfaceAnnotation",
    "SyntheticApiClient",
    "UiSurfaceAnnotation",
    "aggregate_key",
    "assert_no_silent_drops",
    "assert_valid_boundaries",
    "is_permitted",
    "is_write_operation",
    "replay",
    "resolve_conflict",
    "validate_boundaries",
    "validate_requirement_catalogue",
    "validate_surfaces",
]
