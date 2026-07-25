from __future__ import annotations

import logging
from typing import Any

from app.kernel.features.flags import FeatureFlag, FeatureFlagManager
from app.kernel.features.kill_switch import EmergencyKillSwitch
from app.kernel.features.regional import RegionalFeatureManager
from app.kernel.features.tenant_features import TenantFeatureManager
from app.kernel.integration import get_kernel

logger = logging.getLogger("gula.control_plane.config.features")


class FeatureManager:
    def __init__(self):
        self._kernel_ffm: FeatureFlagManager | None = None

    def _get_ffm(self) -> FeatureFlagManager:
        if self._kernel_ffm is None:
            kernel = get_kernel()
            ffm = kernel.get_component("feature_flag_manager")
            if ffm is None:
                ffm = FeatureFlagManager(kernel)
                kernel.register_component("feature_flag_manager", ffm)
            self._kernel_ffm = ffm
        return self._kernel_ffm

    def register(
        self, name: str, enabled: bool = False, description: str = "", owner: str = "",
    ) -> FeatureFlag:
        ffm = self._get_ffm()
        flag = FeatureFlag(name=name, enabled=enabled, description=description, owner=owner)
        ffm.register(flag)
        logger.info("Feature flag registered: %s (enabled=%s)", name, enabled)
        return flag

    def is_enabled(self, name: str) -> bool:
        return self._get_ffm().is_enabled(name)

    def enable(self, name: str) -> None:
        self._get_ffm().enable(name)
        logger.info("Feature flag enabled: %s", name)

    def disable(self, name: str) -> None:
        self._get_ffm().disable(name)
        logger.info("Feature flag disabled: %s", name)

    def list_flags(self) -> list[dict[str, Any]]:
        return [
            {"name": f.name, "enabled": f.enabled, "description": f.description, "owner": f.owner}
            for f in self._get_ffm().list_flags()
        ]

    @property
    def kill_switch(self) -> EmergencyKillSwitch:
        return self._get_ffm().kill_switch

    @property
    def regional(self) -> RegionalFeatureManager:
        return self._get_ffm().regional

    @property
    def tenant_features(self) -> TenantFeatureManager:
        return self._get_ffm().tenant_features
