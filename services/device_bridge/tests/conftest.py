"""Test-wide configuration for the device bridge.

`app.security.auth` used to export a `DEFAULT_API_KEY` constant, and two test
modules imported it. The constant was removed -- correctly: a hardcoded default
API key is a credential in the source tree -- but the tests were not updated, so
`test_sync_and_auth.py` and `test_device_onboarding_api.py` have been failing at
collection ever since, taking their 5 authentication assertions with them.
Nothing noticed, because this service is not in any CI workflow.

The key is supplied the way the service expects it in production: through the
environment. This runs at conftest import, before any test module is imported,
so a module-level read of the variable is safe.
"""
from __future__ import annotations

import os

TEST_API_KEY = "test-lablink-api-key"

os.environ.setdefault("LABLINK_API_KEY", TEST_API_KEY)
