"""Contract-first, synthetic-only API contracts for Health Core development.

Nothing in this package creates a FastAPI router, endpoint or production route.
It is a versioned set of Pydantic models plus error, authorization, event and
idempotency contracts used for contract tests and future owner-authorized work.
"""

from app.health_core.contracts.authorization import (
    AUTHORIZATION_BOUNDARIES,
    AuthorizationBoundary,
    Permission,
    Role,
    boundary_for,
)
from app.health_core.contracts.catalogue import (
    DOMAIN_OPERATIONS,
    ContractDomain,
    ContractOperation,
)
from app.health_core.contracts.errors import (
    ERROR_CATALOGUE,
    ERROR_RESPONSE_BODIES,
    FHIR_ISSUE_CODE_BY_ERROR_CODE,
    ErrorBodyContract,
    HealthCoreErrorResponse,
    error_response_from,
)
from app.health_core.contracts.events import (
    EVENT_CATALOGUE,
    EVENT_SCHEMA_VERSION,
    LEGACY_DIAGNOSIS_RESOLVE_ACTION,
    LEGACY_ENCOUNTER_START_STATUS,
    LEGACY_EVENT_TYPE_MAP,
    LEGACY_TRANSITION_KEY,
    EventContractViolation,
    EventDefinition,
    canonical_event_type,
    validate_domain_event,
)
from app.health_core.contracts.idempotency import (
    IDEMPOTENCY_CONFLICT_CODE,
    IDEMPOTENCY_CONFLICT_STATUS,
    IDEMPOTENCY_HEADER,
    IDEMPOTENCY_POLICIES,
    IDEMPOTENCY_SEMANTICS,
    IDEMPOTENCY_TTL_SECONDS,
    IdempotencyPolicy,
    IdempotencyScope,
    ReplaySemantics,
    new_idempotency_key,
    validate_idempotency_key,
)
from app.health_core.contracts.models import (
    DOMAIN_SCHEMAS,
    ArabicSafeText,
    ContractModel,
    LabResultCreateRequest,
    LabResultResponse,
    SyntheticAggregateResponse,
    SyntheticRef,
    TenantScopedRequest,
)
from app.health_core.contracts.version import (
    COMPATIBLE_MAJOR,
    CONTRACT_STATUS,
    HEALTH_CORE_CONTRACT_VERSION,
    contract_major,
    is_compatible_version,
)

__all__ = [
    "AUTHORIZATION_BOUNDARIES",
    "COMPATIBLE_MAJOR",
    "CONTRACT_STATUS",
    "DOMAIN_OPERATIONS",
    "DOMAIN_SCHEMAS",
    "ERROR_CATALOGUE",
    "ERROR_RESPONSE_BODIES",
    "EVENT_CATALOGUE",
    "EVENT_SCHEMA_VERSION",
    "FHIR_ISSUE_CODE_BY_ERROR_CODE",
    "HEALTH_CORE_CONTRACT_VERSION",
    "IDEMPOTENCY_CONFLICT_CODE",
    "IDEMPOTENCY_CONFLICT_STATUS",
    "IDEMPOTENCY_HEADER",
    "IDEMPOTENCY_POLICIES",
    "IDEMPOTENCY_SEMANTICS",
    "IDEMPOTENCY_TTL_SECONDS",
    "LEGACY_DIAGNOSIS_RESOLVE_ACTION",
    "LEGACY_ENCOUNTER_START_STATUS",
    "LEGACY_EVENT_TYPE_MAP",
    "LEGACY_TRANSITION_KEY",
    "ArabicSafeText",
    "AuthorizationBoundary",
    "ContractDomain",
    "ContractModel",
    "ContractOperation",
    "ErrorBodyContract",
    "EventContractViolation",
    "EventDefinition",
    "HealthCoreErrorResponse",
    "IdempotencyPolicy",
    "IdempotencyScope",
    "LabResultCreateRequest",
    "LabResultResponse",
    "Permission",
    "ReplaySemantics",
    "Role",
    "SyntheticAggregateResponse",
    "SyntheticRef",
    "TenantScopedRequest",
    "boundary_for",
    "canonical_event_type",
    "contract_major",
    "error_response_from",
    "is_compatible_version",
    "new_idempotency_key",
    "validate_domain_event",
    "validate_idempotency_key",
]
