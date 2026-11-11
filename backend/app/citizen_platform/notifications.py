from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime

from app._compat import UTC
from app.citizen_platform.enums import CitizenNotificationType
from app.platform.notifications import NotificationResult
from app.platform.notifications import NotificationService as PlatformNotificationService

logger = logging.getLogger("gula.citizen.notifications")


@dataclass
class CitizenAlert:
    id: str = ""
    citizen_id: str = ""
    alert_type: str = ""
    title: str = ""
    title_ar: str = ""
    message: str = ""
    message_ar: str = ""
    severity: str = "info"
    is_read: bool = False
    reference_type: str = ""
    reference_id: str = ""
    created_at: str = ""
    read_at: str = ""


class CitizenNotificationService:
    def __init__(self, notification_service: PlatformNotificationService | None = None) -> None:
        self._platform = notification_service or PlatformNotificationService()
        self._notifications: dict[str, list[CitizenAlert]] = {}

    def send_notification(
        self,
        citizen_id: str,
        notification_type: CitizenNotificationType,
        title: str,
        title_ar: str,
        message: str,
        message_ar: str,
        channel: str = "in_app",
        reference_type: str = "",
        reference_id: str = "",
        recipient_address: str | None = None,
    ) -> NotificationResult:
        """Record an alert for a citizen, and on an external channel send it.

        IA-078. ``citizen_id`` used to be passed straight through as the SMS or
        email recipient:

            self._platform.send_notification(channel=channel, to=citizen_id, ...)

        Proved against a working stub SMS gateway: ``send_critical_alert`` for
        a potassium of 7.9 mmol/L returned ``success=True`` while the gateway
        received ``{"to": "c7f3a1e2-9b44-4d10-8e55-0a1b2c3d4e5f"}`` — an
        internal identifier where a phone number belongs. The gateway answered
        200, so ``raise_for_status()`` passed, so the platform reported
        delivery. **The alert reached nobody, on a fully configured
        deployment.** No amount of honest transport reporting (IA-076) reaches
        this: the transport succeeded and the address was wrong.

        This class holds no citizen registry, no session and no contact
        repository, so it cannot resolve an identifier to an address — and
        deciding *which* address (verified only? consented? primary?) is a
        policy this audit must not invent. So the address is the caller's to
        supply, and a non-in_app channel without one is refused rather than
        addressed to an identifier.
        """
        if channel != "in_app" and not recipient_address:
            raise ValueError(
                f"channel {channel!r} needs a real recipient_address: "
                f"citizen_id {citizen_id!r} is an internal identifier, not a "
                f"phone number or mailbox, and sending to it reports a "
                f"delivery that reaches nobody. This service cannot resolve "
                f"one — pass the address from whoever read the citizen's "
                f"contact details and consent.",
            )

        alert = CitizenAlert(
            id=str(uuid.uuid4()),
            citizen_id=citizen_id,
            alert_type=notification_type.value,
            title=title,
            title_ar=title_ar,
            message=message,
            message_ar=message_ar,
            severity="info",
            reference_type=reference_type,
            reference_id=reference_id,
            created_at=datetime.now(UTC).isoformat(),
        )
        if citizen_id not in self._notifications:
            self._notifications[citizen_id] = []
        self._notifications[citizen_id].append(alert)

        if channel != "in_app":
            return self._platform.send_notification(
                channel=channel, to=recipient_address, subject=title, body=message,
            )

        return NotificationResult(success=True, channel="in_app", recipient=citizen_id)

    def get_notifications(
        self,
        citizen_id: str,
        notification_type: str | None = None,
        unread_only: bool = False,
        skip: int = 0,
        limit: int = 50,
    ) -> list[CitizenAlert]:
        notifications = self._notifications.get(citizen_id, [])
        if notification_type:
            notifications = [n for n in notifications if n.alert_type == notification_type]
        if unread_only:
            notifications = [n for n in notifications if not n.is_read]
        notifications.sort(key=lambda n: n.created_at, reverse=True)
        return notifications[skip : skip + limit]

    def mark_as_read(self, citizen_id: str, notification_id: str) -> bool:
        notifications = self._notifications.get(citizen_id, [])
        for n in notifications:
            if n.id == notification_id:
                n.is_read = True
                n.read_at = datetime.now(UTC).isoformat()
                return True
        return False

    def mark_all_as_read(self, citizen_id: str) -> int:
        count = 0
        notifications = self._notifications.get(citizen_id, [])
        for n in notifications:
            if not n.is_read:
                n.is_read = True
                n.read_at = datetime.now(UTC).isoformat()
                count += 1
        return count

    def get_unread_count(self, citizen_id: str) -> int:
        return sum(1 for n in self._notifications.get(citizen_id, []) if not n.is_read)

    def broadcast_notification(
        self,
        citizen_ids: list[str],
        notification_type: CitizenNotificationType,
        title: str,
        title_ar: str,
        message: str,
        message_ar: str,
        channel: str = "in_app",
        recipient_addresses: dict[str, str] | None = None,
    ) -> list[NotificationResult]:
        """IA-078. A broadcast on an external channel needs one address each.

        Keyed by citizen id rather than positional, so a mismatched list
        cannot silently shift every message to the wrong recipient.
        """
        addresses = recipient_addresses or {}
        results: list[NotificationResult] = []
        for cid in citizen_ids:
            result = self.send_notification(
                citizen_id=cid,
                notification_type=notification_type,
                title=title,
                title_ar=title_ar,
                message=message,
                message_ar=message_ar,
                channel=channel,
                recipient_address=addresses.get(cid),
            )
            results.append(result)
        return results


