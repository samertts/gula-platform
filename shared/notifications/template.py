from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger("gula.notifications.template")


@dataclass
class NotificationTemplate:
    id: str
    channels: dict[str, dict[str, str]] = field(default_factory=dict)
    default_channel: str = "email"

    def render(self, channel: str, data: dict[str, Any] | None = None) -> dict[str, str]:
        data = data or {}
        channel_config = self.channels.get(channel, self.channels.get(self.default_channel, {}))
        subject = channel_config.get("subject", "").format(**data)
        body = channel_config.get("body", "").format(**data)
        return {"subject": subject, "body": body}


_BUILTIN_TEMPLATES: dict[str, NotificationTemplate] = {
    "welcome_email": NotificationTemplate(
        id="welcome_email",
        channels={
            "email": {
                "subject": "Welcome to GULA Platform",
                "body": "Hello {name},\n\nWelcome to GULA Platform.\n\nBest regards,\nGULA Team",
            }
        },
    ),
    "password_reset": NotificationTemplate(
        id="password_reset",
        channels={
            "email": {
                "subject": "Password Reset",
                "body": "Hello {name},\n\nUse this code to reset your password: {code}\n\nBest regards,\nGULA Team",
            },
            "sms": {"subject": "", "body": "Your GULA password reset code: {code}"},
        },
    ),
    "test_result_ready": NotificationTemplate(
        id="test_result_ready",
        channels={
            "email": {
                "subject": "Your Test Results Are Ready",
                "body": "Hello {name},\n\nYour test results for {test_name} are now available.\n\nBest regards,\nGULA Team",
            },
            "sms": {"subject": "", "body": "Your GULA test results for {test_name} are ready."},
            "push": {
                "subject": "Test Results Ready",
                "body": "Your {test_name} results are now available.",
            },
        },
    ),
    "critical_alert": NotificationTemplate(
        id="critical_alert",
        channels={
            "email": {
                "subject": "CRITICAL ALERT: {patient_name}",
                "body": "CRITICAL ALERT\n\nPatient: {patient_name}\nTest: {test_name}\nValue: {value}\nReference Range: {ref_range}\n\nAction Required Immediately.\n\nGULA Platform",
            },
            "sms": {"subject": "", "body": "CRITICAL: {patient_name} - {test_name}: {value}"},
            "push": {
                "subject": "Critical Alert",
                "body": "Critical value for {patient_name}: {test_name} = {value}",
            },
            "telegram": {
                "subject": "",
                "body": "CRITICAL ALERT\nPatient: {patient_name}\nTest: {test_name}\nValue: {value}\nRef: {ref_range}",
            },
        },
    ),
}


def get_template(template_id: str) -> NotificationTemplate | None:
    return _BUILTIN_TEMPLATES.get(template_id)


def register_template(template: NotificationTemplate) -> None:
    _BUILTIN_TEMPLATES[template.id] = template


def render_template(
    template_id: str, channel: str, data: dict[str, Any] | None = None
) -> dict[str, str] | None:
    template = get_template(template_id)
    if template is None:
        logger.warning("Template not found: %s", template_id)
        return None
    return template.render(channel, data)


__all__ = [
    "NotificationTemplate",
    "get_template",
    "register_template",
    "render_template",
    "NotificationMessage",
]
