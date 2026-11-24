"""Tests for WS-E per-platform client integration manifests and validators.

These tests validate *declarations against read-only observations*. They never
claim or simulate end-to-end client behavior.
"""

from __future__ import annotations

from dataclasses import replace

import pytest
from app.health_core.client_integration import (
    DEFAULT_MANIFESTS,
    IMPLEMENTED,
    OBSERVED_CLIENTS,
    REQUIRED_LAYERS,
    AuthDeclaration,
    ClientManifest,
    ClientObservation,
    ErrorDeclaration,
    LayerKey,
    LayerStatus,
    ManifestValidation,
    ObservedLayer,
    OfflineDeclaration,
    Platform,
    RtlA11yDeclaration,
    SyncDeclaration,
    build_coverage_report,
    canonical_operations,
    manifest_for,
    observation_for,
    render_coverage_report,
    validate_all_manifests,
    validate_manifest,
    verify_observation,
)
from app.health_core.client_integration.manifests import (
    DEFAULT_METHOD_BINDINGS,
    METHOD_BY_DOMAIN,
    PermissionModel,
)
from app.health_core.client_integration.validators import (
    REPO_ROOT,
    canonical_error_fields,
    validate_arabic_catalogue,
)
from app.health_core.common import (
    AggregateType,
    DomainEvent,
    EventType,
    HealthCoreError,
)
from app.health_core.contracts.catalogue import (
    DOMAIN_OPERATIONS,
    ContractDomain,
    ContractOperation,
)
from app.health_core.identity import DEFAULT_SYNTHETIC_TENANT
from app.health_core.integration.api_client import SyntheticApiClient
from app.health_core.integration.arabic_rtl_a11y import (
    MINIMUM_CONTRAST_RATIO,
    Direction,
    RequirementKind,
)
from app.health_core.integration.auth_boundaries import (
    DEFAULT_BOUNDARIES,
    Operation,
    Role,
    is_permitted,
)
from app.health_core.integration.conflicts import (
    ConflictCase,
    ConflictStrategy,
    Disposition,
    resolve_conflict,
)
from app.health_core.integration.offline import (
    ApplyStatus,
    OfflineOutbox,
    ReplayJournal,
    replay,
)


def _event(event_id: str, occurred_at: str, version: int = 1) -> DomainEvent:
    return DomainEvent(
        event_id=event_id,
        event_type=EventType.RESULT_RECORDED,
        aggregate_type=AggregateType.LAB_RESULT,
        aggregate_id="SYN-RES-0001",
        tenant_id=DEFAULT_SYNTHETIC_TENANT,
        occurred_at=occurred_at,
        version=version,
        payload={"fixture": event_id},
    )


# --- positive validation -------------------------------------------------


def test_all_observed_platform_manifests_validate_against_the_checkout() -> None:
    results = validate_all_manifests(repo_root=REPO_ROOT)
    assert len(results) == len(OBSERVED_CLIENTS) == 6
    assert {result.platform for result in results} == set(Platform)
    for result in results:
        assert isinstance(result, ManifestValidation)
        assert result.is_valid, (result.platform, result.errors)
        assert result.status is not IMPLEMENTED
        assert result.checked_operations
        assert result.checked_paths
        result.raise_if_invalid()


def test_every_recorded_observation_is_reproducible_from_disk() -> None:
    for observation in OBSERVED_CLIENTS:
        verification = verify_observation(observation, REPO_ROOT)
        assert verification.is_valid, (observation.platform, verification.errors)
        assert verification.checked_paths
        verification.raise_if_invalid()


def test_observed_facts_are_not_inferred_or_fabricated() -> None:
    ios = observation_for(Platform.IOS)
    assert ios.project_present is False
    assert ios.project_absence_probes == (
        "mobile/ios/Gula.xcodeproj",
        "mobile/ios/Gula.xcworkspace",
    )
    assert all(layer.status is LayerStatus.PARTIAL for layer in ios.layers)

    expo = observation_for(Platform.EXPO)
    assert expo.layer(LayerKey.API_CLIENT).status is LayerStatus.ABSENT
    assert expo.layer(LayerKey.AUTH_BOUNDARY).status is LayerStatus.ABSENT
    assert expo.layer(LayerKey.ARABIC_RTL_A11Y).status is LayerStatus.ABSENT

    web = observation_for(Platform.WEB)
    assert web.layer(LayerKey.OFFLINE_OUTBOX).status is LayerStatus.ABSENT
    assert web.layer(LayerKey.SYNC_CONFLICT).status is LayerStatus.ABSENT

    flutter = observation_for(Platform.FLUTTER)
    assert flutter.layer(LayerKey.SYNC_CONFLICT).status is LayerStatus.PRESENT
    assert flutter.layer(LayerKey.ARABIC_RTL_A11Y).status is LayerStatus.PRESENT

    ios_manifest = validate_manifest(manifest_for(Platform.IOS), repo_root=REPO_ROOT)
    assert ios_manifest.status.value == "not_implemented"
    assert any("project absent" in reason for reason in ios_manifest.reasons)


