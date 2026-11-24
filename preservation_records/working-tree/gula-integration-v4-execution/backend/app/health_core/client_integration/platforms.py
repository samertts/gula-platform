"""Vocabulary shared by client manifests, observations and validators."""

from __future__ import annotations

from enum import StrEnum


class Platform(StrEnum):
    """Client platforms observed in this checkout (no project is inferred)."""

    WEB = "web"
    ANDROID = "android"
    IOS = "ios"
    FLUTTER = "flutter"
    DESKTOP = "desktop"
    EXPO = "expo"


class LayerKey(StrEnum):
    """The six required client integration layers."""

    API_CLIENT = "api_client"
    AUTH_BOUNDARY = "auth_boundary"
    ERROR_HANDLING = "error_handling"
    OFFLINE_OUTBOX = "offline_outbox"
    SYNC_CONFLICT = "sync_conflict"
    ARABIC_RTL_A11Y = "arabic_rtl_a11y"


class LayerStatus(StrEnum):
    """Evidence-backed status of one layer in one observed client project."""

    PRESENT = "present"
    PARTIAL = "partial"
    ABSENT = "absent"


class ImplementationStatus(StrEnum):
    """Honest overall classification for a client platform."""

    IMPLEMENTED = "implemented"
    BLOCKED = "blocked"
    NOT_IMPLEMENTED = "not_implemented"


#: Sentinel used by guard tests to name the claim that must never be asserted here.
IMPLEMENTED = ImplementationStatus.IMPLEMENTED

REQUIRED_LAYERS: tuple[LayerKey, ...] = tuple(LayerKey)
