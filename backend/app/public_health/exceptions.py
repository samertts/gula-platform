class PublicHealthError(Exception):
    ...


class DiseaseCaseNotFoundError(PublicHealthError):
    def __str__(self) -> str:
        return "Disease case not found"


class OutbreakNotFoundError(PublicHealthError):
    def __str__(self) -> str:
        return "Outbreak alert not found"


class InvalidOutbreakStatusError(PublicHealthError):
    def __str__(self) -> str:
        return "Invalid outbreak alert status"


class OutbreakAlreadyDeclaredOverError(PublicHealthError):
    def __str__(self) -> str:
        return "Outbreak has already been declared over"


class VaccineNotFoundError(PublicHealthError):
    def __str__(self) -> str:
        return "Vaccination record not found"


class ReportNotFoundError(PublicHealthError):
    def __str__(self) -> str:
        return "Public health report not found"
