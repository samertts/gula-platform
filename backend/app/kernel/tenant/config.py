from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("gula.kernel.tenant.config")


class TenantConfiguration:
    def __init__(self):
        self._configs: dict[str, dict[str, Any]] = {}

    def set(self, tenant_id: str, key: str, value: Any) -> None:
        if tenant_id not in self._configs:
            self._configs[tenant_id] = {}
        self._configs[tenant_id][key] = value

    def get(self, tenant_id: str, key: str, default: Any = None) -> Any:
        return self._configs.get(tenant_id, {}).get(key, default)

    def get_all(self, tenant_id: str) -> dict[str, Any]:
        return self._configs.get(tenant_id, {})
