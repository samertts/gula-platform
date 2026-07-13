from __future__ import annotations

import logging
from typing import Dict, List, Optional

logger = logging.getLogger("gula.kernel.features.tenant")


class TenantFeatureManager:
    def __init__(self):
        self._tenant_features: dict[str, dict[str, bool]] = {}

    def set_feature(self, tenant_id: str, feature: str, enabled: bool) -> None:
        if tenant_id not in self._tenant_features:
            self._tenant_features[tenant_id] = {}
        self._tenant_features[tenant_id][feature] = enabled

    def is_enabled(self, tenant_id: str, feature: str) -> bool:
        return self._tenant_features.get(tenant_id, {}).get(feature, False)

    def get_tenant_features(self, tenant_id: str) -> dict[str, bool]:
        return self._tenant_features.get(tenant_id, {})
