import json
from pathlib import Path

from app.contracts.engineering_inventory import scan_repository


def test_inventory_is_advisory_and_detects_production_evidence_gap() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    report = scan_repository(repo_root)
    detected = {finding.detected for finding in report.findings}
    assert report.production_ready is False
    assert "migration_present" in detected
    assert "production_evidence_gap" in detected
    assert "missing_authorization" not in detected
    assert report.status in {"REPAIRING", "EXTERNAL_DEPENDENCY", "READY_FOR_REVIEW"}
    assert all(finding.recommended_fix and finding.test_required for finding in report.findings)


def test_inventory_json_is_machine_readable(tmp_path: Path) -> None:
    report = scan_repository(Path(__file__).resolve().parents[2])
    output = report.to_json()
    payload = json.loads(output)
    assert payload["production_ready"] is False
    assert isinstance(payload["findings"], list)
    output_path = tmp_path / "inventory.json"
    output_path.write_text(output, encoding="utf-8")
    assert json.loads(output_path.read_text(encoding="utf-8"))["status"] == report.status
