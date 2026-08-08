from platform.core.modules import module


@module(
    name="gula.patient",
    version="1.0.0",
    description="Patient management",
    dependencies=[],
    events_published=["patient.created", "patient.updated", "patient.merged"],
    events_subscribed=["patient.created"],
    commands_handled=["create_patient", "update_patient"],
    queries_handled=["get_patient", "search_patients"],
)
class PatientModule:
    def __init__(self, patient_service=None, audit_service=None):
        self._patient_service = patient_service
        self._audit_service = audit_service
        self.register_service("patient_service", patient_service)

    async def on_initialize(self) -> None:
        pass

    async def on_start(self) -> None:
        pass

    async def on_stop(self) -> None:
        pass