def test_coverage_report_separates_declaration_from_end_to_end_evidence() -> None:
    rows = build_coverage_report(repo_root=REPO_ROOT)
    assert len(rows) == 6
    assert all(row.contract_declared_and_validated for row in rows)
    assert all(row.end_to_end_verified is False for row in rows)
    assert all(row.status is not IMPLEMENTED for row in rows)
    assert any(row.status.value == "not_implemented" for row in rows)

    rendered = render_coverage_report(rows)
    assert "NOT IMPLEMENTED" in rendered
    assert "BLOCKED" in rendered
    assert "End-to-end verified = NO" in rendered
    assert "Contract declared/validated" in rendered


def test_ws_c_operations_are_exact_and_bound_to_real_client_methods() -> None:
    expected = tuple(operation.value for operation in ContractOperation)
    assert set(canonical_operations()) == set(expected)
    assert len(canonical_operations()) == 22
    assert sum(len(operations) for operations in DOMAIN_OPERATIONS.values()) == 22

    for manifest in DEFAULT_MANIFESTS:
        assert set(manifest.operations) == set(expected)
        assert len(manifest.operations) == len(expected)
        assert set(dict(manifest.method_bindings)) == set(expected)
        assert dict(manifest.method_bindings) == dict(DEFAULT_METHOD_BINDINGS)
        bound_methods = {method for _, method in manifest.method_bindings}
        assert bound_methods == set(SyntheticApiClient.__abstractmethods__)
        for _, method in manifest.method_bindings:
            assert callable(getattr(SyntheticApiClient, method))

    # WS-C has two domains (organization, facility) collapsed into one WS-D
    # DomainCode; the alias is explicit, never implicit.
    assert METHOD_BY_DOMAIN[ContractDomain.ORGANIZATION] == (
        METHOD_BY_DOMAIN[ContractDomain.FACILITY]
    )


def test_error_envelope_matches_the_canonical_contract() -> None:
    fields = canonical_error_fields()
    for manifest in DEFAULT_MANIFESTS:
        assert tuple(manifest.error.canonical_fields) == fields
        assert "code" in fields
        assert "request_id" in fields
        assert "timestamp" in fields
        assert manifest.error.arabic_detail_field == "detail_ar"
        assert "detail_ar" in fields
        assert "application/json" in manifest.error.content_types
        assert manifest.error.fhir_operation_outcome_adapter is False


def test_offline_and_sync_declarations_match_the_read_only_contracts() -> None:
    for manifest in DEFAULT_MANIFESTS:
        assert manifest.offline.outbox is True
        assert manifest.offline.replay is True
        assert manifest.offline.idempotent_by_event_id is True
        assert manifest.offline.deterministic_order is True
        assert tuple(manifest.offline.expected_apply_statuses) == tuple(
            status.value for status in ApplyStatus
        )
        assert manifest.offline.durable_storage is False
        assert manifest.sync.audit_records is True
        assert manifest.sync.no_silent_drops is True
        assert manifest.sync.clinical_content_merge is False


def test_arabic_rtl_a11y_declarations_and_catalogue_are_complete() -> None:
    assert validate_arabic_catalogue() == ()
    for manifest in DEFAULT_MANIFESTS:
        assert manifest.rtl.locale == "ar"
        assert manifest.rtl.direction is Direction.RTL
        assert set(manifest.rtl.required_capabilities) == {
            kind.value for kind in RequirementKind
        }
        assert manifest.rtl.minimum_contrast_ratio >= MINIMUM_CONTRAST_RATIO
        assert manifest.rtl.error_announcement is True


