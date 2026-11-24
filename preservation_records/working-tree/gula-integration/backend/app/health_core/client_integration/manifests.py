"""Per-platform client integration manifests (declarations, never activation).

A manifest states the *required* contract shape and the *observed* layer status
for one platform. All default manifests describe the synthetic readiness target;
none claims an adapter binding or end-to-end verification, because WS-E was not
permitted to modify any client application file.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import StrEnum

from app.health_core.client_integration.observations import (
    OBSERVED_CLIENTS,
    ClientObservation,
)
from app.health_core.client_integration.platforms import (
    ImplementationStatus,
    LayerKey,
    LayerStatus,
    Platform,
)
from app.health_core.contracts.catalogue import DOMAIN_OPERATIONS, ContractDomain
from app.health_core.contracts.errors import ERROR_RESPONSE_BODIES
from app.health_core.integration.arabic_rtl_a11y import (
    MINIMUM_CONTRAST_RATIO,
    Direction,
    RequirementKind,
)
from app.health_core.integration.auth_boundaries import DEFAULT_BOUNDARIES, AuthBoundary
from app.health_core.integration.conflicts import ConflictStrategy, Disposition
from app.health_core.integration.offline import ApplyStatus


class PermissionModel(StrEnum):
    """How a client resolves permission for an operation."""

    EXPLICIT_ROLE = "explicit_role"
    IMPLICIT = "implicit"


CANONICAL_OPERATIONS: tuple[str, ...] = tuple(
    operation.value
    for operations in DOMAIN_OPERATIONS.values()
    for operation in operations
)

#: Explicit mapping from each WS-C operation to the existing WS-D abstract
#: client method. ``organization`` and ``facility`` are two WS-C domains but a
#: single WS-D ``organization_facility`` DomainCode, so both map to the same
#: concrete method pair. Nothing here invents a client method.
METHOD_BY_DOMAIN: dict[ContractDomain, tuple[str, str]] = {
    ContractDomain.PRACTITIONER: ("create_practitioner", "list_practitioners"),
    ContractDomain.ORGANIZATION: ("create_facility", "list_facilities"),
    ContractDomain.FACILITY: ("create_facility", "list_facilities"),
    ContractDomain.MEDICAL_RECORD: ("create_medical_record", "list_medical_records"),
    ContractDomain.ENCOUNTER: ("create_encounter", "list_encounters"),
    ContractDomain.DIAGNOSIS: ("create_diagnosis", "list_diagnoses"),
    ContractDomain.OBSERVATION: ("create_observation", "list_observations"),
    ContractDomain.LAB_ORDER: ("create_lab_order", "list_lab_orders"),
    ContractDomain.SPECIMEN: ("create_specimen", "list_specimens"),
    ContractDomain.LAB_RESULT: ("create_lab_result", "list_lab_results"),
    ContractDomain.RESULT_VERIFICATION: ("create_verification", "list_verifications"),
}

DEFAULT_METHOD_BINDINGS: tuple[tuple[str, str], ...] = tuple(
    (operation.value, METHOD_BY_DOMAIN[domain][index])
    for domain, operations in DOMAIN_OPERATIONS.items()
    for index, operation in enumerate(operations)
)


def _canonical_error_shape() -> tuple[str, ...]:
    for body in ERROR_RESPONSE_BODIES:
        if body.name == "canonical_json":
            return body.shape
    raise RuntimeError("canonical_json error body is missing from the error contract")


@dataclass(frozen=True, slots=True)
class AuthDeclaration:
    """Fail-closed authentication/authorization requirements."""

    permission_model: PermissionModel
    boundaries: tuple[AuthBoundary, ...]
    require_exact_role_match: bool
    anonymous_writes_allowed: bool


@dataclass(frozen=True, slots=True)
class ErrorDeclaration:
    """Canonical error envelope requirements."""

    canonical_fields: tuple[str, ...]
    arabic_detail_field: str
    content_types: tuple[str, ...]
    fhir_operation_outcome_adapter: bool


@dataclass(frozen=True, slots=True)
class OfflineDeclaration:
    """Outbox/replay requirements for disconnected operation."""

    outbox: bool
    replay: bool
    idempotent_by_event_id: bool
    deterministic_order: bool
    expected_apply_statuses: tuple[str, ...]
    durable_storage: bool


@dataclass(frozen=True, slots=True)
class SyncDeclaration:
    """Conflict decision and audit requirements."""

    conflict_strategies: tuple[str, ...]
    dispositions: tuple[str, ...]
    audit_records: bool
    no_silent_drops: bool
    clinical_content_merge: bool


@dataclass(frozen=True, slots=True)
class RtlA11yDeclaration:
    """Arabic-first RTL and accessibility requirements."""

    locale: str
    direction: Direction
    required_capabilities: tuple[str, ...]
    minimum_contrast_ratio: float
    error_announcement: bool


@dataclass(frozen=True, slots=True)
class ClientManifest:
    """Complete contract declaration for one observed client platform."""

    platform: Platform
    layer_statuses: tuple[tuple[LayerKey, LayerStatus], ...]
    operations: tuple[str, ...]
    method_bindings: tuple[tuple[str, str], ...]
    auth: AuthDeclaration
    error: ErrorDeclaration
    offline: OfflineDeclaration
    sync: SyncDeclaration
    rtl: RtlA11yDeclaration
    implementation_status: ImplementationStatus
    adapter_bound: bool
    end_to_end_verified: bool
    notes: str = ""

    def status_for(self, key: LayerKey) -> LayerStatus:
        """Return the declared status for ``key``."""
        for layer_key, status in self.layer_statuses:
            if layer_key is key:
                return status
        raise KeyError(key.value)


DEFAULT_AUTH = AuthDeclaration(
    permission_model=PermissionModel.EXPLICIT_ROLE,
    boundaries=DEFAULT_BOUNDARIES,
    require_exact_role_match=True,
    anonymous_writes_allowed=False,
)

DEFAULT_ERROR = ErrorDeclaration(
    canonical_fields=_canonical_error_shape(),
    arabic_detail_field="detail_ar",
    content_types=("application/json",),
    fhir_operation_outcome_adapter=False,
)

DEFAULT_OFFLINE = OfflineDeclaration(
    outbox=True,
    replay=True,
    idempotent_by_event_id=True,
    deterministic_order=True,
    expected_apply_statuses=tuple(status.value for status in ApplyStatus),
    durable_storage=False,
)

DEFAULT_SYNC = SyncDeclaration(
    conflict_strategies=tuple(strategy.value for strategy in ConflictStrategy),
    dispositions=tuple(disposition.value for disposition in Disposition),
    audit_records=True,
    no_silent_drops=True,
    clinical_content_merge=False,
)

DEFAULT_RTL = RtlA11yDeclaration(
    locale="ar",
    direction=Direction.RTL,
    required_capabilities=tuple(kind.value for kind in RequirementKind),
    minimum_contrast_ratio=MINIMUM_CONTRAST_RATIO,
    error_announcement=True,
)


def derive_implementation_status(
    manifest: ClientManifest, observation: ClientObservation
) -> tuple[ImplementationStatus, tuple[str, ...]]:
    """Derive the only honest classification allowed by observed evidence."""
    reasons: list[str] = []
    if not observation.project_present:
        reasons.append(
            f"project absent from checkout: {', '.join(observation.project_absence_probes)}"
        )
    for key, status in manifest.layer_statuses:
        if status is not LayerStatus.PRESENT:
            reasons.append(f"layer {key.value} is {status.value}")
    if not manifest.adapter_bound:
        reasons.append("no SyntheticApiClient adapter bound in the client application")
    if not manifest.end_to_end_verified:
        reasons.append("no end-to-end client behavior verified")

    if not observation.project_present:
        return ImplementationStatus.NOT_IMPLEMENTED, tuple(reasons)
    if reasons:
        return ImplementationStatus.BLOCKED, tuple(reasons)
    return ImplementationStatus.IMPLEMENTED, ()


def _manifest_from_observation(observation: ClientObservation) -> ClientManifest:
    manifest = ClientManifest(
        platform=observation.platform,
        layer_statuses=tuple(
            (layer.key, layer.status) for layer in observation.layers
        ),
        operations=CANONICAL_OPERATIONS,
        method_bindings=DEFAULT_METHOD_BINDINGS,
        auth=DEFAULT_AUTH,
        error=DEFAULT_ERROR,
        offline=DEFAULT_OFFLINE,
        sync=DEFAULT_SYNC,
        rtl=DEFAULT_RTL,
        implementation_status=ImplementationStatus.BLOCKED,
        adapter_bound=False,
        end_to_end_verified=False,
        notes=observation.note,
    )
    status, _ = derive_implementation_status(manifest, observation)
    return replace(manifest, implementation_status=status)


DEFAULT_MANIFESTS: tuple[ClientManifest, ...] = tuple(
    _manifest_from_observation(observation) for observation in OBSERVED_CLIENTS
)


def manifest_for(platform: Platform) -> ClientManifest:
    """Return the default manifest for ``platform``."""
    for manifest in DEFAULT_MANIFESTS:
        if manifest.platform is platform:
            return manifest
    raise KeyError(platform.value)
