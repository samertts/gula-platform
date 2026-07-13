from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Dict, List, Optional

from backend.app.kernel.exceptions import TenantNotFoundError

if TYPE_CHECKING:
    from backend.app.kernel.tenant.registry import TenantRegistry

logger = logging.getLogger("gula.kernel.tenant.resolver")


class TenantResolver:
    def __init__(self, registry: TenantRegistry):
        self.registry = registry

    def resolve_by_id(self, tenant_id: str) -> str | None:
        tenant = self.registry.get(tenant_id)
        if not tenant:
            return None
        return tenant.id

    def resolve_by_slug(self, slug: str) -> str | None:
        for tenant in self.registry.list_tenants():
            if tenant.slug == slug:
                return tenant.id
        return None
