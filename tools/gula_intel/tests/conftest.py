"""Import-time environment for tests that load the application's ORM.

`app.config` reads `ENV` with a fail-safe default of "production" and calls
`sys.exit` when a production-required setting is missing. That default is
correct for the application — a misconfigured deployment should refuse to
start — but it means any test that imports an `app.*` module dies at import
time unless the environment names a non-production mode first.

`backend/migrations/env.py` solves this for Alembic with the same block. These
detectors resolve `target_metadata` by importing the very modules env.py
imports, so they need the same preconditions. Without it the registry
detectors report every base as unresolved with `SystemExit`, which looks like a
detector defect and is not one.

Values are deliberately obvious placeholders: this file must never be a source
of credentials.
"""
from __future__ import annotations

import os

os.environ.setdefault("ENV", "migration")
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("RUNTIME_MODE", "test")
os.environ.setdefault("SECRET_KEY", "gula-intel-test-key-" + "x" * 48)
os.environ.setdefault("ENCRYPTION_KEY", "6TJUTgJxBREYK9_yDy6VMXBw1HPwwxv1kiynV0WaAdw=")
os.environ.setdefault("NID_HMAC_KEY", "a" * 64)
os.environ.setdefault("REFRESH_TOKEN_SECRET", "gula-intel-test-refresh-" + "x" * 40)
os.environ.setdefault("DEVICE_HMAC_KEY", "b" * 64)
os.environ.setdefault("AUDIT_ANCHOR_KEY", "c" * 64)
os.environ.setdefault("BASE_URL", "http://localhost:8000")
os.environ.setdefault("REDIS_URL", "")
