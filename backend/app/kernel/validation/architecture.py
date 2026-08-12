from __future__ import annotations

import logging

from app.kernel import Kernel

logger = logging.getLogger("gula.kernel.validation.architecture")


class ArchitectureValidator:
    def __init__(self, kernel: Kernel):
        self.kernel = kernel

    def validate(self) -> list[dict]:
        issues = []
        required_components = [
            "application_context",
            "di_container",
            "service_registry",
            "capability_registry",
            "lifecycle_manager",
            "module_loader",
        ]
        for comp in required_components:
            if not self.kernel.get_component(comp):
                issues.append({"type": "missing_component", "name": comp})
        return issues
