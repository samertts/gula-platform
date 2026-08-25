from __future__ import annotations

import hashlib
from datetime import datetime, timedelta

import app.external_ingestion.service as ingestion_service
import pytest
from app._compat import UTC
from app.external_ingestion.matcher import (
    CandidateFingerprint,
    build_fingerprints,
    resolve_candidate,
)
from app.external_ingestion.models import (
    ExternalImportBatch,
    ExternalProfessionalEntity,
    ExternalProfessionalRecord,
    ExternalSource,
)
from app.external_ingestion.schemas import ImportManifest, ProfessionalRecordInput
from app.external_ingestion.service import (
    IngestionConflictError,
    IngestionDisabledError,
    activate_source,
    create_batch,
    register_source,
    stage_professional_chunk,
)

KEY = "test-external-ingestion-hmac-key"


def _record(**overrides) -> ProfessionalRecordInput:
    values = {
        "source_record_id": "doctor-1",
        "source_record_version": "v1",
        "profession": "doctor",
        "full_name": "محمد أحمد علي",
        "national_id": None,
        "license_number": "DOC-100",
        "license_authority": "iraqi-medical-syndicate",
        "specialty": "internal medicine",
        "phone": None,
        "birth_date": None,
        "employer_reference": "moh-facility-1",
        "employment_status": "active",
    }
    values.update(overrides)
    return ProfessionalRecordInput(**values)


def test_hard_anchor_links_union_and_ministry_without_pii() -> None:
    first = build_fingerprints(
        _record(full_name="محمد أحمد علي", national_id="1234567890"),
        hmac_key=KEY,
    )
    second = build_fingerprints(
        _record(full_name="Mohammed Ahmed Ali", national_id="1234567890", license_number="DOC-100"),
        hmac_key=KEY,
    )
    candidate = CandidateFingerprint(
        entity_id=42,
        national_id_hmac=first.national_id_hmac,
        license_hmac=first.license_hmac,
        license_authority=first.license_authority,
        profession=first.profession,
        name_hmac=first.name_hmac,
        phone_hmac=first.phone_hmac,
        birth_date_hmac=first.birth_date_hmac,
    )

    result = resolve_candidate(second, [candidate])

    assert result.status == "auto_matched"
    assert result.method == "national_id_exact"
    assert result.candidate_entity_id == 42
    assert "1234567890" not in first.name_hmac
    assert "محمد" not in first.name_hmac


def test_name_phone_birth_never_auto_links() -> None:
    incoming = build_fingerprints(
        _record(national_id=None, license_number=None, license_authority=None, phone="07701234567", birth_date="1980-01-02"),
        hmac_key=KEY,
    )
    candidate = CandidateFingerprint(
        entity_id=7,
        national_id_hmac=None,
        license_hmac=None,
        license_authority=None,
        profession="doctor",
        name_hmac=incoming.name_hmac,
        phone_hmac=incoming.phone_hmac,
        birth_date_hmac=incoming.birth_date_hmac,
    )

    result = resolve_candidate(incoming, [candidate])

    assert result.status == "pending_review"
    assert result.method == "name_phone_birth_exact"
    assert result.candidate_entity_id == 7
    assert result.score < 100


def test_multiple_hard_candidates_are_conflict() -> None:
    incoming = build_fingerprints(_record(national_id="1234567890"), hmac_key=KEY)
    candidates = [
        CandidateFingerprint(1, incoming.national_id_hmac, None, None, "doctor", incoming.name_hmac, None, None),
        CandidateFingerprint(2, incoming.national_id_hmac, None, None, "doctor", incoming.name_hmac, None, None),
    ]

    result = resolve_candidate(incoming, candidates)

    assert result.status == "conflict"
    assert result.candidate_entity_id is None


def _active_source(db, source_key: str, *, source_kind: str = "professional_registry") -> ExternalSource:
    source = ExternalSource(
        source_key=source_key,
        source_kind=source_kind,
        display_name=source_key,
        contract_status="active",
        contract_expires_at=datetime.now(UTC) + timedelta(days=30),
        schema_version=1,
        allowed_fields=[
            "full_name",
            "national_id",
            "license_number",
            "license_authority",
            "specialty",
            "phone",
            "birth_date",
            "employer_reference",
            "employment_status",
        ],
        is_enabled=True,
        version=1,
    )
    db.add(source)
    db.flush()
    return source


