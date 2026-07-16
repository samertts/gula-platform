from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from backend.app.integration.api_management.catalog import APICatalog, APIService

logger = logging.getLogger("gula.integration.api_management.portal")


@dataclass
class PortalApp:
    id: str = ""
    name: str = ""
    description: str = ""
    api_services: list[str] = field(default_factory=list)
    owner: str = ""
    active: bool = True
    documentation_url: str = ""
    support_contact: str = ""


class APIPortal:
    def __init__(self, catalog: APICatalog | None = None):
        self._catalog = catalog or APICatalog()
        self._apps: dict[str, PortalApp] = {}

    def register_app(self, app: PortalApp) -> None:
        self._apps[app.id] = app
        logger.info("Portal app registered: %s", app.name)

    def unregister_app(self, app_id: str) -> bool:
        if app_id in self._apps:
            del self._apps[app_id]
            logger.info("Portal app unregistered: %s", app_id)
            return True
        return False

    def get_app(self, app_id: str) -> PortalApp | None:
        return self._apps.get(app_id)

    def list_apps(self) -> list[PortalApp]:
        return list(self._apps.values())

    def subscribe_to_api(self, app_id: str, service_id: str) -> bool:
        app = self._apps.get(app_id)
        if not app:
            logger.warning("App not found: %s", app_id)
            return False
        service = self._catalog.get_service(service_id)
        if not service:
            logger.warning("Service not found: %s", service_id)
            return False
        if service_id not in app.api_services:
            app.api_services.append(service_id)
            logger.info("App '%s' subscribed to API: %s", app.name, service.name)
        return True

    def unsubscribe_from_api(self, app_id: str, service_id: str) -> bool:
        app = self._apps.get(app_id)
        if not app:
            return False
        if service_id in app.api_services:
            app.api_services.remove(service_id)
            logger.info("App '%s' unsubscribed from API: %s", app.name, service_id)
            return True
        return False

    def get_app_apis(self, app_id: str) -> list[APIService]:
        app = self._apps.get(app_id)
        if not app:
            return []
        return [s for sid in app.api_services if (s := self._catalog.get_service(sid))]

    def search_apis(self, query: str) -> list[APIService]:
        query_lower = query.lower()
        results = []
        for service in self._catalog.list_services():
            if query_lower in service.name.lower() or query_lower in service.description.lower():
                results.append(service)
        return results

    def get_analytics(self) -> dict[str, Any]:
        return {
            "total_apps": len(self._apps),
            "total_services": self._catalog.count(),
            "active_apps": sum(1 for a in self._apps.values() if a.active),
        }
