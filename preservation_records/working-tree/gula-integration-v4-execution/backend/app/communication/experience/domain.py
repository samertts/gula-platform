"""Pure domain of the User Communication Experience Layer.

Everything here is deterministic and side-effect free (no DB, no I/O) so the
entire rule surface — categories, priorities, quiet hours, weekend/holiday
rules, mandatory channels — is unit-testable in isolation.

Canonical values:

  - Category: security, authentication, password_reset, account, clinical,
    laboratory, pharmacy, hospital, finance, billing, appointments, orders,
    reports, inventory, administration, system, monitoring, emergency,
    marketing (future categories are additive StrEnum members).
  - Priority: informational, low, medium, high, critical — mapped to the
    Communication Core ``Priority`` at dispatch time.
  - Inbox state: unread, read, archived, deleted.
"""

from __future__ import annotations

import enum
import json
from dataclasses import dataclass, field
from datetime import datetime, time
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from shared.communication import Priority

#: Categories whose notifications can NEVER be disabled or muted.
MANDATORY_CATEGORIES: frozenset[str] = frozenset(
    {"security", "authentication", "password_reset", "emergency"},
)

#: Channels that always stay enabled for mandatory categories.
MANDATORY_CHANNELS: frozenset[str] = frozenset({"inapp"})

#: All channels the experience layer manages (providers may be DOWN).
KNOWN_CHANNELS: tuple[str, ...] = (
    "inapp",
    "email",
    "push",
    "sms",
    "telegram",
    "discord",
    "slack",
    "teams",
    "webhook",
)


class NotificationCategory(enum.StrEnum):
    SECURITY = "security"
    AUTHENTICATION = "authentication"
    PASSWORD_RESET = "password_reset"
    ACCOUNT = "account"
    CLINICAL = "clinical"
    LABORATORY = "laboratory"
    PHARMACY = "pharmacy"
    HOSPITAL = "hospital"
    FINANCE = "finance"
    BILLING = "billing"
    APPOINTMENTS = "appointments"
    ORDERS = "orders"
    REPORTS = "reports"
    INVENTORY = "inventory"
    ADMINISTRATION = "administration"
    SYSTEM = "system"
    MONITORING = "monitoring"
    EMERGENCY = "emergency"
    MARKETING = "marketing"

    @classmethod
    def _missing_(cls, value: object) -> NotificationCategory:
        return cls.SYSTEM


class UserPriority(enum.StrEnum):
    INFORMATIONAL = "informational"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

    @classmethod
    def _missing_(cls, value: object) -> UserPriority:
        return cls.MEDIUM

    def to_core(self) -> Priority:
        return {
            UserPriority.INFORMATIONAL: Priority.LOW,
            UserPriority.LOW: Priority.LOW,
            UserPriority.MEDIUM: Priority.NORMAL,
            UserPriority.HIGH: Priority.HIGH,
            UserPriority.CRITICAL: Priority.MANDATORY,
        }[self]

    @classmethod
    def from_core(cls, priority: Priority | str) -> UserPriority:
        core = Priority(priority)
        return {
            Priority.LOW: UserPriority.LOW,
            Priority.NORMAL: UserPriority.MEDIUM,
            Priority.HIGH: UserPriority.HIGH,
            Priority.URGENT: UserPriority.CRITICAL,
            Priority.MANDATORY: UserPriority.CRITICAL,
        }[core]


class InboxState(enum.StrEnum):
    UNREAD = "unread"
    READ = "read"
    ARCHIVED = "archived"
    DELETED = "deleted"

    @classmethod
    def _missing_(cls, value: object) -> InboxState:
        return cls.UNREAD


class Frequency(enum.StrEnum):
    IMMEDIATE = "immediate"
    DIGEST = "digest"

    @classmethod
    def _missing_(cls, value: object) -> Frequency:
        return cls.IMMEDIATE


def is_mandatory(category: str) -> bool:
    return category in MANDATORY_CATEGORIES


def category_enabled(
    category: str,
    categories: dict[str, bool],
    *,
    emergency_override: bool = False,
) -> bool:
    """A category is on unless explicitly disabled — except mandatory ones."""
    if is_mandatory(category) or emergency_override:
        return True
    return categories.get(category, True)


