from __future__ import annotations

import logging
import uuid
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

current_tenant: ContextVar[str | None] = ContextVar("current_tenant", default=None)
current_lab_id: ContextVar[uuid.UUID | None] = ContextVar("current_lab_id", default=None)


@dataclass
class Tenant:
    id: str
    name: str
    lab_id: uuid.UUID | None = None
    features: dict[str, bool] = field(default_factory=dict)
    quotas: dict[str, int] = field(default_factory=dict)
    config: dict[str, Any] = field(default_factory=dict)


class TenantContext:
    @staticmethod
    def set(tenant_id: str):
        current_tenant.set(tenant_id)

    @staticmethod
    def get() -> str | None:
        return current_tenant.get()

    @staticmethod
    def clear():
        current_tenant.set(None)

    @staticmethod
    def set_lab_id(lab_id: uuid.UUID):
        current_lab_id.set(lab_id)

    @staticmethod
    def get_lab_id() -> uuid.UUID | None:
        return current_lab_id.get()


class TenantManager:
    def __init__(self):
        self._tenants: dict[str, Tenant] = {}

    def register_tenant(self, tenant: Tenant):
        self._tenants[tenant.id] = tenant
        logger.info("Registered tenant: %s (%s)", tenant.id, tenant.name)

    def get_tenant(self, tenant_id: str) -> Tenant | None:
        return self._tenants.get(tenant_id)

    def unregister_tenant(self, tenant_id: str):
        self._tenants.pop(tenant_id, None)

    def list_tenants(self) -> list[Tenant]:
        return list(self._tenants.values())

    def tenant_exists(self, tenant_id: str) -> bool:
        return tenant_id in self._tenants


class TenantIsolationMiddleware:
    def __init__(self, tenant_manager: TenantManager, header_name: str = "X-Tenant-ID"):
        self._manager = tenant_manager
        self._header = header_name

    async def __call__(self, request: Any, call_next: Any) -> Any:
        tenant_id = request.headers.get(self._header)
        if tenant_id and self._manager.tenant_exists(tenant_id):
            TenantContext.set(tenant_id)
        try:
            return await call_next(request)
        finally:
            TenantContext.clear()


class QuotaManager:
    def __init__(self, tenant_manager: TenantManager):
        self._tenant_manager = tenant_manager
        self._usage: dict[str, dict[str, int]] = {}

    async def check_quota(self, tenant_id: str, resource: str, amount: int = 1) -> bool:
        tenant = self._tenant_manager.get_tenant(tenant_id)
        if not tenant:
            return False
        limit = tenant.quotas.get(resource)
        if limit is None:
            return True
        current = self._usage.get(tenant_id, {}).get(resource, 0)
        return (current + amount) <= limit

    async def increment_usage(self, tenant_id: str, resource: str, amount: int = 1):
        if tenant_id not in self._usage:
            self._usage[tenant_id] = {}
        self._usage[tenant_id][resource] = self._usage[tenant_id].get(resource, 0) + amount

    async def get_usage(self, tenant_id: str, resource: str | None = None) -> dict[str, int] | int:
        usage = self._usage.get(tenant_id, {})
        if resource:
            return usage.get(resource, 0)
        return usage

    async def reset_usage(self, tenant_id: str):
        self._usage.pop(tenant_id, None)
