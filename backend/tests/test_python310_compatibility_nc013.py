"""NC013-H02 — UTC compatibility on Python 3.10."""

from __future__ import annotations

import importlib.util
from datetime import datetime
from pathlib import Path

from app._compat import UTC

_MIGRATIONS = [
    "20260814_0005_role_permission_engine.py",
    "20260814_0006_security_audit_governance.py",
    "20260814_0007_clinical_gateway_scope.py",
]


def test_compat_utc_supports_timezone_aware_now() -> None:
    assert datetime.now(UTC).tzinfo is not None


def test_utc_using_migrations_import_on_this_python() -> None:
    migrations_dir = Path(__file__).resolve().parents[1] / "migrations" / "versions"
    for index, filename in enumerate(_MIGRATIONS):
        path = migrations_dir / filename
        spec = importlib.util.spec_from_file_location(f"nc013_migration_{index}", path)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        assert module.UTC is not None
