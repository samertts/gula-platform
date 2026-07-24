from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger("gula.kernel.config.versioned")


@dataclass
class ConfigVersion:
    version: int
    config: dict
    created_at: float = 0.0
    comment: str = ""

    def __post_init__(self):
        if not self.created_at:
            import time

            self.created_at = time.time()


class VersionedConfiguration:
    def __init__(self):
        self._versions: list[ConfigVersion] = []
        self._current_version: int = 0

    def snapshot(self, config: dict, comment: str = "") -> int:
        self._current_version += 1
        self._versions.append(
            ConfigVersion(
                version=self._current_version,
                config=dict(config),
                comment=comment,
            ),
        )
        return self._current_version

    def get_version(self, version: int) -> ConfigVersion | None:
        for v in self._versions:
            if v.version == version:
                return v
        return None

    def list_versions(self) -> list[ConfigVersion]:
        return list(self._versions)
