from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app._compat import UTC
from app.core.events import events
from app.national_data.models.event_store.StoredEvent import StoredEvent
from app.national_data.models.event_store.EventSnapshot import EventSnapshot
from app.national_data.models.mdm.GoldenRecord import GoldenRecord
from app.national_data.models.mdm.DuplicateRecord import DuplicateRecord
from app.national_data.models.mdm.MergeAction import MergeAction
from app.national_data.models.governance.DataLineageEntry import DataLineageEntry
from app.national_data.models.governance.DataCatalogEntry import DataCatalogEntry
from app.national_data.models.governance.DataQualityCheck import DataQualityCheck
from app.national_data.models.governance.RetentionPolicy import RetentionPolicy
from app.national_data.models.governance.ConsentDirective import ConsentDirective
from app.national_data.models.ai_data.FeatureStore import FeatureStore
from app.national_data.models.ai_data.FeatureValue import FeatureValue
from app.national_data.models.ai_data.DeidentificationJob import DeidentificationJob
from app.national_data.models.warehouse.DimDate import DimDate
from app.services.outbox_service import emit_to_outbox
from app.national_data.models.ai_data.VectorEmbedding import VectorEmbedding
from app.national_data.models.ai_data.TrainingDataset import TrainingDataset

logger = logging.getLogger("gula.data_platform")


