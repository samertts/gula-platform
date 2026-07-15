from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.lab_user import LabUser
from ..national_data.models.canonical_patient import CanonicalPatient
from ..national_data.models.canonical_encounter import CanonicalEncounter
from ..national_data.models.canonical_observation import CanonicalObservation
from ..national_data.models.mdm.GoldenRecord import GoldenRecord
from ..national_data.models.governance.DataCatalogEntry import DataCatalogEntry
from ..national_data.models.governance.RetentionPolicy import RetentionPolicy
from ..national_data.models.governance.ConsentDirective import ConsentDirective
from ..national_data.models.ai_data.DeidentificationJob import DeidentificationJob
from ..national_data.models.ai_data.FeatureStore import FeatureStore
from ..national_data.models.ai_data.FeatureValue import FeatureValue
from ..national_data.models.ai_data.TrainingDataset import TrainingDataset
from ..national_data.models.ai_data.VectorEmbedding import VectorEmbedding
from ..security.dependencies import require_permission
from ..services.data_platform_service import DataPlatformService

router = APIRouter(prefix="/national-data", tags=["national-data"])


# ── Pydantic Schemas ──────────────────────────────────────────────────────────

class GoldenRecordCreate(BaseModel):
    patient_id: int | None = None
    national_patient_id: str | None = None
    citizen_id: str | None = None
    confidence_score: float = 0.0
    matching_algorithm: str | None = None
    matched_fields: str | None = None
    notes: str | None = None


class DuplicateCheckRequest(BaseModel):
    golden_record_id: int
    source_patient_id: int | None = None
    source_national_patient_id: str | None = None
    source_system: str = "lims"
    duplicate_probability: float = 0.0
    matching_algorithm: str | None = None
    matched_fields: str | None = None


class MergeActionRequest(BaseModel):
    golden_record_id: int
    source_patient_id: int | None = None
    target_patient_id: int | None = None
    merge_type: str = "automatic"
    merge_reason: str | None = None
    merge_fields: str | None = None
    conflict_resolution: str | None = None


class RecordEventRequest(BaseModel):
    event_type: str
    aggregate_type: str
    aggregate_id: str
    event_data: dict[str, Any]
    metadata_: dict[str, Any] | None = None
    partition_key: str | None = None
    causation_id: str | None = None
    correlation_id: str | None = None


class CatalogEntryCreate(BaseModel):
    entry_name: str
    entry_type: str
    schema_name: str | None = None
    table_name: str | None = None
    column_name: str | None = None
    description: str | None = None
    classification: str | None = None
    sensitivity_level: str | None = None
    source_system: str | None = None
    is_sensitive: bool = False
    is_pii: bool = False
    is_phi: bool = False


class QualityCheckCreate(BaseModel):
    rule_id: int
    entity_type: str
    entity_id: str | None = None
    field_name: str | None = None
    result_status: str = "pass"
    result_value: str | None = None
    records_checked: int | None = None
    records_failed: int | None = None
    score: int | None = None


class RetentionPolicyCreate(BaseModel):
    policy_name: str
    entity_type: str
    retention_days: int
    action_on_expiry: str = "archive"
    archive_after_days: int | None = None
    purge_after_days: int | None = None
    allows_extension: bool = False
    legal_hold_enabled: bool = False
    notes: str | None = None


class DeidentificationJobCreate(BaseModel):
    job_name: str
    entity_type: str
    techniques: dict[str, Any]
    fields_to_deidentify: list[str] | None = None
    fields_to_keep: list[str] | None = None


class FeatureDefinitionCreate(BaseModel):
    feature_name: str
    feature_type: str
    entity_type: str
    data_type: str = "float"
    description: str | None = None
    source_query: str | None = None
    is_required: bool = False
    tags: dict[str, Any] | None = None


class FeatureValueCreate(BaseModel):
    feature_id: int
    entity_type: str
    entity_id: str
    value_numeric: float | None = None
    value_text: str | None = None
    value_json: str | None = None


class TrainingDatasetCreate(BaseModel):
    dataset_name: str
    dataset_version: str
    dataset_type: str
    description: str | None = None
    feature_list: list[str] | None = None
    target_variable: str | None = None
    total_records: int | None = None
    tags: dict[str, Any] | None = None


