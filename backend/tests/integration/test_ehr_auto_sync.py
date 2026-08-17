from datetime import UTC, datetime
from types import SimpleNamespace

from app.integration.healthcare.ehr_sync import assess_readiness, build_immunization_fhir, queue_immunization_sync, upsert_connector_config
from app.models.ehr_integration import EHRSyncRecord
from app.models.outbox import OutboxEvent


def test_ehr_connector_is_fail_closed_until_contract_and_trust_are_approved(db):
    assert assess_readiness(db, 1)["ready"] is False
    config = upsert_connector_config(
        db,
        1,
        {"endpoint": "https://ehr.example.test/fhir", "protocol": "fhir_r4", "contract_version": "", "trust_material_ref": "", "auto_activate": True},
        approved_by="operator-1",
    )
    assert config.enabled is False
    assert config.last_health_status == "blocked"


def test_ehr_connector_auto_activates_only_when_all_readiness_checks_pass(db, monkeypatch):
    monkeypatch.setenv("GULA_EHR_BEARER_TOKEN", "synthetic-ehr-token")
    config = upsert_connector_config(
        db,
        1,
        {"endpoint": "https://ehr.example.test/fhir", "protocol": "fhir_r4", "contract_version": "iraq-ehr-r4-v1", "trust_material_ref": "secret-ref:ehr-staging", "auto_activate": True},
        approved_by="operator-1",
    )
    assert config.enabled is True
    assert assess_readiness(db, 1)["status"] == "ready"


def test_immunization_is_queued_once_and_payload_has_no_raw_national_id(db, monkeypatch):
    monkeypatch.setenv("GULA_EHR_BEARER_TOKEN", "synthetic-ehr-token")
    upsert_connector_config(
        db,
        1,
        {"endpoint": "https://ehr.example.test/fhir", "protocol": "fhir_r4", "contract_version": "iraq-ehr-r4-v1", "trust_material_ref": "secret-ref:ehr-staging", "auto_activate": True},
        approved_by="operator-1",
    )
    record = SimpleNamespace(
        id=77,
        health_number="THN-SYNTHETIC-77",
        vaccine_code="BCG",
        vaccine="BCG",
        administration_date=datetime.now(UTC),
        dose_number=1,
        total_doses=1,
        lot_number="LOT-SYNTHETIC-1",
        manufacturer="Synthetic Manufacturer",
        route="intradermal",
        site="left-arm",
    )
    first = queue_immunization_sync(db, record, 1)
    replay = queue_immunization_sync(db, record, 1)
    outbox = db.query(OutboxEvent).filter(OutboxEvent.id == first.outbox_event_id).one()
    assert first.status == "queued"
    assert replay.id == first.id
    assert db.query(EHRSyncRecord).filter(EHRSyncRecord.lab_id == 1).count() == 1
    assert "THN-SYNTHETIC-77" not in outbox.payload
    assert "resourceType" in outbox.payload


def test_fhir_builder_uses_scoped_reference_for_temporary_health_number():
    resource = build_immunization_fhir(
        SimpleNamespace(
            id=88, health_number="THN-SYNTHETIC-88", vaccine_code="OPV", vaccine="OPV",
            administration_date=datetime(2026, 1, 1, tzinfo=UTC), dose_number=1, total_doses=3,
            lot_number=None, manufacturer=None, route=None, site=None,
        ),
        4,
    )
    assert resource["resourceType"] == "Immunization"
    assert resource["patient"]["reference"].startswith("Patient/gula-health-")
    assert "THN-SYNTHETIC-88" not in str(resource)
