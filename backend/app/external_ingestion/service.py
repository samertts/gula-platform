from __future__ import annotations

import hashlib
import hmac
from datetime import datetime
from typing import Any

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app._compat import UTC
from app.config import (
    EXTERNAL_INGESTION_COMMIT_ENABLED,
    EXTERNAL_INGESTION_ENABLED,
    EXTERNAL_INGESTION_ER_HMAC_KEY,
    EXTERNAL_INGESTION_MAX_CHUNK_RECORDS,
    EXTERNAL_INGESTION_STAGE_TTL_HOURS,
)
from app.models.service_account import ServiceAccount
from app.security.service_accounts import has_service_account_scope
from app.services.audit_service import log_action

from .matcher import CandidateFingerprint, build_fingerprints, resolve_candidate
from .models import (
    ExternalImportBatch,
    ExternalProfessionalEntity,
    ExternalProfessionalMatchReview,
    ExternalProfessionalRecord,
    ExternalSource,
)
from .schemas import ImportManifest, MatchDecisionInput, ProfessionalRecordInput


class IngestionDisabledError(RuntimeError):
    pass


class IngestionConflictError(RuntimeError):
    pass


_RECORD_METADATA_FIELDS = frozenset({"source_record_id", "source_record_version", "profession"})
_RECORD_CONTRACT_FIELDS = frozenset({
    "full_name",
    "national_id",
    "license_number",
    "license_authority",
    "specialty",
    "phone",
    "birth_date",
    "employer_reference",
    "employment_status",
})


def _validate_contract_fields(source: ExternalSource, input_record: ProfessionalRecordInput) -> None:
    supplied = set(getattr(input_record, "model_fields_set", set()))
    disallowed = (supplied & _RECORD_CONTRACT_FIELDS) - set(source.allowed_fields or [])
    if disallowed:
        raise IngestionConflictError("record contains fields outside source contract")


def _require_enabled(*, commit: bool = False) -> None:
    if not EXTERNAL_INGESTION_ENABLED:
        raise IngestionDisabledError("external ingestion is disabled")
    if commit and not EXTERNAL_INGESTION_COMMIT_ENABLED:
        raise IngestionDisabledError("external ingestion commit path is disabled")
    if not EXTERNAL_INGESTION_ER_HMAC_KEY:
        raise IngestionDisabledError("external ingestion HMAC key is not configured")


def _manifest_payload(manifest: ImportManifest) -> dict[str, Any]:
    # Keep only bounded metadata. The object store remains the quarantine source.
    return {
        "schema_version": manifest.schema_version,
        "content_sha256": manifest.content_sha256.lower(),
        "declared_record_count": manifest.declared_record_count,
        "object_scheme": manifest.object_uri.split(":", 1)[0],
    }


def _validate_source_binding(db: Session, service_account_id: int | None) -> None:
    if service_account_id is None:
        raise IngestionConflictError("source requires a bound service account")
    account = db.get(ServiceAccount, service_account_id)
    if account is None or not bool(account.is_active):
        raise IngestionConflictError("bound service account is missing or inactive")
    if account.expires_at and account.expires_at <= datetime.now(UTC):
        raise IngestionConflictError("bound service account is expired")
    if not has_service_account_scope(account, "integration:identity:write"):
        raise IngestionConflictError("bound service account lacks identity scope")


def _source_or_reject(
    db: Session,
    source_key: str,
    *,
    actor_id: int | None = None,
    actor_is_service_account: bool = False,
) -> ExternalSource:
    source = db.query(ExternalSource).filter(ExternalSource.source_key == source_key).first()
    if source is None or not source.is_enabled or source.contract_status != "active":
        raise IngestionConflictError("source is not active or has no approved contract")
    if source.contract_expires_at and source.contract_expires_at <= datetime.now(UTC):
        raise IngestionConflictError("source contract is expired")
    if actor_is_service_account and source.service_account_id != actor_id:
        raise IngestionConflictError("service account is not bound to this source")
    return source


