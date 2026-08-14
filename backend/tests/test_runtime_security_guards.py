from __future__ import annotations

from pathlib import Path

import pytest

from app.certification.engine import CertificationEngine
from app.certification.report import _safe_output_path
from app.integration.testing import _join_target, _validate_target


def test_integration_target_rejects_unconfigured_external_hosts() -> None:
    with pytest.raises(ValueError, match="not in GULA_INTEGRATION_ALLOWED_HOSTS"):
        _validate_target("https://169.254.169.254/latest/meta-data")


def test_integration_endpoint_must_remain_relative_to_validated_origin() -> None:
    base = "http://localhost:8000"
    assert _join_target(base, "/health") == "http://localhost:8000/health"
    with pytest.raises(ValueError, match="relative"):
        _join_target(base, "https://attacker.invalid/collect")
    with pytest.raises(ValueError, match="traverse"):
        _join_target(base, "/../../etc/passwd")


def test_certification_engine_rejects_module_path_escape(tmp_path: Path) -> None:
    engine = CertificationEngine(tmp_path)
    with pytest.raises(ValueError, match="inside the project root"):
        engine._safe_path(tmp_path.parent / "outside")


def test_report_output_path_rejects_escape(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    safe_root = tmp_path / "reports"
    safe_root.mkdir()
    monkeypatch.setenv("GULA_TEMP_DIR", str(safe_root))
    assert _safe_output_path(safe_root / "report.json") == safe_root / "report.json"
    with pytest.raises(ValueError, match="configured temporary directory"):
        _safe_output_path(tmp_path.parent / "outside.json")
