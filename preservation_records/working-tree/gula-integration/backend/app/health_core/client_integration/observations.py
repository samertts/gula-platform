"""Read-only, evidence-backed inventory of the client trees in this checkout.

Every path in :data:`OBSERVED_CLIENTS` was inspected with read-only filesystem
commands on 2026-11-18 in ``/home/samertts/workspace/projects/gula-integration``.
No client file is imported, executed or modified by this package.

``present_evidence`` paths must exist and ``absent_probes`` paths must not exist
for the recorded classification to verify. Absence probes are **scoped checks**,
not a proof that an arbitrary alternative implementation cannot exist; that
limitation is stated in the handoff report.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.health_core.client_integration.platforms import (
    REQUIRED_LAYERS,
    LayerKey,
    LayerStatus,
    Platform,
)
from app.health_core.common import HealthCoreError


@dataclass(frozen=True, slots=True)
class ObservedLayer:
    """One layer's observed status with the concrete paths backing it."""

    key: LayerKey
    status: LayerStatus
    present_evidence: tuple[str, ...] = ()
    absent_probes: tuple[str, ...] = ()
    note: str = ""


@dataclass(frozen=True, slots=True)
class ClientObservation:
    """Scoped, reproducible observation of one client project."""

    platform: Platform
    project_present: bool
    project_evidence: tuple[str, ...]
    layers: tuple[ObservedLayer, ...]
    project_absence_probes: tuple[str, ...] = ()
    note: str = ""

    def layer(self, key: LayerKey) -> ObservedLayer:
        """Return the observation for ``key`` or fail closed."""
        for layer in self.layers:
            if layer.key is key:
                return layer
        raise HealthCoreError(
            "client layer was not observed",
            details={"platform": self.platform.value, "layer": key.value},
        )

    def status_map(self) -> dict[LayerKey, LayerStatus]:
        """Return a plain map of observed layer statuses."""
        return {layer.key: layer.status for layer in self.layers}


@dataclass(frozen=True, slots=True)
class ObservationVerification:
    """Result of re-checking an observation against the filesystem."""

    errors: tuple[str, ...]
    checked_paths: tuple[str, ...]

    @property
    def is_valid(self) -> bool:
        """True when every recorded evidence path matched the declaration."""
        return not self.errors

    def raise_if_invalid(self) -> None:
        """Raise a structured error when the observation cannot be verified."""
        if self.errors:
            raise HealthCoreError(
                "client observation does not match the checkout",
                details={"errors": list(self.errors)},
            )


def _layer(
    key: LayerKey,
    status: LayerStatus,
    present: tuple[str, ...] = (),
    absent: tuple[str, ...] = (),
    note: str = "",
) -> ObservedLayer:
    return ObservedLayer(
        key=key,
        status=status,
        present_evidence=present,
        absent_probes=absent,
        note=note,
    )