def register_source(
    db: Session,
    *,
    source_key: str,
    source_kind: str,
    display_name: str,
    schema_version: int,
    allowed_fields: list[str],
    contract_expires_at: datetime | None,
    actor_id: int | None,
    actor_role: str | None,
    service_account_id: int | None = None,
) -> ExternalSource:
    _require_enabled()
    if service_account_id is not None:
        _validate_source_binding(db, service_account_id)
    if db.query(ExternalSource).filter(ExternalSource.source_key == source_key).first() is not None:
        raise IngestionConflictError("source_key already exists")
    source = ExternalSource(
        source_key=source_key,
        source_kind=source_kind,
        display_name=display_name,
        contract_status="pending",
        contract_expires_at=contract_expires_at,
        schema_version=schema_version,
        allowed_fields=sorted(set(allowed_fields)),
        is_enabled=False,
        service_account_id=service_account_id,
    )
    db.add(source)
    db.flush()
    log_action(
        db,
        action="external_ingestion.source_registered",
        resource_type="ingestion_source",
        resource_id=source.id,
        user_id=actor_id,
        user_role=actor_role,
        details={"source_key": source.source_key, "source_kind": source.source_kind, "enabled": False},
    )
    return source


def activate_source(
    db: Session,
    *,
    source_id: int,
    expected_version: int,
    legal_approval_ref: str,
    security_review_ref: str,
    second_reviewer_id: int,
    actor_id: int | None,
    actor_role: str | None,
) -> ExternalSource:
    _require_enabled()
    if actor_id is None or second_reviewer_id == actor_id:
        raise IngestionConflictError("source activation requires a distinct second reviewer")
    source = db.get(ExternalSource, source_id)
    if source is None:
        raise IngestionConflictError("source not found")
    if source.version != expected_version:
        raise IngestionConflictError("source version changed; reload before activation")
    _validate_source_binding(db, source.service_account_id)
    if source.contract_expires_at is None or source.contract_expires_at <= datetime.now(UTC):
        raise IngestionConflictError("source requires a future contract expiry")
    if source.contract_status == "active" and source.is_enabled:
        return source
    source.contract_status = "active"
    source.is_enabled = True
    source.vault_reference = f"approval:{legal_approval_ref}|security:{security_review_ref}|reviewer:{second_reviewer_id}"
    source.version += 1
    log_action(
        db,
        action="external_ingestion.source_activated",
        resource_type="ingestion_source",
        resource_id=source.id,
        user_id=actor_id,
        user_role=actor_role,
        details={"source_key": source.source_key, "second_reviewer_id": second_reviewer_id},
    )
    db.flush()
    return source


def create_batch(
    db: Session,
    *,
    manifest: ImportManifest,
    actor_id: int | None,
    actor_role: str | None,
    actor_is_service_account: bool = False,
) -> ExternalImportBatch:
    _require_enabled()
    source = _source_or_reject(
        db,
        manifest.source_key,
        actor_id=actor_id,
        actor_is_service_account=actor_is_service_account,
    )
    if manifest.schema_version != source.schema_version:
        raise IngestionConflictError("schema version is not accepted for this source")
    if manifest.expires_at <= datetime.now(UTC):
        raise IngestionConflictError("manifest expiry must be in the future")
    if (manifest.expires_at - datetime.now(UTC)).total_seconds() > EXTERNAL_INGESTION_STAGE_TTL_HOURS * 3600:
        raise IngestionConflictError("manifest expiry exceeds staging TTL")

    existing = (
        db.query(ExternalImportBatch)
        .filter(
            ExternalImportBatch.source_id == source.id,
            ExternalImportBatch.idempotency_key == manifest.idempotency_key,
        )
        .first()
    )
    if existing is not None:
        if existing.content_sha256 != manifest.content_sha256.lower() or existing.export_id != manifest.export_id:
            raise IngestionConflictError("idempotency key is already bound to a different export")
        return existing

    duplicate_export = (
        db.query(ExternalImportBatch)
        .filter(
            ExternalImportBatch.source_id == source.id,
            ExternalImportBatch.export_id == manifest.export_id,
            ExternalImportBatch.content_sha256 == manifest.content_sha256.lower(),
        )
        .first()
    )
    if duplicate_export is not None:
        return duplicate_export

    batch = ExternalImportBatch(
        source_id=source.id,
        export_id=manifest.export_id,
        idempotency_key=manifest.idempotency_key,
        content_sha256=manifest.content_sha256.lower(),
        object_uri=manifest.object_uri,
        schema_version=manifest.schema_version,
        declared_record_count=manifest.declared_record_count,
        status="received",
        expires_at=manifest.expires_at,
        manifest=_manifest_payload(manifest),
        created_by=actor_id,
    )
    db.add(batch)
    db.flush()
    log_action(
        db,
        action="external_ingestion.receive",
        resource_type="import_batch",
        resource_id=batch.id,
        user_id=actor_id,
        user_role=actor_role,
        details={"source_key": source.source_key, "export_id": batch.export_id, "record_count": batch.declared_record_count},
    )
    return batch


