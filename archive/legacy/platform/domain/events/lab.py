from platform.core.event_bus import Event


class LabCreated(Event):
    def __init__(self, data: dict):
        super().__init__(topic="lab.created", data=data)


class LabSettingsChanged(Event):
    def __init__(self, data: dict):
        super().__init__(topic="lab.settings_changed", data=data)