def test_no_platform_claims_an_adapter_or_end_to_end_verification() -> None:
    for manifest in DEFAULT_MANIFESTS:
        assert manifest.adapter_bound is False
        assert manifest.end_to_end_verified is False
        assert manifest.implementation_status is not IMPLEMENTED


# --- negative / fail-closed tests ---------------------------------------


def test_api_operation_mismatch_fails_closed() -> None:
    manifest = manifest_for(Platform.WEB)
    operations = tuple(manifest.operations)
    bad = replace(
        manifest,
        operations=(*operations[1:], "practitioner.delete"),
    )
    validation = validate_manifest(bad, repo_root=REPO_ROOT)
    assert not validation.is_valid
    assert any("MISSING_WS_C_OPERATION" in error for error in validation.errors)
    assert any("UNKNOWN_WS_C_OPERATION" in error for error in validation.errors)

    unbound = replace(manifest, method_bindings=manifest.method_bindings[:-1])
    unbound_result = validate_manifest(unbound, repo_root=REPO_ROOT)
    assert not unbound_result.is_valid
    assert any("MISSING_METHOD_BINDING" in error for error in unbound_result.errors)
    assert any("UNBOUND_CLIENT_METHOD" in error for error in unbound_result.errors)


def test_invented_client_method_fails_closed() -> None:
    manifest = manifest_for(Platform.FLUTTER)
    bindings = (*manifest.method_bindings[:-1], ("result_verification.read", "fetchLabResultsFromCloud"))
    validation = validate_manifest(replace(manifest, method_bindings=bindings), repo_root=REPO_ROOT)
    assert not validation.is_valid
    assert any("UNKNOWN_CLIENT_METHOD" in error for error in validation.errors)


def test_anonymous_writes_and_bypass_paths_fail_closed() -> None:
    from app.health_core.integration.auth_boundaries import AuthBoundary

    assert is_permitted(DEFAULT_BOUNDARIES, Operation.WRITE_LAB_RESULT, Role.ANONYMOUS) is False
    assert is_permitted(DEFAULT_BOUNDARIES, Operation.WRITE_LAB_RESULT, Role.CLINICIAN) is False
    assert is_permitted(DEFAULT_BOUNDARIES, Operation.READ_LAB_RESULT, Role.ANONYMOUS) is False

    anonymous_rule = AuthBoundary(
        operation=Operation.WRITE_LAB_RESULT,
        required_role=Role.ANONYMOUS,
        anonymous_allowed=True,
        bypass_paths=("demo-write",),
    )
    boundaries = tuple(
        anonymous_rule if rule.operation is Operation.WRITE_LAB_RESULT else rule
        for rule in DEFAULT_BOUNDARIES
    )
    manifest = replace(
        manifest_for(Platform.ANDROID),
        auth=AuthDeclaration(
            permission_model=PermissionModel.EXPLICIT_ROLE,
            boundaries=boundaries,
            require_exact_role_match=True,
            anonymous_writes_allowed=True,
        ),
    )
    validation = validate_manifest(manifest, repo_root=REPO_ROOT)
    assert not validation.is_valid
    assert any("ANONYMOUS_ROLE" in error for error in validation.errors)
    assert any("PUBLIC_WRITE" in error for error in validation.errors)
    assert any("BYPASS_PATH" in error for error in validation.errors)
    assert any("ANONYMOUS_WRITES_ALLOWED" in error for error in validation.errors)
    with pytest.raises(HealthCoreError):
        validation.raise_if_invalid()


def test_implicit_permissions_fail_closed() -> None:
    manifest = manifest_for(Platform.DESKTOP)
    bad_auth = replace(
        manifest.auth,
        permission_model=PermissionModel.IMPLICIT,
        require_exact_role_match=False,
    )
    validation = validate_manifest(replace(manifest, auth=bad_auth), repo_root=REPO_ROOT)
    assert not validation.is_valid
    assert "IMPLICIT_PERMISSION_MODEL" in validation.errors
    assert "NON_EXACT_ROLE_MATCH" in validation.errors


