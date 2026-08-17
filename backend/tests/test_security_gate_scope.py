from pathlib import Path
import importlib.util


ROOT = Path(__file__).resolve().parents[2]
_SPEC = importlib.util.spec_from_file_location("security_gate", ROOT / "config/quality-gates/security-gate.py")
assert _SPEC and _SPEC.loader
_gate = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_gate)


def test_audit_coverage_scans_national_route_tree(tmp_path):
    route = tmp_path / "backend/app/national/api/routes"
    route.mkdir(parents=True)
    (route / "write_route.py").write_text(
        "@router.post('/unsafe')\ndef unsafe():\n    return {'ok': True}\n",
        encoding="utf-8",
    )
    findings = _gate.check_audit_log_coverage(tmp_path)
    assert any(item["file"].endswith("national/api/routes/write_route.py") for item in findings)


def test_audit_coverage_accepts_route_with_audit_marker(tmp_path):
    route = tmp_path / "backend/app/national/api/routes"
    route.mkdir(parents=True)
    (route / "safe_route.py").write_text(
        "from app.services.audit_service import log_action\n@router.post('/safe')\ndef safe():\n    log_action(None, 'safe', 'resource')\n",
        encoding="utf-8",
    )
    findings = _gate.check_audit_log_coverage(tmp_path)
    assert findings == []
