"""GULA's ASGI worker configuration for Gunicorn.

Values are read from environment at worker import time so deployments can tune
concurrency and graceful shutdown without rebuilding the image. The defaults
are deliberately conservative for memory-bound instances.
"""

import os

from uvicorn_worker import UvicornWorker


def _positive_int(name: str, default: int) -> int:
    value = int(os.getenv(name, str(default)))
    if value < 1:
        raise ValueError(f"{name} must be positive")
    return value


class GulaUvicornWorker(UvicornWorker):
    """Uvicorn worker with bounded concurrency and keep-alive behavior."""

    CONFIG_KWARGS = {
        "limit_concurrency": _positive_int("UVICORN_LIMIT_CONCURRENCY", 400),
        "timeout_keep_alive": _positive_int("UVICORN_TIMEOUT_KEEP_ALIVE", 5),
        "timeout_graceful_shutdown": _positive_int(
            "UVICORN_TIMEOUT_GRACEFUL_SHUTDOWN", 30
        ),
        "limit_max_requests": _positive_int("UVICORN_LIMIT_MAX_REQUESTS", 10000),
    }