def _batch(db, source_key: str, export_id: str) -> ExternalImportBatch:
    manifest = ImportManifest(
        source_key=source_key,
        export_id=export_id,
        idempotency_key=f"idempotency-{source_key}-{export_id}",
        content_sha256=hashlib.sha256(export_id.encode()).hexdigest(),
        object_uri=f"s3://gula-quarantine/{source_key}/{export_id}.ndjson",
        schema_version=1,
        declared_record_count=1,
        expires_at=datetime.now(UTC) + timedelta(hours=2),
    )
    return create_batch(db, manifest=manifest, actor_id=100, actor_role="system_admin")


def test_service_is_fail_closed_when_disabled(monkeypatch, db) -> None:
    monkeypatch.setattr(ingestion_service, "EXTERNAL_INGESTION_ENABLED", False)
    with pytest.raises(IngestionDisabledError):
        register_source(
            db,
            source_key="disabled-source",
            source_kind="professional_registry",
            display_name="Disabled source",
            schema_version=1,
            allowed_fields=["full_name"],
            contract_expires_at=datetime.now(UTC) + timedelta(days=1),
            actor_id=1,
            actor_role="system_admin",
        )


def test_union_and_ministry_records_share_one_canonical_entity(monkeypatch, db) -> None:
    monkeypatch.setattr(ingestion_service, "EXTERNAL_INGESTION_ENABLED", True)
    monkeypatch.setattr(ingestion_service, "EXTERNAL_INGESTION_ER_HMAC_KEY", KEY)
    union = _active_source(db, "union-doctors")
    ministry = _active_source(db, "moh-workforce", source_kind="ministry_workforce")
    union_batch = _batch(db, union.source_key, "union-export-1")
    ministry_batch = _batch(db, ministry.source_key, "moh-export-1")

    first = _record(source_record_id="union-1", full_name="محمد أحمد علي", license_number="DOC-100")
    second = _record(source_record_id="moh-1", full_name="Mohammed Ahmed Ali", license_number="DOC-100")
    first_result = stage_professional_chunk(db, batch_id=union_batch.id, records=[first], actor_id=100, actor_role="system_admin")
    second_result = stage_professional_chunk(db, batch_id=ministry_batch.id, records=[second], actor_id=100, actor_role="system_admin")
    db.flush()

    records = db.query(ExternalProfessionalRecord).order_by(ExternalProfessionalRecord.id).all()
    entities = db.query(ExternalProfessionalEntity).all()
    assert first_result["staged"] == 1
    assert second_result["auto_matched"] == 1
    assert len(entities) == 1
    assert records[0].canonical_entity_id == records[1].canonical_entity_id
    assert records[1].resolution_method == "license_authority_exact"
    assert records[0].name_hmac and records[1].name_hmac
    assert records[0].source_record_id_hmac
    assert not hasattr(records[0], "source_record_id")
    assert not hasattr(records[0], "birth_date")
    assert not hasattr(records[0], "specialty")


def test_replaying_same_record_is_idempotent_and_version_conflict_is_explicit(monkeypatch, db) -> None:
    monkeypatch.setattr(ingestion_service, "EXTERNAL_INGESTION_ENABLED", True)
    monkeypatch.setattr(ingestion_service, "EXTERNAL_INGESTION_ER_HMAC_KEY", KEY)
    source = _active_source(db, "union-idempotency")
    batch = _batch(db, source.source_key, "export-idempotency")
    record = _record(source_record_id="same-id", source_record_version="v1")

    first = stage_professional_chunk(db, batch_id=batch.id, records=[record], actor_id=1, actor_role="system_admin")
    replay = stage_professional_chunk(db, batch_id=batch.id, records=[record], actor_id=1, actor_role="system_admin")
    assert first["staged"] == 1
    assert replay["staged"] == 0
    assert db.query(ExternalProfessionalRecord).count() == 1

    with pytest.raises(IngestionConflictError, match="version changed"):
        stage_professional_chunk(
            db,
            batch_id=batch.id,
            records=[record.model_copy(update={"source_record_version": "v2"})],
            actor_id=1,
            actor_role="system_admin",
        )

    next_batch = _batch(db, source.source_key, "export-idempotency-v2")
    updated = stage_professional_chunk(
        db,
        batch_id=next_batch.id,
        records=[record.model_copy(update={"source_record_version": "v2"})],
        actor_id=1,
        actor_role="system_admin",
    )
    assert updated["auto_matched"] == 1
    assert db.query(ExternalProfessionalRecord).count() == 2


