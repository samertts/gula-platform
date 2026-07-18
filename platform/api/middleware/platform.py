import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response


class PlatformMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = str(uuid.uuid4())
        start_time = time.monotonic()

        response = await call_next(request)

        elapsed = time.monotonic() - start_time
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{elapsed * 1000:.0f}ms"

        return response
