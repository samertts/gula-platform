"""Standardized notification module — wraps existing notifications/service.py."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime

from ..notifications.service import get_service as get_legacy_service
from . import PlatformRegistry

logger = logging.getLogger("gula.platform.notifications")


#: IA-079. Named once so the refusal and the capability listing cannot drift
#: apart, and so a reader of either finds the same statement.
SCHEDULING_UNAVAILABLE_REASON = (
    "no deferred-execution primitive exists: TaskPayload carries no delay, "
    "run_at or eta field and TaskQueue.enqueue accepts none, so a task cannot "
    "be held until a future time. Scheduling a notification requires either a "
    "delay-capable queue or a due-schedule poller; neither is present."
)


class NotificationSchedulingUnavailable(RuntimeError):
    """Raised instead of silently delivering a future-dated notification now."""


@dataclass
class NotificationResult:
    success: bool = False
    channel: str = ""
    recipient: str = ""
    error: str | None = None


class NotificationService:
    def __init__(self) -> None:
        self._service = get_legacy_service()

    def send_notification(
        self,
        channel: str,
        to: str,
        subject: str = "",
        body: str = "",
        template_id: str = "",
        template_data: dict | None = None,
    ) -> NotificationResult:
        result = self._service.send(
            channel=channel, to=to, subject=subject, body=body,
            template_id=template_id, template_data=template_data,
        )
        return NotificationResult(success=result.success, channel=result.channel, recipient=result.recipient, error=result.error)

    def broadcast(
        self,
        channel: str,
        recipients: list[str],
        subject: str = "",
        body: str = "",
    ) -> list[NotificationResult]:
        results = []
        for to in recipients:
            result = self._service.send(channel=channel, to=to, subject=subject, body=body)
            results.append(NotificationResult(success=result.success, channel=result.channel, recipient=result.recipient, error=result.error))
        return results

    def schedule_notification(
        self,
        channel: str,
        to: str,
        subject: str = "",
        body: str = "",
        schedule_at: datetime | None = None,
    ) -> NotificationResult:
        """Send now. There is no deferred-delivery primitive to schedule with.

        IA-079. This used to ignore ``schedule_at`` entirely and send
        immediately while returning success, so a reminder scheduled for next
        week fired at once and the caller was told it was scheduled. Measured:
        ``schedule_at=2027-01-01`` produced an immediate gateway POST with no
        trace of the date.

        ``app.tasks.schema.TaskPayload`` has no delay, run-at or eta field, and
        ``app.tasks.queue.TaskQueue.enqueue`` takes none, so nothing in this
        platform can hold a task until a future time. Rather than build a
        scheduler on the way past -- which would mean choosing retry,
        visibility and recurrence semantics for a clinical notification path --
        a future time is refused and named.
        """
        if schedule_at is not None:
            now = datetime.now(schedule_at.tzinfo) if schedule_at.tzinfo else datetime.now()
            if schedule_at > now:
                raise NotificationSchedulingUnavailable(
                    f"cannot schedule delivery for {schedule_at.isoformat()}: "
                    f"{SCHEDULING_UNAVAILABLE_REASON}",
                )
        result = self._service.send(channel=channel, to=to, subject=subject, body=body)
        return NotificationResult(success=result.success, channel=result.channel, recipient=result.recipient, error=result.error)


PlatformRegistry.register("notifications", NotificationService(), capabilities=[
    {"name": "send_notification", "description": "Send a single notification via a channel"},
    {"name": "broadcast", "description": "Send the same notification to multiple recipients"},
    {
        "name": "schedule_notification",
        "description": "Send a notification immediately; a future schedule_at is refused",
        "available": False,
        "unavailable_reason": SCHEDULING_UNAVAILABLE_REASON,
    },
])
