import datetime as _datetime
import sys

if sys.version_info >= (3, 11):
    from datetime import UTC
    from enum import StrEnum
else:
    from datetime import timezone

    UTC = timezone.utc
    _datetime.UTC = UTC  # type: ignore[attr-defined]

    from enum import Enum as _Enum

    class StrEnum(str, _Enum):
        pass


__all__ = ["UTC", "StrEnum"]
