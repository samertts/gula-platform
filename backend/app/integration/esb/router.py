from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from backend.app.integration.esb.types import ESBMessage

logger = logging.getLogger("gula.integration.esb.router")


@dataclass
class RouteEntry:
    event_name: str = ""
    handler_name: str = ""
    pattern: str = ""
    priority: int = 5
    active: bool = True


class ESBRouter:
    def __init__(self):
        self._routes: dict[str, RouteEntry] = {}
        self._wildcard_routes: list[RouteEntry] = []

    def register_route(self, event_name: str, handler_name: str, priority: int = 5) -> None:
        route = RouteEntry(event_name=event_name, handler_name=handler_name, priority=priority)
        if "*" in event_name:
            self._wildcard_routes.append(route)
        else:
            self._routes[event_name] = route
        logger.info("Route registered: %s -> %s", event_name, handler_name)

    def unregister_route(self, event_name: str) -> bool:
        if event_name in self._routes:
            del self._routes[event_name]
            logger.info("Route unregistered: %s", event_name)
            return True
        self._wildcard_routes[:] = [r for r in self._wildcard_routes if r.event_name != event_name]
        return False

    def route(self, message: ESBMessage) -> list[str]:
        handlers: list[str] = []
        route = self._routes.get(message.event_name)
        if route and route.active:
            handlers.append(route.handler_name)

        for wc_route in self._wildcard_routes:
            if wc_route.active:
                handlers.append(wc_route.handler_name)

        return handlers

    def disable_route(self, event_name: str) -> bool:
        route = self._routes.get(event_name)
        if route:
            route.active = False
            return True
        return False

    def enable_route(self, event_name: str) -> bool:
        route = self._routes.get(event_name)
        if route:
            route.active = True
            return True
        return False

    def list_routes(self) -> list[dict[str, Any]]:
        result = []
        for route in self._routes.values():
            result.append(
                {
                    "event_name": route.event_name,
                    "handler": route.handler_name,
                    "active": route.active,
                    "priority": route.priority,
                }
            )
        for route in self._wildcard_routes:
            result.append(
                {
                    "event_name": route.event_name,
                    "handler": route.handler_name,
                    "active": route.active,
                    "priority": route.priority,
                    "wildcard": True,
                }
            )
        return result

    def route_count(self) -> int:
        return len(self._routes) + len(self._wildcard_routes)