def test_activation_requires_contract_and_distinct_second_reviewer(monkeypatch, db) -> None:
    monkeypatch.setattr(ingestion_service, "EXTERNAL_INGESTION_ENABLED", True)
    monkeypatch.setattr(ingestion_service, "EXTERNAL_INGESTION_ER_HMAC_KEY", KEY)
    from app.models.service_account import ServiceAccount

    service_account = ServiceAccount(
        name="activation-service",
        api_key_hash="test-hash",
        scopes='["integration:identity:write"]',
        is_active=1,
        expires_at=datetime.now(UTC) + timedelta(days=30),
    )
    db.add(service_account)
    db.flush()
    source = ExternalSource(
        source_key="activation-source",
        source_kind="professional_registry",
        display_name="Activation source",
        contract_status="pending",
        contract_expires_at=datetime.now(UTC) + timedelta(days=10),
        schema_version=1,
        allowed_fields=["full_name"],
        is_enabled=False,
        service_account_id=service_account.id,
        version=1,
    )
    db.add(source)
    db.flush()

    with pytest.raises(IngestionConflictError, match="distinct second reviewer"):
        activate_source(
            db,
            source_id=source.id,
            expected_version=1,
            legal_approval_ref="legal-1",
            security_review_ref="security-1",
            second_reviewer_id=10,
            actor_id=10,
            actor_role="system_admin",
        )

    active = activate_source(
        db,
        source_id=source.id,
        expected_version=1,
        legal_approval_ref="legal-1",
        security_review_ref="security-1",
        second_reviewer_id=11,
        actor_id=10,
        actor_role="system_admin",
    )
    assert active.is_enabled is True
    assert active.contract_status == "active"
    assert active.version == 2


def test_http_ingestion_route_is_disabled_by_default(client, make_lab, make_lab_user) -> None:
    from app.security.auth import create_token

    lab = make_lab()
    user = make_lab_user(lab.id, role="master_admin")
    token = create_token({"user_id": user.id, "lab_id": lab.id, "role": user.role})

    response = client.post(
        "/integration/external-ingestion/sources",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "source_key": "test-source",
            "source_kind": "professional_registry",
            "display_name": "Test source",
            "schema_version": 1,
            "allowed_fields": ["full_name"],
            "contract_expires_at": "2030-01-01T00:00:00Z",
        },
    )

    assert response.status_code == 503
    assert response.json().get("detail")


def test_ingestion_writer_requires_identity_scope() -> None:
    from app.external_ingestion.routes import require_ingestion_writer
    from app.models.service_account import ServiceAccount
    from fastapi import HTTPException

    permitted = ServiceAccount(scopes='["integration:identity:write"]')
    assert require_ingestion_writer(permitted) is permitted

    denied = ServiceAccount(scopes='["integration:events:write"]')
    with pytest.raises(HTTPException) as exc_info:
        require_ingestion_writer(denied)
    assert exc_info.value.status_code == 403


def test_disagreeing_hard_anchors_are_not_auto_merged() -> None:
    incoming = build_fingerprints(
        _record(national_id="1234567890", license_number="DOC-100"),
        hmac_key=KEY,
    )
    different_nid = build_fingerprints(
        _record(national_id="9999999999", license_number="DOC-100"),
        hmac_key=KEY,
    )
    candidate = CandidateFingerprint(
        entity_id=8,
        national_id_hmac=different_nid.national_id_hmac,
        license_hmac=different_nid.license_hmac,
        license_authority=different_nid.license_authority,
        profession="doctor",
        name_hmac=different_nid.name_hmac,
        phone_hmac=None,
        birth_date_hmac=None,
    )

    result = resolve_candidate(incoming, [candidate])

    assert result.status == "conflict"
    assert result.candidate_entity_id is None
    assert "disagreement" in result.method


