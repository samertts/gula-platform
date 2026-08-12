from platform.core.event_bus import Event


class PatientCreatedHandler:
    def __init__(self, audit_service=None, notification_service=None):
        self._audit = audit_service
        self._notifications = notification_service

    async def handle(self, event: Event) -> None:
        data = event.data
        patient_id = data.get("patient_id", "")
        lab_id = data.get("lab_id", "")

        if self._audit:
            await self._audit.log(
                action="patient.created",
                entity_type="patient",
                entity_id=patient_id,
                performed_by="system",
                lab_id=lab_id,
                details=data,
            )
