from platform.core.modules import module


@module(
    name="gula.lab",
    version="1.0.0",
    description="Lab administration",
    dependencies=[],
    events_published=["lab.created", "lab.settings_changed"],
    events_subscribed=["lab.created"],
    commands_handled=["create_lab", "update_lab_settings"],
    queries_handled=["get_lab", "list_labs"],
)
class LabModule:
    def __init__(self, lab_service=None, audit_service=None):
        self._lab_service = lab_service
        self._audit_service = audit_service
        self.register_service("lab_service", lab_service)

    async def on_initialize(self) -> None:
        pass

    async def on_start(self) -> None:
        pass

    async def on_stop(self) -> None:
        pass