class DataPlatformService:

    # ── Master Data Management ─────────────────────────────────────────────────

    @staticmethod
    def create_golden_record(
        db: Session,
        patient_id: int | None = None,
        national_patient_id: str | None = None,
        citizen_id: str | None = None,
        confidence_score: float = 0.0,
        matching_algorithm: str | None = None,
        matched_fields: str | None = None,
        notes: str | None = None,
    ) -> GoldenRecord:
        record = GoldenRecord(
            patient_id=patient_id,
            national_patient_id=national_patient_id,
            citizen_id=citizen_id,
            confidence_score=confidence_score,
            matching_algorithm=matching_algorithm,
            matched_fields=matched_fields,
            is_active_golden=1,
            activated_at=datetime.now(UTC),
            notes=notes,
        )
        db.add(record)
        db.flush()
        emit_to_outbox(
            db,
            event_type="data_platform.golden_record.created",
            payload={
                "golden_record_id": record.id,
                "patient_id": patient_id,
                "citizen_id": citizen_id,
                "confidence_score": confidence_score,
            },
            aggregate_type="GoldenRecord",
            aggregate_id=record.id,
        )
        return record

    @staticmethod
    def check_duplicates(
        db: Session,
        golden_record_id: int,
        source_patient_id: int | None = None,
        source_national_patient_id: str | None = None,
        source_system: str = "lims",
        duplicate_probability: float = 0.0,
        matching_algorithm: str | None = None,
        matched_fields: str | None = None,
        match_details: str | None = None,
    ) -> DuplicateRecord:
        record = DuplicateRecord(
            golden_record_id=golden_record_id,
            source_patient_id=source_patient_id,
            source_national_patient_id=source_national_patient_id,
            source_system=source_system,
            duplicate_probability=duplicate_probability,
            matching_algorithm=matching_algorithm,
            matched_fields=matched_fields,
            match_details=match_details,
            status="pending",
        )
        db.add(record)
        db.flush()
        return record

    @staticmethod
    def merge_records(
        db: Session,
        golden_record_id: int,
        source_patient_id: int | None = None,
        target_patient_id: int | None = None,
        merge_type: str = "automatic",
        merge_reason: str | None = None,
        merge_fields: str | None = None,
        conflict_resolution: str | None = None,
        merged_by: int | None = None,
    ) -> MergeAction:
        action = MergeAction(
            golden_record_id=golden_record_id,
            source_patient_id=source_patient_id,
            target_patient_id=target_patient_id,
            merge_type=merge_type,
            merge_reason=merge_reason,
            merge_fields=merge_fields,
            conflict_resolution=conflict_resolution,
            merged_by=merged_by,
            merged_at=datetime.now(UTC),
        )
        db.add(action)
        db.flush()

        DuplicateRecord.update_golden(
            db, golden_record_id=golden_record_id, resolution="merged"
        )

        emit_to_outbox(
            db,
            event_type="data_platform.merge.completed",
            payload={
                "merge_action_id": action.id,
                "golden_record_id": golden_record_id,
                "merge_type": merge_type,
            },
            aggregate_type="MergeAction",
            aggregate_id=action.id,
        )
        return action

    # ── Event Store ───────────────────────────────────────────────────────────

    @staticmethod
    def record_event(
        db: Session,
        event_type: str,
        aggregate_type: str,
        aggregate_id: str,
        event_data: dict[str, Any],
        metadata_: dict[str, Any] | None = None,
        partition_key: str | None = None,
        causation_id: str | None = None,
        correlation_id: str | None = None,
        recorded_by: str | None = None,
    ) -> StoredEvent:
        last_event = (
            db.query(StoredEvent)
            .filter(
                StoredEvent.aggregate_type == aggregate_type,
                StoredEvent.aggregate_id == aggregate_id,
            )
            .order_by(StoredEvent.version.desc())
            .first()
        )
        next_version = (last_event.version + 1) if last_event else 1

        event = StoredEvent(
            event_type=event_type,
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            event_data=event_data,
            metadata_=metadata_,
            version=next_version,
            partition_key=partition_key,
            occurred_at=datetime.now(UTC),
            recorded_at=datetime.now(UTC),
            causation_id=causation_id,
            correlation_id=correlation_id,
            recorded_by=recorded_by,
        )
        db.add(event)
        db.flush()

        events.emit(event_type, {
            "event_id": event.id,
            "aggregate_type": aggregate_type,
            "aggregate_id": aggregate_id,
            "event_data": event_data,
        })

        return event

    @staticmethod
    def replay_events(
        db: Session,
        aggregate_type: str,
        aggregate_id: str,
        from_version: int = 1,
        to_version: int | None = None,
    ) -> list[StoredEvent]:
        query = db.query(StoredEvent).filter(
            StoredEvent.aggregate_type == aggregate_type,
            StoredEvent.aggregate_id == aggregate_id,
            StoredEvent.version >= from_version,
        )
        if to_version is not None:
            query = query.filter(StoredEvent.version <= to_version)
        query = query.order_by(StoredEvent.version.asc())
        return query.all()

    @staticmethod
    def create_snapshot(
        db: Session,
        aggregate_type: str,
        aggregate_id: str,
        snapshot_data: dict[str, Any],
        version: int,
        snapshot_type: str = "full",
        created_by: str | None = None,
    ) -> EventSnapshot:
        snapshot = EventSnapshot(
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            snapshot_data=snapshot_data,
            version=version,
            snapshot_type=snapshot_type,
            created_by=created_by,
            snapshot_at=datetime.now(UTC),
        )
        db.add(snapshot)
        db.flush()
        return snapshot

    # ── Data Governance ───────────────────────────────────────────────────────

    @staticmethod
    def record_lineage(
        db: Session,
        source_entity: str,
        source_entity_id: str,
        target_entity: str,
        target_entity_id: str,
        transformation_type: str | None = None,
        transformation_description: str | None = None,
        pipeline_name: str | None = None,
        pipeline_run_id: str | None = None,
        status: str = "completed",
        lab_id: int | None = None,
    ) -> DataLineageEntry:
        entry = DataLineageEntry(
            source_entity=source_entity,
            source_entity_id=source_entity_id,
            target_entity=target_entity,
            target_entity_id=target_entity_id,
            transformation_type=transformation_type,
            transformation_description=transformation_description,
            pipeline_name=pipeline_name,
            pipeline_run_id=pipeline_run_id,
            status=status,
            lab_id=lab_id,
        )
        db.add(entry)
        db.flush()
        return entry

    @staticmethod
    def get_lineage(
        db: Session,
        entity_type: str,
        entity_id: str,
        direction: str = "both",
    ) -> dict[str, list[dict[str, Any]]]:
        upstream = []
        downstream = []

        if direction in ("upstream", "both"):
            entries = (
                db.query(DataLineageEntry)
                .filter(
                    DataLineageEntry.target_entity == entity_type,
                    DataLineageEntry.target_entity_id == entity_id,
                )
                .order_by(DataLineageEntry.processed_at.desc())
                .all()
            )
            upstream = [{
                "id": e.id,
                "source_entity": e.source_entity,
                "source_entity_id": e.source_entity_id,
                "transformation_type": e.transformation_type,
                "pipeline_name": e.pipeline_name,
                "processed_at": e.processed_at.isoformat() if e.processed_at else None,
            } for e in entries]

        if direction in ("downstream", "both"):
            entries = (
                db.query(DataLineageEntry)
                .filter(
                    DataLineageEntry.source_entity == entity_type,
                    DataLineageEntry.source_entity_id == entity_id,
                )
                .order_by(DataLineageEntry.processed_at.desc())
                .all()
            )
            downstream = [{
                "id": e.id,
                "target_entity": e.target_entity,
                "target_entity_id": e.target_entity_id,
                "transformation_type": e.transformation_type,
                "pipeline_name": e.pipeline_name,
                "processed_at": e.processed_at.isoformat() if e.processed_at else None,
            } for e in entries]

        return {"upstream": upstream, "downstream": downstream}

    @staticmethod
    def create_catalog_entry(
        db: Session,
        entry_name: str,
        entry_type: str,
        schema_name: str | None = None,
        table_name: str | None = None,
        column_name: str | None = None,
        description: str | None = None,
        classification: str | None = None,
        sensitivity_level: str | None = None,
        source_system: str | None = None,
        is_sensitive: bool = False,
        is_pii: bool = False,
        is_phi: bool = False,
    ) -> DataCatalogEntry:
        entry = DataCatalogEntry(
            entry_name=entry_name,
            entry_type=entry_type,
            schema_name=schema_name,
            table_name=table_name,
            column_name=column_name,
            description=description,
            classification=classification,
            sensitivity_level=sensitivity_level,
            source_system=source_system,
            is_sensitive=is_sensitive,
            is_pii=is_pii,
            is_phi=is_phi,
        )
        db.add(entry)
        db.flush()
        return entry

    @staticmethod
    def run_quality_check(
        db: Session,
        rule_id: int,
        entity_type: str,
        entity_id: str | None = None,
        field_name: str | None = None,
        result_status: str = "pass",
        result_value: str | None = None,
        records_checked: int | None = None,
        records_failed: int | None = None,
        score: int | None = None,
        checked_by: str | None = None,
        lab_id: int | None = None,
    ) -> DataQualityCheck:
        check = DataQualityCheck(
            rule_id=rule_id,
            entity_type=entity_type,
            entity_id=entity_id,
            field_name=field_name,
            result_status=result_status,
            result_value=result_value,
            records_checked=records_checked,
            records_failed=records_failed,
            score=score,
            checked_at=datetime.now(UTC),
            checked_by=checked_by,
            lab_id=lab_id,
        )
        db.add(check)
        db.flush()
        return check

    @staticmethod
    def create_retention_policy(
        db: Session,
        policy_name: str,
        entity_type: str,
        retention_days: int,
        action_on_expiry: str = "archive",
        archive_after_days: int | None = None,
        purge_after_days: int | None = None,
        allows_extension: bool = False,
        legal_hold_enabled: bool = False,
        notes: str | None = None,
    ) -> RetentionPolicy:
        policy = RetentionPolicy(
            policy_name=policy_name,
            entity_type=entity_type,
            retention_days=retention_days,
            action_on_expiry=action_on_expiry,
            archive_after_days=archive_after_days,
            purge_after_days=purge_after_days,
            allows_extension=allows_extension,
            legal_hold_enabled=legal_hold_enabled,
            notes=notes,
        )
        db.add(policy)
        db.flush()
        return policy

    # ── Feature Store ─────────────────────────────────────────────────────────

    @staticmethod
    def create_feature(
        db: Session,
        feature_name: str,
        feature_type: str,
        entity_type: str,
        data_type: str = "float",
        description: str | None = None,
        source_query: str | None = None,
        is_required: bool = False,
        tags: dict | None = None,
    ) -> FeatureStore:
        feature = FeatureStore(
            feature_name=feature_name,
            feature_type=feature_type,
            entity_type=entity_type,
            data_type=data_type,
            description=description,
            source_query=source_query,
            is_required=is_required,
            tags=tags,
        )
        db.add(feature)
        db.flush()
        return feature

    @staticmethod
    def store_feature_value(
        db: Session,
        feature_id: int,
        entity_type: str,
        entity_id: str,
        value_numeric: float | None = None,
        value_text: str | None = None,
        value_json: str | None = None,
        lab_id: int | None = None,
        source: str | None = None,
    ) -> FeatureValue:
        fv = FeatureValue(
            feature_id=feature_id,
            entity_type=entity_type,
            entity_id=str(entity_id),
            value_numeric=value_numeric,
            value_text=value_text,
            value_json=value_json,
            effective_at=datetime.now(UTC),
            recorded_at=datetime.now(UTC),
            lab_id=lab_id,
            source=source,
        )
        db.add(fv)
        db.flush()
        return fv

    # ── De-identification ────────────────────────────────────────────────────

    @staticmethod
    def create_deidentification_job(
        db: Session,
        job_name: str,
        entity_type: str,
        techniques: dict[str, Any],
        fields_to_deidentify: list[str] | None = None,
        fields_to_keep: list[str] | None = None,
        requested_by: int | None = None,
    ) -> DeidentificationJob:
        job = DeidentificationJob(
            job_name=job_name,
            entity_type=entity_type,
            techniques=techniques,
            fields_to_deidentify=fields_to_deidentify,
            fields_to_keep=fields_to_keep,
            status="pending",
            requested_by=requested_by,
        )
        db.add(job)
        db.flush()
        return job

    # ── Warehouse ─────────────────────────────────────────────────────────────

    @staticmethod
    def ensure_date_dimension(db: Session, date_value: str) -> DimDate:
        from datetime import date

        existing = db.query(DimDate).filter(DimDate.date_value == date_value).first()
        if existing:
            return existing

        d = date.fromisoformat(date_value)
        dim = DimDate(
            date_value=date_value,
            year=d.year,
            quarter=(d.month - 1) // 3 + 1,
            month=d.month,
            month_name=d.strftime("%B"),
            month_name_ar=_month_name_ar(d.month),
            week=d.isocalendar()[1],
            day=d.day,
            day_of_week=d.weekday(),
            day_name=d.strftime("%A"),
            is_weekend=1 if d.weekday() >= 5 else 0,
            is_holiday=0,
            fiscal_year=d.year,
            fiscal_quarter=(d.month - 1) // 3 + 1,
        )
        db.add(dim)
        db.flush()
        return dim

    # ── Consent Directive ─────────────────────────────────────────────────────

    @staticmethod
    def create_consent_directive(
        db: Session,
        consent_type: str,
        data_use_purpose: str,
        patient_id: int | None = None,
        citizen_id: str | None = None,
        consent_id: int | None = None,
        data_categories: str | None = None,
        authorized_party: str | None = None,
        granted_at: datetime | None = None,
        expires_at: datetime | None = None,
        jurisdiction: str | None = None,
    ) -> ConsentDirective:
        directive = ConsentDirective(
            consent_id=consent_id,
            patient_id=patient_id,
            citizen_id=citizen_id,
            consent_type=consent_type,
            consent_status="active",
            data_use_purpose=data_use_purpose,
            data_categories=data_categories,
            authorized_party=authorized_party,
            granted_at=(granted_at or datetime.now(UTC)).date(),
            expires_at=expires_at.date() if expires_at else None,
            is_active=True,
            jurisdiction=jurisdiction,
        )
        db.add(directive)
        db.flush()
        return directive

    # ── Vector Embedding ──────────────────────────────────────────────────────

    @staticmethod
    def store_embedding(
        db: Session,
        entity_type: str,
        entity_id: str,
        embedding_model: str,
        embedding_dimension: int,
        chunk_text: str | None = None,
        metadata_: dict | None = None,
        lab_id: int | None = None,
    ) -> VectorEmbedding:
        emb = VectorEmbedding(
            entity_type=entity_type,
            entity_id=entity_id,
            embedding_model=embedding_model,
            embedding_dimension=embedding_dimension,
            chunk_text=chunk_text,
            metadata_=metadata_,
            lab_id=lab_id,
        )
        db.add(emb)
        db.flush()
        return emb

    # ── Training Dataset ──────────────────────────────────────────────────────

    @staticmethod
    def create_training_dataset(
        db: Session,
        dataset_name: str,
        dataset_version: str,
        dataset_type: str,
        description: str | None = None,
        feature_list: list[str] | None = None,
        target_variable: str | None = None,
        total_records: int | None = None,
        created_by: str | None = None,
        tags: dict | None = None,
    ) -> TrainingDataset:
        ds = TrainingDataset(
            dataset_name=dataset_name,
            dataset_version=dataset_version,
            dataset_type=dataset_type,
            description=description,
            feature_list=feature_list,
            target_variable=target_variable,
            total_records=total_records,
            created_by=created_by,
            status="preparing",
            tags=tags,
        )
        db.add(ds)
        db.flush()
        return ds


def _month_name_ar(month: int) -> str:
    names = {
        1: "كانون الثاني",
        2: "شباط",
        3: "آذار",
        4: "نيسان",
        5: "أيار",
        6: "حزيران",
        7: "تموز",
        8: "آب",
        9: "أيلول",
        10: "تشرين الأول",
        11: "تشرين الثاني",
        12: "كانون الأول",
    }
    return names.get(month, "")