class VectorEmbeddingCreate(BaseModel):
    entity_type: str
    entity_id: str
    embedding_model: str
    embedding_dimension: int
    chunk_text: str | None = None
    metadata_: dict[str, Any] | None = None


class ConsentDirectiveCreate(BaseModel):
    consent_type: str
    data_use_purpose: str
    patient_id: int | None = None
    citizen_id: str | None = None
    consent_id: int | None = None
    data_categories: str | None = None
    authorized_party: str | None = None
    jurisdiction: str | None = None


# ── Canonical Patient ─────────────────────────────────────────────────────────

@router.get("/patients", summary="List canonical patient records")
def list_canonical_patients(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: LabUser = Depends(require_permission("patients:read")),
    db: Session = Depends(get_db),
):
    return CanonicalPatient.query_all(db=db, lab_id=current_user.lab_id, skip=skip, limit=limit)


@router.get("/patients/{patient_id}", summary="Get canonical patient record")
def get_canonical_patient(
    patient_id: int,
    current_user: LabUser = Depends(require_permission("patients:read")),
    db: Session = Depends(get_db),
):
    result = CanonicalPatient.get_by_id(db=db, patient_id=patient_id, lab_id=current_user.lab_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    return result


# ── Canonical Encounter ───────────────────────────────────────────────────────

@router.get("/encounters", summary="List canonical encounter records")
def list_canonical_encounters(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: LabUser = Depends(require_permission("patients:read")),
    db: Session = Depends(get_db),
):
    return CanonicalEncounter.query_all(db=db, lab_id=current_user.lab_id, skip=skip, limit=limit)


@router.get("/encounters/{encounter_id}", summary="Get canonical encounter record")
def get_canonical_encounter(
    encounter_id: str,
    current_user: LabUser = Depends(require_permission("patients:read")),
    db: Session = Depends(get_db),
):
    result = CanonicalEncounter.get_by_id(db=db, encounter_id=encounter_id, lab_id=current_user.lab_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Encounter not found")
    return result


@router.post("/encounters", summary="Record a canonical encounter")
def record_canonical_encounter(
    data: dict[str, Any],
    current_user: LabUser = Depends(require_permission("patients:write")),
    db: Session = Depends(get_db),
):
    DataPlatformService.record_event(
        db=db,
        event_type="encounter.recorded",
        aggregate_type="Encounter",
        aggregate_id=data.get("encounter_id", str(datetime.now().timestamp())),
        event_data=data,
        recorded_by=str(current_user.id),
    )
    db.commit()
    return {"status": "recorded"}


# ── Canonical Observation ─────────────────────────────────────────────────────

@router.get("/observations", summary="List canonical observations")
def list_canonical_observations(
    patient_id: int | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: LabUser = Depends(require_permission("patients:read")),
    db: Session = Depends(get_db),
):
    return CanonicalObservation.query_all(
        db=db, lab_id=current_user.lab_id, patient_id=patient_id, skip=skip, limit=limit,
    )


@router.get("/observations/{observation_id}", summary="Get canonical observation")
def get_canonical_observation(
    observation_id: int,
    current_user: LabUser = Depends(require_permission("patients:read")),
    db: Session = Depends(get_db),
):
    result = CanonicalObservation.get_by_id(db=db, observation_id=observation_id, lab_id=current_user.lab_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Observation not found")
    return result


@router.post("/observations", summary="Record a canonical observation")
def record_canonical_observation(
    data: dict[str, Any],
    current_user: LabUser = Depends(require_permission("results:write")),
    db: Session = Depends(get_db),
):
    DataPlatformService.record_event(
        db=db,
        event_type="observation.recorded",
        aggregate_type="Observation",
        aggregate_id=str(data.get("observation_id", datetime.now().timestamp())),
        event_data=data,
        recorded_by=str(current_user.id),
    )
    db.commit()
    return {"status": "recorded"}


# ── Golden Records (MDM) ──────────────────────────────────────────────────────

@router.get("/golden-records", summary="List golden records")
def list_golden_records(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: LabUser = Depends(require_permission("patients:read")),
    db: Session = Depends(get_db),
):
    query = db.query(GoldenRecord).filter(GoldenRecord.is_deleted == False)
    total = query.count()
    records = query.order_by(GoldenRecord.confidence_score.desc()).offset(skip).limit(limit).all()
    return {"total": total, "records": [_golden_to_dict(r) for r in records]}


@router.post("/golden-records", summary="Create golden record", status_code=201)
def create_golden_record(
    data: GoldenRecordCreate,
    current_user: LabUser = Depends(require_permission("patients:write")),
    db: Session = Depends(get_db),
):
    record = DataPlatformService.create_golden_record(
        db=db,
        patient_id=data.patient_id,
        national_patient_id=data.national_patient_id,
        citizen_id=data.citizen_id,
        confidence_score=data.confidence_score,
        matching_algorithm=data.matching_algorithm,
        matched_fields=data.matched_fields,
        notes=data.notes,
    )
    db.commit()
    return _golden_to_dict(record)


@router.post("/golden-records/{golden_record_id}/resolve", summary="Resolve a golden record")
def resolve_golden_record(
    golden_record_id: int,
    current_user: LabUser = Depends(require_permission("patients:write")),
    db: Session = Depends(get_db),
):
    record = db.query(GoldenRecord).filter(
        GoldenRecord.id == golden_record_id,
        GoldenRecord.is_deleted == False,
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="Golden record not found")
    record.is_active_golden = 1
    record.activated_at = datetime.now()
    db.commit()
    return _golden_to_dict(record)


# ── Duplicate Check ───────────────────────────────────────────────────────────

@router.post("/duplicate-check", summary="Check for duplicate records")
def check_duplicates(
    data: DuplicateCheckRequest,
    current_user: LabUser = Depends(require_permission("patients:write")),
    db: Session = Depends(get_db),
):
    result = DataPlatformService.check_duplicates(
        db=db,
        golden_record_id=data.golden_record_id,
        source_patient_id=data.source_patient_id,
        source_national_patient_id=data.source_national_patient_id,
        source_system=data.source_system,
        duplicate_probability=data.duplicate_probability,
        matching_algorithm=data.matching_algorithm,
        matched_fields=data.matched_fields,
    )
    db.commit()
    return {
        "id": result.id,
        "golden_record_id": result.golden_record_id,
        "duplicate_probability": result.duplicate_probability,
        "status": result.status,
    }


# ── Merge Action ──────────────────────────────────────────────────────────────

@router.post("/merge", summary="Perform merge action")
def perform_merge(
    data: MergeActionRequest,
    current_user: LabUser = Depends(require_permission("patients:write")),
    db: Session = Depends(get_db),
):
    action = DataPlatformService.merge_records(
        db=db,
        golden_record_id=data.golden_record_id,
        source_patient_id=data.source_patient_id,
        target_patient_id=data.target_patient_id,
        merge_type=data.merge_type,
        merge_reason=data.merge_reason,
        merge_fields=data.merge_fields,
        conflict_resolution=data.conflict_resolution,
        merged_by=current_user.id,
    )
    db.commit()
    return {
        "id": action.id,
        "golden_record_id": action.golden_record_id,
        "merge_type": action.merge_type,
        "merged_at": action.merged_at.isoformat() if action.merged_at else None,
    }


# ── Event Store ───────────────────────────────────────────────────────────────

@router.post("/events", summary="Record an event", status_code=201)
def record_event(
    data: RecordEventRequest,
    current_user: LabUser = Depends(require_permission("patients:write")),
    db: Session = Depends(get_db),
):
    event = DataPlatformService.record_event(
        db=db,
        event_type=data.event_type,
        aggregate_type=data.aggregate_type,
        aggregate_id=data.aggregate_id,
        event_data=data.event_data,
        metadata_=data.metadata_,
        partition_key=data.partition_key,
        causation_id=data.causation_id,
        correlation_id=data.correlation_id,
        recorded_by=str(current_user.id),
    )
    db.commit()
    return {"event_id": event.id, "version": event.version}


@router.get("/events/replay", summary="Replay events for aggregate")
def replay_events(
    aggregate_type: str = Query(...),
    aggregate_id: str = Query(...),
    from_version: int = Query(1, ge=1),
    to_version: int | None = Query(None),
    current_user: LabUser = Depends(require_permission("patients:read")),
    db: Session = Depends(get_db),
):
    events_list = DataPlatformService.replay_events(
        db=db,
        aggregate_type=aggregate_type,
        aggregate_id=aggregate_id,
        from_version=from_version,
        to_version=to_version,
    )
    return [
        {
            "event_id": e.id,
            "event_type": e.event_type,
            "version": e.version,
            "event_data": e.event_data,
            "occurred_at": e.occurred_at.isoformat() if e.occurred_at else None,
        }
        for e in events_list
    ]


# ── Data Catalog ──────────────────────────────────────────────────────────────

@router.get("/data-catalog", summary="List data catalog entries")
def list_data_catalog(
    entry_type: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: LabUser = Depends(require_permission("patients:read")),
    db: Session = Depends(get_db),
):
    query = db.query(DataCatalogEntry).filter(DataCatalogEntry.is_deleted == False)
    if entry_type:
        query = query.filter(DataCatalogEntry.entry_type == entry_type)
    total = query.count()
    entries = query.order_by(DataCatalogEntry.entry_name).offset(skip).limit(limit).all()
    return {"total": total, "entries": [_catalog_to_dict(e) for e in entries]}


@router.post("/data-catalog", summary="Create data catalog entry", status_code=201)
def create_data_catalog_entry(
    data: CatalogEntryCreate,
    current_user: LabUser = Depends(require_permission("patients:write")),
    db: Session = Depends(get_db),
):
    entry = DataPlatformService.create_catalog_entry(
        db=db,
        entry_name=data.entry_name,
        entry_type=data.entry_type,
        schema_name=data.schema_name,
        table_name=data.table_name,
        column_name=data.column_name,
        description=data.description,
        classification=data.classification,
        sensitivity_level=data.sensitivity_level,
        source_system=data.source_system,
        is_sensitive=data.is_sensitive,
        is_pii=data.is_pii,
        is_phi=data.is_phi,
    )
    db.commit()
    return _catalog_to_dict(entry)


# ── Data Quality ──────────────────────────────────────────────────────────────

@router.post("/data-quality-checks", summary="Record data quality check")
def create_quality_check(
    data: QualityCheckCreate,
    current_user: LabUser = Depends(require_permission("patients:write")),
    db: Session = Depends(get_db),
):
    check = DataPlatformService.run_quality_check(
        db=db,
        rule_id=data.rule_id,
        entity_type=data.entity_type,
        entity_id=data.entity_id,
        field_name=data.field_name,
        result_status=data.result_status,
        result_value=data.result_value,
        records_checked=data.records_checked,
        records_failed=data.records_failed,
        score=data.score,
        checked_by=str(current_user.id),
    )
    db.commit()
    return {
        "id": check.id,
        "rule_id": check.rule_id,
        "result_status": check.result_status,
        "score": check.score,
        "checked_at": check.checked_at.isoformat() if check.checked_at else None,
    }


# ── Data Lineage ──────────────────────────────────────────────────────────────

@router.get("/data-lineage", summary="Get data lineage")
def get_data_lineage(
    entity_type: str = Query(...),
    entity_id: str = Query(...),
    direction: str = Query("both", regex="^(upstream|downstream|both)$"),
    current_user: LabUser = Depends(require_permission("patients:read")),
    db: Session = Depends(get_db),
):
    return DataPlatformService.get_lineage(
        db=db, entity_type=entity_type, entity_id=entity_id, direction=direction,
    )


@router.post("/data-lineage", summary="Record data lineage entry")
def record_data_lineage(
    data: dict[str, Any],
    current_user: LabUser = Depends(require_permission("patients:write")),
    db: Session = Depends(get_db),
):
    entry = DataPlatformService.record_lineage(
        db=db,
        source_entity=data["source_entity"],
        source_entity_id=str(data["source_entity_id"]),
        target_entity=data["target_entity"],
        target_entity_id=str(data["target_entity_id"]),
        transformation_type=data.get("transformation_type"),
        transformation_description=data.get("transformation_description"),
        pipeline_name=data.get("pipeline_name"),
        pipeline_run_id=data.get("pipeline_run_id"),
        lab_id=current_user.lab_id,
    )
    db.commit()
    return {"id": entry.id, "status": entry.status}


# ── Retention Policies ────────────────────────────────────────────────────────

@router.get("/retention-policies", summary="List retention policies")
def list_retention_policies(
    entity_type: str | None = Query(None),
    current_user: LabUser = Depends(require_permission("patients:read")),
    db: Session = Depends(get_db),
):
    query = db.query(RetentionPolicy).filter(RetentionPolicy.is_deleted == False)
    if entity_type:
        query = query.filter(RetentionPolicy.entity_type == entity_type)
    policies = query.order_by(RetentionPolicy.policy_name).all()
    return [_retention_to_dict(p) for p in policies]


@router.post("/retention-policies", summary="Create retention policy", status_code=201)
def create_retention_policy(
    data: RetentionPolicyCreate,
    current_user: LabUser = Depends(require_permission("patients:write")),
    db: Session = Depends(get_db),
):
    policy = DataPlatformService.create_retention_policy(
        db=db,
        policy_name=data.policy_name,
        entity_type=data.entity_type,
        retention_days=data.retention_days,
        action_on_expiry=data.action_on_expiry,
        archive_after_days=data.archive_after_days,
        purge_after_days=data.purge_after_days,
        allows_extension=data.allows_extension,
        legal_hold_enabled=data.legal_hold_enabled,
        notes=data.notes,
    )
    db.commit()
    return _retention_to_dict(policy)


# ── Consent Directives ────────────────────────────────────────────────────────

@router.get("/consent-directives", summary="List consent directives")
def list_consent_directives(
    patient_id: int | None = Query(None),
    consent_type: str | None = Query(None),
    current_user: LabUser = Depends(require_permission("patients:read")),
    db: Session = Depends(get_db),
):
    query = db.query(ConsentDirective).filter(ConsentDirective.is_deleted == False)
    if patient_id:
        query = query.filter(ConsentDirective.patient_id == patient_id)
    if consent_type:
        query = query.filter(ConsentDirective.consent_type == consent_type)
    directives = query.order_by(ConsentDirective.granted_at.desc()).all()
    return [_consent_to_dict(d) for d in directives]


@router.post("/consent-directives", summary="Create consent directive", status_code=201)
def create_consent_directive(
    data: ConsentDirectiveCreate,
    current_user: LabUser = Depends(require_permission("patients:write")),
    db: Session = Depends(get_db),
):
    directive = DataPlatformService.create_consent_directive(
        db=db,
        consent_type=data.consent_type,
        data_use_purpose=data.data_use_purpose,
        patient_id=data.patient_id,
        citizen_id=data.citizen_id,
        consent_id=data.consent_id,
        data_categories=data.data_categories,
        authorized_party=data.authorized_party,
        jurisdiction=data.jurisdiction,
    )
    db.commit()
    return _consent_to_dict(directive)


# ── De-identification Jobs ────────────────────────────────────────────────────

@router.post("/deidentification-jobs", summary="Create de-identification job", status_code=201)
def create_deidentification_job(
    data: DeidentificationJobCreate,
    current_user: LabUser = Depends(require_permission("patients:write")),
    db: Session = Depends(get_db),
):
    job = DataPlatformService.create_deidentification_job(
        db=db,
        job_name=data.job_name,
        entity_type=data.entity_type,
        techniques=data.techniques,
        fields_to_deidentify=data.fields_to_deidentify,
        fields_to_keep=data.fields_to_keep,
        requested_by=current_user.id,
    )
    db.commit()
    return {
        "id": job.id,
        "job_name": job.job_name,
        "status": job.status,
    }


@router.get("/deidentification-jobs", summary="List de-identification jobs")
def list_deidentification_jobs(
    status: str | None = Query(None),
    current_user: LabUser = Depends(require_permission("patients:read")),
    db: Session = Depends(get_db),
):
    query = db.query(DeidentificationJob).filter(DeidentificationJob.is_deleted == False)
    if status:
        query = query.filter(DeidentificationJob.status == status)
    jobs = query.order_by(DeidentificationJob.id.desc()).all()
    return [
        {
            "id": j.id,
            "job_name": j.job_name,
            "entity_type": j.entity_type,
            "status": j.status,
            "progress": j.progress,
            "started_at": j.started_at.isoformat() if j.started_at else None,
            "completed_at": j.completed_at.isoformat() if j.completed_at else None,
        }
        for j in jobs
    ]


# ── Feature Definitions ───────────────────────────────────────────────────────

@router.get("/features", summary="List feature definitions")
def list_features(
    entity_type: str | None = Query(None),
    current_user: LabUser = Depends(require_permission("patients:read")),
    db: Session = Depends(get_db),
):
    query = db.query(FeatureStore).filter(FeatureStore.is_deleted == False, FeatureStore.is_active == True)
    if entity_type:
        query = query.filter(FeatureStore.entity_type == entity_type)
    features = query.order_by(FeatureStore.feature_name).all()
    return [
        {
            "id": f.id,
            "feature_name": f.feature_name,
            "feature_type": f.feature_type,
            "entity_type": f.entity_type,
            "data_type": f.data_type,
            "description": f.description,
            "is_required": f.is_required,
        }
        for f in features
    ]


@router.post("/features", summary="Create feature definition", status_code=201)
def create_feature(
    data: FeatureDefinitionCreate,
    current_user: LabUser = Depends(require_permission("patients:write")),
    db: Session = Depends(get_db),
):
    feature = DataPlatformService.create_feature(
        db=db,
        feature_name=data.feature_name,
        feature_type=data.feature_type,
        entity_type=data.entity_type,
        data_type=data.data_type,
        description=data.description,
        source_query=data.source_query,
        is_required=data.is_required,
        tags=data.tags,
    )
    db.commit()
    return {
        "id": feature.id,
        "feature_name": feature.feature_name,
        "is_active": feature.is_active,
    }


# ── Feature Values ────────────────────────────────────────────────────────────

@router.post("/feature-values", summary="Store feature values", status_code=201)
def store_feature_values(
    data: FeatureValueCreate,
    current_user: LabUser = Depends(require_permission("patients:write")),
    db: Session = Depends(get_db),
):
    fv = DataPlatformService.store_feature_value(
        db=db,
        feature_id=data.feature_id,
        entity_type=data.entity_type,
        entity_id=data.entity_id,
        value_numeric=data.value_numeric,
        value_text=data.value_text,
        value_json=data.value_json,
        lab_id=current_user.lab_id,
    )
    db.commit()
    return {"id": fv.id, "feature_id": fv.feature_id, "entity_id": fv.entity_id}


@router.get("/feature-values", summary="Get feature values for entity")
def get_feature_values(
    feature_id: int | None = Query(None),
    entity_type: str = Query(...),
    entity_id: str = Query(...),
    current_user: LabUser = Depends(require_permission("patients:read")),
    db: Session = Depends(get_db),
):
    query = db.query(FeatureValue).filter(
        FeatureValue.entity_type == entity_type,
        FeatureValue.entity_id == entity_id,
        FeatureValue.is_deleted == False,
    )
    if feature_id:
        query = query.filter(FeatureValue.feature_id == feature_id)
    values = query.order_by(FeatureValue.effective_at.desc()).all()
    return [
        {
            "id": v.id,
            "feature_id": v.feature_id,
            "value_numeric": v.value_numeric,
            "value_text": v.value_text,
            "effective_at": v.effective_at.isoformat() if v.effective_at else None,
        }
        for v in values
    ]


# ── Training Datasets ─────────────────────────────────────────────────────────

@router.get("/training-datasets", summary="List training datasets")
def list_training_datasets(
    dataset_type: str | None = Query(None),
    current_user: LabUser = Depends(require_permission("patients:read")),
    db: Session = Depends(get_db),
):
    query = db.query(TrainingDataset).filter(TrainingDataset.is_deleted == False)
    if dataset_type:
        query = query.filter(TrainingDataset.dataset_type == dataset_type)
    datasets = query.order_by(TrainingDataset.id.desc()).all()
    return [
        {
            "id": d.id,
            "dataset_name": d.dataset_name,
            "dataset_version": d.dataset_version,
            "dataset_type": d.dataset_type,
            "total_records": d.total_records,
            "status": d.status,
            "created_at": d.created_at.isoformat() if d.created_at else None,
        }
        for d in datasets
    ]


@router.post("/training-datasets", summary="Create training dataset", status_code=201)
def create_training_dataset(
    data: TrainingDatasetCreate,
    current_user: LabUser = Depends(require_permission("patients:write")),
    db: Session = Depends(get_db),
):
    ds = DataPlatformService.create_training_dataset(
        db=db,
        dataset_name=data.dataset_name,
        dataset_version=data.dataset_version,
        dataset_type=data.dataset_type,
        description=data.description,
        feature_list=data.feature_list,
        target_variable=data.target_variable,
        total_records=data.total_records,
        created_by=str(current_user.id),
        tags=data.tags,
    )
    db.commit()
    return {
        "id": ds.id,
        "dataset_name": ds.dataset_name,
        "dataset_version": ds.dataset_version,
        "status": ds.status,
    }


# ── Vector Embeddings ─────────────────────────────────────────────────────────

@router.get("/vector-embeddings", summary="List vector embeddings for entity")
def list_vector_embeddings(
    entity_type: str = Query(...),
    entity_id: str = Query(...),
    current_user: LabUser = Depends(require_permission("patients:read")),
    db: Session = Depends(get_db),
):
    embeddings = (
        db.query(VectorEmbedding)
        .filter(
            VectorEmbedding.entity_type == entity_type,
            VectorEmbedding.entity_id == entity_id,
            VectorEmbedding.is_deleted == False,
        )
        .order_by(VectorEmbedding.chunk_index)
        .all()
    )
    return [
        {
            "id": e.id,
            "embedding_model": e.embedding_model,
            "embedding_dimension": e.embedding_dimension,
            "chunk_index": e.chunk_index,
            "chunk_text": e.chunk_text[:200] if e.chunk_text else None,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
        for e in embeddings
    ]


@router.post("/vector-embeddings", summary="Store vector embedding", status_code=201)
def store_vector_embedding(
    data: VectorEmbeddingCreate,
    current_user: LabUser = Depends(require_permission("patients:write")),
    db: Session = Depends(get_db),
):
    emb = DataPlatformService.store_embedding(
        db=db,
        entity_type=data.entity_type,
        entity_id=data.entity_id,
        embedding_model=data.embedding_model,
        embedding_dimension=data.embedding_dimension,
        chunk_text=data.chunk_text,
        metadata_=data.metadata_,
        lab_id=current_user.lab_id,
    )
    db.commit()
    return {
        "id": emb.id,
        "entity_type": emb.entity_type,
        "entity_id": emb.entity_id,
        "embedding_model": emb.embedding_model,
    }


# ── Helper serializers ────────────────────────────────────────────────────────

def _golden_to_dict(r: GoldenRecord) -> dict:
    return {
        "id": r.id,
        "patient_id": r.patient_id,
        "national_patient_id": r.national_patient_id,
        "citizen_id": r.citizen_id,
        "confidence_score": r.confidence_score,
        "matching_algorithm": r.matching_algorithm,
        "is_active_golden": r.is_active_golden,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }


def _catalog_to_dict(e: DataCatalogEntry) -> dict:
    return {
        "id": e.id,
        "entry_name": e.entry_name,
        "entry_type": e.entry_type,
        "schema_name": e.schema_name,
        "table_name": e.table_name,
        "column_name": e.column_name,
        "description": e.description,
        "classification": e.classification,
        "sensitivity_level": e.sensitivity_level,
        "is_sensitive": e.is_sensitive,
        "is_pii": e.is_pii,
        "is_phi": e.is_phi,
    }


def _retention_to_dict(p: RetentionPolicy) -> dict:
    return {
        "id": p.id,
        "policy_name": p.policy_name,
        "entity_type": p.entity_type,
        "retention_days": p.retention_days,
        "action_on_expiry": p.action_on_expiry,
        "allows_extension": p.allows_extension,
        "legal_hold_enabled": p.legal_hold_enabled,
        "is_active": p.is_active,
    }


def _consent_to_dict(d: ConsentDirective) -> dict:
    return {
        "id": d.id,
        "consent_type": d.consent_type,
        "consent_status": d.consent_status,
        "data_use_purpose": d.data_use_purpose,
        "patient_id": d.patient_id,
        "citizen_id": d.citizen_id,
        "granted_at": str(d.granted_at) if d.granted_at else None,
        "expires_at": str(d.expires_at) if d.expires_at else None,
        "is_active": d.is_active,
    }
