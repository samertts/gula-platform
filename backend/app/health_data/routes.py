from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from app.health_data.canonical import map_patient
from app.health_data.data_lake.catalog import DataLakeCatalog
from app.health_data.data_lake.ingestion import IngestionPipeline
from app.health_data.data_lake.storage import LocalStorageBackend
from app.health_data.enums import DataClassification, DataQuality, StorageTier
from app.health_data.event_store import HealthEventStore
from app.health_data.event_store.subscriptions import (
    SubscriptionManager,
)
from app.health_data.governance.audit import DataAccessAuditTrail
from app.health_data.governance.lineage import LineageTracker
from app.health_data.governance.policies import GovernancePolicy, PolicyEngine
from app.health_data.warehouse.service import WarehouseQuery, WarehouseService

router = APIRouter(prefix="/health-data", tags=["Health Data"])

_catalog = DataLakeCatalog()
_storage = LocalStorageBackend()
_ingestion = IngestionPipeline(_catalog, _storage)
_event_store = HealthEventStore()
_subscription_mgr = SubscriptionManager(_event_store)
_policy_engine = PolicyEngine()
_audit_trail = DataAccessAuditTrail()
_lineage_tracker = LineageTracker()
_warehouse = WarehouseService()


def _json_default(obj: Any) -> str:
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, Enum):
        return obj.value
    return str(obj)


# ── Catalog ────────────────────────────────────────────────────────────────────


@router.get("/catalog")
async def list_catalog(
    pattern: str | None = Query(None, description="Filter by dataset name pattern"),
) -> list[dict]:
    datasets = _catalog.list(pattern=pattern)
    return [
        {
            "name": ds.name,
            "description": ds.description,
            "classification": ds.classification.value,
            "quality": ds.quality.value,
            "storage_tier": ds.storage_tier.value,
            "source_system": ds.source_system,
            "record_count": ds.record_count,
            "size_bytes": ds.size_bytes,
            "partition_count": len(ds.partitions),
            "retention_days": ds.retention_days,
            "tags": ds.tags,
            "created_at": ds.created_at.isoformat(),
            "updated_at": ds.updated_at.isoformat(),
        }
        for ds in datasets
    ]


@router.get("/catalog/{dataset}")
async def get_dataset_metadata(dataset: str) -> dict:
    ds = _catalog.get(dataset)
    if not ds:
        raise HTTPException(status_code=404, detail=f"Dataset not found: {dataset}")
    return {
        "name": ds.name,
        "description": ds.description,
        "schema": ds.schema,
        "classification": ds.classification.value,
        "quality": ds.quality.value,
        "storage_tier": ds.storage_tier.value,
        "source_system": ds.source_system,
        "owner": ds.owner,
        "record_count": ds.record_count,
        "size_bytes": ds.size_bytes,
        "retention_days": ds.retention_days,
        "tags": ds.tags,
        "partitions": [
            {
                "key": p.key,
                "path": p.path,
                "row_count": p.row_count,
                "size_bytes": p.size_bytes,
                "format": p.format,
                "created_at": p.created_at.isoformat(),
            }
            for p in ds.partitions
        ],
        "created_at": ds.created_at.isoformat(),
        "updated_at": ds.updated_at.isoformat(),
    }


# ── Lineage ────────────────────────────────────────────────────────────────────


@router.get("/lineage/{entity_type}/{entity_id}")
async def get_lineage(entity_type: str, entity_id: str) -> dict:
    lineage = _lineage_tracker.get(entity_type, entity_id)
    if not lineage:
        raise HTTPException(status_code=404, detail="Lineage not found")
    return {
        "id": lineage.id,
        "entity_type": lineage.entity_type,
        "entity_id": lineage.entity_id,
        "nodes": [
            {
                "id": n.id,
                "entity_type": n.entity_type,
                "entity_id": n.entity_id,
                "system": n.system,
                "operation": n.operation,
                "timestamp": n.timestamp.isoformat(),
                "details": n.details,
            }
            for n in lineage.nodes
        ],
        "edges": [
            {
                "source_id": e.source_id,
                "target_id": e.target_id,
                "transformation": e.transformation,
                "transformation_details": e.transformation_details,
            }
            for e in lineage.edges
        ],
        "created_at": lineage.created_at.isoformat(),
    }


# ── Governance Policies ────────────────────────────────────────────────────────


@router.get("/governance/policies")
async def list_policies() -> list[dict]:
    return [
        {
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "scope": p.scope.value if isinstance(p.scope, Enum) else p.scope,
            "effect": p.effect.value if isinstance(p.effect, Enum) else p.effect,
            "classification": p.classification.value if p.classification else None,
            "priority": p.priority,
            "enabled": p.enabled,
            "created_at": p.created_at.isoformat(),
            "updated_at": p.updated_at.isoformat(),
        }
        for p in _policy_engine.list()
    ]


@router.post("/governance/policies")
async def create_policy(policy_data: dict[str, Any]) -> dict:
    policy = GovernancePolicy(
        id=policy_data.get("id", str(uuid.uuid4())),
        name=policy_data["name"],
        description=policy_data.get("description", ""),
        scope=policy_data.get("scope", "global"),
        effect=policy_data.get("effect", "audit"),
        classification=DataClassification(policy_data["classification"])
        if policy_data.get("classification")
        else None,
        priority=policy_data.get("priority", 100),
        enabled=policy_data.get("enabled", True),
    )
    _policy_engine.add(policy)
    return {
        "id": policy.id,
        "name": policy.name,
        "status": "created",
    }


