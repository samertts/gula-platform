"""User communication preferences service (PROGRAM-COMM-003).

CRUD for the per-user preference document, the channel catalog (which
channels exist, which are health-UP, which are admin-mandatory) and the
mute category/channel helpers. Pure decision logic lives in
:mod:`domain`; this module only persists + validates.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app._compat import UTC

from ...models.communication_experience import UserPreferencesRow
from .domain import (
    KNOWN_CHANNELS,
    MANDATORY_CATEGORIES,
    MANDATORY_CHANNELS,
    NotificationCategory,
    UserPreferences,
    UserPriority,
)

logger = logging.getLogger("gula.communication.experience.preferences")


def get_preferences(db: Session, user_id: int) -> UserPreferences:
    row = db.query(UserPreferencesRow).filter(UserPreferencesRow.user_id == user_id).first()
    if row is None:
        return UserPreferences.defaults(user_id)
    return UserPreferences.from_json(user_id, row.preferences)


def save_preferences(db: Session, user_id: int, prefs: UserPreferences) -> UserPreferences:
    prefs.user_id = user_id
    prefs.updated_at = datetime.now(UTC).isoformat()
    row = db.query(UserPreferencesRow).filter(UserPreferencesRow.user_id == user_id).first()
    if row is None:
        db.add(UserPreferencesRow(user_id=user_id, preferences=prefs.to_json()))
    else:
        row.preferences = prefs.to_json()
    db.commit()
    return prefs


def update_preferences(
    db: Session,
    user_id: int,
    patch: dict[str, Any],
) -> UserPreferences:
    """Merge a partial patch into the stored document (no Core changes).

    Mandatory categories and channels can never be disabled — the patch is
    sanitized before persistence.
    """
    current = get_preferences(db, user_id)
    if patch.get("locale"):
        current.locale = str(patch["locale"])[:10]
    if patch.get("timezone"):
        current.timezone = str(patch["timezone"])[:64]
    if "channels" in patch and isinstance(patch["channels"], dict):
        for channel, enabled in patch["channels"].items():
            if channel in MANDATORY_CHANNELS:
                continue
            current.channels[str(channel)] = bool(enabled)
    if "channel_priority" in patch and isinstance(patch["channel_priority"], list):
        current.channel_priority = [str(c) for c in patch["channel_priority"]]
    if "categories" in patch and isinstance(patch["categories"], dict):
        for category, enabled in patch["categories"].items():
            if category in MANDATORY_CATEGORIES:
                continue
            current.categories[str(category)] = bool(enabled)
    if "frequency" in patch:
        current.frequency = UserPreferences.frequency.__class__(str(patch["frequency"]))
    if patch.get("digest_schedule"):
        current.digest_schedule = str(patch["digest_schedule"])[:10]
    if "quiet_hours" in patch and isinstance(patch["quiet_hours"], dict):
        current.quiet_hours = current.quiet_hours.from_dict(
            {**current.quiet_hours.to_dict(), **patch["quiet_hours"]},
        )
    if "weekend_rules" in patch:
        current.weekend_rules = bool(patch["weekend_rules"])
    if "holiday_rules" in patch:
        current.holiday_rules = bool(patch["holiday_rules"])
    if "emergency_override" in patch:
        current.emergency_override = bool(patch["emergency_override"])
    return save_preferences(db, user_id, current)


def mute_category(db: Session, user_id: int, category: str, muted: bool = True) -> UserPreferences:
    """Mute/unmute one category (mandatory categories are protected)."""
    if category in MANDATORY_CATEGORIES:
        raise ValueError(f"category is mandatory and cannot be muted: {category}")
    current = get_preferences(db, user_id)
    current.categories[str(category)] = not muted
    return save_preferences(db, user_id, current)


def mute_channel(db: Session, user_id: int, channel: str, muted: bool = True) -> UserPreferences:
    """Mute/unmute one channel (mandatory channels are protected)."""
    if channel in MANDATORY_CHANNELS:
        raise ValueError(f"channel is mandatory and cannot be muted: {channel}")
    current = get_preferences(db, user_id)
    current.channels[str(channel)] = not muted
    return save_preferences(db, user_id, current)


def channel_catalog(
    *,
    provider_channels: list[str] | None = None,
    provider_states: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    """Catalog of every manageable channel + its runtime status.

    ``provider_channels``/``provider_states`` come from the Communication
    Center health snapshot; ``inapp`` is always available. Every known channel
    is listed so users can configure all providers even when one is down or
    not yet registered.
    """
    provider_channels = set(provider_channels or ()) | {"inapp"}
    provider_states = provider_states or {}
    catalog = []
    for channel in KNOWN_CHANNELS:
        available = channel in provider_channels
        if channel in provider_states:
            status = provider_states[channel]
        elif channel == "inapp":
            status = "ready"
        elif available:
            status = "down"
        else:
            status = "unregistered"
        catalog.append(
            {
                "id": channel,
                "available": available,
                "status": status,
                "mandatory": channel in MANDATORY_CHANNELS,
            },
        )
    return catalog


def categories() -> list[dict[str, str]]:
    return [
        {
            "id": c.value,
            "mandatory": c.value in MANDATORY_CATEGORIES,
            "label_ar": _CATEGORY_LABEL_AR.get(c.value, c.value),
            "label_en": _CATEGORY_LABEL_EN.get(c.value, c.value),
        }
        for c in NotificationCategory
    ]


def priorities() -> list[dict[str, str]]:
    return [
        {
            "id": p.value,
            "label_ar": _PRIORITY_LABEL_AR.get(p.value, p.value),
            "label_en": _PRIORITY_LABEL_EN.get(p.value, p.value),
        }
        for p in UserPriority
    ]


_CATEGORY_LABEL_AR = {
    "security": "الأمان",
    "authentication": "المصادقة",
    "password_reset": "إعادة تعيين كلمة المرور",
    "account": "الحساب",
    "clinical": "سريري",
    "laboratory": "المختبر",
    "pharmacy": "الصيدلية",
    "hospital": "المستشفى",
    "finance": "المالية",
    "billing": "الفوترة",
    "appointments": "المواعيد",
    "orders": "الطلبات",
    "reports": "التقارير",
    "inventory": "المخزون",
    "administration": "الإدارة",
    "system": "النظام",
    "monitoring": "المراقبة",
    "emergency": "الطوارئ",
    "marketing": "التسويق",
}

_CATEGORY_LABEL_EN = {
    "security": "Security",
    "authentication": "Authentication",
    "password_reset": "Password Reset",
    "account": "Account",
    "clinical": "Clinical",
    "laboratory": "Laboratory",
    "pharmacy": "Pharmacy",
    "hospital": "Hospital",
    "finance": "Finance",
    "billing": "Billing",
    "appointments": "Appointments",
    "orders": "Orders",
    "reports": "Reports",
    "inventory": "Inventory",
    "administration": "Administration",
    "system": "System",
    "monitoring": "Monitoring",
    "emergency": "Emergency",
    "marketing": "Marketing",
}

_PRIORITY_LABEL_AR = {
    "informational": "معلوماتي",
    "low": "منخفض",
    "medium": "متوسط",
    "high": "مرتفع",
    "critical": "حرج",
}

_PRIORITY_LABEL_EN = {
    "informational": "Informational",
    "low": "Low",
    "medium": "Medium",
    "high": "High",
    "critical": "Critical",
}


__all__ = [
    "categories",
    "channel_catalog",
    "get_preferences",
    "mute_category",
    "mute_channel",
    "priorities",
    "save_preferences",
    "update_preferences",
]
