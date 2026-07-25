from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class AttributeCategory(Enum):
    SUBJECT = "subject"
    RESOURCE = "resource"
    ACTION = "action"
    ENVIRONMENT = "environment"


@dataclass
class Attribute:
    category: AttributeCategory
    key: str
    value: Any


@dataclass
class AccessRequest:
    subject_id: str
    subject_roles: list[str]
    subject_organization: str | None = None
    subject_facility: str | None = None
    resource_type: str = ""
    resource_id: str = ""
    resource_owner: str | None = None
    resource_organization: str | None = None
    resource_is_sensitive: bool = False
    resource_is_vip: bool = False
    resource_is_minor: bool = False
    action: str = ""
    purpose_of_use: str | None = None
    environment_is_emergency: bool = False
    environment_ip: str | None = None
    environment_time: str | None = None
    attributes: list[Attribute] = field(default_factory=list)


@dataclass
class ABACDecision:
    granted: bool
    reason: str = ""
    obligations: list[str] = field(default_factory=list)
    advice: list[str] = field(default_factory=list)


class ABACEngine:
    def __init__(self) -> None:
        self._policies: list[dict] = []

    def evaluate(self, request: AccessRequest) -> ABACDecision:
        if request.resource_is_sensitive and not self._is_authorized_sensitive(request):
            return ABACDecision(granted=False, reason="Insufficient clearance for sensitive record")
        if request.resource_is_vip and not self._is_authorized_vip(request):
            return ABACDecision(granted=False, reason="VIP protection: unauthorized access")
        if request.resource_is_minor and not self._is_authorized_minor(request):
            return ABACDecision(granted=False, reason="Minor protection: unauthorized access")
        if request.environment_is_emergency:
            return self._handle_emergency(request)
        if request.purpose_of_use:
            return self._evaluate_purpose(request)
        return ABACDecision(granted=True)

    def _is_authorized_sensitive(self, request: AccessRequest) -> bool:
        return "sensitive_access" in request.subject_roles

    def _is_authorized_vip(self, request: AccessRequest) -> bool:
        return "vip_access" in request.subject_roles

    def _is_authorized_minor(self, request: AccessRequest) -> bool:
        return "minor_access" in request.subject_roles or "guardian" in request.subject_roles

    def _handle_emergency(self, request: AccessRequest) -> ABACDecision:
        return ABACDecision(
            granted=True,
            reason="Emergency access granted",
            obligations=["log_break_glass", "notify_administrator", "require_review_within_24h"],
        )

    def _evaluate_purpose(self, request: AccessRequest) -> ABACDecision:
        allowed_purposes = {"treatment", "payment", "operations", "emergency"}
        if request.purpose_of_use in allowed_purposes:
            return ABACDecision(
                granted=True, reason=f"Purpose '{request.purpose_of_use}' authorized",
            )
        return ABACDecision(
            granted=False, reason=f"Purpose '{request.purpose_of_use}' not authorized",
        )
