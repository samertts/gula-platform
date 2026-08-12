from __future__ import annotations


class GulaError(Exception):
    def __init__(self, message: str, status_code: int | None = None, body: dict | None = None):
        self.status_code = status_code
        self.body = body or {}
        super().__init__(message)


class AuthenticationError(GulaError):
    def __init__(self, message: str = "Authentication failed", body: dict | None = None):
        super().__init__(message, status_code=401, body=body)


class PermissionError(GulaError):
    def __init__(self, message: str = "Insufficient permissions", body: dict | None = None):
        super().__init__(message, status_code=403, body=body)


class NotFoundError(GulaError):
    def __init__(self, message: str = "Resource not found", body: dict | None = None):
        super().__init__(message, status_code=404, body=body)


class ConflictError(GulaError):
    def __init__(self, message: str = "Resource conflict", body: dict | None = None):
        super().__init__(message, status_code=409, body=body)


class ValidationError(GulaError):
    def __init__(self, message: str = "Validation failed", body: dict | None = None):
        super().__init__(message, status_code=422, body=body)


class RateLimitError(GulaError):
    def __init__(self, message: str = "Rate limit exceeded", body: dict | None = None):
        super().__init__(message, status_code=429, body=body)


class ServerError(GulaError):
    def __init__(self, message: str = "Internal server error", body: dict | None = None):
        super().__init__(message, status_code=500, body=body)


class IdempotencyError(GulaError):
    def __init__(self, message: str = "Idempotency conflict", body: dict | None = None):
        super().__init__(message, status_code=409, body=body)


_EXCEPTION_MAP: dict[int, type[GulaError]] = {
    401: AuthenticationError,
    403: PermissionError,
    404: NotFoundError,
    409: ConflictError,
    422: ValidationError,
    429: RateLimitError,
}


def map_status_code(status_code: int, body: dict | None = None) -> GulaError:
    cls = _EXCEPTION_MAP.get(status_code)
    if cls:
        return cls(body=body or {})
    if status_code >= 500:
        return ServerError(body=body or {})
    return GulaError(f"HTTP {status_code}", status_code=status_code, body=body or {})