def _hmac_key_for_provisional(source_key: str, source_record_id: str) -> str:
    return hmac.new(
        EXTERNAL_INGESTION_ER_HMAC_KEY.encode(),
        f"provisional:{source_key}:{source_record_id}".encode(),
        hashlib.sha256,
    ).hexdigest()


def _source_record_id_hmac(source_key: str, source_record_id: str) -> str:
    return hmac.new(
        EXTERNAL_INGESTION_ER_HMAC_KEY.encode(),
        f"source-record:{source_key}:{source_record_id}".encode(),
        hashlib.sha256,
    ).hexdigest()


def _candidate_query(db: Session, fp) -> list[CandidateFingerprint]:
    strong_anchors = []
    if fp.national_id_hmac:
        strong_anchors.append(ExternalProfessionalRecord.national_id_hmac == fp.national_id_hmac)
    if fp.license_hmac and fp.license_authority:
        strong_anchors.append(
            and_(
                ExternalProfessionalRecord.license_hmac == fp.license_hmac,
                ExternalProfessionalRecord.license_authority == fp.license_authority,
            )
        )

    filters = [ExternalProfessionalRecord.profession == fp.profession]
    if strong_anchors:
        filters.append(or_(*strong_anchors))
    else:
        filters.extend([
            ExternalProfessionalRecord.name_hmac == fp.name_hmac,
            ExternalProfessionalRecord.phone_hmac == fp.phone_hmac,
            ExternalProfessionalRecord.birth_date_hmac == fp.birth_date_hmac,
        ])
    rows = (
        db.query(ExternalProfessionalRecord, ExternalProfessionalEntity)
        .join(ExternalProfessionalEntity, ExternalProfessionalEntity.id == ExternalProfessionalRecord.canonical_entity_id)
        .filter(and_(*filters), ExternalProfessionalEntity.state != "revoked")
        .limit(50)
        .all()
    )
    seen: set[int] = set()
    candidates: list[CandidateFingerprint] = []
    for record, entity in rows:
        if entity.id in seen:
            continue
        seen.add(entity.id)
        candidates.append(CandidateFingerprint(
            entity_id=entity.id,
            national_id_hmac=record.national_id_hmac,
            license_hmac=record.license_hmac,
            license_authority=record.license_authority,
            profession=record.profession,
            name_hmac=record.name_hmac,
            phone_hmac=record.phone_hmac,
            birth_date_hmac=record.birth_date_hmac,
        ))
    return candidates


def _same_source_record(
    db: Session,
    *,
    batch_id: int,
    source_key: str,
    source_record_id_hmac: str,
    source_record_version: str,
) -> tuple[str, ExternalProfessionalRecord | None]:
    existing = (
        db.query(ExternalProfessionalRecord)
        .filter(
            ExternalProfessionalRecord.batch_id == batch_id,
            ExternalProfessionalRecord.source_key == source_key,
            ExternalProfessionalRecord.source_record_id_hmac == source_record_id_hmac,
        )
        .first()
    )
    if existing is None:
        return "new", None
    if existing.source_record_version != source_record_version:
        raise IngestionConflictError("source record version changed inside the same batch")
    return "duplicate", existing


def _new_provisional_entity(db: Session, *, source_key: str, record_id: str, profession: str) -> ExternalProfessionalEntity:
    entity_key = _hmac_key_for_provisional(source_key, record_id)
    existing = db.query(ExternalProfessionalEntity).filter(ExternalProfessionalEntity.entity_key_hmac == entity_key).first()
    if existing is not None:
        if existing.profession != profession:
            raise IngestionConflictError("source record identity changed profession")
        return existing
    entity = ExternalProfessionalEntity(
        entity_key_hmac=entity_key,
        profession=profession,
        state="provisional",
        source_count=0,
    )
    db.add(entity)
    db.flush()
    return entity


