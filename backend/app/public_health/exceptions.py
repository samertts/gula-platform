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


class ReportNotFoundError(PublicHealthError):
    def __str__(self) -> str:
        return "Public health report not found"