OBSERVED_CLIENTS: tuple[ClientObservation, ...] = (
    ClientObservation(
        platform=Platform.WEB,
        project_present=True,
        project_evidence=("frontend-v3/package.json", "frontend-v3/vite.config.ts"),
        layers=(
            _layer(
                LayerKey.API_CLIENT,
                LayerStatus.PRESENT,
                ("frontend-v3/src/api/client.ts", "frontend-v3/src/api/endpoints.ts"),
                note="axios + TanStack Query client with same-origin demo/live mode switch.",
            ),
            _layer(
                LayerKey.AUTH_BOUNDARY,
                LayerStatus.PRESENT,
                (
                    "frontend-v3/src/api/client.ts",
                    "frontend-v3/src/api/demoIsolation.test.ts",
                    "frontend-v3/src/api/client.writeBarrier.test.ts",
                ),
                note="withCredentials, /auth/refresh interceptor and demo isolation tests.",
            ),
            _layer(
                LayerKey.ERROR_HANDLING,
                LayerStatus.PARTIAL,
                (
                    "frontend-v3/src/hooks/useApiError.ts",
                    "frontend-v3/src/components/shared/AsyncBoundary.tsx",
                ),
                note="Reads legacy 'detail' only; canonical envelope fields and detail_ar are not consumed.",
            ),
            _layer(
                LayerKey.OFFLINE_OUTBOX,
                LayerStatus.ABSENT,
                ("frontend-v3/src/pages/patient-visit/PatientVisitReadinessPage.tsx",),
                ("frontend-v3/src/offline", "frontend-v3/src/api/offlineOutbox.ts"),
                note="Only monitoring types/UI and a generated dist/sw.js; no client outbox or replay module.",
            ),
            _layer(
                LayerKey.SYNC_CONFLICT,
                LayerStatus.ABSENT,
                ("frontend-v3/src/pages/patient-visit/PatientVisitReadinessPage.tsx",),
                ("frontend-v3/src/sync", "frontend-v3/src/api/conflictResolver.ts"),
                note="Readiness page explicitly records version conflict/audit contract as unproven.",
            ),
            _layer(
                LayerKey.ARABIC_RTL_A11Y,
                LayerStatus.PRESENT,
                (
                    "frontend-v3/index.html",
                    "frontend-v3/src/contexts/LocaleContext.tsx",
                    "frontend-v3/package.json",
                ),
                note="index.html lang=ar dir=rtl; LocaleContext direction; vitest-axe dependency present.",
            ),
        ),
        note="React/Vite web app; no synthetic Health Core adapter observed.",
    ),
    ClientObservation(
        platform=Platform.ANDROID,
        project_present=True,
        project_evidence=(
            "mobile/android/settings.gradle.kts",
            "mobile/android/app/build.gradle.kts",
        ),
        layers=(
            _layer(
                LayerKey.API_CLIENT,
                LayerStatus.PRESENT,
                (
                    "mobile/android/app/src/main/java/io/gula/android/di/NetworkModule.kt",
                    "mobile/android/app/src/main/java/io/gula/android/data/remote/interceptor/AuthInterceptor.kt",
                ),
                note="BuildConfig.API_BASE_URL consumed by NetworkModule and AuthInterceptor.",
            ),
            _layer(
                LayerKey.AUTH_BOUNDARY,
                LayerStatus.PRESENT,
                (
                    "mobile/android/app/src/main/java/io/gula/android/data/remote/interceptor/AuthInterceptor.kt",
                    "mobile/android/app/src/main/java/io/gula/android/data/remote/interceptor/CertificatePinningInterceptor.kt",
                ),
                note="Bearer/refresh interceptor and certificate pinning observed.",
            ),
            _layer(
                LayerKey.ERROR_HANDLING,
                LayerStatus.PRESENT,
                (
                    "mobile/android/app/src/main/java/io/gula/android/data/remote/interceptor/ErrorInterceptor.kt",
                    "mobile/android/app/src/main/java/io/gula/android/data/repository/ParseError.kt",
                ),
                note="Dedicated HTTP error interceptor and parse-error mapping observed.",
            ),
            _layer(
                LayerKey.OFFLINE_OUTBOX,
                LayerStatus.PRESENT,
                (
                    "mobile/android/app/src/main/java/io/gula/android/data/local/dao/SyncQueueDao.kt",
                    "mobile/android/app/src/main/java/io/gula/android/domain/usecase/ProcessOfflineQueueUseCase.kt",
                ),
                note="Room sync queue and offline queue use case with instrumented sync tests.",
            ),
            _layer(
                LayerKey.SYNC_CONFLICT,
                LayerStatus.PARTIAL,
                (
                    "mobile/android/app/src/main/java/io/gula/android/domain/usecase/SyncDataUseCase.kt",
                    "mobile/android/app/src/main/java/io/gula/android/data/repository/SyncRepositoryImpl.kt",
                ),
                (
                    "mobile/android/app/src/main/java/io/gula/android/domain/usecase/ResolveConflictsUseCase.kt",
                ),
                note="Sync process exists; only SQLite OnConflictStrategy.REPLACE, no decision/audit record.",
            ),
            _layer(
                LayerKey.ARABIC_RTL_A11Y,
                LayerStatus.PARTIAL,
                (
                    "mobile/android/app/src/main/res/values-ar/strings.xml",
                    "mobile/android/app/src/main/res/values-ar/themes.xml",
                ),
                note="Arabic resource bundles observed; RTL/a11y completeness not certified in this pass.",
            ),
        ),
        note="Kotlin/Gradle/Compose project with Hilt/KSP; no synthetic Health Core adapter observed.",
    ),
    ClientObservation(
        platform=Platform.IOS,
        project_present=False,
        project_evidence=(
            "mobile/ios/Gula/Core/Networking/APIClient.swift",
            "mobile/ios/GulaAppDelegate.swift",
        ),
        project_absence_probes=(
            "mobile/ios/Gula.xcodeproj",
            "mobile/ios/Gula.xcworkspace",
        ),
        layers=(
            _layer(
                LayerKey.API_CLIENT,
                LayerStatus.PARTIAL,
                ("mobile/ios/Gula/Core/Networking/APIClient.swift",),
                note="Swift source only: no Xcode project, so build/XCTest execution cannot be inspected.",
            ),
            _layer(
                LayerKey.AUTH_BOUNDARY,
                LayerStatus.PARTIAL,
                (
                    "mobile/ios/Gula/Core/Networking/APIAuthMiddleware.swift",
                    "mobile/ios/Gula/Core/Auth/KeychainManager.swift",
                ),
                note="Source-only auth middleware and Keychain token storage.",
            ),
            _layer(
                LayerKey.ERROR_HANDLING,
                LayerStatus.PARTIAL,
                ("mobile/ios/Gula/Core/Networking/APIError.swift",),
                note="Source-only typed errors; canonical envelope/Arabic detail not evidenced.",
            ),
            _layer(
                LayerKey.OFFLINE_OUTBOX,
                LayerStatus.PARTIAL,
                (
                    "mobile/ios/Gula/Core/Offline/SyncQueue.swift",
                    "mobile/ios/Gula/Core/Offline/SyncEngine.swift",
                ),
                note="Source-only sync queue/engine.",
            ),
            _layer(
                LayerKey.SYNC_CONFLICT,
                LayerStatus.PARTIAL,
                (
                    "mobile/ios/Gula/Core/Offline/ConflictResolver.swift",
                    "mobile/ios/Gula/Core/Offline/NetworkSynchronizer.swift",
                ),
                note="Source-only conflict resolver; executable test target could not be inspected.",
            ),
            _layer(
                LayerKey.ARABIC_RTL_A11Y,
                LayerStatus.PARTIAL,
                (
                    "mobile/ios/Gula/UI/Theme/RTLManager.swift",
                    "mobile/ios/Gula/Resources/ar.lproj/Localizable.strings",
                ),
                note="RTLManager.isRTL defaults to false until an Arabic locale/saved language is set.",
            ),
        ),
        note="Xcode project/workspace absent from checkout; sources and XCTest files exist but are not buildable here.",
    ),
    ClientObservation(
        platform=Platform.FLUTTER,
        project_present=True,
        project_evidence=("mobile/desktop/pubspec.yaml",),
        layers=(
            _layer(
                LayerKey.API_CLIENT,
                LayerStatus.PRESENT,
                (
                    "mobile/desktop/lib/core/api/api_client.dart",
                    "mobile/desktop/lib/core/utils/constants.dart",
                ),
                note="dio client, default API URL and validated URL override.",
            ),
            _layer(
                LayerKey.AUTH_BOUNDARY,
                LayerStatus.PRESENT,
                (
                    "mobile/desktop/lib/core/auth/auth_manager.dart",
                    "mobile/desktop/lib/core/auth/secure_storage.dart",
                ),
                note="Auth manager plus secure token storage.",
            ),
            _layer(
                LayerKey.ERROR_HANDLING,
                LayerStatus.PARTIAL,
                ("mobile/desktop/lib/core/api/api_exceptions.dart",),
                note="parseApiError reads detail/message; request_id/timestamp/detail_ar are not consumed.",
            ),
            _layer(
                LayerKey.OFFLINE_OUTBOX,
                LayerStatus.PRESENT,
                (
                    "mobile/desktop/lib/core/offline/database.dart",
                    "mobile/desktop/lib/core/offline/sync_queue_manager.dart",
                ),
                note="drift/sqlite database and sync queue manager.",
            ),
            _layer(
                LayerKey.SYNC_CONFLICT,
                LayerStatus.PRESENT,
                (
                    "mobile/desktop/lib/core/offline/conflict_resolver.dart",
                    "mobile/desktop/lib/core/offline/sync_engine.dart",
                ),
                note="Explicit ConflictStrategy/ConflictRecord/ConflictResolution vocabulary observed.",
            ),
            _layer(
                LayerKey.ARABIC_RTL_A11Y,
                LayerStatus.PRESENT,
                (
                    "mobile/desktop/lib/core/theme/theme_provider.dart",
                    "mobile/desktop/lib/l10n/app_ar.arb",
                ),
                note="Locale('ar','IQ') and isRtl=true defaults; Arabic ARB catalogue present.",
            ),
        ),
        note="Flutter desktop project (pubspec, macos/linux runners); no synthetic Health Core adapter observed.",
    ),
    ClientObservation(
        platform=Platform.DESKTOP,
        project_present=True,
        project_evidence=(
            "hospital_desktop/requirements.txt",
            "hospital_desktop/run.py",
            "hospital_desktop/config.py",
        ),
        layers=(
            _layer(
                LayerKey.API_CLIENT,
                LayerStatus.PRESENT,
                ("hospital_desktop/api_client.py", "hospital_desktop/config.py"),
                note="requests client with host allow-list and API base URL.",
            ),
            _layer(
                LayerKey.AUTH_BOUNDARY,
                LayerStatus.PRESENT,
                ("hospital_desktop/session.py", "hospital_desktop/api_client.py"),
                note="Encrypted token session plus bearer/refresh handling.",
            ),
            _layer(
                LayerKey.ERROR_HANDLING,
                LayerStatus.PARTIAL,
                ("hospital_desktop/api_client.py",),
                note="ApiError reads legacy detail; canonical envelope and detail_ar are not consumed.",
            ),
            _layer(
                LayerKey.OFFLINE_OUTBOX,
                LayerStatus.PRESENT,
                ("hospital_desktop/offline.py",),
                note="sqlite sync_log outbox with pending/synced/failed states.",
            ),
            _layer(
                LayerKey.SYNC_CONFLICT,
                LayerStatus.PARTIAL,
                ("hospital_desktop/offline.py",),
                note="resolve_conflict uses timestamp comparison only; no immutable disposition/audit record.",
            ),
            _layer(
                LayerKey.ARABIC_RTL_A11Y,
                LayerStatus.PRESENT,
                (
                    "hospital_desktop/main.py",
                    "hospital_desktop/l10n.py",
                    "hospital_desktop/widgets/dialogs.py",
                ),
                note="Qt RightToLeft layout when language=ar (default ar); translation manager present.",
            ),
        ),
        note="PySide6 hospital desktop app. Legacy real-identifier-shaped cache columns observed read-only in offline.py; not copied or modified.",
    ),
    ClientObservation(
        platform=Platform.EXPO,
        project_present=True,
        project_evidence=("mobile-expo/package.json", "mobile-expo/app.json"),
        layers=(
            _layer(
                LayerKey.API_CLIENT,
                LayerStatus.ABSENT,
                ("mobile-expo/App.tsx", "mobile-expo/README.md"),
                ("mobile-expo/src/api", "mobile-expo/src/api/client.ts"),
                note="App.tsx states a production submit must call the authenticated API; README states no data is sent to a backend.",
            ),
            _layer(
                LayerKey.AUTH_BOUNDARY,
                LayerStatus.ABSENT,
                ("mobile-expo/App.tsx",),
                ("mobile-expo/src/auth", "mobile-expo/src/auth/tokenStore.ts"),
                note="No token store, auth client or permission boundary observed.",
            ),
            _layer(
                LayerKey.ERROR_HANDLING,
                LayerStatus.PARTIAL,
                (
                    "mobile-expo/src/speech/types.ts",
                    "mobile-expo/src/speech/SpeechRecognitionService.ts",
                ),
                note="Speech-recognition-specific errors only; no canonical API error envelope handling.",
            ),
            _layer(
                LayerKey.OFFLINE_OUTBOX,
                LayerStatus.ABSENT,
                ("mobile-expo/README.md",),
                ("mobile-expo/src/offline", "mobile-expo/src/offline/outbox.ts"),
                note="Voice draft is saved locally with no outbox/replay contract module.",
            ),
            _layer(
                LayerKey.SYNC_CONFLICT,
                LayerStatus.ABSENT,
                ("mobile-expo/App.tsx",),
                ("mobile-expo/src/sync", "mobile-expo/src/sync/conflictResolver.ts"),
                note="No sync engine, conflict decision or audit record observed.",
            ),
            _layer(
                LayerKey.ARABIC_RTL_A11Y,
                LayerStatus.ABSENT,
                ("mobile-expo/app.json",),
                ("mobile-expo/src/i18n", "mobile-expo/src/localization"),
                note="Arabic UI copy and mic permission strings only; no locale library or direction/RTL setting in code.",
            ),
        ),
        note="Expo 54 voice-draft example; no API/RTL/i18n layer confirmed by read-only inspection.",
    ),
)


