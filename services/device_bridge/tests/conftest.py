"""Test-only environment for the isolated device bridge."""

from __future__ import annotations

import os

TEST_API_KEY = "device-bridge-test-key"
os.environ.setdefault("LABLINK_API_KEY", TEST_API_KEY)
