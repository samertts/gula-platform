from __future__ import annotations

import logging

from app.kernel.tenant.config import TenantConfiguration
from app.kernel.tenant.isolation import TenantIsolation
from app.kernel.tenant.quotas import TenantQuotaManager
from app.kernel.tenant.resolver import TenantResolver
from app.kernel.types import TenantDescriptor

logger = logging.getLogger("gula.kernel.tenant.registry")


class TenantRegistry:
    def __init__(self):
        self._tenants: dict[str, TenantDescriptor] = {}
        self.resolver = TenantResolver(self)
        self.isolation = TenantIsolation()
        self.quotas = TenantQuotaManager()
        self.config = TenantConfiguration()

    def register(self, descriptor: TenantDescriptor) -> None:
        self._tenants[descriptor.id] = descriptor

    def get(self, tenant_id: str) -> TenantDescriptor | None:
        return self._tenants.get(tenant_id)

    def list_tenants(self) -> list[TenantDescriptor]:
        return list(self._tenants.values())

    def has(self, tenant_id: str) -> bool:
        return tenant_id in self._tenants