class AlertService:
    def __init__(self, notification_service: CitizenNotificationService) -> None:
        self._notification_service = notification_service

    def send_critical_alert(
        self,
        citizen_id: str,
        title: str,
        title_ar: str,
        message: str,
        message_ar: str,
        reference_type: str = "",
        reference_id: str = "",
        recipient_phone: str | None = None,
    ) -> NotificationResult:
        """IA-078. ``recipient_phone`` is required in practice, not optional.

        It is keyword-with-default only so that no existing positional call is
        silently re-bound to the wrong argument; omitting it raises in
        ``send_notification`` rather than texting a UUID. This is the path that
        carries a critical result, so a loud refusal is the safe failure.
        """
        return self._notification_service.send_notification(
            citizen_id=citizen_id,
            notification_type=CitizenNotificationType.EMERGENCY_ALERT,
            title=title,
            title_ar=title_ar,
            message=message,
            message_ar=message_ar,
            channel="sms",
            reference_type=reference_type,
            reference_id=reference_id,
            recipient_address=recipient_phone,
        )

    def send_lab_result_alert(
        self,
        citizen_id: str,
        lab_name: str,
        result_summary: str,
    ) -> NotificationResult:
        return self._notification_service.send_notification(
            citizen_id=citizen_id,
            notification_type=CitizenNotificationType.LAB_RESULT,
            title="New Lab Result",
            title_ar="نتيجة مختبر جديدة",
            message=f"New result from {lab_name}: {result_summary}",
            message_ar=f"نتيجة جديدة من {lab_name}: {result_summary}",
            channel="in_app",
            reference_type="lab_result",
        )

    def send_medication_alert(
        self,
        citizen_id: str,
        medication_name: str,
        reminder_type: str = "refill",
    ) -> NotificationResult:
        messages = {
            "refill": ("Medication Refill Reminder", "تذكير بتعبئة الدواء"),
            "dose": ("Medication Dose Reminder", "تذكير بجرعة الدواء"),
            "interaction": ("Drug Interaction Alert", "تنبيه تفاعل دوائي"),
        }
        title, title_ar = messages.get(reminder_type, ("Medication Alert", "تنبيه دوائي"))
        return self._notification_service.send_notification(
            citizen_id=citizen_id,
            notification_type=CitizenNotificationType.MEDICATION_ALERT,
            title=title,
            title_ar=title_ar,
            message=f"Alert for {medication_name}",
            message_ar=f"تنبيه بخصوص {medication_name}",
            channel="in_app",
            reference_type="medication",
        )

    def send_appointment_reminder(
        self,
        citizen_id: str,
        appointment_id: str,
        appointment_type: str,
        appointment_time: str,
        recipient_phone: str | None = None,
    ) -> NotificationResult:
        """IA-078, as send_critical_alert."""
        return self._notification_service.send_notification(
            citizen_id=citizen_id,
            notification_type=CitizenNotificationType.APPOINTMENT_REMINDER,
            title="Appointment Reminder",
            title_ar="تذكير موعد",
            message=f"You have a {appointment_type} appointment at {appointment_time}",
            message_ar=f"لديك موعد {appointment_type} في {appointment_time}",
            channel="sms",
            recipient_address=recipient_phone,
            reference_type="appointment",
            reference_id=appointment_id,
        )
