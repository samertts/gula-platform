class PilotPlatformError(Exception):
    ...


class PilotNotFoundError(PilotPlatformError):
    def __str__(self) -> str:
        return "Pilot program not found"


class FacilityNotInPilotError(PilotPlatformError):
    def __str__(self) -> str:
        return "Facility not enrolled in this pilot"


class ReadinessAssessmentNotFoundError(PilotPlatformError):
    def __str__(self) -> str:
        return "Readiness assessment not found"


class DeploymentRecordNotFoundError(PilotPlatformError):
    def __str__(self) -> str:
        return "Deployment record not found"


class GoNoGoGateNotFoundError(PilotPlatformError):
    def __str__(self) -> str:
        return "Go/No-Go gate not found"
