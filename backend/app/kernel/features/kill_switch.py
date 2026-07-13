from __future__ import annotations

import logging
import time
from typing import Optional

logger = logging.getLogger("gula.kernel.features.kill_switch")


class EmergencyKillSwitch:
    def __init__(self):
        self._active = False
        self._activated_at: float = 0.0
        self._reason: str = ""

    def activate(self, reason: str = "Emergency kill switch activated") -> None:
        self._active = True
        self._activated_at = time.time()
        self._reason = reason

    def deactivate(self) -> None:
        self._active = False
        self._reason = ""
        self._activated_at = 0.0

    @property
    def is_active(self) -> bool:
        return self._active

    @property
    def reason(self) -> str:
        return self._reason
