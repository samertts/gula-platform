"""Print the package requirements the Dockerfile's pip install declares.

Used by scripts/verify_image_equivalent.sh so that the image-equivalent run
installs what the Dockerfile really says, not a list transcribed next to it. A
transcribed list drifts, and then the script proves something about the copy —
which is how IA-044's pyserial gap stayed unverified.
"""
from __future__ import annotations

import re
import shlex
import sys


def packages(dockerfile_text: str) -> list[str]:
    joined = dockerfile_text.replace("\\\n", " ")
    for line in joined.splitlines():
        if "pip install" in line and "--no-cache-dir" in line:
            return re.findall(r'"([^"]+)"', line)
    raise SystemExit("no `pip install --no-cache-dir` line found in the Dockerfile")


if __name__ == "__main__":
    with open(sys.argv[1]) as handle:
        # Printing the package list to stdout IS this script's interface —
        # the Dockerfile consumes it — so T201 is suppressed deliberately.
        print(" ".join(shlex.quote(p) for p in packages(handle.read())))  # noqa: T201
