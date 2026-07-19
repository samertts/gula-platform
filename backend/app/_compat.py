
import sys

if sys.version_info >= (3, 11):  # noqa: UP036 — Python <3.11 compat
    from datetime import UTC as _UTC
    from enum import StrEnum
else:
    from datetime import timezone
    _UTC = timezone.utc
    from enum import Enum
    class StrEnum(str, Enum):  # noqa: UP042 — Python <3.11 compat
        pass

UTC = _UTC

__all__ = ["UTC", "StrEnum"]