# ── Data Quality Metrics ───────────────────────────────────────────────────────


@router.get("/quality/metrics")
async def get_quality_metrics() -> dict:
    datasets = _catalog.list()
    total_records = sum(ds.record_count for ds in datasets)
    total_size = sum(ds.size_bytes for ds in datasets)
    return {
        "total_datasets": len(datasets),
        "total_records": total_records,
        "total_size_bytes": total_size,
        "quality_distribution": {
            quality.value: sum(1 for ds in datasets if ds.quality == quality)
            for quality in DataQuality
        },
        "storage_distribution": {
            tier.value: sum(ds.size_bytes for ds in datasets if ds.storage_tier == tier)
            for tier in StorageTier
        },
        "classification_distribution": {
            cls.value: sum(1 for ds in datasets if ds.classification == cls)
            for cls in DataClassification
        },
    }


# ── Ingestion ──────────────────────────────────────────────────────────────────


@router.post("/ingest")
async def trigger_ingestion(body: dict[str, Any]) -> dict:
    dataset_name = body.get("dataset", "ingested_data")
    records = body.get("records", [])
    source = body.get("source", "api")

    if not records:
        raise HTTPException(status_code=400, detail="No records provided")

    result = await _ingestion.ingest(
        dataset_name=dataset_name,
        records=records,
        source_system=source,
        classification=DataClassification(body.get("classification", "internal")),
        quality=DataQuality(body.get("quality", "raw")),
        storage_tier=StorageTier(body.get("storage_tier", "hot")),
        partition_by=body.get("partition_by", "day"),
    )

    _event_store.append(
        aggregate_id=dataset_name,
        aggregate_type="dataset",
        event_name="health.data.ingested",
        data={"dataset": dataset_name, "records": len(records), "source": source},
        metadata={"source": source, "result": result.checksum},
    )

    return {
        "status": "ingested",
        "dataset": result.dataset,
        "partition": result.partition_key,
        "records_written": result.records_written,
        "bytes_written": result.bytes_written,
        "checksum": result.checksum,
        "duration_ms": result.duration_ms,
    }


# ── Event Store ────────────────────────────────────────────────────────────────


@router.get("/event-store/events")
async def query_event_store(
    aggregate_id: str | None = Query(None),
    event_name: str | None = Query(None),
    start: str | None = Query(None),
    end: str | None = Query(None),
    limit: int = Query(100, le=1000),
) -> list[dict]:
    if aggregate_id:
        events = _event_store.replay_aggregate(aggregate_id)
    elif event_name:
        events = _event_store.replay_by_name(event_name)
    elif start and end:
        start_dt = datetime.fromisoformat(start)
        end_dt = datetime.fromisoformat(end)
        events = _event_store.replay_by_time_range(start_dt, end_dt)
    else:
        events = _event_store.replay_all()

    return [
        {
            "event_id": e.event_id,
            "event_name": e.event_name,
            "aggregate_id": e.aggregate_id,
            "aggregate_type": e.aggregate_type,
            "version": e.version,
            "data": e.data,
            "metadata": e.metadata,
            "timestamp": e.timestamp.isoformat(),
            "correlation_id": e.correlation_id,
            "tenant_id": e.tenant_id,
        }
        for e in events[:limit]
    ]


# ── Warehouse ──────────────────────────────────────────────────────────────────


@router.get("/warehouse/query")
async def run_warehouse_query(
    dimensions: str = Query(""),
    measures: str = Query(""),
    group_by: str = Query(""),
    order_by: str = Query(""),
    order_desc: bool = Query(True),
    limit: int = Query(100, le=10000),
    offset: int = Query(0),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
) -> dict:
    query = WarehouseQuery(
        dimensions=[d.strip() for d in dimensions.split(",") if d.strip()],
        measures=[m.strip() for m in measures.split(",") if m.strip()],
        group_by=[g.strip() for g in group_by.split(",") if g.strip()],
        order_by=order_by,
        order_desc=order_desc,
        limit=limit,
        offset=offset,
        date_from=datetime.fromisoformat(date_from).date() if date_from else None,
        date_to=datetime.fromisoformat(date_to).date() if date_to else None,
    )
    return _warehouse.query(query)


# ── Mapping / FHIR conversion ──────────────────────────────────────────────────


@router.post("/canonical/map-patient")
async def map_fhir_patient(fhir_resource: dict[str, Any]) -> dict:
    canonical = map_patient(fhir_resource)
    return {
        "id": canonical.id,
        "names": canonical.names,
        "gender": canonical.gender,
        "birth_date": canonical.birth_date.isoformat() if canonical.birth_date else None,
        "identifiers": canonical.identifiers,
        "source_system": canonical.source_system,
    }


# ── Event Store summary ────────────────────────────────────────────────────────


@router.get("/event-store/summary")
async def event_store_summary() -> dict:
    return _event_store.get_stream_summary()
