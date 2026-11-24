"""Fail-closed validators for client integration manifests.

Every validator compares a declaration against an authoritative read-only
source: WS-C ``DOMAIN_OPERATIONS`` for operation names, the WS-D synthetic API
client for method bindings, the WS-D boundary/offline/conflict/a11y contracts
for the required semantics, and a filesystem-backed observation for the truthful
presence of a project and its layers.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.health_core.client_integration.manifests import (
    DEFAULT_MANIFESTS,
    ClientManifest,
    PermissionModel,
    derive_implementation_status,
)
from app.health_core.client_integration.observations import (
    OBSERVED_CLIENTS,
    ClientObservation,
    observation_for,
    verify_observation,
)
from app.health_core.client_integration.platforms import (
    REQUIRED_LAYERS,
    ImplementationStatus,
    LayerStatus,
    Platform,
)
from app.health_core.common import HealthCoreError
from app.health_core.contracts.catalogue import DOMAIN_OPERATIONS
from app.health_core.contracts.errors import ERROR_RESPONSE_BODIES
from app.health_core.integration.api_client import SyntheticApiClient
from app.health_core.integration.arabic_rtl_a11y import (
    DEFAULT_SURFACE_ANNOTATIONS,
    MINIMUM_CONTRAST_RATIO,
    Direction,
    RequirementKind,
    validate_requirement_catalogue,
    validate_surfaces,
)
from app.health_core.integration.auth_boundaries import (
    ELIGIBLE_OPERATIONS,
    Role,
    is_permitted,
    is_write_operation,
    validate_boundaries,
)
from app.health_core.integration.conflicts import ConflictStrategy, Disposition
from app.health_core.integration.offline import ApplyStatus

#: Repository root derived from this file; no absolute checkout path is required.
REPO_ROOT = Path(__file__).resolve().parents[4]


@dataclass(frozen=True, slots=True)
class ManifestValidation:
    """Structured, fail-closed result of validating one manifest."""

    platform: Platform
    errors: tuple[str, ...]
    reasons: tuple[str, ...]
    status: ImplementationStatus
    checked_operations: tuple[str, ...]
    checked_paths: tuple[str, ...]

    @property
    def is_valid(self) -> bool:
        """True when the declaration is complete and truthful."""
        return not self.errors

    def raise_if_invalid(self) -> None:
        """Raise a structured error containing every violation."""
        if self.errors:
            raise HealthCoreError(
                "client integration manifest failed validation",
                details={
                    "platform": self.platform.value,
                    "errors": list(self.errors),
                },
            )


def canonical_operations() -> tuple[str, ...]:
    """Derive the authoritative operation names directly from WS-C."""
    return tuple(
        operation.value
        for operations in DOMAIN_OPERATIONS.values()
        for operation in operations
    )


def canonical_error_fields() -> tuple[str, ...]:
    """Derive the canonical JSON error envelope fields from the error contract."""
    for body in ERROR_RESPONSE_BODIES:
        if body.name == "canonical_json":
            return body.shape
    raise HealthCoreError("canonical_json error body is missing")


def validate_arabic_catalogue() -> tuple[str, ...]:
    """Validate the read-only Arabic/RTL/a11y catalogue and its surfaces."""
    errors = list(validate_requirement_catalogue().errors)
    errors.extend(validate_surfaces(DEFAULT_SURFACE_ANNOTATIONS).errors)
    return tuple(errors)


def _validate_operations(
    manifest: ClientManifest, errors: list[str], checked_operations: list[str]
) -> None:
    expected = canonical_operations()
    declared = tuple(manifest.operations)
    checked_operations.extend(declared)
    if len(declared) != len(set(declared)):
        errors.append("DUPLICATE_OPERATION_DECLARATION")
    missing = sorted(set(expected) - set(declared))
    extra = sorted(set(declared) - set(expected))
    errors.extend(f"MISSING_WS_C_OPERATION: {name}" for name in missing)
    errors.extend(f"UNKNOWN_WS_C_OPERATION: {name}" for name in extra)

    bindings = tuple(manifest.method_bindings)
    binding_keys = [operation for operation, _ in bindings]
    if len(binding_keys) != len(set(binding_keys)):
        errors.append("DUPLICATE_METHOD_BINDING")
    binding_map = dict(bindings)
    errors.extend(
        f"MISSING_METHOD_BINDING: {name}" for name in sorted(set(expected) - set(binding_map))
    )
    errors.extend(
        f"UNKNOWN_METHOD_BINDING: {name}" for name in sorted(set(binding_map) - set(expected))
    )

    abstract_methods = frozenset(SyntheticApiClient.__abstractmethods__)
    for operation, method_name in sorted(binding_map.items()):
        method = getattr(SyntheticApiClient, method_name, None)
        if not callable(method):
            errors.append(f"UNKNOWN_CLIENT_METHOD: {operation}: {method_name}")
    bound_methods = {name for _, name in bindings if name in abstract_methods}
    errors.extend(
        f"UNBOUND_CLIENT_METHOD: {name}"
        for name in sorted(abstract_methods - bound_methods)
    )
    errors.extend(
        f"NON_CONTRACT_CLIENT_METHOD: {name}"
        for name in sorted(bound_methods - abstract_methods)
    )


def _validate_auth(manifest: ClientManifest, errors: list[str]) -> None:
    auth = manifest.auth
    if auth.permission_model is not PermissionModel.EXPLICIT_ROLE:
        errors.append("IMPLICIT_PERMISSION_MODEL")
    if not auth.require_exact_role_match:
        errors.append("NON_EXACT_ROLE_MATCH")
    if auth.anonymous_writes_allowed:
        errors.append("ANONYMOUS_WRITES_ALLOWED")
    errors.extend(f"AUTH_{error}" for error in validate_boundaries(auth.boundaries).errors)

    for operation in ELIGIBLE_OPERATIONS:
        if is_permitted(auth.boundaries, operation, Role.ANONYMOUS):
            errors.append(f"ANONYMOUS_ACCESS_ALLOWED: {operation.value}")
        if is_write_operation(operation) and is_permitted(
            auth.boundaries, operation, Role.SYNTHETIC_VIEWER
        ):
            errors.append(f"IMPLICIT_VIEWER_WRITE: {operation.value}")


def _validate_error(manifest: ClientManifest, errors: list[str]) -> None:
    error = manifest.error
    fields = tuple(error.canonical_fields)
    if fields != canonical_error_fields():
        errors.append("ERROR_ENVELOPE_FIELD_MISMATCH")
    if "detail" not in fields:
        errors.append("MISSING_LEGACY_DETAIL_FIELD")
    if error.arabic_detail_field != "detail_ar" or error.arabic_detail_field not in fields:
        errors.append("MISSING_ARABIC_DETAIL")
    if "application/json" not in error.content_types:
        errors.append("MISSING_JSON_CONTENT_TYPE")
    if error.fhir_operation_outcome_adapter:
        errors.append("UNVERIFIED_FHIR_ADAPTER_CLAIM")


def _validate_offline(manifest: ClientManifest, errors: list[str]) -> None:
    offline = manifest.offline
    if not offline.outbox:
        errors.append("MISSING_OUTBOX_DECLARATION")
    if not offline.replay:
        errors.append("MISSING_REPLAY_DECLARATION")
    if not offline.idempotent_by_event_id:
        errors.append("NON_IDEMPOTENT_REPLAY_DECLARATION")
    if not offline.deterministic_order:
        errors.append("NON_DETERMINISTIC_REPLAY_DECLARATION")
    expected_statuses = tuple(status.value for status in ApplyStatus)
    if tuple(offline.expected_apply_statuses) != expected_statuses:
        errors.append("APPLY_STATUS_VOCABULARY_MISMATCH")
    if offline.durable_storage:
        errors.append("OVERCLAIMED_DURABLE_STORAGE")


def _validate_sync(manifest: ClientManifest, errors: list[str]) -> None:
    sync = manifest.sync
    expected_strategies = tuple(strategy.value for strategy in ConflictStrategy)
    expected_dispositions = tuple(disposition.value for disposition in Disposition)
    if tuple(sync.conflict_strategies) != expected_strategies:
        errors.append("CONFLICT_STRATEGY_VOCABULARY_MISMATCH")
    if tuple(sync.dispositions) != expected_dispositions:
        errors.append("DISPOSITION_VOCABULARY_MISMATCH")
    if not sync.audit_records:
        errors.append("MISSING_CONFLICT_AUDIT")
    if not sync.no_silent_drops:
        errors.append("SILENT_CONFLICT_DROPS_ALLOWED")
    if sync.clinical_content_merge:
        errors.append("OVERCLAIMED_CLINICAL_MERGE")


def _validate_rtl(manifest: ClientManifest, errors: list[str]) -> None:
    rtl = manifest.rtl
    if not rtl.locale.startswith("ar"):
        errors.append("NON_ARABIC_LOCALE")
    if rtl.direction is not Direction.RTL:
        errors.append("NON_RTL_DIRECTION")
    expected_capabilities = tuple(kind.value for kind in RequirementKind)
    if tuple(rtl.required_capabilities) != expected_capabilities:
        errors.append("INCOMPLETE_A11Y_CAPABILITIES")
    if rtl.minimum_contrast_ratio < MINIMUM_CONTRAST_RATIO:
        errors.append("INSUFFICIENT_CONTRAST")
    if not rtl.error_announcement:
        errors.append("MISSING_ERROR_ANNOUNCEMENT")
    errors.extend(f"A11Y_CATALOGUE_{error}" for error in validate_arabic_catalogue())


def validate_manifest(
    manifest: ClientManifest,
    observation: ClientObservation | None = None,
    *,
    repo_root: Path | None = None,
) -> ManifestValidation:
    """Validate one manifest; every mismatch is returned as a structured reason."""
    observed = observation if observation is not None else observation_for(manifest.platform)
    errors: list[str] = []
    checked_operations: list[str] = []
    checked_paths: list[str] = []

    if repo_root is not None:
        verification = verify_observation(observed, repo_root)
        checked_paths.extend(verification.checked_paths)
        errors.extend(verification.errors)

    if manifest.platform is not observed.platform:
        errors.append("PLATFORM_MISMATCH")

    observed_statuses = observed.status_map()
    for key in REQUIRED_LAYERS:
        declared_status = dict(manifest.layer_statuses).get(key)
        if declared_status is None:
            errors.append(f"MISSING_LAYER_DECLARATION: {key.value}")
        elif declared_status is not observed_statuses.get(key):
            errors.append(
                f"LAYER_STATUS_MISMATCH: {key.value}: "
                f"declared={declared_status.value} observed={observed_statuses.get(key)}"
            )

    _validate_operations(manifest, errors, checked_operations)
    _validate_auth(manifest, errors)
    _validate_error(manifest, errors)
    _validate_offline(manifest, errors)
    _validate_sync(manifest, errors)
    _validate_rtl(manifest, errors)

    derived_status, reasons = derive_implementation_status(manifest, observed)
    if manifest.implementation_status is not derived_status:
        errors.append(
            f"IMPLEMENTATION_STATUS_MISMATCH: declared={manifest.implementation_status.value} "
            f"derived={derived_status.value}"
        )
    if manifest.implementation_status is ImplementationStatus.IMPLEMENTED:
        errors.append("UNVERIFIED_IMPLEMENTED_CLAIM")
    if (
        not observed.project_present
        and manifest.implementation_status is ImplementationStatus.IMPLEMENTED
    ):
        errors.append("ABSENT_PROJECT_CLAIMED_IMPLEMENTED")
    if manifest.adapter_bound:
        errors.append("UNVERIFIED_ADAPTER_CLAIM")
    if manifest.end_to_end_verified:
        errors.append("UNVERIFIED_END_TO_END_CLAIM")
    if derived_status is ImplementationStatus.NOT_IMPLEMENTED and any(
        status is LayerStatus.PRESENT for _, status in manifest.layer_statuses
    ):
        errors.append("ABSENT_PROJECT_WITH_PRESENT_LAYER")

    return ManifestValidation(
        platform=manifest.platform,
        errors=tuple(errors),
        reasons=reasons,
        status=derived_status,
        checked_operations=tuple(checked_operations),
        checked_paths=tuple(checked_paths),
    )


def validate_all_manifests(
    manifests: tuple[ClientManifest, ...] = DEFAULT_MANIFESTS,
    observations: tuple[ClientObservation, ...] = OBSERVED_CLIENTS,
    *,
    repo_root: Path | None = REPO_ROOT,
) -> tuple[ManifestValidation, ...]:
    """Validate every manifest, also checking platform completeness/uniqueness.

    Each manifest is validated against the caller-supplied observation for its
    platform, never against the module-global default. A missing observation is
    reported exactly once as ``NO_OBSERVATION_FOR_PLATFORM`` and the manifest is
    still checked against the recorded default observation (the historical,
    fail-closed fallback), so no silent defaulting can mask a caller's scenario.
    """
    platforms = [manifest.platform for manifest in manifests]
    observations_by_platform = {
        observation.platform: observation for observation in observations
    }
    results: list[ManifestValidation] = []
    for manifest in manifests:
        observation = observations_by_platform.get(manifest.platform)
        result = validate_manifest(manifest, observation=observation, repo_root=repo_root)
        extra_errors: list[str] = []
        if observation is None:
            extra_errors.append("NO_OBSERVATION_FOR_PLATFORM")
        if platforms.count(manifest.platform) != 1:
            extra_errors.append("DUPLICATE_PLATFORM_MANIFEST")
        if extra_errors:
            result = ManifestValidation(
                platform=result.platform,
                errors=result.errors + tuple(extra_errors),
                reasons=result.reasons,
                status=result.status,
                checked_operations=result.checked_operations,
                checked_paths=result.checked_paths,
            )
        results.append(result)
    return tuple(results)
