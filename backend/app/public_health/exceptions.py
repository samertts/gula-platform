class PublicHealthError(Exception):
    ...


class DiseaseCaseNotFoundError(PublicHealthError):
    def __str__(self) -> str:
        return "Disease case not found"


class OutbreakNotFoundError(PublicHealthError):
    def __str__(self) -> str:
        return "Outbreak alert not found"


class VaccineNotFoundError(PublicHealthError):
    def __str__(self) -> str:
        return "Vaccination record not found"


class ImmunizationScheduleNotFoundError(PublicHealthError):
    def __str__(self) -> str:
        return "Immunization schedule entry not found"


class ImmunizationScheduleConfigurationError(PublicHealthError):
    def __str__(self) -> str:
        return "No active approved immunization schedule is available"


class ImmunizationStateError(PublicHealthError):
    def __str__(self) -> str:
        return "The requested immunization state transition is not allowed"


class ReportNotFoundError(PublicHealthError):
    def __str__(self) -> str:
        return "Public health report not found"
