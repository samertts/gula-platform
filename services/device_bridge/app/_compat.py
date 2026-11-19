"""Version shims for the device bridge, local to this service.

Four modules imported `backend.app._compat` for `UTC`. The Dockerfile's build
context is services/device_bridge and it copies only `app/`, so `backend` is not
in the image at all: `import app.main` raised

    ModuleNotFoundError: No module named 'backend'

and the published image could not start. The compose healthcheck polls /health,
which never answered, so the documented
`docker compose --profile device-bridge up device-bridge` could not come up.

Reproducing it required running with the module path the image really has. Every
local test run put the repository root on PYTHONPATH, which satisfied the import
and hid the failure. See IA-044.

This file is deliberately a copy rather than a shared package: a service whose
image contains only its own `app/` tree must not import from a sibling tree.
"""
from __future__ import annotations

import sys

if sys.version_info >= (3, 11):  # noqa: UP036 — Python <3.11 compat
    from datetime import UTC
    from enum import StrEnum
else:
    from datetime import timezone
    from enum import Enum

    UTC = timezone.utc  # noqa: UP017 — datetime.UTC does not exist on <3.11

    class StrEnum(str, Enum):  # noqa: UP042 — Python <3.11 compat
        pass

__all__ = ["UTC", "StrEnum"]
