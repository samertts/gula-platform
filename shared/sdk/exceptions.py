class GulaError(Exception):
    pass


class AuthenticationError(GulaError):
    pass


class NotFoundError(GulaError):
    pass


class ValidationError(GulaError):
    pass


class RateLimitError(GulaError):
    pass


class ServerError(GulaError):
    pass


__all__ = ["GulaError", "AuthenticationError", "NotFoundError", "ValidationError", "RateLimitError", "ServerError"]
