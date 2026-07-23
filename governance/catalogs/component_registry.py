from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from governance.compiler.models import ComponentRegistryEntry, ModuleStatus


class NationalComponentRegistry:
    _instance: NationalComponentRegistry | None = None
    REGISTRY_PATH = Path(__file__).resolve().parent / "component_registry.json"

    def __new__(cls) -> NationalComponentRegistry:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._components: list[ComponentRegistryEntry] = []
            cls._instance._loaded = False
        return cls._instance

    def load(self) -> None:
        if self._loaded:
            return
        if self.REGISTRY_PATH.exists():
            data = json.loads(self.REGISTRY_PATH.read_text(encoding="utf-8"))
            self._components = [ComponentRegistryEntry(**c) for c in data.get("components", [])]
        else:
            self._components = self._default_components()
            self.save()
        self._loaded = True

    def save(self) -> None:
        data = {
            "version": "1.0.0",
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "components": [c.to_dict() for c in self._components],
        }
        self.REGISTRY_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    @property
    def components(self) -> list[ComponentRegistryEntry]:
        self.load()
        return self._components

    def search(self, query: str = "", status: str = "") -> list[ComponentRegistryEntry]:
        results = self.components
        if query:
            q = query.lower()
            results = [c for c in results if q in c.name.lower() or q in c.documentation.lower()]
        if status:
            results = [c for c in results if c.status.value.lower() == status.lower()]
        return results

    def get_by_name(self, name: str) -> ComponentRegistryEntry | None:
        for c in self.components:
            if c.name.lower() == name.lower():
                return c
        return None

    def get_by_status(self, status: ModuleStatus) -> list[ComponentRegistryEntry]:
        return [c for c in self.components if c.status == status]

    def add_component(self, component: ComponentRegistryEntry) -> None:
        self.load()
        existing = self.get_by_name(component.name)
        if existing:
            self._components.remove(existing)
        self._components.append(component)
        self.save()

    def to_dict(self) -> dict[str, Any]:
        return {
            "components": [c.to_dict() for c in self.components],
            "count": len(self.components),
        }

    def _default_components(self) -> list[ComponentRegistryEntry]:
        return [
            ComponentRegistryEntry("Identity", "platform", "2.5.0", ["PostgreSQL", "Redis"], ModuleStatus.CERTIFIED, "docs/identity/", ["/api/v1/auth/*", "/api/v1/identity/*"], "Import IdentityService from app.identity", ["FastAPI", "PostgreSQL", "Redis"]),
            ComponentRegistryEntry("Audit", "platform", "2.5.0", ["PostgreSQL"], ModuleStatus.CERTIFIED, "docs/audit/", ["/api/v1/audit/*"], "Import AuditService from app.audit", ["FastAPI", "PostgreSQL"]),
            ComponentRegistryEntry("Notification", "platform", "2.5.0", ["Redis"], ModuleStatus.APPROVED, "docs/notifications/", ["/api/v1/notifications/*"], "Import NotificationService from app.notifications", ["FastAPI", "Redis"]),
            ComponentRegistryEntry("Workflow", "platform", "1.0.0", ["PostgreSQL", "Redis"], ModuleStatus.STABLE, "docs/workflows/", ["/api/v1/workflows/*"], "Import WorkflowEngine from app.workflows", ["FastAPI", "PostgreSQL"]),
            ComponentRegistryEntry("Storage", "platform", "1.0.0", ["MinIO"], ModuleStatus.CERTIFIED, "docs/storage/", ["/api/v1/storage/*"], "Import StorageBackend from app.gateways", ["FastAPI", "MinIO"]),
            ComponentRegistryEntry("Logging", "platform", "1.0.0", ["Loki"], ModuleStatus.CERTIFIED, "docs/logging/", [], "Use structured JSON logging via logging_config.py", ["Loki", "Prometheus"]),
            ComponentRegistryEntry("Observability", "platform", "1.0.0", ["Prometheus", "Grafana", "Loki", "Tempo"], ModuleStatus.CERTIFIED, "docs/observability/", ["/health/*", "/metrics"], "Use OpenTelemetry for tracing, Prometheus for metrics", ["OpenTelemetry", "Prometheus", "Grafana"]),
            ComponentRegistryEntry("API Gateway", "platform", "2.5.0", ["Nginx"], ModuleStatus.CERTIFIED, "docs/gateway/", ["/api/v1/*"], "Configure via nginx config in config/nginx/", ["Nginx"]),
            ComponentRegistryEntry("FHIR", "platform", "1.0.0", ["PostgreSQL"], ModuleStatus.APPROVED, "docs/fhir/", ["/api/v1/fhir/*"], "Import FHIRService from app.fhir", ["FastAPI", "FHIR R4"]),
            ComponentRegistryEntry("AI Platform", "platform", "1.0.0", ["PostgreSQL", "Redis", "Ollama"], ModuleStatus.EXPERIMENTAL, "docs/ai/", ["/api/v1/ai/*"], "Import AIService from app.ai_fabric", ["FastAPI", "Ollama"]),
            ComponentRegistryEntry("Authentication", "platform", "2.5.0", ["PostgreSQL", "Redis", "Keycloak"], ModuleStatus.CERTIFIED, "docs/security/auth.md", ["/api/v1/auth/*"], "Use get_current_user dependency", ["FastAPI", "JWT", "Keycloak"]),
            ComponentRegistryEntry("Authorization", "platform", "2.5.0", ["PostgreSQL"], ModuleStatus.CERTIFIED, "docs/security/rbac.md", ["/api/v1/auth/*"], "Use require_permission decorator", ["FastAPI", "RBAC", "ABAC"]),
            ComponentRegistryEntry("Scheduling", "platform", "1.0.0", ["PostgreSQL", "Redis"], ModuleStatus.STABLE, "docs/scheduling/", ["/api/v1/schedule/*"], "Import SchedulingService from app.tasks", ["FastAPI", "APScheduler"]),
            ComponentRegistryEntry("Messaging", "platform", "1.0.0", ["RabbitMQ", "Redis"], ModuleStatus.APPROVED, "docs/messaging/", ["/api/v1/messages/*"], "Import EventBus from app.kernel", ["RabbitMQ", "NATS"]),
        ]
