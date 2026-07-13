from __future__ import annotations

import logging

from backend.app.kernel import Kernel

logger = logging.getLogger("gula.kernel.validation.dependencies")


class DependencyValidator:
    def __init__(self, kernel: Kernel):
        self.kernel = kernel

    def validate(self) -> list[dict]:
        issues = []
        sr = self.kernel.get_component("service_registry")
        if sr:
            for service_name in sr.list_services():
                metadata = sr.get_metadata(service_name)
                if metadata and "dependencies" in metadata:
                    for dep in metadata["dependencies"]:
                        if not sr.has(dep):
                            issues.append(
                                {
                                    "type": "missing_dependency",
                                    "service": service_name,
                                    "dependency": dep,
                                }
                            )
        return issues
