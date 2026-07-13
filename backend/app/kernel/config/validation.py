from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from backend.app.kernel.exceptions import ConfigurationError

logger = logging.getLogger("gula.kernel.config.validation")


class ConfigurationValidator:
    def __init__(self):
        self._schemas: dict[str, dict] = {}

    def register_schema(self, key: str, schema: dict) -> None:
        self._schemas[key] = schema

    def validate(self, key: str, value: Any) -> None:
        schema = self._schemas.get(key)
        if not schema:
            return
        expected_type = schema.get("type")
        if expected_type and expected_type == "string" and not isinstance(value, str):
            raise TypeError(f"Config '{key}' must be of type {expected_type}")
        if expected_type == "int" and not isinstance(value, int):
            raise TypeError(f"Config '{key}' must be of type int")
        if expected_type == "bool" and not isinstance(value, bool):
            raise TypeError(f"Config '{key}' must be of type bool")
