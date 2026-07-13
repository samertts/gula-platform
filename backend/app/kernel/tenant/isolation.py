from __future__ import annotations

import logging

logger = logging.getLogger("gula.kernel.tenant.isolation")


class TenantIsolation:
    def __init__(self):
        self._isolated: dict[str, bool] = {}

    def isolate(self, tenant_id: str) -> None:
        self._isolated[tenant_id] = True

    def deisolate(self, tenant_id: str) -> None:
        self._isolated[tenant_id] = False

    def is_isolated(self, tenant_id: str) -> bool:
        return self._isolated.get(tenant_id, False)
