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
    ) -> NotificationResult:
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
            return self._platform.send_notification(channel=channel, to=citizen_id, subject=title, body=message)

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
    ) -> list[NotificationResult]:
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
    ) -> NotificationResult:
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
    ) -> NotificationResult:
        return self._notification_service.send_notification(
            citizen_id=citizen_id,
            notification_type=CitizenNotificationType.APPOINTMENT_REMINDER,
            title="Appointment Reminder",
            title_ar="تذكير موعد",
            message=f"You have a {appointment_type} appointment at {appointment_time}",
            message_ar=f"لديك موعد {appointment_type} في {appointment_time}",
            channel="sms",
            reference_type="appointment",
            reference_id=appointment_id,
        )
