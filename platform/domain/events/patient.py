from platform.core.event_bus import Event


class PatientCreated(Event):
    def __init__(self, data: dict):
        super().__init__(topic="patient.created", data=data)


class PatientUpdated(Event):
    def __init__(self, data: dict):
        super().__init__(topic="patient.updated", data=data)


class PatientMerged(Event):
    def __init__(self, data: dict):
        super().__init__(topic="patient.merged", data=data)
