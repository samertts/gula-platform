from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


_BASE_ENV = {
    "ENV": "production",
    "RUNTIME_MODE": "openapi",
    "BASE_URL": "https://api.gula-platform.org",
    "DATABASE_URL": "postgresql://db.example.invalid/gula",
    # These subprocesses test config guards, not Redis networking. Explicitly
    # acknowledge degraded mode so fail-closed Redis policy remains testable in
    # test_redis_security_policy.py without an external service dependency.
    "REDIS_URL": "",
    "ALLOW_DEGRADED_REDIS": "true",
    "SECRET_KEY": "prod-" + "a" * 64,
    "REFRESH_TOKEN_SECRET": "refresh-" + "b" * 64,
    "ENCRYPTION_KEY": "enc-" + "c" * 64,
    "NID_HMAC_KEY": "nid-" + "d" * 64,
    "AUDIT_ANCHOR_KEY": "audit-" + "e" * 64,
    "PYTHONPATH": f"{ROOT}:{ROOT / 'backend'}",
}


_BUILD_MIDDLEWARE = """
from fastapi import FastAPI
from app.factory import _build_middleware_stack
app = FastAPI()
_build_middleware_stack(app)
"""


def _run(overrides: dict[str, str | None]) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.update(_BASE_ENV)
    for key, value in overrides.items():
        if value is None:
            env.pop(key, None)
        else:
            env[key] = value
    return subprocess.run(
        [sys.executable, "-c", _BUILD_MIDDLEWARE],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def test_production_configuration_accepts_explicit_strong_defaults():
    result = _run({"CORS_ORIGINS": ""})

    assert result.returncode == 0, result.stderr


def test_production_requires_base_url():
    result = _run({"BASE_URL": None})

    assert result.returncode != 0
    assert "BASE_URL" in (result.stdout + result.stderr)


def test_production_rejects_wildcard_cors_with_credentials():
    result = _run({"CORS_ORIGINS": "*"})

    assert result.returncode != 0
    assert "CORS_ORIGINS" in (result.stdout + result.stderr)
