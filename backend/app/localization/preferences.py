"""Language preference API backed by the existing accessibility profile table.

No duplicate user-language table is introduced. The effective language is
English until the requested language pack reaches READY.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from .language_registry import LanguageRegistry
from .pack_manager import PackManager
from .runtime import LanguageRuntime


class LanguagePreferenceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    preferred_language: str = Field(min_length=2, max_length=64)
    fallback_language: str = "en"
    auto_download: bool = True


class LanguagePreferenceResponse(BaseModel):
    preferred_language: str
    fallback_language: str
    effective_language: str
    direction: str
    lifecycle_state: str
    auto_download: bool
    download_required: bool


class PreferenceStore(Protocol):
    def load(self, user_id: int, lab_id: int) -> dict[str, Any]: ...
    def save(
        self,
        user_id: int,
        lab_id: int,
        payload: dict[str, Any],
        request: Request,
        current_user: Any,
    ) -> int: ...


@dataclass(slots=True)
class InMemoryPreferenceStore:
    records: dict[tuple[int, int], dict[str, Any]]

    def __init__(self) -> None:
        self.records = {}

    def load(self, user_id: int, lab_id: int) -> dict[str, Any]:
        return dict(self.records.get((user_id, lab_id), {}))

    def save(
        self,
        user_id: int,
        lab_id: int,
        payload: dict[str, Any],
        request: Request,
        current_user: Any,
    ) -> int:
        self.records[(user_id, lab_id)] = dict(payload)
        return 1


class AccessibilityProfilePreferenceStore:
    """Production adapter using the pre-existing accessibility profile record."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def load(self, user_id: int, lab_id: int) -> dict[str, Any]:
        from app.models.user_preferences import AccessibilityProfile

        profile = (
            self.db.query(AccessibilityProfile)
            .filter(
                AccessibilityProfile.user_id == user_id,
                AccessibilityProfile.lab_id == lab_id,
            )
            .first()
        )
        return dict(profile.preferences) if profile else {}

    def save(
        self,
        user_id: int,
        lab_id: int,
        payload: dict[str, Any],
        request: Request,
        current_user: Any,
    ) -> int:
        from datetime import datetime

        from app._compat import UTC
        from app.models.user_preferences import AccessibilityProfile
        from app.routes.user_preferences import _audit

        profile = (
            self.db.query(AccessibilityProfile)
            .filter(
                AccessibilityProfile.user_id == user_id,
                AccessibilityProfile.lab_id == lab_id,
            )
            .first()
        )
        before_version = profile.version if profile else 0
        if profile is None:
            profile = AccessibilityProfile(
                user_id=user_id,
                lab_id=lab_id,
                preferences={},
                version=1,
            )
            self.db.add(profile)
        else:
            profile.version += 1
        merged = dict(profile.preferences or {})
        merged.update(payload)
        profile.preferences = merged
        profile.updated_at = datetime.now(UTC)
        self.db.flush()
        _audit(
            self.db,
            request,
            current_user,
            "updated",
            {
                "section": "localization",
                "before_version": before_version,
                "after_version": profile.version,
                "preferred_language": payload["preferred_language"],
            },
        )
        self.db.commit()
        return int(profile.version)


def _runtime() -> LanguageRuntime:
    return LanguageRuntime(LanguageRegistry.load())


def _pack_manager() -> PackManager:
    import os
    from pathlib import Path

    synthetic_enabled = os.getenv("GULS_ALLOW_SYNTHETIC_PACKS", "0") == "1"
    return PackManager(
        Path(os.getenv("GULS_LOCAL_PACK_ROOT", str(Path.home() / ".gula" / "language-packs"))),
        LanguageRegistry.load(),
        allow_synthetic_packs=synthetic_enabled,
        synthetic_signer_key_id=os.getenv("GULS_SYNTHETIC_SIGNER_KEY_ID", "")
        if synthetic_enabled
        else "",
    )


def validate_preference(
    payload: LanguagePreferenceRequest,
    registry: LanguageRegistry,
    pack_manager: PackManager,
) -> LanguagePreferenceResponse:
    definition = registry.resolve(payload.preferred_language)
    if definition is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "LANGUAGE_NOT_FOUND",
                "message": "The requested language is not registered.",
            },
        )
    if (
        not definition.is_active
        or definition.locale_tag is None
        or not definition.is_publishable
        or definition.approval_status != "approved"
        or definition.linguistic_approval_status != "approved"
    ):
        raise HTTPException(
            status_code=409,
            detail={
                "code": "LANGUAGE_NOT_ACTIVE",
                "message": "The requested language standard is not approved.",
            },
        )
    fallback = registry.resolve(payload.fallback_language)
    if fallback is None or fallback.language_id != registry.fallback_language:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "INVALID_FALLBACK_LANGUAGE",
                "message": "English is the only permitted fallback.",
            },
        )
    state = pack_manager.state(definition.language_id)
    ready = state == "READY" and definition.is_active
    effective = definition.language_id if ready else registry.fallback_language
    return LanguagePreferenceResponse(
        preferred_language=definition.language_id,
        fallback_language=fallback.language_id,
        effective_language=effective,
        direction="ltr" if effective == "en" else LanguageRuntime(registry).direction(effective),
        lifecycle_state=state,
        auto_download=payload.auto_download,
        download_required=not ready and payload.auto_download,
    )


def create_router(
    *,
    registry: LanguageRegistry,
    pack_manager: PackManager,
    preference_store_provider: Any,
    current_user_provider: Any,
) -> APIRouter:
    local_router = APIRouter(
        prefix="/api/v1/users/me/preferences", tags=["localization-preferences"]
    )

    @local_router.put("/language", response_model=LanguagePreferenceResponse)
    def set_language(
        payload: LanguagePreferenceRequest,
        request: Request,
        current_user: Any = Depends(current_user_provider),
        preference_store: PreferenceStore = Depends(preference_store_provider),
    ) -> LanguagePreferenceResponse:
        response = validate_preference(payload, registry, pack_manager)
        preference_store.save(
            int(current_user.id),
            int(current_user.lab_id),
            {
                "language": response.preferred_language,
                "fallback_language": response.fallback_language,
                "auto_download": response.auto_download,
            },
            request,
            current_user,
        )
        return response

    return local_router