def test_error_envelope_violations_fail_closed() -> None:
    manifest = manifest_for(Platform.WEB)
    bad = ErrorDeclaration(
        canonical_fields=("code", "message"),
        arabic_detail_field="message_ar",
        content_types=("text/plain",),
        fhir_operation_outcome_adapter=True,
    )
    validation = validate_manifest(replace(manifest, error=bad), repo_root=REPO_ROOT)
    assert not validation.is_valid
    assert "ERROR_ENVELOPE_FIELD_MISMATCH" in validation.errors
    assert "MISSING_LEGACY_DETAIL_FIELD" in validation.errors
    assert "MISSING_ARABIC_DETAIL" in validation.errors
    assert "MISSING_JSON_CONTENT_TYPE" in validation.errors
    assert "UNVERIFIED_FHIR_ADAPTER_CLAIM" in validation.errors


def test_offline_contract_violations_fail_closed() -> None:
    manifest = manifest_for(Platform.FLUTTER)
    bad = OfflineDeclaration(
        outbox=False,
        replay=False,
        idempotent_by_event_id=False,
        deterministic_order=False,
        expected_apply_statuses=("applied",),
        durable_storage=True,
    )
    validation = validate_manifest(replace(manifest, offline=bad), repo_root=REPO_ROOT)
    assert not validation.is_valid
    assert "MISSING_OUTBOX_DECLARATION" in validation.errors
    assert "MISSING_REPLAY_DECLARATION" in validation.errors
    assert "NON_IDEMPOTENT_REPLAY_DECLARATION" in validation.errors
    assert "NON_DETERMINISTIC_REPLAY_DECLARATION" in validation.errors
    assert "APPLY_STATUS_VOCABULARY_MISMATCH" in validation.errors
    assert "OVERCLAIMED_DURABLE_STORAGE" in validation.errors


def test_sync_contract_violations_fail_closed() -> None:
    manifest = manifest_for(Platform.IOS)
    bad = SyncDeclaration(
        conflict_strategies=("last_write_wins",),
        dispositions=("kept",),
        audit_records=False,
        no_silent_drops=False,
        clinical_content_merge=True,
    )
    validation = validate_manifest(replace(manifest, sync=bad), repo_root=REPO_ROOT)
    assert not validation.is_valid
    assert "CONFLICT_STRATEGY_VOCABULARY_MISMATCH" in validation.errors
    assert "DISPOSITION_VOCABULARY_MISMATCH" in validation.errors
    assert "MISSING_CONFLICT_AUDIT" in validation.errors
    assert "SILENT_CONFLICT_DROPS_ALLOWED" in validation.errors
    assert "OVERCLAIMED_CLINICAL_MERGE" in validation.errors


def test_rtl_a11y_violations_fail_closed() -> None:
    manifest = manifest_for(Platform.EXPO)
    bad = RtlA11yDeclaration(
        locale="en",
        direction=Direction.LTR,
        required_capabilities=("field_label",),
        minimum_contrast_ratio=2.0,
        error_announcement=False,
    )
    validation = validate_manifest(replace(manifest, rtl=bad), repo_root=REPO_ROOT)
    assert not validation.is_valid
    assert "NON_ARABIC_LOCALE" in validation.errors
    assert "NON_RTL_DIRECTION" in validation.errors
    assert "INCOMPLETE_A11Y_CAPABILITIES" in validation.errors
    assert "INSUFFICIENT_CONTRAST" in validation.errors
    assert "MISSING_ERROR_ANNOUNCEMENT" in validation.errors


def test_claiming_an_absent_or_partial_layer_implemented_fails_closed() -> None:
    observation = observation_for(Platform.EXPO)
    manifest = manifest_for(Platform.EXPO)
    overclaim = replace(
        manifest,
        layer_statuses=tuple((key, LayerStatus.PRESENT) for key in REQUIRED_LAYERS),
        implementation_status=IMPLEMENTED,
        adapter_bound=True,
        end_to_end_verified=True,
    )
    validation = validate_manifest(overclaim, observation, repo_root=REPO_ROOT)
    assert not validation.is_valid
    assert any("LAYER_STATUS_MISMATCH" in error for error in validation.errors)
    assert "UNVERIFIED_IMPLEMENTED_CLAIM" in validation.errors
    assert "UNVERIFIED_ADAPTER_CLAIM" in validation.errors
    assert "UNVERIFIED_END_TO_END_CLAIM" in validation.errors

    # The same claim against an absent project gets an explicit project reason.
    ios_observation = observation_for(Platform.IOS)
    ios_overclaim = replace(
        manifest_for(Platform.IOS),
        layer_statuses=tuple((key, LayerStatus.PRESENT) for key in REQUIRED_LAYERS),
        implementation_status=IMPLEMENTED,
        adapter_bound=True,
        end_to_end_verified=True,
    )
    ios_validation = validate_manifest(ios_overclaim, ios_observation, repo_root=REPO_ROOT)
    assert "ABSENT_PROJECT_CLAIMED_IMPLEMENTED" in ios_validation.errors


