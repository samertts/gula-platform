from __future__ import annotations

import logging

logger = logging.getLogger("gula.kernel.tenant.quotas")


class TenantQuotaManager:
    def __init__(self):
        self._quotas: dict[str, dict[str, int]] = {}
        self._usage: dict[str, dict[str, int]] = {}

    def set_quota(self, tenant_id: str, resource: str, limit: int) -> None:
        if tenant_id not in self._quotas:
            self._quotas[tenant_id] = {}
        self._quotas[tenant_id][resource] = limit

    def get_quota(self, tenant_id: str, resource: str) -> int:
        return self._quotas.get(tenant_id, {}).get(resource, 0)

    def check_quota(self, tenant_id: str, resource: str) -> bool:
        limit = self.get_quota(tenant_id, resource)
        if limit == 0:
            return True
        usage = self._usage.get(tenant_id, {}).get(resource, 0)
        return usage < limit

    def increment_usage(self, tenant_id: str, resource: str, amount: int = 1) -> None:
        if tenant_id not in self._usage:
            self._usage[tenant_id] = {}
        self._usage[tenant_id][resource] = self._usage[tenant_id].get(resource, 0) + amount
