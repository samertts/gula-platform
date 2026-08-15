"""Authenticated user-owned accessibility and health-preference APIs.

Accessibility preferences are presentation-only. Health preferences are optional,
consent-bound, encrypted at rest, and never consulted by authorization code.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app._compat import UTC
from shared.security.encryption import decrypt_value, encrypt_value

from ..config import ENCRYPTION_KEY
from ..database import get_db
from ..models.lab_user import LabUser
from ..models.user_preferences import AccessibilityProfile, HealthPreference
from ..security.dependencies import require_institutional_user
from ..services.audit_service import log_action

router = APIRouter(prefix="/user-preferences", tags=["user-preferences"])


AccessibilityLanguage = Literal["ar-IQ", "ar", "en", "ku", "tk", "syr", "fa"]
FontSize = Literal["small", "medium", "large", "x-large"]
ColorBlindMode = Literal["none", "protanopia", "deuteranopia", "tritanopia", "monochrome"]


class AccessibilityPreferences(BaseModel):
    model_config = ConfigDict(extra="forbid")

    language: AccessibilityLanguage = "ar-IQ"
    font_size: FontSize = "medium"
    text_scale: float = Field(default=1.0, ge=0.85, le=2.0)
    high_contrast: bool = False
    color_blind_mode: ColorBlindMode = "none"
    reduced_color_dependence: bool = True
    screen_reader_optimized: bool = False
    reduced_motion: bool = False
    captions: bool = True
    text_alternatives: bool = True
    visual_alerts: bool = True
    transcripts: bool = True
    mute_safe_notifications: bool = True
    larger_touch_targets: bool = False
    reduced_interaction_complexity: bool = False
    longer_timeout: bool = False
    keyboard_navigation: bool = True
    voice_interaction: bool = False
    dyslexia_friendly: bool = False
    simplified_interface: bool = False
    reduced_visual_density: bool = False
    clear_language: bool = False
    step_by_step_workflows: bool = False
    reduced_notifications: bool = False
    disable_flashing: bool = True
    static_alternatives: bool = True


class AccessibilityUpdateRequest(AccessibilityPreferences):
    version: int | None = Field(default=None, ge=1)


class AccessibilityResponse(AccessibilityPreferences):
    version: int
    status: Literal["saved", "default"] = "saved"


class HealthPreferencesPayload(BaseModel):
    """User-entered health information; never inferred by GULA."""

    model_config = ConfigDict(extra="forbid")

    allergies: list[str] = Field(default_factory=list, max_length=20)
    chronic_conditions: list[str] = Field(default_factory=list, max_length=20)
    communication_needs: str | None = Field(default=None, max_length=2000)
    emergency_assistance_preferences: str | None = Field(default=None, max_length=2000)
    other_health_considerations: str | None = Field(default=None, max_length=4000)


class HealthUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    preferences: HealthPreferencesPayload
    consent: bool
    consent_version: str = Field(..., min_length=1, max_length=32)
    version: int | None = Field(default=None, ge=1)


class HealthResponse(BaseModel):
    status: Literal["saved", "consent_required", "empty"]
    consent_granted: bool
    consent_version: str | None = None
    version: int | None = None
    preferences: HealthPreferencesPayload | None = None


_DEFAULT_ACCESSIBILITY = AccessibilityPreferences().model_dump()


def _audit(
    db: Session,
    request: Request,
    current_user: LabUser,
    action: str,
    details: dict[str, object],
) -> None:
    """Write only metadata to the audit log; never place health payloads in it."""
    log_action(
        db=db,
        action=action,
        resource_type="user_preferences",
        resource_id=current_user.id,
        user_id=current_user.id,
        user_role=current_user.role,
        lab_id=current_user.lab_id,
        details=details,
        ip_address=request.client.host if request.client else None,
    )


def _check_version(existing_version: int, requested_version: int | None) -> None:
    if requested_version is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "VERSION_REQUIRED", "message": "A current version is required for updates."},
        )
    if requested_version != existing_version:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "STALE_VERSION",
                "message": "The preferences changed; reload before saving.",
                "current_version": existing_version,
            },
        )


def _encryption_key() -> str:
    if not ENCRYPTION_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Sensitive preference storage is unavailable until encryption is configured.",
        )
    return ENCRYPTION_KEY


@router.get("/accessibility", response_model=AccessibilityResponse)
def get_accessibility(
    current_user: LabUser = Depends(require_institutional_user),
    db: Session = Depends(get_db),
) -> AccessibilityResponse:
    profile = (
        db.query(AccessibilityProfile)
        .filter(
            AccessibilityProfile.user_id == current_user.id,
            AccessibilityProfile.lab_id == current_user.lab_id,
        )
        .first()
    )
    if profile is None:
        return AccessibilityResponse(**_DEFAULT_ACCESSIBILITY, version=0, status="default")
    return AccessibilityResponse(**profile.preferences, version=profile.version, status="saved")


@router.put("/accessibility", response_model=AccessibilityResponse)
def update_accessibility(
    data: AccessibilityUpdateRequest,
    request: Request,
    current_user: LabUser = Depends(require_institutional_user),
    db: Session = Depends(get_db),
) -> AccessibilityResponse:
    profile = (
        db.query(AccessibilityProfile)
        .filter(
            AccessibilityProfile.user_id == current_user.id,
            AccessibilityProfile.lab_id == current_user.lab_id,
        )
        .first()
    )
    before_version = profile.version if profile else 0
    if profile is not None:
        _check_version(profile.version, data.version)
        profile.preferences = data.model_dump(exclude={"version"})
        profile.version += 1
        profile.updated_at = datetime.now(UTC)
    else:
        profile = AccessibilityProfile(
            user_id=current_user.id,
            lab_id=current_user.lab_id,
            preferences=data.model_dump(exclude={"version"}),
            version=1,
        )
        db.add(profile)
    _audit(
        db,
        request,
        current_user,
        "updated",
        {"section": "accessibility", "before_version": before_version, "after_version": profile.version},
    )
    db.commit()
    db.refresh(profile)
    return AccessibilityResponse(**profile.preferences, version=profile.version, status="saved")


@router.get("/health", response_model=HealthResponse)
def get_health_preferences(
    current_user: LabUser = Depends(require_institutional_user),
    db: Session = Depends(get_db),
) -> HealthResponse:
    profile = (
        db.query(HealthPreference)
        .filter(
            HealthPreference.user_id == current_user.id,
            HealthPreference.lab_id == current_user.lab_id,
        )
        .first()
    )
    if profile is None:
        return HealthResponse(status="empty", consent_granted=False)
    if not profile.consent_granted or not profile.encrypted_payload:
        return HealthResponse(
            status="consent_required",
            consent_granted=False,
            consent_version=profile.consent_version,
            version=profile.version,
        )
    try:
        payload = HealthPreferencesPayload.model_validate(
            json.loads(decrypt_value(profile.encrypted_payload, _encryption_key())),
        )
    except HTTPException:
        raise
    except Exception as exc:
        # Do not disclose ciphertext or plaintext in logs/responses.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Sensitive preference storage could not be decrypted.",
        ) from exc
    return HealthResponse(
        status="saved",
        consent_granted=True,
        consent_version=profile.consent_version,
        version=profile.version,
        preferences=payload,
    )


@router.put("/health", response_model=HealthResponse)
def update_health_preferences(
    data: HealthUpdateRequest,
    request: Request,
    current_user: LabUser = Depends(require_institutional_user),
    db: Session = Depends(get_db),
) -> HealthResponse:
    if not data.consent:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "CONSENT_REQUIRED", "message": "Explicit consent is required to save health preferences."},
        )
    profile = (
        db.query(HealthPreference)
        .filter(
            HealthPreference.user_id == current_user.id,
            HealthPreference.lab_id == current_user.lab_id,
        )
        .first()
    )
    before_version = profile.version if profile else 0
    if profile is not None:
        _check_version(profile.version, data.version)
    encrypted = encrypt_value(
        json.dumps(data.preferences.model_dump(), sort_keys=True, ensure_ascii=False),
        _encryption_key(),
    )
    now = datetime.now(UTC)
    if profile is None:
        profile = HealthPreference(
            user_id=current_user.id,
            lab_id=current_user.lab_id,
            encrypted_payload=encrypted,
            consent_granted=True,
            consent_version=data.consent_version,
            consented_at=now,
            revoked_at=None,
            version=1,
        )
        db.add(profile)
    else:
        profile.encrypted_payload = encrypted
        profile.consent_granted = True
        profile.consent_version = data.consent_version
        profile.consented_at = now
        profile.revoked_at = None
        profile.version += 1
        profile.updated_at = now
    _audit(
        db,
        request,
        current_user,
        "updated",
        {
            "section": "health_preferences",
            "before_version": before_version,
            "after_version": profile.version,
            "consent_granted": True,
            "consent_version": data.consent_version,
        },
    )
    db.commit()
    db.refresh(profile)
    return HealthResponse(
        status="saved",
        consent_granted=True,
        consent_version=profile.consent_version,
        version=profile.version,
        preferences=data.preferences,
    )


@router.delete("/health", response_model=HealthResponse)
def revoke_health_preferences(
    request: Request,
    current_user: LabUser = Depends(require_institutional_user),
    db: Session = Depends(get_db),
) -> HealthResponse:
    profile = (
        db.query(HealthPreference)
        .filter(
            HealthPreference.user_id == current_user.id,
            HealthPreference.lab_id == current_user.lab_id,
        )
        .first()
    )
    if profile is None:
        return HealthResponse(status="empty", consent_granted=False)
    before_version = profile.version
    profile.encrypted_payload = None
    profile.consent_granted = False
    profile.revoked_at = datetime.now(UTC)
    profile.version += 1
    profile.updated_at = datetime.now(UTC)
    _audit(
        db,
        request,
        current_user,
        "revoked",
        {
            "section": "health_preferences",
            "before_version": before_version,
            "after_version": profile.version,
            "consent_granted": False,
        },
    )
    db.commit()
    return HealthResponse(
        status="consent_required",
        consent_granted=False,
        consent_version=profile.consent_version,
        version=profile.version,
    )