def test_tampered_observation_is_detected() -> None:
    ios = observation_for(Platform.IOS)
    fake_present_ios = replace(
        ios,
        project_present=True,
        project_absence_probes=(),
        note="tampered: claims an Xcode project exists",
    )
    verification = verify_observation(fake_present_ios, REPO_ROOT)
    assert verification.is_valid  # the tampered paths that remain are all real

    validation = validate_manifest(manifest_for(Platform.IOS), fake_present_ios)
    assert not validation.is_valid
    assert any(
        error.startswith("IMPLEMENTATION_STATUS_MISMATCH") for error in validation.errors
    )

    tampered_paths = replace(
        observation_for(Platform.WEB),
        project_evidence=("frontend-v3/does-not-exist.js",),
    )
    path_result = verify_observation(tampered_paths, REPO_ROOT)
    assert not path_result.is_valid
    assert any("EXPECTED_PATH_MISSING" in error for error in path_result.errors)


def test_unobserved_or_duplicate_platform_manifests_fail_closed() -> None:
    # Supplying only one observation leaves the other five manifests unobserved.
    partial = validate_all_manifests(observations=(observation_for(Platform.WEB),))
    assert len(partial) == 6
    assert all("NO_OBSERVATION_FOR_PLATFORM" in result.errors for result in partial[1:])
    assert "NO_OBSERVATION_FOR_PLATFORM" not in partial[0].errors

    duplicated = (*DEFAULT_MANIFESTS, manifest_for(Platform.WEB))
    results = validate_all_manifests(manifests=duplicated)
    assert not results[0].is_valid
    assert "DUPLICATE_PLATFORM_MANIFEST" in results[0].errors


# --- caller-supplied observations are actually honoured (F-04) ------------


def _synthetic_all_absent_web_observation() -> ClientObservation:
    """SYN-only scenario: WEB project absent and every required layer absent."""
    return ClientObservation(
        platform=Platform.WEB,
        project_present=False,
        project_evidence=(),
        project_absence_probes=("frontend-v3/SYN-WEB-PROJECT-ABSENT-PROBE",),
        layers=tuple(
            ObservedLayer(
                key=key,
                status=LayerStatus.ABSENT,
                absent_probes=(f"frontend-v3/SYN-WEB-{key.value.upper()}-ABSENT-PROBE",),
                note="SYN synthetic all-absent layer",
            )
            for key in REQUIRED_LAYERS
        ),
        note="SYN synthetic scenario: web project absent and all layers absent",
    )


def test_supplied_custom_observation_is_used_instead_of_the_default() -> None:
    default_results = validate_all_manifests(repo_root=REPO_ROOT)
    default_by_platform = {result.platform: result for result in default_results}
    assert default_by_platform[Platform.WEB].errors == ()

    custom_web = _synthetic_all_absent_web_observation()
    assert verify_observation(custom_web, REPO_ROOT).is_valid

    scoped_observations = tuple(
        custom_web if observation.platform is Platform.WEB else observation
        for observation in OBSERVED_CLIENTS
    )
    custom_results = validate_all_manifests(
        observations=scoped_observations, repo_root=REPO_ROOT
    )
    custom_by_platform = {result.platform: result for result in custom_results}

    web_errors = custom_by_platform[Platform.WEB].errors
    default_web_errors = default_by_platform[Platform.WEB].errors
    assert web_errors != default_web_errors
    assert any(error.startswith("LAYER_STATUS_MISMATCH") for error in web_errors)
    assert "ABSENT_PROJECT_WITH_PRESENT_LAYER" in web_errors
    assert not any("LAYER_STATUS_MISMATCH" in error for error in default_web_errors)
    assert "ABSENT_PROJECT_WITH_PRESENT_LAYER" not in default_web_errors

    # The custom observation is scoped to WEB; no other platform may change.
    for platform in (
        Platform.ANDROID,
        Platform.IOS,
        Platform.FLUTTER,
        Platform.DESKTOP,
        Platform.EXPO,
    ):
        assert custom_by_platform[platform].errors == ()
        assert custom_by_platform[platform].errors == default_by_platform[platform].errors


