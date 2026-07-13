from __future__ import annotations

import logging
from typing import Dict, List, Optional

logger = logging.getLogger("gula.kernel.features.capabilities")


class CapabilityFlagManager:
    def __init__(self):
        self._capabilities: dict[str, bool] = {}

    def register(self, name: str, enabled: bool = False) -> None:
        self._capabilities[name] = enabled

    def is_enabled(self, name: str) -> bool:
        return self._capabilities.get(name, False)

    def enable(self, name: str) -> None:
        self._capabilities[name] = True

    def disable(self, name: str) -> None:
        self._capabilities[name] = False
