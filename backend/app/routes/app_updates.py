"""Public application update policy endpoint.

The endpoint intentionally returns only release metadata. It does not expose
credentials, clinical data, deployment internals, or provider configuration.
The minimum supported version can be raised through environment configuration
when a release must become mandatory.
"""

from __future__ import annotations

import logging
import os
import re
from datetime import UTC, datetime
from typing import Final

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

logger = logging.getLogger("gula.app_updates")

router = APIRouter(prefix="/app-updates", tags=["app-updates"])

_DEFAULT_VERSION: Final[str] = "2.5.0"
_DEFAULT_STORE_URLS: Final[dict[str, str]] = {
    "android": "https://play.google.com/store/apps/details?id=io.gula.android",
    "windows": "https://github.com/samertts/gula-platform/releases",
    "macos": "https://github.com/samertts/gula-platform/releases",
    "linux": "https://github.com/samertts/gula-platform/releases",
    "web": "https://www.gula-platform.org/",
}
_VERSION_RE = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:[-+][0-9A-Za-z.-]+)?$")


class UpdatePolicy(BaseModel):
    platform: str
    current_version: str
    latest_version: str
    minimum_supported_version: str
    update_available: bool
    force_update: bool
    store_url: str
    release_notes_url: str = "https://github.com/samertts/gula-platform/releases"
    message: str = "A newer GULA version is available."
    message_ar: str = "يتوفر إصدار أحدث من منصة GULA."


class UpdateManifest(BaseModel):
    schema_version: int = Field(default=1, frozen=True)
    generated_at: datetime
    policies: dict[str, UpdatePolicy]


def _valid_version(value: str | None, fallback: str = _DEFAULT_VERSION) -> str:
    candidate = (value or "").strip()
    return candidate if _VERSION_RE.fullmatch(candidate) else fallback


def _version_tuple(value: str) -> tuple[int, int, int]:
    core = value.split("-", 1)[0].split("+", 1)[0]
    major, minor, patch = core.split(".")
    return int(major), int(minor), int(patch)


def version_is_less(current: str, target: str) -> bool:
    """Compare supported semantic versions without accepting arbitrary strings."""

    return _version_tuple(_valid_version(current)) < _version_tuple(_valid_version(target))


def _env_version(name: str, fallback: str) -> str:
    return _valid_version(os.getenv(name), fallback)


def _store_url(platform: str) -> str:
    env_name = f"GULA_{platform.upper()}_STORE_URL"
    return os.getenv(env_name, _DEFAULT_STORE_URLS.get(platform, _DEFAULT_STORE_URLS["web"]))


def build_policy(platform: str, current_version: str) -> UpdatePolicy:
    latest = _env_version(f"GULA_{platform.upper()}_LATEST_VERSION", _DEFAULT_VERSION)
    minimum = _env_version(
        f"GULA_{platform.upper()}_MINIMUM_SUPPORTED_VERSION",
        _DEFAULT_VERSION,
    )
    # A malformed or accidentally higher minimum must never make a client
    # impossible to update. Clamp minimum to latest for deterministic behavior.
    if _version_tuple(minimum) > _version_tuple(latest):
        logger.warning("Ignoring invalid update policy ordering for platform=%s", platform)
        minimum = latest
    normalized_current = _valid_version(current_version)
    return UpdatePolicy(
        platform=platform,
        current_version=normalized_current,
        latest_version=latest,
        minimum_supported_version=minimum,
        update_available=version_is_less(normalized_current, latest),
        force_update=version_is_less(normalized_current, minimum),
        store_url=_store_url(platform),
        release_notes_url=os.getenv(
            "GULA_RELEASE_NOTES_URL",
            "https://github.com/samertts/gula-platform/releases",
        ),
    )


@router.get("", response_model=UpdateManifest, response_class=JSONResponse)
async def get_update_manifest(
    platform: str = Query("web", pattern="^(android|windows|macos|linux|web)$"),
    version: str = Query(_DEFAULT_VERSION, min_length=5, max_length=32),
) -> UpdateManifest:
    """Return the update policy for one client platform.

    This is intentionally unauthenticated so an expired client can learn that
    it must update before login. The response contains release metadata only.
    """

    policy = build_policy(platform, version)
    return UpdateManifest(
        generated_at=datetime.now(UTC),
        policies={platform: policy},
    )
