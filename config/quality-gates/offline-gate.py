#!/usr/bin/env python3
"""Offline capability validation gate."""

import json
import os
import sys

PASS = 0
FAIL = 1

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'frontend-v2')


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    def check(condition: bool, msg: str, critical: bool = True) -> bool:
        if not condition:
            (errors if critical else warnings).append(msg)
            return False
        print(f"  {'PASS' if condition else 'FAIL'}: {msg}")
        return True

    print("=== Offline Validation Gate ===")

    print("\n1. Checking PWA manifest...")
    manifest_found = False
    for root, dirs, files in os.walk(FRONTEND_DIR):
        for f in files:
            if 'manifest' in f.lower() and f.endswith('.json'):
                manifest_found = True
                path = os.path.join(root, f)
                with open(path) as fh:
                    try:
                        manifest = json.load(fh)
                        check('name' in manifest, "Manifest has 'name'")
                        check('short_name' in manifest, "Manifest has 'short_name'")
                        check('start_url' in manifest, "Manifest has 'start_url'")
                        check('display' in manifest, "Manifest has 'display'")
                        check('icons' in manifest, "Manifest has 'icons'")
                    except json.JSONDecodeError:
                        errors.append(f"Invalid manifest JSON: {path}")
    check(manifest_found, "PWA manifest file exists (*.webmanifest or manifest.json)")

    print("\n2. Checking service worker...")
    sw_found = False
    for root, dirs, files in os.walk(FRONTEND_DIR):
        for f in files:
            if 'service-worker' in f.lower() or 'sw.' in f.lower():
                sw_found = True
                path = os.path.join(root, f)
                with open(path) as fh:
                    content = fh.read()
                    check('self.addEventListener' in content or 'self.addEventHandler' in content,
                          "Service worker has event listeners")
                    check('install' in content or 'activate' in content or 'fetch' in content,
                          "Service worker handles install/activate/fetch events")
    check(sw_found, "Service worker file exists")

    print("\n3. Checking offline page...")
    offline_found = False
    for root, dirs, files in os.walk(FRONTEND_DIR):
        for f in files:
            if 'offline' in f.lower():
                offline_found = True
                path = os.path.join(root, f)
                print(f"  Found: {path}")
    check(offline_found, "Offline fallback page exists")

    print("\n4. Checking IndexedDB usage...")
    idb_found = False
    for root, dirs, files in os.walk(FRONTEND_DIR):
        for f in files:
            if f.endswith('.ts') or f.endswith('.tsx') or f.endswith('.js'):
                path = os.path.join(root, f)
                with open(path) as fh:
                    content = fh.read()
                    if 'indexedDB' in content or 'IndexedDB' in content or 'idb' in content:
                        idb_found = True
                        break
    check(idb_found, "IndexedDB usage for offline data storage")

    print("\n5. Checking sync queue...")
    sync_found = False
    for root, dirs, files in os.walk(FRONTEND_DIR):
        for f in files:
            if f.endswith('.ts') or f.endswith('.tsx') or f.endswith('.js'):
                path = os.path.join(root, f)
                with open(path) as fh:
                    content = fh.read()
                    if 'sync' in content.lower() and ('queue' in content.lower() or 'SyncManager' in content):
                        sync_found = True
                        break
    check(sync_found, "Background sync queue for offline mutations")

    print("\n6. Checking degraded mode in backend...")
    degraded_found = False
    backend_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'backend', 'app')
    for root, dirs, files in os.walk(backend_dir):
        for f in files:
            if f.endswith('.py'):
                path = os.path.join(root, f)
                with open(path) as fh:
                    content = fh.read()
                    if 'degraded' in content.lower() or 'DegradedMode' in content:
                        degraded_found = True
                        break
    check(degraded_found, "Backend degraded mode for offline resilience")

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
