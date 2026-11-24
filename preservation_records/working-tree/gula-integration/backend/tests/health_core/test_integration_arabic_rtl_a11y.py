"""Tests for the Arabic-first RTL and WCAG AA requirement catalogue."""

from __future__ import annotations

from dataclasses import replace

import pytest
from app.health_core.common import HealthCoreError
from app.health_core.integration import (
    DEFAULT_SURFACE_ANNOTATIONS,
    REQUIRED_SURFACES,
    REQUIREMENT_CATALOGUE,
    A11yRequirement,
    Direction,
    RequirementKind,
    UiSurfaceAnnotation,
    validate_requirement_catalogue,
    validate_surfaces,
)


def _with_first_surface_changed(**changes: object) -> tuple[UiSurfaceAnnotation, ...]:
    changed = replace(DEFAULT_SURFACE_ANNOTATIONS[0], **changes)
    return (changed, *DEFAULT_SURFACE_ANNOTATIONS[1:])


def test_catalogue_covers_all_five_requirement_kinds() -> None:
    validation = validate_requirement_catalogue()
    assert validation.is_valid
    assert validation.errors == ()
    assert {item.kind for item in REQUIREMENT_CATALOGUE} == set(RequirementKind)
    assert len(REQUIREMENT_CATALOGUE) == 5


def test_default_annotations_cover_every_required_surface() -> None:
    validation = validate_surfaces(DEFAULT_SURFACE_ANNOTATIONS)
    assert validation.is_valid
    assert validation.checked_surfaces == tuple(
        surface.surface_id for surface in REQUIRED_SURFACES
    )
    assert {surface.client for surface in REQUIRED_SURFACES} == {
        "web",
        "android",
        "ios",
        "desktop",
        "mobile_expo",
    }


def test_missing_surface_is_reported() -> None:
    validation = validate_surfaces(DEFAULT_SURFACE_ANNOTATIONS[1:])
    assert not validation.is_valid
    assert any(
        error.startswith("MISSING_SURFACE") for error in validation.errors
    )


def test_ltr_direction_is_rejected() -> None:
    validation = validate_surfaces(_with_first_surface_changed(direction=Direction.LTR))
    assert "NON_RTL_DIRECTION: web.login" in validation.errors


def test_low_contrast_is_rejected() -> None:
    validation = validate_surfaces(_with_first_surface_changed(contrast_ratio=3.0))
    assert "LOW_CONTRAST: web.login" in validation.errors


def test_missing_focus_indicator_is_rejected() -> None:
    validation = validate_surfaces(_with_first_surface_changed(focus_indicator=False))
    assert "MISSING_FOCUS: web.login" in validation.errors


def test_missing_error_announcement_is_rejected() -> None:
    validation = validate_surfaces(
        _with_first_surface_changed(error_announcement=False)
    )
    assert "MISSING_ERROR_ANNOUNCEMENT: web.login" in validation.errors


def test_missing_localized_field_labels_are_rejected() -> None:
    validation = validate_surfaces(
        _with_first_surface_changed(field_labels_localized=False)
    )
    assert "MISSING_FIELD_LABELS: web.login" in validation.errors


def test_non_arabic_locale_is_rejected() -> None:
    validation = validate_surfaces(_with_first_surface_changed(locale="en"))
    assert "NON_ARABIC_LOCALE: web.login" in validation.errors
    assert "NON_RTL_DIRECTION: web.login" not in validation.errors


def test_duplicate_surface_annotation_is_rejected() -> None:
    validation = validate_surfaces(
        (*DEFAULT_SURFACE_ANNOTATIONS, DEFAULT_SURFACE_ANNOTATIONS[0])
    )
    assert "DUPLICATE_SURFACE: web.login" in validation.errors


def test_client_mismatch_is_rejected() -> None:
    validation = validate_surfaces(_with_first_surface_changed(client="android"))
    assert "CLIENT_MISMATCH: web.login" in validation.errors


def test_incomplete_catalogue_is_rejected() -> None:
    catalogue = tuple(
        item
        for item in REQUIREMENT_CATALOGUE
        if item.kind is not RequirementKind.FOCUS
    )
    validation = validate_requirement_catalogue(catalogue)
    assert not validation.is_valid
    assert any(
        error.startswith("REQUIREMENT_KIND:") for error in validation.errors
    )


def test_catalogue_rejects_missing_translation_and_low_threshold() -> None:
    bad = A11yRequirement(
        requirement_id="HC-A11Y-BAD",
        kind=RequirementKind.CONTRAST,
        detail_ar="",
        detail_en="",
        wcag_criterion="",
        minimum_contrast_ratio=3.0,
    )
    validation = validate_requirement_catalogue((*REQUIREMENT_CATALOGUE, bad))
    assert any(error.startswith("MISSING_DETAIL") for error in validation.errors)
    assert any(error.startswith("MISSING_WCAG") for error in validation.errors)
    assert any(
        error.startswith("LOW_CONTRAST_THRESHOLD") for error in validation.errors
    )


def test_validation_failure_raises_structured_error() -> None:
    validation = validate_surfaces(DEFAULT_SURFACE_ANNOTATIONS[1:])
    with pytest.raises(HealthCoreError) as exc:
        validation.raise_if_invalid()
    assert exc.value.code == "HEALTH_CORE_ERROR"
