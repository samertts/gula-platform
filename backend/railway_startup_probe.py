"""Opt-in Railway startup diagnostic.

This module intentionally prints no environment-variable values.  When enabled
through GULA_STARTUP_DIAGNOSTICS=true, it imports the application before
Gunicorn so any import/configuration exception is emitted with a full traceback
in Railway's deploy logs.
"""

from __future__ import annotations

import sys
import traceback


def main() -> int:
    try:
        from app.main import app  # noqa: F401
    except BaseException:
        print("GULA startup diagnostic: application import failed", file=sys.stderr)
        traceback.print_exc()
        return 1

    print("GULA startup diagnostic: application import completed", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
