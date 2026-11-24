"""Arabic-first RTL and WCAG AA requirement catalogue (read-only contracts).

This module declares structured, testable accessibility requirements and
per-surface annotations for the synthetic client integrations. It contains no
UI code, no framework import and no rendering logic. The default annotations
express the *target* contract; the read-only client inventory in the workstream
report records where existing clients already satisfy it and where work remains.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum

from app.health_core.common import HealthCoreError

MINIMUM_CONTRAST_RATIO = 4.5


class Direction(StrEnum):
    RTL = "rtl"
    LTR = "ltr"


class RequirementKind(StrEnum):
    FIELD_LABEL = "field_label"
    DIRECTION = "direction"
    CONTRAST = "contrast"
    FOCUS = "focus"
    ERROR_ANNOUNCEMENT = "error_announcement"


@dataclass(frozen=True, slots=True)
class A11yRequirement:
    """One Arabic-first accessibility requirement."""

    requirement_id: str
    kind: RequirementKind
    detail_ar: str
    detail_en: str
    wcag_criterion: str
    minimum_contrast_ratio: float | None = None


REQUIREMENT_CATALOGUE: tuple[A11yRequirement, ...] = (
    A11yRequirement(
        requirement_id="HC-A11Y-001",
        kind=RequirementKind.FIELD_LABEL,
        detail_ar="كل حقل إدخال له تسمية عربية واضحة ومتصلة به برمجياً.",
        detail_en="Every input field has a clear Arabic label programmatically associated with it.",
        wcag_criterion="3.3.2 Labels or Instructions",
    ),
    A11yRequirement(
        requirement_id="HC-A11Y-002",
        kind=RequirementKind.DIRECTION,
        detail_ar="اتجاه الواجهة من اليمين إلى اليسار افتراضياً للعربية.",
        detail_en="The interface direction is right-to-left by default for Arabic.",
        wcag_criterion="3.1.1 Language of Page",
    ),
    A11yRequirement(
        requirement_id="HC-A11Y-003",
        kind=RequirementKind.CONTRAST,
        detail_ar="تباين النص العادي لا يقل عن 4.5:1 مع الخلفية.",
        detail_en="Normal text contrast is at least 4.5:1 against its background.",
        wcag_criterion="1.4.3 Contrast (Minimum)",
        minimum_contrast_ratio=MINIMUM_CONTRAST_RATIO,
    ),
    A11yRequirement(
        requirement_id="HC-A11Y-004",
        kind=RequirementKind.FOCUS,
        detail_ar="مؤشر تركيز مرئي لكل عنصر قابل للتشغيل بلوحة المفاتيح.",
        detail_en="A visible focus indicator exists for every keyboard-operable control.",
        wcag_criterion="2.4.7 Focus Visible",
    ),
    A11yRequirement(
        requirement_id="HC-A11Y-005",
        kind=RequirementKind.ERROR_ANNOUNCEMENT,
        detail_ar="تُعلن أخطاء التحقق للمستخدم عبر تقنية مساعدة دون اعتماد على اللون فقط.",
        detail_en="Validation errors are announced to assistive technology and not conveyed by colour alone.",
        wcag_criterion="3.3.1 Error Identification; 4.1.3 Status Messages",
    ),
)


@dataclass(frozen=True, slots=True)
class SurfaceAnnotation:
    """A required UI surface, identified by client and surface id."""

    surface_id: str
    client: str
    locale: str = "ar"


REQUIRED_SURFACES: tuple[SurfaceAnnotation, ...] = (
    SurfaceAnnotation("web.login", "web"),
    SurfaceAnnotation("web.workspace_selector", "web"),
    SurfaceAnnotation("web.patient_list", "web"),
    SurfaceAnnotation("web.result_entry", "web"),
    SurfaceAnnotation("web.offline_queue", "web"),
    SurfaceAnnotation("android.login", "android"),
    SurfaceAnnotation("android.result_entry", "android"),
    SurfaceAnnotation("android.offline_queue", "android"),
    SurfaceAnnotation("ios.login", "ios"),
    SurfaceAnnotation("ios.result_entry", "ios"),
    SurfaceAnnotation("ios.offline_queue", "ios"),
    SurfaceAnnotation("desktop.login", "desktop"),
    SurfaceAnnotation("desktop.patient_list", "desktop"),
    SurfaceAnnotation("desktop.result_entry", "desktop"),
    SurfaceAnnotation("mobile_expo.voice_draft", "mobile_expo"),
)


@dataclass(frozen=True, slots=True)
class UiSurfaceAnnotation:
    """Declarative RTL and accessibility annotation for one UI surface."""

    surface_id: str
    client: str
    direction: Direction
    field_labels_localized: bool
    contrast_ratio: float
    focus_indicator: bool
    error_announcement: bool
    locale: str = "ar"
    notes: str = ""


@dataclass(frozen=True, slots=True)
class A11yValidation:
    """Result of catalogue/surface validation."""

    errors: tuple[str, ...]
    checked_surfaces: tuple[str, ...]

    @property
    def is_valid(self) -> bool:
        """True when no violation was found."""
        return not self.errors

    def raise_if_invalid(self) -> None:
        """Raise a structured synthetic error when violations exist."""
        if self.errors:
            raise HealthCoreError(
                "Arabic RTL / WCAG AA contract violations",
                details={"errors": list(self.errors)},
            )


def validate_requirement_catalogue(
    catalogue: Iterable[A11yRequirement] = REQUIREMENT_CATALOGUE,
) -> A11yValidation:
    """Validate catalogue completeness and bilingual requirement records."""
    records = tuple(catalogue)
    errors: list[str] = []
    kinds = [record.kind for record in records]
    for kind in RequirementKind:
        if kinds.count(kind) != 1:
            errors.append(f"REQUIREMENT_KIND: expected exactly one {kind.value}")
    for record in records:
        if not record.detail_ar.strip() or not record.detail_en.strip():
            errors.append(f"MISSING_DETAIL: {record.requirement_id}")
        if not record.wcag_criterion.strip():
            errors.append(f"MISSING_WCAG: {record.requirement_id}")
        if (
            record.kind is RequirementKind.CONTRAST
            and (record.minimum_contrast_ratio or 0) < MINIMUM_CONTRAST_RATIO
        ):
            errors.append(f"LOW_CONTRAST_THRESHOLD: {record.requirement_id}")
    return A11yValidation(errors=tuple(errors), checked_surfaces=())


def validate_surfaces(
    surfaces: Iterable[UiSurfaceAnnotation],
    required_surfaces: Iterable[SurfaceAnnotation] = REQUIRED_SURFACES,
) -> A11yValidation:
    """Validate that every required surface has direction and a11y annotations."""
    annotations = tuple(surfaces)
    required = tuple(required_surfaces)
    errors = list(validate_requirement_catalogue().errors)
    checked: list[str] = []

    by_id: dict[str, list[UiSurfaceAnnotation]] = {}
    for annotation in annotations:
        by_id.setdefault(annotation.surface_id, []).append(annotation)

    for expected in required:
        checked.append(expected.surface_id)
        candidates = by_id.get(expected.surface_id, [])
        if not candidates:
            errors.append(f"MISSING_SURFACE: {expected.surface_id}")
            continue
        if len(candidates) > 1:
            errors.append(f"DUPLICATE_SURFACE: {expected.surface_id}")
            continue
        annotation = candidates[0]
        prefix = expected.surface_id
        if annotation.client != expected.client:
            errors.append(f"CLIENT_MISMATCH: {prefix}")
        if not annotation.locale.startswith("ar"):
            errors.append(f"NON_ARABIC_LOCALE: {prefix}")
        if annotation.direction is not Direction.RTL:
            errors.append(f"NON_RTL_DIRECTION: {prefix}")
        if not annotation.field_labels_localized:
            errors.append(f"MISSING_FIELD_LABELS: {prefix}")
        if annotation.contrast_ratio < MINIMUM_CONTRAST_RATIO:
            errors.append(f"LOW_CONTRAST: {prefix}")
        if not annotation.focus_indicator:
            errors.append(f"MISSING_FOCUS: {prefix}")
        if not annotation.error_announcement:
            errors.append(f"MISSING_ERROR_ANNOUNCEMENT: {prefix}")

    return A11yValidation(errors=tuple(errors), checked_surfaces=tuple(checked))


def _annotate(surface: SurfaceAnnotation, notes: str = "") -> UiSurfaceAnnotation:
    return UiSurfaceAnnotation(
        surface_id=surface.surface_id,
        client=surface.client,
        direction=Direction.RTL,
        field_labels_localized=True,
        contrast_ratio=MINIMUM_CONTRAST_RATIO,
        focus_indicator=True,
        error_announcement=True,
        locale=surface.locale,
        notes=notes,
    )


DEFAULT_SURFACE_ANNOTATIONS: tuple[UiSurfaceAnnotation, ...] = tuple(
    _annotate(surface) for surface in REQUIRED_SURFACES
)
