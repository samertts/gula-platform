from __future__ import annotations

import pytest
from app.integration.fhir_r4_exchange import (
    FHIRExchangeBlocked,
    InMemoryAuditRecorder,
    SyntheticFHIRReadOnlyExchange,
    capability_statement,
    synthetic_bundle,
    validate_synthetic_bundle,
)


def test_synthetic_bundle_is_valid_and_contains_no_real_identity_fields() -> None:
    bundle = synthetic_bundle()

    assert validate_synthetic_bundle(bundle) == []
    assert "telecom" not in str(bundle)
    assert "identifier" not in str(bundle)


def test_capability_statement_exposes_read_and_search_only() -> None:
    capability = capability_statement()
    resources = capability["rest"][0]["resource"]

    assert capability["fhirVersion"] == "4.0.1"
    assert resources
    assert all(
        {item["code"] for item in resource["interaction"]} == {"read", "search"}
        for resource in resources
    )


def test_exchange_is_blocked_by_default_and_audited() -> None:
    audit = InMemoryAuditRecorder()
    exchange = SyntheticFHIRReadOnlyExchange(audit=audit)

    with pytest.raises(FHIRExchangeBlocked):
        exchange.read_bundle()

    assert audit.decisions[-1].outcome == "denied"


def test_enabled_exchange_reads_only_synthetic_bundle_and_audits_allow() -> None:
    audit = InMemoryAuditRecorder()
    exchange = SyntheticFHIRReadOnlyExchange(enabled=True, audit=audit)

    result = exchange.read_bundle()

    assert result["resourceType"] == "Bundle"
    assert result["id"] == "synthetic-bundle-001"
    assert audit.decisions[-1].outcome == "allowed"


def test_exchange_rejects_unknown_resource_and_write_operations() -> None:
    audit = InMemoryAuditRecorder()
    exchange = SyntheticFHIRReadOnlyExchange(enabled=True, audit=audit)

    with pytest.raises(KeyError):
        exchange.read_bundle(resource_type="Observation", resource_id="not-in-synthetic-bundle")
    with pytest.raises(FHIRExchangeBlocked):
        exchange.write({"resourceType": "Observation"})

    assert audit.decisions[-1].action == "fhir.synthetic.write"
    assert audit.decisions[-1].outcome == "denied"


def test_validator_rejects_non_synthetic_payloads() -> None:
    bundle = synthetic_bundle()
    bundle["meta"]["tag"] = []

    errors = validate_synthetic_bundle(bundle)

    assert "bundle must be explicitly tagged as synthetic" in errors


def test_exchange_returns_a_defensive_copy_and_redacts_arbitrary_ids() -> None:
    audit = InMemoryAuditRecorder()
    exchange = SyntheticFHIRReadOnlyExchange(enabled=True, audit=audit)

    result = exchange.read_bundle()
    result["entry"].clear()

    assert exchange.read_bundle()["entry"]
    with pytest.raises(KeyError):
        exchange.read_bundle(resource_type="Patient", resource_id="patient-real-looking-001")
    assert audit.decisions[-1].resource_id == "<redacted>"


def test_validator_handles_malformed_metadata_and_missing_bundle_id() -> None:
    bundle = synthetic_bundle()
    bundle.pop("id")
    bundle["meta"] = {"tag": "invalid"}
    bundle["entry"][0]["resource"]["meta"] = {"tag": [None, {"system": "other"}]}

    errors = validate_synthetic_bundle(bundle)

    assert "bundle id is required" in errors
    assert "bundle must be explicitly tagged as synthetic" in errors
    assert "entry[0] resource must be explicitly tagged as synthetic" in errors


def test_exchange_rejects_invalid_bundle_without_leaking_payload_id() -> None:
    audit = InMemoryAuditRecorder()
    bundle = synthetic_bundle()
    bundle["meta"] = None
    exchange = SyntheticFHIRReadOnlyExchange(enabled=True, audit=audit, _bundle=bundle)

    with pytest.raises(ValueError, match="synthetic"):
        exchange.read_bundle(resource_id="patient-real-looking-002")

    assert audit.decisions[-1].outcome == "rejected"
    assert audit.decisions[-1].resource_id == "<redacted>"


def test_write_audit_does_not_store_caller_payload() -> None:
    audit = InMemoryAuditRecorder()
    exchange = SyntheticFHIRReadOnlyExchange(audit=audit)

    with pytest.raises(FHIRExchangeBlocked):
        exchange.write({"patient_id": "patient-real-looking-003"})

    assert audit.decisions[-1].resource_id == "<redacted>"
