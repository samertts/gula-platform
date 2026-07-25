#!/usr/bin/env python3
"""Pre-commit hook: check staged files for hardcoded secrets."""

import json
import os
import subprocess
import sys


def main() -> int:
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        capture_output=True, text=True,
    )
    files = [f for f in result.stdout.strip().split("\n") if f and os.path.isfile(f)]
    if not files:
        return 0

    exit_code = 0
    for f in files:
        if any(skip in f for skip in (".env.example", "/test", "/tests")):
            continue
        r = subprocess.run(
            ["python3", "-m", "detect_secrets", "scan", "--no-baseline", f],
            capture_output=True, text=True,
        )
        try:
            data = json.loads(r.stdout)
            if data.get("results") and any(data["results"].values()):
                print(f"SECRETS FOUND in {f}")
                exit_code = 1
        except json.JSONDecodeError:
            pass
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
