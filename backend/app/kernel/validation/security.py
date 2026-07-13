from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from backend.app.kernel import Kernel

logger = logging.getLogger("gula.kernel.validation.security")


class SecurityValidator:
    def __init__(self, kernel: Kernel):
        self.kernel = kernel

    def validate(self) -> list[dict]:
        issues = []
        pm = self.kernel.get_component("plugin_manager")
        if pm:
            for plugin in pm.list_plugins():
                if not plugin.permissions:
                    issues.append(
                        {
                            "type": "missing_permissions",
                            "plugin": plugin.name,
                            "severity": "warning",
                        }
                    )
        return issues
