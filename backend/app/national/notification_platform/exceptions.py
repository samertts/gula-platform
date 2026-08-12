from __future__ import annotations


class NotificationPlatformError(Exception):
    pass


class NotificationNotFoundError(NotificationPlatformError):
    def __init__(self, notification_id: str) -> None:
        self.notification_id = notification_id
        super().__init__(f"Notification not found: {notification_id}")


class TemplateNotFoundError(NotificationPlatformError):
    def __init__(self, template_id: str) -> None:
        self.template_id = template_id
        super().__init__(f"Notification template not found: {template_id}")


class TemplateRenderError(NotificationPlatformError):
    def __init__(self, template_id: str, reason: str) -> None:
        self.template_id = template_id
        self.reason = reason
        super().__init__(f"Failed to render template {template_id}: {reason}")


class DeliveryFailedError(NotificationPlatformError):
    def __init__(self, notification_id: str, channel: str, recipient: str, reason: str) -> None:
        self.notification_id = notification_id
        self.channel = channel
        self.recipient = recipient
        self.reason = reason
        super().__init__(
            f"Delivery failed for {notification_id} via {channel} to {recipient}: {reason}",
        )


class ChannelNotAvailableError(NotificationPlatformError):
    def __init__(self, channel: str) -> None:
        self.channel = channel
        super().__init__(f"Notification channel not available: {channel}")


class RateLimitExceededError(NotificationPlatformError):
    def __init__(self, channel: str, recipient: str) -> None:
        self.channel = channel
        self.recipient = recipient
        super().__init__(f"Rate limit exceeded for {channel} to {recipient}")


class QuietHoursBlockedError(NotificationPlatformError):
    def __init__(self, channel: str, user_id: str) -> None:
        self.channel = channel
        self.user_id = user_id
        super().__init__(f"Quiet hours active for {channel} for user {user_id}")


class NotificationPreferenceNotFoundError(NotificationPlatformError):
    def __init__(self, user_id: str, channel: str) -> None:
        self.user_id = user_id
        self.channel = channel
        super().__init__(f"Notification preference not found for user {user_id} channel {channel}")


class RecipientNotSpecifiedError(NotificationPlatformError):
    def __init__(self) -> None:
        super().__init__("No recipients specified for notification")


class ScheduleNotFoundError(NotificationPlatformError):
    def __init__(self, schedule_id: str) -> None:
        self.schedule_id = schedule_id
        super().__init__(f"Notification schedule not found: {schedule_id}")
