import datetime as _datetime
import sys

if sys.version_info >= (3, 11):  # noqa: UP036 — Python <3.11 compat
    from datetime import UTC
    from enum import StrEnum
else:

    UTC = UTC
    _datetime.UTC = UTC
    from enum import Enum

    class StrEnum(str, Enum):  # noqa: UP042 — Python <3.11 compat
        pass


__all__ = ["UTC", "StrEnum"]