def test_service_account_is_bound_to_one_source(monkeypatch, db) -> None:
    monkeypatch.setattr(ingestion_service, "EXTERNAL_INGESTION_ENABLED", True)
    monkeypatch.setattr(ingestion_service, "EXTERNAL_INGESTION_ER_HMAC_KEY", KEY)
    source = _active_source(db, "bound-source")
    source.service_account_id = 501
    db.flush()
    manifest = ImportManifest(
        source_key=source.source_key,
        export_id="bound-export",
        idempotency_key="idempotency-bound-source-1",
        content_sha256=hashlib.sha256(b"bound-export").hexdigest(),
        object_uri="s3://gula-quarantine/bound-source/bound-export.ndjson",
        schema_version=1,
        declared_record_count=1,
        expires_at=datetime.now(UTC) + timedelta(hours=2),
    )

    with pytest.raises(IngestionConflictError, match="not bound"):
        create_batch(
            db,
            manifest=manifest,
            actor_id=502,
            actor_role="service_account",
            actor_is_service_account=True,
        )

    batch = create_batch(
        db,
        manifest=manifest,
        actor_id=501,
        actor_role="service_account",
        actor_is_service_account=True,
    )
    assert batch.source_id == source.id


def test_source_contract_rejects_unlisted_field(monkeypatch, db) -> None:
    monkeypatch.setattr(ingestion_service, "EXTERNAL_INGESTION_ENABLED", True)
    monkeypatch.setattr(ingestion_service, "EXTERNAL_INGESTION_ER_HMAC_KEY", KEY)
    source = ExternalSource(
        source_key="restricted-source",
        source_kind="professional_registry",
        display_name="Restricted source",
        contract_status="active",
        contract_expires_at=datetime.now(UTC) + timedelta(days=30),
        schema_version=1,
        allowed_fields=["full_name", "profession"],
        is_enabled=True,
        version=1,
    )
    db.add(source)
    db.flush()
    batch = _batch(db, source.source_key, "restricted-export")

    with pytest.raises(IngestionConflictError, match="outside source contract"):
        stage_professional_chunk(
            db,
            batch_id=batch.id,
            records=[_record(source_record_id="restricted-1", license_number="DOC-1")],
            actor_id=1,
            actor_role="system_admin",
        )

    assert db.query(ExternalProfessionalRecord).count() == 0


def test_weak_match_requires_explicit_manual_decision(monkeypatch, db) -> None:
    monkeypatch.setattr(ingestion_service, "EXTERNAL_INGESTION_ENABLED", True)
    monkeypatch.setattr(ingestion_service, "EXTERNAL_INGESTION_ER_HMAC_KEY", KEY)
    first_source = _active_source(db, "weak-source-a")
    second_source = _active_source(db, "weak-source-b")
    first_batch = _batch(db, first_source.source_key, "weak-export-a")
    second_batch = _batch(db, second_source.source_key, "weak-export-b")
    first = _record(
        source_record_id="weak-a",
        license_number=None,
        license_authority=None,
        national_id=None,
        phone="07701234567",
        birth_date="1980-01-02",
    )
    second = _record(
        source_record_id="weak-b",
        license_number=None,
        license_authority=None,
        national_id=None,
        phone="07701234567",
        birth_date="1980-01-02",
    )

    stage_professional_chunk(db, batch_id=first_batch.id, records=[first], actor_id=1, actor_role="system_admin")
    stage_professional_chunk(db, batch_id=second_batch.id, records=[second], actor_id=1, actor_role="system_admin")
    pending = (
        db.query(ExternalProfessionalRecord)
        .filter(ExternalProfessionalRecord.source_key == second_source.source_key)
        .one()
    )
    assert pending.resolution_status == "pending_review"
    assert pending.canonical_entity_id is None

    from app.external_ingestion.schemas import MatchDecisionInput
    from app.external_ingestion.service import decide_match

    decided = decide_match(
        db,
        record_id=pending.id,
        decision=MatchDecisionInput(
            decision="approve",
            candidate_entity_id=db.query(ExternalProfessionalEntity).one().id,
            reason_code="verified_by_authority",
            expected_version=pending.version,
        ),
        actor_id=99,
        actor_role="master_admin",
    )
    assert decided.resolution_status == "approved_manual"
    assert decided.canonical_entity_id is not None
