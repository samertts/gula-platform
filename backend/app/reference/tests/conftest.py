"""conftest for reference tests.

Sets environment to 'test' mode so app.config doesn't hard-exit,
and provides a minimal DATABASE_URL to satisfy config validation.
"""

from __future__ import annotations

import os

# Must be set before ANY app code is imported to prevent config.py
# from hard-exiting on missing production secrets.
os.environ.setdefault("ENV", "test")
os.environ.setdefault("RUNTIME_MODE", "test")
os.environ.setdefault("DATABASE_URL", "sqlite:///test.db")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production")
os.environ.setdefault("ENCRYPTION_KEY", "test-encryption-key-not-for-production")
os.environ.setdefault("REFRESH_TOKEN_SECRET", "test-refresh-token-secret-not-for-production")
os.environ.setdefault("NID_HMAC_KEY", "test-nid-hmac-key-not-for-production")
os.environ.setdefault("DEVICE_HMAC_KEY", "test-device-hmac-key-not-for-production")
os.environ.setdefault("FEATURE_BACKGROUND_TASKS", "false")