def observation_for(platform: Platform) -> ClientObservation:
    """Return the single observation recorded for ``platform``."""
    for observation in OBSERVED_CLIENTS:
        if observation.platform is platform:
            return observation
    raise HealthCoreError(
        "platform was not observed",
        details={"platform": platform.value},
    )


def verify_observation(
    observation: ClientObservation, repo_root: Path
) -> ObservationVerification:
    """Re-check recorded evidence against the checkout without modifying it."""
    errors: list[str] = []
    checked: list[str] = []

    def check(path: str, must_exist: bool, label: str) -> None:
        checked.append(path)
        exists = (repo_root / path).exists()
        if must_exist and not exists:
            errors.append(f"EXPECTED_PATH_MISSING: {label}: {path}")
        if not must_exist and exists:
            errors.append(f"ABSENCE_PROBE_PRESENT: {label}: {path}")

    prefix = observation.platform.value
    for path in observation.project_evidence:
        check(path, True, f"{prefix}.project")
    for path in observation.project_absence_probes:
        check(path, False, f"{prefix}.project")
    if not observation.project_present and not observation.project_absence_probes:
        errors.append(f"NO_PROJECT_ABSENCE_EVIDENCE: {prefix}")

    observed_keys = [layer.key for layer in observation.layers]
    if len(observed_keys) != len(set(observed_keys)):
        errors.append(f"DUPLICATE_LAYER_OBSERVATION: {prefix}")
    for key in REQUIRED_LAYERS:
        if key not in observed_keys:
            errors.append(f"MISSING_LAYER_OBSERVATION: {prefix}: {key.value}")

    for layer in observation.layers:
        label = f"{prefix}.{layer.key.value}"
        if not layer.present_evidence and layer.status is not LayerStatus.ABSENT:
            errors.append(f"NO_PRESENT_EVIDENCE: {label}")
        if not layer.absent_probes and layer.status is LayerStatus.ABSENT:
            errors.append(f"NO_ABSENCE_EVIDENCE: {label}")
        if layer.status is LayerStatus.PARTIAL and not layer.note.strip():
            errors.append(f"NO_PARTIAL_REASON: {label}")
        if not observation.project_present and layer.status is LayerStatus.PRESENT:
            errors.append(f"SOURCE_ONLY_LAYER_CLAIMED_PRESENT: {label}")
        for path in layer.present_evidence:
            check(path, True, label)
        for path in layer.absent_probes:
            check(path, False, label)

    return ObservationVerification(errors=tuple(errors), checked_paths=tuple(checked))