def _persist_record(
    db: Session,
    *,
    batch: ExternalImportBatch,
    source: ExternalSource,
    input_record: ProfessionalRecordInput,
    actor_id: int | None,
) -> tuple[str, ExternalProfessionalRecord]:
    source_version = input_record.source_record_version or "0"
    source_record_id_hmac = _source_record_id_hmac(source.source_key, input_record.source_record_id)
    existing_state, existing = _same_source_record(
        db,
        batch_id=batch.id,
        source_key=source.source_key,
        source_record_id_hmac=source_record_id_hmac,
        source_record_version=source_version,
    )
    if existing_state == "duplicate" and existing is not None:
        return "duplicate", existing

    fp = build_fingerprints(input_record, hmac_key=EXTERNAL_INGESTION_ER_HMAC_KEY)
    match = resolve_candidate(fp, _candidate_query(db, fp))

    canonical_entity_id = match.candidate_entity_id
    resolution_status = match.status
    if match.status == "no_match":
        # A source-scoped provisional identity is safe for history but cannot
        # grant a GULA account or clinical permission.
        provisional = _new_provisional_entity(
            db,
            source_key=source.source_key,
            record_id=input_record.source_record_id,
            profession=fp.profession,
        )
        canonical_entity_id = provisional.id
        resolution_status = "unmatched"
    elif match.status in {"pending_review", "conflict"}:
        resolution_status = "pending_review"

    record = ExternalProfessionalRecord(
        batch_id=batch.id,
        source_key=source.source_key,
        source_record_id_hmac=source_record_id_hmac,
        source_record_version=source_version,
        person_ref_hmac=fp.person_ref_hmac,
        national_id_hmac=fp.national_id_hmac,
        license_hmac=fp.license_hmac,
        license_authority=fp.license_authority,
        profession=fp.profession,
        specialty_hmac=fp.specialty_hmac,
        name_hmac=fp.name_hmac,
        name_tokens_hmac=list(fp.name_tokens_hmac),
        phone_hmac=fp.phone_hmac,
        birth_date_hmac=fp.birth_date_hmac,
        employer_ref_hmac=fp.employer_ref_hmac,
        employment_status=fp.employment_status,
        canonical_entity_id=canonical_entity_id if match.status == "auto_matched" or match.status == "no_match" else None,
        resolution_status=resolution_status,
        resolution_method=match.method,
        resolution_score=match.score,
        resolution_features=match.features,
    )
    db.add(record)
    db.flush()

    if record.canonical_entity_id:
        entity = db.get(ExternalProfessionalEntity, record.canonical_entity_id)
        if entity:
            entity.source_count += 1
            entity.version += 1

    if match.status in {"pending_review", "conflict"}:
        review = ExternalProfessionalMatchReview(
            record_id=record.id,
            candidate_entity_id=match.candidate_entity_id,
            status="pending",
            reason=(
                "ambiguous or weak professional identity signals; manual adjudication required"
                if match.status == "pending_review"
                else "multiple canonical candidates share a hard identity anchor"
            ),
            evidence=match.features,
        )
        db.add(review)
        db.flush()

    return ("auto_matched" if match.status == "auto_matched" else "pending_review" if match.status in {"pending_review", "conflict"} else "staged"), record


