"""Deterministic coverage report built only from validated manifests."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.health_core.client_integration.manifests import (
    DEFAULT_MANIFESTS,
    ClientManifest,
)
from app.health_core.client_integration.observations import (
    OBSERVED_CLIENTS,
    ClientObservation,
    observation_for,
)
from app.health_core.client_integration.platforms import (
    ImplementationStatus,
    LayerKey,
    LayerStatus,
    Platform,
)
from app.health_core.client_integration.validators import (
    REPO_ROOT,
    validate_manifest,
)


@dataclass(frozen=True, slots=True)
class PlatformCoverage:
    """One row of the honest client coverage report."""

    platform: Platform
    project_present: bool
    status: ImplementationStatus
    layer_statuses: tuple[tuple[LayerKey, LayerStatus], ...]
    reasons: tuple[str, ...]
    validation_errors: tuple[str, ...]
    checked_paths: tuple[str, ...]

    @property
    def contract_declared_and_validated(self) -> bool:
        """True only when the manifest passed every fail-closed check."""
        return not self.validation_errors

    @property
    def end_to_end_verified(self) -> bool:
        """Always false: no client application was modified or exercised here."""
        return False


def build_coverage_report(
    manifests: tuple[ClientManifest, ...] = DEFAULT_MANIFESTS,
    observations: tuple[ClientObservation, ...] = OBSERVED_CLIENTS,
    *,
    repo_root: Path | None = REPO_ROOT,
) -> tuple[PlatformCoverage, ...]:
    """Build coverage rows, keeping validation errors visible instead of hiding them."""
    observed_platforms = {item.platform for item in observations}
    rows: list[PlatformCoverage] = []
    for manifest in manifests:
        if manifest.platform not in observed_platforms:
            continue
        observation = observation_for(manifest.platform)
        validation = validate_manifest(manifest, observation, repo_root=repo_root)
        rows.append(
            PlatformCoverage(
                platform=manifest.platform,
                project_present=observation.project_present,
                status=validation.status,
                layer_statuses=tuple(manifest.layer_statuses),
                reasons=validation.reasons,
                validation_errors=validation.errors,
                checked_paths=validation.checked_paths,
            )
        )
    return tuple(rows)


def render_coverage_report(rows: tuple[PlatformCoverage, ...]) -> str:
    """Render a markdown table without any implied implementation claim."""
    lines = [
        "| Platform | Project present | Classification | Layers (present/partial/absent) | Manifest valid | End-to-end verified |",
        "|---|---|---|---|---|---|",
    ]
    for row in rows:
        counts = {
            status.value: sum(1 for _, layer_status in row.layer_statuses if layer_status is status)
            for status in LayerStatus
        }
        layers = "/".join(str(counts[status.value]) for status in LayerStatus)
        lines.append(
            f"| {row.platform.value} | {'YES' if row.project_present else 'NO'} | "
            f"{row.status.value.upper().replace('_', ' ')} | {layers} | "
            f"{'YES' if row.contract_declared_and_validated else 'NO'} | NO |"
        )
    lines.extend(
        [
            "",
            "Contract declared/validated = the manifest is complete, WS-C aligned and "
            "consistent with the read-only filesystem observation.",
            "End-to-end verified = NO for every platform: no client application file was "
            "modified and no real client behavior was executed.",
        ]
    )
    return "\n".join(lines)
