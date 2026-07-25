class CommandCenterError(Exception): ...


class EmergencyNotFoundError(CommandCenterError):
    def __str__(self) -> str:
        return "Emergency declaration not found"


class ResourceRequestNotFoundError(CommandCenterError):
    def __str__(self) -> str:
        return "Resource request not found"


class SituationReportNotFoundError(CommandCenterError):
    def __str__(self) -> str:
        return "Situation report not found"


class AfterActionReportNotFoundError(CommandCenterError):
    def __str__(self) -> str:
        return "After-action report not found"
