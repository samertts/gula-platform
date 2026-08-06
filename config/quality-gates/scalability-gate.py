#!/usr/bin/env python3
"""Scalability validation gate."""

import os
import sys

PASS = 0
FAIL = 1

BACKEND_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "backend", "app")


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    def check(condition: bool, msg: str, critical: bool = True) -> bool:
        if not condition:
            (errors if critical else warnings).append(msg)
            return False
        print(f"  {'PASS' if condition else 'FAIL'}: {msg}")
        return True

    print("=== Scalability Validation Gate ===")

    print("\n1. Checking statelessness...")
    has_local_state = False
    for root, dirs, files in os.walk(BACKEND_DIR):
        for f in files:
            if f.endswith(".py"):
                path = os.path.join(root, f)
                with open(path) as fh:
                    content = fh.read()
                    if "open(" in content and ("/tmp/" in content or "/data/" in content):
                        if "audit-anchors" in content or "volume_mount" in content:
                            continue
                        has_local_state = True
    check(not has_local_state, "No local filesystem state in API handlers")

    print("\n2. Checking connection pool formula...")
    web_concurrency = int(os.environ.get("WEB_CONCURRENCY", "3"))
    db_pool_size = int(os.environ.get("DB_POOL_SIZE", "6"))
    db_max_overflow = int(os.environ.get("DB_MAX_OVERFLOW", "12"))
    max_connections = int(os.environ.get("POSTGRES_MAX_CONNECTIONS", "100"))
    budget = web_concurrency * (db_pool_size + db_max_overflow)
    check(budget < max_connections,
          f"Connection budget ({budget}) < max_connections ({max_connections})")

    print("\n3. Checking no singleton patterns in API handlers...")
    for root, dirs, files in os.walk(os.path.join(BACKEND_DIR, "routes")):
        for f in files:
            if f.endswith(".py"):
                path = os.path.join(root, f)
                with open(path) as fh:
                    content = fh.read()
                    if "_singleton" in content or "_instance" in content:
                        warnings.append(f"Possible singleton in routes: {path}")

    print("\n4. Checking background task usage...")
    for root, dirs, files in os.walk(BACKEND_DIR):
        for f in files:
            if f.endswith(".py"):
                path = os.path.join(root, f)
                with open(path) as fh:
                    content = fh.read()
                    if "time.sleep(" in content and ".py" not in content:
                        warnings.append(f"Possible blocking call in {path}: time.sleep")

    print("\n5. Checking thread-local usage...")
    for root, dirs, files in os.walk(BACKEND_DIR):
        for f in files:
            if f.endswith(".py"):
                path = os.path.join(root, f)
                with open(path) as fh:
                    content = fh.read()
                    if "threading.local" in content or "thread_local" in content:
                        warnings.append(f"Thread-local state in {path}")

    print("\n6. Checking no concurrent operations...")
    for root, dirs, files in os.walk(BACKEND_DIR):
        for f in files:
            if f.endswith(".py"):
                path = os.path.join(root, f)
                with open(path) as fh:
                    content = fh.read()
                    if "asyncio.create_task" in content and "RUNTIME_MODE" not in content:
                        warnings.append(f"Background task in {path}")

    if errors:
        print(f"\n** FAILED ** ({len(errors)} errors)")
        for e in errors:
            print(f"  ERROR: {e}")
        return FAIL

    if warnings:
        print(f"\n** PASSED ** ({len(warnings)} warnings)")
        for w in warnings:
            print(f"  WARN: {w}")
    else:
        print("\n** PASSED **")

    return PASS


if __name__ == "__main__":
    sys.exit(main())
