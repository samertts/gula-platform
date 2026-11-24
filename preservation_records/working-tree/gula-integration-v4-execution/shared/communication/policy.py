"""Policy Engine for the GULA Communication Platform Core.

Decides WHO gets WHAT through WHICH channels with WHICH priority — before
any provider is consulted. Supports: priority, escalation, fallback,
required channels, optional channels, recipient preferences, and mandatory
notifications (which bypass user preferences).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Protocol

from .model import ChannelAttempt, ContentFormat, Priority

logger = logging.getLogger("gula.communication.policy")

MANDATORY_PRIORITY = Priority.MANDATORY


@dataclass(frozen=True)
class RecipientPreferences:
    """Per-recipient delivery preferences."""

    allowed_channels: frozenset[str] = frozenset()
    preferred_channels: tuple[str, ...] = ()
    locale: str = ""
    quiet_hours: bool = False

    @classmethod
    def unrestricted(cls) -> RecipientPreferences:
        return cls()

    def allows(self, channel: str) -> bool:
        return not self.allowed_channels or channel in self.allowed_channels

    def to_dict(self) -> dict[str, Any]:
        return {
            "allowed_channels": sorted(self.allowed_channels),
            "preferred_channels": list(self.preferred_channels),
            "locale": self.locale,
            "quiet_hours": self.quiet_hours,
        }


@dataclass(frozen=True)
class Policy:
    """Declarative communication policy bound to an event or explicit send."""

    id: str
    template_id: str = ""
    locale: str = ""
    priority: Priority = Priority.NORMAL
    required_channels: tuple[str, ...] = ()
    optional_channels: tuple[str, ...] = ()
    fallback_channels: tuple[str, ...] = ()
    escalation_channels: tuple[str, ...] = ()
    escalation_after_seconds: int = 300
    mandatory: bool = False
    format: ContentFormat = ContentFormat.PLAIN
    max_retries: int = 2

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("policy requires an id")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "template_id": self.template_id,
            "locale": self.locale,
            "priority": self.priority.value,
            "required_channels": list(self.required_channels),
            "optional_channels": list(self.optional_channels),
            "fallback_channels": list(self.fallback_channels),
            "escalation_channels": list(self.escalation_channels),
            "escalation_after_seconds": self.escalation_after_seconds,
            "mandatory": self.mandatory,
            "format": self.format.value,
            "max_retries": self.max_retries,
        }


@dataclass(frozen=True)
class PolicyDecision:
    """The resolved plan: ordered channel attempts + delivery parameters."""

    policy: Policy
    attempts: tuple[ChannelAttempt, ...]
    skipped: tuple[tuple[str, str], ...] = ()  # (channel, reason)
    subject: str = ""

    @property
    def channels(self) -> list[str]:
        return [a.channel for a in self.attempts]

    def to_dict(self) -> dict[str, Any]:
        return {
            "policy_id": self.policy.id,
            "priority": self.policy.priority.value,
            "attempts": [a.to_dict() for a in self.attempts],
            "skipped": [{"channel": c, "reason": r} for c, r in self.skipped],
        }


class PreferenceStore(Protocol):
    """Lookup of recipient preferences (implemented outside the Core)."""

    def preferences_for(self, recipient_address: str) -> RecipientPreferences: ...


class PolicyEngine:
    """Pure decision logic: policy + preferences + context → plan.

    Mandatory notifications always include required channels and never
    respect quiet hours; optional channels are still preference-filtered.
    """

    def __init__(self, preference_store: PreferenceStore | None = None) -> None:
        self._preferences = preference_store
        self._policies: dict[str, Policy] = {}

    def register(self, policy: Policy) -> Policy:
        if policy.id in self._policies:
            raise ValueError(f"policy already registered: {policy.id}")
        self._policies[policy.id] = policy
        return policy

    def get(self, policy_id: str) -> Policy | None:
        return self._policies.get(policy_id)

    def list_policies(self) -> list[dict[str, Any]]:
        return [p.to_dict() for p in self._policies.values()]

    def decide(
        self,
        policy: Policy,
        recipient_address: str,
        prefs: RecipientPreferences | None = None,
    ) -> PolicyDecision:
        preferences = prefs or self._resolve_preferences(recipient_address)
        attempts: list[ChannelAttempt] = []
        skipped: list[tuple[str, str]] = []

        # Required channels always ship (unless preference-blocked and not mandatory).
        for channel in policy.required_channels:
            if preferences.allows(channel) or policy.mandatory:
                attempts.append(
                    ChannelAttempt(channel, priority=policy.priority, is_required=True),
                )
            else:
                skipped.append((channel, "recipient_preference"))

        # Fallback channels come after required ones.
        for channel in policy.fallback_channels:
            attempts.append(ChannelAttempt(channel, priority=policy.priority, is_fallback=True))

        # Optional channels are preference-filtered; preferred ones go first.
        optional = list(policy.optional_channels)
        if preferences.preferred_channels:
            optional.sort(
                key=lambda c: (
                    preferences.preferred_channels.index(c)
                    if c in preferences.preferred_channels
                    else len(preferences.preferred_channels),
                ),
            )
        for channel in optional:
            if not preferences.allows(channel):
                skipped.append((channel, "recipient_preference"))
                continue
            if policy.mandatory and preferences.quiet_hours:
                pass  # mandatory bypasses quiet hours
            attempts.append(ChannelAttempt(channel, priority=policy.priority))

        return PolicyDecision(
            policy=policy,
            attempts=tuple(attempts),
            skipped=tuple(skipped),
        )

    def _resolve_preferences(self, recipient_address: str) -> RecipientPreferences:
        if self._preferences is None:
            return RecipientPreferences.unrestricted()
        try:
            return self._preferences.preferences_for(recipient_address)
        except Exception:
            logger.exception("preference_lookup_failed recipient=%s", recipient_address)
            return RecipientPreferences.unrestricted()


__all__ = [
    "MANDATORY_PRIORITY",
    "Policy",
    "PolicyDecision",
    "PolicyEngine",
    "PreferenceStore",
    "RecipientPreferences",
]