def channel_enabled(
    channel: str,
    category: str,
    channels: dict[str, bool],
    *,
    emergency_override: bool = False,
) -> bool:
    """Channel on/off respecting mandatory channels for critical categories."""
    if channel in MANDATORY_CHANNELS and (is_mandatory(category) or emergency_override):
        return True
    return channels.get(channel, True)


# ── Quiet hours / weekend / holiday rules ─────────────────────────────────────


@dataclass(frozen=True)
class QuietHoursRules:
    """Do-not-disturb window; ``None`` times disable the rule."""

    enabled: bool = False
    start: str = "22:00"  # HH:MM in user timezone
    end: str = "06:00"  # HH:MM in user timezone (may cross midnight)

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> QuietHoursRules:
        data = data or {}
        return cls(
            enabled=bool(data.get("enabled", False)),
            start=str(data.get("start", "22:00")),
            end=str(data.get("end", "06:00")),
        )

    def to_dict(self) -> dict[str, Any]:
        return {"enabled": self.enabled, "start": self.start, "end": self.end}

    def covers(self, moment: datetime) -> bool:
        """True when ``moment`` (local to its own tz) sits inside the window."""
        if not self.enabled:
            return False
        try:
            start = time.fromisoformat(self.start)
            end = time.fromisoformat(self.end)
        except ValueError:
            return False
        current = moment.time()
        if start <= end:
            return start <= current < end
        return current >= start or current < end


def parse_tz(timezone: str) -> ZoneInfo:
    try:
        return ZoneInfo(timezone or "UTC")
    except (ZoneInfoNotFoundError, ValueError):
        return ZoneInfo("UTC")


def to_user_local(now: datetime, timezone: str) -> datetime:
    """Project ``now`` (tz-aware or naive-UTC) into the user timezone."""
    if now.tzinfo is None:
        now = now.replace(tzinfo=ZoneInfo("UTC"))
    return now.astimezone(parse_tz(timezone))


def quiet_hours_blocked(
    now: datetime,
    timezone: str,
    rules: QuietHoursRules | None,
    *,
    category: str,
    priority: UserPriority,
    emergency_override: bool = False,
    weekend_rules: bool = False,
    holiday_rules: bool = False,
) -> tuple[bool, str]:
    """Do-not-disturb decision. Returns ``(blocked, reason)``.

    Critical/emergency categories and high/critical priorities bypass quiet
    hours unless the user explicitly opted into them via weekend/holiday
    suppression. Emergency override always delivers.
    """
    if emergency_override:
        return False, "emergency_override"
    if is_mandatory(category) or priority in (UserPriority.CRITICAL, UserPriority.HIGH):
        return False, "mandatory"
    if rules is not None and rules.covers(to_user_local(now, timezone)):
        return True, "quiet_hours"
    if weekend_rules and _is_weekend(now, timezone):
        return True, "weekend"
    if holiday_rules:
        return True, "holiday"
    return False, ""


def _is_weekend(now: datetime, timezone: str) -> bool:
    local = to_user_local(now, timezone)
    return local.weekday() >= 5  # Sat/Sun


# ── User preferences value object ─────────────────────────────────────────────


