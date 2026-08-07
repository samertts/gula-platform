from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urljoin

import httpx

from app.integration.api_management.auth import APIAuth

logger = logging.getLogger("gula.integration.api_management.gateway")


@dataclass
class GatewayRoute:
    path: str = ""
    target_url: str = ""
    methods: list[str] = field(default_factory=lambda: ["GET"])
    rate_limit: int = 0
    auth_required: bool = True
    timeout: float = 30.0
    active: bool = True
    transform_request: str = ""
    transform_response: str = ""


class APIGateway:
    def __init__(self, auth: APIAuth | None = None):
        self._routes: list[GatewayRoute] = []
        self._auth = auth or APIAuth()
        self._client: httpx.AsyncClient | None = None

    async def start(self) -> None:
        self._client = httpx.AsyncClient(timeout=httpx.Timeout(30.0))
        logger.info("API Gateway started with %d routes", len(self._routes))

    async def stop(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None
        logger.info("API Gateway stopped")

    def add_route(self, route: GatewayRoute) -> None:
        self._routes.append(route)
        logger.info("Route added: %s -> %s", route.path, route.target_url)

    def remove_route(self, path: str) -> bool:
        for i, route in enumerate(self._routes):
            if route.path == path:
                self._routes.pop(i)
                logger.info("Route removed: %s", path)
                return True
        return False

    async def forward(
        self, method: str, path: str, headers: dict[str, str] | None = None, body: Any = None
    ) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("API Gateway not started")

        route = self._find_route(path, method)
        if not route:
            return {"success": False, "status_code": 404, "error": f"No route for {method} {path}"}

        if route.auth_required and headers:
            auth_header = headers.get("Authorization", "")
            if not self._auth.validate_token(auth_header):
                return {"success": False, "status_code": 401, "error": "Unauthorized"}

        target_url = urljoin(route.target_url, path)
        req_headers = {"Content-Type": "application/json"}
        if headers:
            req_headers.update(headers)

        try:
            start = time.monotonic()
            resp = await self._client.request(
                method=method,
                url=target_url,
                headers=req_headers,
                json=body if method in ("POST", "PUT", "PATCH") else None,
                timeout=route.timeout,
            )
            latency_ms = (time.monotonic() - start) * 1000
            return {
                "success": resp.is_success,
                "status_code": resp.status_code,
                "data": resp.json() if resp.is_success else resp.text,
                "latency_ms": latency_ms,
            }
        except Exception as exc:
            logger.error("Gateway forwarding failed: %s", exc)
            return {"success": False, "status_code": 502, "error": str(exc)}

    def _find_route(self, path: str, method: str) -> GatewayRoute | None:
        for route in self._routes:
            if not route.active:
                continue
            if route.path == path and method.upper() in [m.upper() for m in route.methods]:
                return route
        return None

    def list_routes(self) -> list[GatewayRoute]:
        return list(self._routes)

    def set_auth(self, auth: APIAuth) -> None:
        self._auth = auth
