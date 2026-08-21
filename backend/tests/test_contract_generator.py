import json
from datetime import UTC, datetime
from pathlib import Path

from app.contracts.generator import ContractGenerator


def test_contract_export_manifest_uses_timezone_aware_utc_timestamp():
    generator = ContractGenerator()

    exported = generator.export_all("contract-test")
    manifest_path = Path(next(path for path in exported if path.endswith("manifest.json")))
    manifest = json.loads(manifest_path.read_text())
    generated_at = datetime.fromisoformat(manifest["generated_at"])

    assert manifest_path.name == "manifest.json"
    assert generated_at.tzinfo == UTC
