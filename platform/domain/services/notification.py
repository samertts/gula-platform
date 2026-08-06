from uuid import uuid4


class NotificationService:
    def __init__(self, db_adapter=None, event_bus=None):
        self._db = db_adapter
        self._event_bus = event_bus

    async def send(self, recipient: str, subject: str, body: str, channel: str = "in_app") -> str:
        notification_id = str(uuid4())
        if self._event_bus:
            from platform.core.event_bus import Event
            event = Event(
                topic="notification.sent",
                data={
                    "notification_id": notification_id,
                    "recipient": recipient,
                    "subject": subject,
                    "channel": channel,
                },
            )
            await self._event_bus.publish("notification.sent", event)
        return notification_id

    async def send_bulk(self, recipients: list[str], subject: str, body: str, channel: str = "in_app") -> list[str]:
        ids = []
        for recipient in recipients:
            nid = await self.send(recipient, subject, body, channel)
            ids.append(nid)
        return ids
