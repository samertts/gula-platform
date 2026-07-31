from __future__ import annotations

import json
import os
import pathlib

os.environ.setdefault("ENV", "test")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production-" + "x" * 32)
os.environ.setdefault("ENCRYPTION_KEY", "6TJUTgJxBREYK9_yDy6VMXBw1HPwwxv1kiynV0WaAdw=")
os.environ.setdefault("NID_HMAC_KEY", "a" * 64)
os.environ.setdefault("REDIS_URL", "")

import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

from scripts import operations_certification as ops_cert


def test_full_certification_production_ready(tmp_path: pathlib.Path) -> None:
    cert = ops_cert.OpsCertification(tmp_path)
    cert.run()
    passed = sum(1 for r in cert.results if r["status"] == ops_cert.PASS)
    failed = sum(1 for r in cert.results if r["status"] == ops_cert.FAIL)
    assert passed >= 95
    assert failed == 0
    assert len(cert.results) >= 100


def test_health_json_written(tmp_path: pathlib.Path) -> None:
    cert = ops_cert.OpsCertification(tmp_path)
    cert.run()
    health = json.loads((tmp_path / "overall_health.json").read_text())
    assert health["score"] >= 90
    assert health["level"] == "PRODUCTION READY"
    assert health["failed"] == 0


def test_readiness_report_written(tmp_path: pathlib.Path) -> None:
    cert = ops_cert.OpsCertification(tmp_path)
    cert.run()
    report = (tmp_path / "OPERATIONS_READINESS_REPORT.md").read_text()
    assert "Overall Platform Health Score" in report
    assert "Phase Summary" in report
    for phase, _ in ops_cert.PHASES:
        assert phase in report


def test_per_phase_reports_written(tmp_path: pathlib.Path) -> None:
    cert = ops_cert.OpsCertification(tmp_path)
    cert.run()
    files = {report for _, report in ops_cert.PHASES}
    files.add("overall_health.json")
    for f in files:
        assert (tmp_path / f).exists(), f"missing report: {f}"


def test_phase_summary_counts_are_nonzero(tmp_path: pathlib.Path) -> None:
    cert = ops_cert.OpsCertification(tmp_path)
    cert.run()
    report = (tmp_path / "OPERATIONS_READINESS_REPORT.md").read_text()
    for phase, _ in ops_cert.PHASES:
        line = next(x for x in report.splitlines() if x.startswith(f"| {phase}"))
        assert "| 0 | 0 | 0 |" not in line, f"phase {phase} has no checks"
