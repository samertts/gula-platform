from __future__ import annotations

import logging
from collections.abc import Callable

logger = logging.getLogger("gula.kernel.gateway.routing")


class Route:
    def __init__(self, path: str, method: str, handler: Callable, service: str = ""):
        self.path = path
        self.method = method
        self.handler = handler
        self.service = service


class InternalRouter:
    def __init__(self):
        self._routes: list[Route] = []

    def register(self, route: Route) -> None:
        self._routes.append(route)

    def match(self, path: str, method: str) -> Route | None:
        for route in self._routes:
            if route.path == path and route.method == method:
                return route
        return None
