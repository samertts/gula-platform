from __future__ import annotations

import logging
from typing import Dict, List, Optional, Set

logger = logging.getLogger("gula.kernel.features.regional")


class RegionalFeatureManager:
    def __init__(self):
        self._regional_features: dict[str, set[str]] = {}

    def register(self, region: str, features: list[str]) -> None:
        if region not in self._regional_features:
            self._regional_features[region] = set()
        self._regional_features[region].update(features)

    def is_enabled_in_region(self, region: str, feature: str) -> bool:
        return feature in self._regional_features.get(region, set())

    def get_regional_features(self, region: str) -> list[str]:
        return list(self._regional_features.get(region, set()))
