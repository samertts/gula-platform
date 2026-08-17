from pathlib import Path
import sys

import importlib.util


ROOT = Path(__file__).resolve().parents[2]
_SPEC = importlib.util.spec_from_file_location("government_readiness_gate", ROOT / "scripts/government_readiness_gate.py")
assert _SPEC and _SPEC.loader
_gate = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = _gate
_SPEC.loader.exec_module(_gate)


def test_readiness_gate_sees_single_sync_migration_head():
    findings = _gate.check_alembic_heads(ROOT)
    assert findings[0].status == "pass"
    assert "20260817_0025" in findings[0].message


def test_readiness_gate_validates_sync_contracts():
    findings = _gate.check_sync_contracts(ROOT)
    assert all(item.status == "pass" for item in findings), findings


def test_production_gate_fails_closed_without_production_environment(monkeypatch):
    monkeypatch.delenv("IS_PRODUCTION", raising=False)
    monkeypatch.delenv("RUNTIME_MODE", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    findings = _gate.check_production_environment(production=True)
    assert any(item.status == "fail" and item.severity == "P0" for item in findings)


def test_readiness_report_never_grants_government_approval_automatically():
    report = _gate.build_report(ROOT, allow_dirty=True, production=False, run_tests=False)
    assert report["government_production_approval"] is False
    assert report["passed"] is True
