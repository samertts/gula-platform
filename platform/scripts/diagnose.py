#!/usr/bin/env python3
import argparse
import json
import os
import sys


def diagnose():
    parser = argparse.ArgumentParser(description="Platform diagnostics")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    print("=" * 50)
    print("GULA Platform Diagnostics")
    print("=" * 50)

    print(f"\nPython:       {sys.version}")
    print(f"Platform:     {sys.platform}")
    print(f"PID:          {os.getpid()}")
    print(f"CWD:          {os.getcwd()}")

    platform_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    print(f"Platform:     {platform_path}")

    core_files = []
    for root, dirs, files in os.walk(os.path.join(platform_path, "core")):
        for f in files:
            if f.endswith(".py") and not f.startswith("_"):
                core_files.append(os.path.join(root, f))
    print(f"Core modules: {len(core_files)}")

    app_files = []
    for root, dirs, files in os.walk(os.path.join(platform_path, "apps")):
        for f in files:
            if f.endswith(".py"):
                app_files.append(os.path.join(root, f))
    print(f"App modules:  {len(app_files)}")

    import_size = 0
    try:
        from platform.core import Kernel
        import_size += 1
    except ImportError:
        pass
    try:
        from platform.api import create_app
        import_size += 1
    except ImportError:
        pass

    print(f"Imports OK:   {import_size}/2")

    print("\nEnvironment:")
    for key in sorted(os.environ.keys()):
        if key.startswith("GULA_") or key in ("ENVIRONMENT", "DATABASE_URL", "REDIS_URL", "PORT", "HOST"):
            val = os.environ.get(key, "")
            if "PASSWORD" in key.upper() or "SECRET" in key.upper() or "TOKEN" in key.upper():
                val = "***"
            print(f"  {key}={val}")

    print("\nDone.")
