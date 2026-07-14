import sys as _sys

if _sys.version_info >= (3, 11):
    from datetime import UTC
else:
    from datetime import timezone as _timezone

    UTC = _timezone.utc

if _sys.version_info >= (3, 11):
    from enum import StrEnum
else:
    from enum import Enum

    class StrEnum(str, Enum):
        """Python 3.10 compatibility shim."""


__all__ = ["UTC", "StrEnum"]
