from __future__ import annotations

import logging
from dataclasses import dataclass

from app.kernel.features.capabilities import CapabilityFlagManager
from app.kernel.features.experimental import ExperimentalFeatureManager
from app.kernel.features.kill_switch import EmergencyKillSwitch
from app.kernel.features.regional import RegionalFeatureManager
from app.kernel.features.tenant_features import TenantFeatureManager

logger = logging.getLogger("gula.kernel.features")


@dataclass
class FeatureFlag:
    name: str
    enabled: bool = False
    description: str = ""
    owner: str = ""
    dependencies: list[str] = None

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


class FeatureFlagManager:
    def __init__(self, kernel=None):
        self.kernel = kernel
        self._flags: dict[str, FeatureFlag] = {}
        self.capabilities = CapabilityFlagManager()
        self.experimental = ExperimentalFeatureManager()
        self.regional = RegionalFeatureManager()
        self.tenant_features = TenantFeatureManager()
        self.kill_switch = EmergencyKillSwitch()

    def register(self, flag: FeatureFlag) -> None:
        self._flags[flag.name] = flag

    def is_enabled(self, name: str) -> bool:
        flag = self._flags.get(name)
        if not flag:
            return False
        if not flag.enabled:
            return False
        return all(self.is_enabled(dep) for dep in flag.dependencies or [])

    def enable(self, name: str) -> None:
        flag = self._flags.get(name)
        if flag:
            flag.enabled = True

    def disable(self, name: str) -> None:
        flag = self._flags.get(name)
        if flag:
            flag.enabled = False

    def list_flags(self) -> list[FeatureFlag]:
        return list(self._flags.values())
