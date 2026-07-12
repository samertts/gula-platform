from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger("gula.feature_flags")


class FeatureFlag:
    def __init__(self, name: str, default: bool = False, env_var: str | None = None) -> None:
        self._name = name
        self._default = default
        self._env_var = env_var or f"FF_{name.upper()}"
        self._enabled: bool | None = None

    @property
    def enabled(self) -> bool:
        if self._enabled is not None:
            return self._enabled
        raw = os.getenv(self._env_var)
        if raw is not None:
            self._enabled = raw.lower() in ("true", "1", "yes")
        else:
            self._enabled = self._default
        return self._enabled

    def enable(self) -> None:
        self._enabled = True
        logger.info("Feature flag '%s' enabled", self._name)

    def disable(self) -> None:
        self._enabled = False
        logger.info("Feature flag '%s' disabled", self._name)

    def __bool__(self) -> bool:
        return self.enabled


class FeatureFlagRegistry:
    def __init__(self) -> None:
        self._flags: dict[str, FeatureFlag] = {}

    def register(self, name: str, default: bool = False, env_var: str | None = None) -> FeatureFlag:
        flag = FeatureFlag(name, default, env_var)
        self._flags[name] = flag
        return flag

    def get(self, name: str) -> FeatureFlag | None:
        return self._flags.get(name)

    def is_enabled(self, name: str) -> bool:
        flag = self._flags.get(name)
        return flag.enabled if flag else False

    def all_flags(self) -> dict[str, bool]:
        return {name: flag.enabled for name, flag in self._flags.items()}


registry = FeatureFlagRegistry()

SNDHS_VISITS = registry.register("sndhs_visits", env_var="SNDHS_ENABLE_VISITS")
SNDHS_NATIONAL_ID = registry.register("sndhs_national_id", env_var="SNDHS_ENABLE_NATIONAL_ID")
FINANCIAL_ENGINE = registry.register("financial_engine", env_var="ENABLE_FINANCIAL_ENGINE")
ADS = registry.register("ads", env_var="ENABLE_ADS")
BACKGROUND_TASKS = registry.register("background_tasks", default=True, env_var="FEATURE_BACKGROUND_TASKS")
AI_DATASET = registry.register("ai_dataset", env_var="ENABLE_AI_DATASET")

__all__ = ["FeatureFlag", "FeatureFlagRegistry", "registry", "SNDHS_VISITS",
           "SNDHS_NATIONAL_ID", "FINANCIAL_ENGINE", "ADS", "BACKGROUND_TASKS", "AI_DATASET"]