@dataclass
class UserPreferences:
    """Complete per-user communication configuration (JSON round-trippable)."""

    user_id: int
    locale: str = "ar"
    timezone: str = "Asia/Baghdad"
    channels: dict[str, bool] = field(
        default_factory=lambda: dict.fromkeys(KNOWN_CHANNELS, True),
    )
    channel_priority: list[str] = field(
        default_factory=lambda: ["inapp", "email", "push", "telegram", "sms", "discord", "slack", "teams"],
    )
    categories: dict[str, bool] = field(
        default_factory=lambda: {c.value: True for c in NotificationCategory},
    )
    frequency: Frequency = Frequency.IMMEDIATE
    digest_schedule: str = "18:00"
    quiet_hours: QuietHoursRules = field(default_factory=QuietHoursRules)
    weekend_rules: bool = False
    holiday_rules: bool = False
    emergency_override: bool = False
    updated_at: str = ""

    @classmethod
    def defaults(cls, user_id: int) -> UserPreferences:
        return cls(user_id=user_id)

    def category_on(self, category: str) -> bool:
        return category_enabled(category, self.categories, emergency_override=self.emergency_override)

    def channel_on(self, channel: str, category: str) -> bool:
        return channel_enabled(
            channel,
            category,
            self.channels,
            emergency_override=self.emergency_override,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "user_id": self.user_id,
            "locale": self.locale,
            "timezone": self.timezone,
            "channels": dict(sorted(self.channels.items())),
            "channel_priority": list(self.channel_priority),
            "categories": dict(sorted(self.categories.items())),
            "frequency": self.frequency.value,
            "digest_schedule": self.digest_schedule,
            "quiet_hours": self.quiet_hours.to_dict(),
            "weekend_rules": self.weekend_rules,
            "holiday_rules": self.holiday_rules,
            "emergency_override": self.emergency_override,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> UserPreferences:
        channels = {
            c: bool(data.get("channels", {}).get(c, True))
            for c in KNOWN_CHANNELS
        }
        categories = {
            c.value: bool(data.get("categories", {}).get(c.value, True))
            for c in NotificationCategory
        }
        return cls(
            user_id=int(data.get("user_id", 0)),
            locale=str(data.get("locale", "ar")),
            timezone=str(data.get("timezone", "Asia/Baghdad")),
            channels=channels,
            channel_priority=[str(c) for c in data.get("channel_priority", [])],
            categories=categories,
            frequency=Frequency(data.get("frequency", "immediate")),
            digest_schedule=str(data.get("digest_schedule", "18:00")),
            quiet_hours=QuietHoursRules.from_dict(data.get("quiet_hours")),
            weekend_rules=bool(data.get("weekend_rules", False)),
            holiday_rules=bool(data.get("holiday_rules", False)),
            emergency_override=bool(data.get("emergency_override", False)),
            updated_at=str(data.get("updated_at", "")),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_json(cls, user_id: int, raw: str | None) -> UserPreferences:
        if not raw:
            return cls.defaults(user_id)
        try:
            data = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return cls.defaults(user_id)
        data["user_id"] = user_id
        return cls.from_dict(data)

    # ── Delivery decision (pure) ────────────────────────────────────────────

    def decide_delivery(
        self,
        *,
        category: str,
        priority: UserPriority,
        now: datetime | None = None,
    ) -> tuple[list[str], list[tuple[str, str]]]:
        """Ordered channels + skipped reasons for one notification.

        Mandatory categories keep mandatory channels + every enabled channel
        ordered by ``channel_priority``. Quiet hours / weekend / holiday
        rules suppress non-critical deliveries.
        """
        now = now or datetime.now(ZoneInfo("UTC"))
        enabled = [
            c for c in self.channel_priority if self.channels.get(c)
        ]
        for channel in MANDATORY_CHANNELS:
            if channel not in enabled:
                enabled.insert(0, channel)

        skipped: list[tuple[str, str]] = []
        if category in MANDATORY_CATEGORIES or priority in (
            UserPriority.CRITICAL,
            UserPriority.HIGH,
        ):
            allowed = enabled
        else:
            blocked, reason = quiet_hours_blocked(
                now,
                self.timezone,
                self.quiet_hours,
                category=category,
                priority=priority,
                emergency_override=self.emergency_override,
                weekend_rules=self.weekend_rules,
                holiday_rules=self.holiday_rules,
            )
            if blocked:
                allowed = [c for c in enabled if c in MANDATORY_CHANNELS]
                skipped = [(c, reason) for c in enabled if c not in MANDATORY_CHANNELS]
            else:
                allowed = enabled
        channels = [c for c in allowed if self.channel_on(c, category)]
        return channels, skipped

    def to_core_preferences(self) -> Any:
        """Adapter to the Core ``RecipientPreferences`` (no Core changes)."""
        from shared.communication import RecipientPreferences

        return RecipientPreferences(
            allowed_channels=frozenset(
                c for c, enabled in self.channels.items() if enabled
            ),
            preferred_channels=tuple(self.channel_priority),
            locale=self.locale,
            quiet_hours=self.quiet_hours.enabled,
        )


__all__ = [
    "KNOWN_CHANNELS",
    "MANDATORY_CATEGORIES",
    "MANDATORY_CHANNELS",
    "Frequency",
    "InboxState",
    "NotificationCategory",
    "QuietHoursRules",
    "UserPreferences",
    "UserPriority",
    "category_enabled",
    "channel_enabled",
    "is_mandatory",
    "parse_tz",
    "quiet_hours_blocked",
    "to_user_local",
]