def test_missing_observation_emits_no_observation_error_exactly_once() -> None:
    web_only = (observation_for(Platform.WEB),)
    partial = validate_all_manifests(observations=web_only, repo_root=REPO_ROOT)
    assert len(partial) == len(DEFAULT_MANIFESTS)
    for result in partial:
        occurrences = result.errors.count("NO_OBSERVATION_FOR_PLATFORM")
        if result.platform is Platform.WEB:
            assert occurrences == 0
        else:
            assert occurrences == 1, (result.platform, result.errors)

    unobserved = validate_all_manifests(observations=(), repo_root=REPO_ROOT)
    assert len(unobserved) == len(DEFAULT_MANIFESTS)
    for result in unobserved:
        assert result.errors.count("NO_OBSERVATION_FOR_PLATFORM") == 1

    duplicated = (*DEFAULT_MANIFESTS, manifest_for(Platform.WEB))
    dup_results = validate_all_manifests(manifests=duplicated, repo_root=REPO_ROOT)
    for result in dup_results:
        assert result.errors.count("NO_OBSERVATION_FOR_PLATFORM") == 0
        expected_duplicates = 1 if result.platform is Platform.WEB else 0
        assert result.errors.count("DUPLICATE_PLATFORM_MANIFEST") == expected_duplicates


def test_default_validate_all_manifests_keeps_the_clean_result_shape() -> None:
    results = validate_all_manifests()
    assert len(results) == len(DEFAULT_MANIFESTS) == len(OBSERVED_CLIENTS) == 6
    assert tuple(result.platform for result in results) == tuple(
        manifest.platform for manifest in DEFAULT_MANIFESTS
    )
    for result in results:
        assert isinstance(result, ManifestValidation)
        assert result.errors == ()
        assert result.is_valid is True
        assert result.status is not IMPLEMENTED
        assert result.reasons
        assert result.checked_operations
        assert result.checked_paths
        result.raise_if_invalid()


# --- runtime contract proof (declaration semantics, not client behavior) --


def test_declared_offline_semantics_hold_for_in_memory_primitives() -> None:
    outbox = OfflineOutbox()
    first = _event("SYN-EVT-0001", "2026-11-18T10:00:00+00:00", version=1)
    divergent = _event("SYN-EVT-0002", "2026-11-18T10:01:00+00:00", version=1)
    assert outbox.enqueue(first) == outbox.enqueue(first)
    outbox.enqueue(divergent)

    decisions = replay(outbox)
    assert [decision.status for decision in decisions] == [
        ApplyStatus.APPLIED,
        ApplyStatus.CONFLICT,
    ]
    assert decisions[0].aggregate_key.startswith(DEFAULT_SYNTHETIC_TENANT)
    assert decisions[1].reason

    journal = ReplayJournal()
    assert journal.apply(first).status is ApplyStatus.APPLIED
    assert journal.apply(first).status is ApplyStatus.DUPLICATE
    assert journal.applied_event_ids == frozenset({first.event_id})


def test_declared_sync_semantics_produce_decisions_and_audit() -> None:
    first = _event("SYN-EVT-0010", "2026-11-18T10:00:00+00:00")
    second = _event("SYN-EVT-0011", "2026-11-18T10:05:00+00:00")
    case = ConflictCase(
        conflict_id="SYN-CONF-0001",
        aggregate_key=f"{DEFAULT_SYNTHETIC_TENANT}/lab_result/SYN-RES-0001",
        tenant_id=DEFAULT_SYNTHETIC_TENANT,
        events=(first, second),
        expected_version=2,
        observed_version=1,
    )
    decision = resolve_conflict(case, ConflictStrategy.KEEP_LAST_WITH_AUDIT)
    assert decision.accepted_event is second
    assert {item.event_id for item in decision.dispositions} == {
        first.event_id,
        second.event_id,
    }
    assert [item.disposition for item in decision.dispositions] == [
        Disposition.SUPERSEDED,
        Disposition.ACCEPTED,
    ]
    assert len(decision.audit) == 1
    assert decision.audit[0].event_id == first.event_id
    assert decision.audit[0].action is Disposition.SUPERSEDED
