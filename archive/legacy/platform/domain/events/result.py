from platform.core.event_bus import Event


class ResultCreated(Event):
    def __init__(self, data: dict):
        super().__init__(topic="result.created", data=data)


class ResultValidated(Event):
    def __init__(self, data: dict):
        super().__init__(topic="result.validated", data=data)


class ResultCorrected(Event):
    def __init__(self, data: dict):
        super().__init__(topic="result.corrected", data=data)
