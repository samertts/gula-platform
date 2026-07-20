"""Domain exceptions — raised by domain logic, handled at the boundary."""


class DomainError(Exception):
    """Base class for all domain-level errors."""


class OrderStateError(DomainError):
    """Raised when an order state transition is illegal or the order is locked."""

    def __init__(self, message: str, status_code: int = 409):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class ServiceError(DomainError):
    """Base for service-layer errors — raised by business services."""

    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(ServiceError):
    """Raised when a requested resource was not found."""

    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=404)


class ConflictError(ServiceError):
    """Raised when a conflict prevents the operation."""

    def __init__(self, message: str = "Conflict"):
        super().__init__(message, status_code=409)
