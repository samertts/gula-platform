import json
from datetime import UTC, datetime
from pathlib import Path

from app.contracts.generator import ContractGenerator
from app.engineering.generators.capability import CapabilityGenerator, CapabilitySpec


def test_contract_export_manifest_uses_timezone_aware_utc_timestamp() -> None:
    generator = ContractGenerator()

    exported = generator.export_all("contract-test")
    manifest_path = Path(next(path for path in exported if path.endswith("manifest.json")))
    manifest = json.loads(manifest_path.read_text())
    generated_at = datetime.fromisoformat(manifest["generated_at"])

    assert manifest_path.name == "manifest.json"
    assert generated_at.tzinfo == UTC


def test_capability_generator_writes_valid_json_descriptor(tmp_path: Path) -> None:
    spec = CapabilitySpec(
        name="Audit Export",
        description="Export audit metadata",
        events=["exported"],
        permissions=["read_audit"],
        with_api=False,
        with_tests=False,
        with_adr=False,
        with_docs=False,
        with_sbom=False,
    )

    result = CapabilityGenerator(target_dir=tmp_path).generate(spec=spec)
    descriptor_path = tmp_path / "audit_export" / "capability.json"
    descriptor = json.loads(descriptor_path.read_text())

    assert result.success is True
    assert descriptor["name"] == "Audit Export"
    assert descriptor["events"] == [
        {"name": "exported", "version": 1, "description": "", "type": "domain"}
    ]
    assert descriptor["permissions"] == ["read_audit"]
