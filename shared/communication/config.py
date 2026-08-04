"""Environment-only configuration for the GULA Communication Platform Core.

All knobs come from ``COMMUNICATION_*`` environment variables. The Core
never holds secrets — provider credentials are owned by provider plugins and
loaded by them from their own environment variables.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass

logger = logging.getLogger("gula.communication.config")

_PREFIX = "COMMUNICATION_"


def _env_str(name: str, default: str = "") -> str:
    return os.getenv(_PREFIX + name, default)


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(_PREFIX + name, "")
    if value == "":
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


def _env_int(name: str, default: int) -> int:
    value = os.getenv(_PREFIX + name, "")
    if value == "":
        return default
    try:
        return int(value)
    except ValueError:
        logger.warning("communication_config_invalid name=%s value=%r", name, value)
        return default


@dataclass(frozen=True)
class CommunicationConfig:
    """Resolved configuration snapshot (immutable)."""

    enabled: bool = True
    default_priority: str = "normal"
    default_locale: str = ""
    template_strict_variables: bool = False
    audit_enabled: bool = True
    telemetry_enabled: bool = True
    queue_name: str = ""

    def to_dict(self) -> dict[str, str]:
        return {
            key: str(getattr(self, key)) for key in self.__dataclass_fields__
        }

    @classmethod
    def from_env(cls) -> CommunicationConfig:
        return cls(
            enabled=_env_bool("ENABLED", True),
            default_priority=_env_str("DEFAULT_PRIORITY", "normal").lower(),
            default_locale=_env_str("DEFAULT_LOCALE", ""),
            template_strict_variables=_env_bool("TEMPLATE_STRICT_VARIABLES", False),
            audit_enabled=_env_bool("AUDIT_ENABLED", True),
            telemetry_enabled=_env_bool("TELEMETRY_ENABLED", True),
            queue_name=_env_str("DEFAULT_QUEUE", ""),
        )


__all__ = ["CommunicationConfig"]