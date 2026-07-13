from __future__ import annotations

import logging
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("gula.kernel.gateway.validation")


class RequestValidator:
    def __init__(self):
        self._validators: dict[str, Callable] = {}

    def register(self, path: str, validator: Callable) -> None:
        self._validators[path] = validator

    def validate(self, path: str, request: Any) -> bool:
        validator = self._validators.get(path)
        if not validator:
            return True
        return validator(request)