def stage_professional_chunk(
    db: Session,
    *,
    batch_id: int,
    records: list[ProfessionalRecordInput],
    actor_id: int | None,
    actor_role: str | None,
    actor_is_service_account: bool = False,
) -> dict[str, int | str]:
    _require_enabled()
    if len(records) > EXTERNAL_INGESTION_MAX_CHUNK_RECORDS:
        raise IngestionConflictError("chunk exceeds configured record limit")

    batch = db.get(ExternalImportBatch, batch_id)
    if batch is None:
        raise IngestionConflictError("batch not found")
    if batch.status in {"rejected", "committed", "expired"}:
        raise IngestionConflictError(f"batch cannot be staged from status {batch.status}")
    if batch.expires_at <= datetime.now(UTC):
        batch.status = "expired"
        raise IngestionConflictError("batch staging window has expired")
    source = db.get(ExternalSource, batch.source_id)
    if source is None:
        raise IngestionConflictError("batch source not found")
    if source.source_kind not in {"professional_registry", "ministry_workforce"}:
        raise IngestionConflictError("civil identity sources cannot use professional-records staging")
    if actor_is_service_account and source.service_account_id != actor_id:
        raise IngestionConflictError("service account is not bound to this source")

    for input_record in records:
        _validate_contract_fields(source, input_record)

    new_record_count = 0
    for input_record in records:
        source_version = input_record.source_record_version or "0"
        source_record_id_hmac = _source_record_id_hmac(source.source_key, input_record.source_record_id)
        existing_state, _existing = _same_source_record(
            db,
            batch_id=batch.id,
            source_key=source.source_key,
            source_record_id_hmac=source_record_id_hmac,
            source_record_version=source_version,
        )
        if existing_state == "new":
            new_record_count += 1
    if batch.staged_record_count + new_record_count > batch.declared_record_count:
        raise IngestionConflictError("chunk exceeds manifest declared_record_count")

    counts: dict[str, int] = {"staged": 0, "auto_matched": 0, "pending_review": 0, "rejected": 0}
    batch.status = "staging"
    for input_record in records:
        outcome, _record = _persist_record(
            db,
            batch=batch,
            source=source,
            input_record=input_record,
            actor_id=actor_id,
        )
        if outcome == "duplicate":
            continue
        counts[outcome] = counts.get(outcome, 0) + 1
        batch.staged_record_count += 1
        if outcome == "auto_matched":
            batch.auto_matched_count = getattr(batch, "auto_matched_count", 0) + 1
            batch.accepted_record_count += 1
        elif outcome == "pending_review":
            batch.review_record_count += 1
        else:
            batch.accepted_record_count += 1

    batch.status = "review_required" if batch.review_record_count else "ready_for_approval"
    batch.version += 1
    log_action(
        db,
        action="external_ingestion.stage",
        resource_type="import_batch",
        resource_id=batch.id,
        user_id=actor_id,
        user_role=actor_role,
        details={"staged": counts.get("staged", 0), "auto_matched": counts.get("auto_matched", 0), "pending_review": counts.get("pending_review", 0)},
    )
    db.flush()
    return {"batch_id": batch.id, **counts}


def decide_match(
    db: Session,
    *,
    record_id: int,
    decision: MatchDecisionInput,
    actor_id: int | None,
    actor_role: str | None,
) -> ExternalProfessionalRecord:
    _require_enabled()
    review = db.query(ExternalProfessionalMatchReview).filter(ExternalProfessionalMatchReview.record_id == record_id).first()
    record = db.get(ExternalProfessionalRecord, record_id)
    if record is None or review is None:
        raise IngestionConflictError("match review not found")
    if record.version != decision.expected_version:
        raise IngestionConflictError("record version changed; reload before deciding")
    if review.status != "pending" or record.resolution_status != "pending_review":
        raise IngestionConflictError("match review is no longer pending")

    if decision.decision == "approve":
        if decision.candidate_entity_id is None:
            raise IngestionConflictError("candidate_entity_id is required to approve a match")
        entity = db.get(ExternalProfessionalEntity, decision.candidate_entity_id)
        if entity is None or entity.profession != record.profession or entity.state == "revoked":
            raise IngestionConflictError("candidate entity is invalid for this record")
        record.canonical_entity_id = entity.id
        entity.source_count += 1
        entity.version += 1
        record.resolution_status = "approved_manual"
        record.resolution_method = "manual_adjudication"
        record.resolution_score = 100
        review.status = "approved"
    else:
        record.resolution_status = "rejected"
        record.resolution_method = "manual_rejection"
        review.status = "rejected"

    review.reason = decision.reason_code
    review.decided_by = actor_id
    review.decided_at = datetime.now(UTC)
    record.version += 1
    review.version += 1
    log_action(
        db,
        action="external_ingestion.match_decision",
        resource_type="professional_record",
        resource_id=record.id,
        user_id=actor_id,
        user_role=actor_role,
        details={"decision": decision.decision, "candidate_entity_id": decision.candidate_entity_id, "reason_code": decision.reason_code},
    )
    db.flush()
    return record
