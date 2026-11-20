"""Compatibility shims for Python versions earlier than 3.11.

The backend declares Python >=3.12, but the device bridge and local validation
toolchain still run on 3.10. The previous ``UTC = UTC`` branch raised NameError
on 3.10, and several modules import ``StrEnum``/``Self`` directly from
3.11+ standard-library locations. Centralizing the shims keeps those modules
importable without changing their behavior on supported runtimes.
"""

from __future__ import annotations

import sys
from datetime import timezone

if sys.version_info >= (3, 11):  # noqa: UP036 — Python <3.11 compat
    from datetime import UTC
    from enum import StrEnum
    from typing import Self
else:
    UTC = timezone.utc  # noqa: UP017 — Python 3.10 compatible
    from enum import Enum

    class StrEnum(str, Enum):  # noqa: UP042 — Python <3.11 compat
        pass

    try:  # typing_extensions is already present via pydantic.
        from typing_extensions import Self  # noqa: UP035 — Python 3.10 compatible
    except ImportError:  # pragma: no cover - annotation-only fallback
        from typing import TypeVar

        Self = TypeVar("Self")


__all__ = ["UTC", "Self", "StrEnum"]
