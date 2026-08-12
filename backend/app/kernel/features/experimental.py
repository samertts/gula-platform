from __future__ import annotations

import logging

logger = logging.getLogger("gula.kernel.features.experimental")


class ExperimentalFeatureManager:
    def __init__(self):
        self._features: dict[str, bool] = {}

    def register(self, name: str, enabled: bool = False) -> None:
        self._features[name] = enabled

    def is_enabled(self, name: str) -> bool:
        return self._features.get(name, False)

    def enable(self, name: str) -> None:
        self._features[name] = True

    def disable(self, name: str) -> None:
        self._features[name] = False

    def list_experimental(self) -> list[str]:
        return list(self._features.keys())
