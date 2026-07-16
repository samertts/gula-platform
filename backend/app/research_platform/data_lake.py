from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app._compat import UTC
from app.health_data.data_lake import (
    DataLakeCatalog,
    DataLakeQuery,
    DatasetMetadata,
    IngestionPipeline,
    LocalStorageBackend,
    StorageBackend,
)
from app.health_data.enums import DataClassification, DataQuality, StorageTier

logger = logging.getLogger("gula.research_platform.data_lake")


@dataclass
class DataLineageEntry:
    dataset: str
    source_system: str
    transformation: str
    input_datasets: list[str] = field(default_factory=list)
    output_datasets: list[str] = field(default_factory=list)
    transformation_details: dict[str, Any] = field(default_factory=dict)
    run_id: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class DataCatalog:
    def __init__(self, catalog: DataLakeCatalog | None = None):
        self._inner = catalog or DataLakeCatalog()

    def register_dataset(
        self,
        name: str,
        description: str = "",
        schema: dict[str, str] | None = None,
        classification: DataClassification = DataClassification.INTERNAL,
        quality: DataQuality = DataQuality.RAW,
        storage_tier: StorageTier = StorageTier.HOT,
        source_system: str = "",
        owner: str = "",
        tags: list[str] | None = None,
    ) -> DatasetMetadata:
        ds = DatasetMetadata(
            name=name,
            description=description,
            schema=schema or {},
            classification=classification,
            quality=quality,
            storage_tier=storage_tier,
            source_system=source_system,
            owner=owner,
            tags=tags or [],
        )
        self._inner.register(ds)
        return ds

    def get(self, name: str) -> DatasetMetadata | None:
        return self._inner.get(name)

    def list(self, pattern: str | None = None) -> list[DatasetMetadata]:
        return self._inner.list(pattern)

    def search(self, query: str) -> list[DatasetMetadata]:
        return [
            ds for ds in self._inner.list()
            if query.lower() in ds.name.lower()
            or query.lower() in ds.description.lower()
            or any(query.lower() in t.lower() for t in ds.tags)
        ]


class DataLineage:
    def __init__(self):
        self._entries: dict[str, list[DataLineageEntry]] = {}

    def trace(self, dataset: str) -> dict[str, Any]:
        entries = self._entries.get(dataset, [])
        return {
            "dataset": dataset,
            "entries": [
                {
                    "source_system": e.source_system,
                    "transformation": e.transformation,
                    "input_datasets": e.input_datasets,
                    "output_datasets": e.output_datasets,
                    "run_id": e.run_id,
                    "created_at": e.created_at.isoformat(),
                }
                for e in entries
            ],
            "provenance_count": len(entries),
        }

    def add_entry(self, entry: DataLineageEntry) -> None:
        self._entries.setdefault(entry.dataset, []).append(entry)
        logger.info("Lineage entry added for dataset: %s", entry.dataset)

    def upstream(self, dataset: str) -> list[str]:
        sources: set[str] = set()
        for entry in self._entries.get(dataset, []):
            sources.update(entry.input_datasets)
        return list(sources)

    def downstream(self, dataset: str) -> list[str]:
        targets: set[str] = set()
        for ds, entries in self._entries.items():
            for entry in entries:
                if dataset in entry.input_datasets:
                    targets.add(ds)
        return list(targets)


@dataclass
class DatasetVersion:
    version_id: str
    dataset: str
    version: str
    checksum: str
    record_count: int
    size_bytes: int
    schema_snapshot: dict[str, str] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = field(default_factory=dict)


class DataVersioning:
    def __init__(self):
        self._versions: dict[str, list[DatasetVersion]] = {}

    def snapshot(
        self,
        dataset: str,
        records: list[dict],
        schema: dict[str, str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> DatasetVersion:
        payload = str(records).encode("utf-8")
        checksum = hashlib.sha256(payload).hexdigest()[:16]

        existing = self._versions.get(dataset, [])
        version_num = len(existing) + 1
        version_str = f"v{version_num}"

        sv = DatasetVersion(
            version_id=f"{dataset}@{version_str}",
            dataset=dataset,
            version=version_str,
            checksum=checksum,
            record_count=len(records),
            size_bytes=len(payload),
            schema_snapshot=schema or {},
            metadata=metadata or {},
        )
        self._versions.setdefault(dataset, []).append(sv)
        logger.info("Dataset versioned: %s@%s (%d records)", dataset, version_str, len(records))
        return sv

    def list_versions(self, dataset: str) -> list[DatasetVersion]:
        return list(self._versions.get(dataset, []))

    def get_version(self, dataset: str, version: str) -> DatasetVersion | None:
        for v in self._versions.get(dataset, []):
            if v.version == version:
                return v
        return None

    def rollback(self, dataset: str, version: str) -> DatasetVersion | None:
        versions = self._versions.get(dataset, [])
        for i, v in enumerate(versions):
            if v.version == version:
                return versions[i - 1] if i > 0 else None
        return None


class ImmutableArchive:
    def __init__(self, storage: StorageBackend | None = None):
        self._storage = storage or LocalStorageBackend("/data/research/archive")

    async def archive(
        self,
        dataset: str,
        records: list[dict],
        classification: DataClassification = DataClassification.RESTRICTED,
    ) -> dict[str, Any]:
        import json

        now = datetime.now(UTC)
        timestamp = now.strftime("%Y%m%d_%H%M%S")
        payload = json.dumps(
            {"records": records, "archived_at": now.isoformat(), "dataset": dataset},
            default=str,
        ).encode("utf-8")
        checksum = hashlib.sha256(payload).hexdigest()
        archive_path = f"immutable/{dataset}/{timestamp}_{checksum[:8]}.json"
        await self._storage.write(archive_path, payload)
        logger.info("Archive written: %s (%d bytes)", archive_path, len(payload))
        return {
            "archive_path": archive_path,
            "record_count": len(records),
            "checksum": checksum,
            "size_bytes": len(payload),
            "archived_at": now.isoformat(),
        }

    async def retrieve(self, archive_path: str) -> list[dict]:
        import json

        data = await self._storage.read(archive_path)
        payload = json.loads(data.decode("utf-8"))
        return payload.get("records", [])

    async def list_archives(self, dataset: str) -> list[str]:
        prefix = f"immutable/{dataset}/"
        return await self._storage.list(prefix)


class DataLakeManager:
    def __init__(
        self,
        catalog: DataLakeCatalog | None = None,
        storage: StorageBackend | None = None,
    ):
        self.catalog = DataCatalog(catalog)
        inner_storage = storage or LocalStorageBackend()
        self.storage = inner_storage
        self.ingestion = IngestionPipeline(catalog or DataLakeCatalog(), inner_storage)
        self.query_engine = DataLakeQuery(catalog or DataLakeCatalog(), inner_storage)
        self.lineage = DataLineage()
        self.versioning = DataVersioning()
        self.archive = ImmutableArchive(inner_storage)

    async def search_datasets(self, query: str) -> list[DatasetMetadata]:
        return self.catalog.search(query)

    async def get_lineage(self, dataset: str) -> dict[str, Any]:
        return self.lineage.trace(dataset)

    async def get_versions(self, dataset: str) -> list[DatasetVersion]:
        return self.versioning.list_versions(dataset)

    async def snapshot_dataset(
        self,
        dataset: str,
        records: list[dict],
        schema: dict[str, str] | None = None,
    ) -> DatasetVersion:
        return self.versioning.snapshot(dataset, records, schema)

    async def to_storage_tier(
        self,
        dataset: str,
        target_tier: StorageTier,
    ) -> None:
        ds = self.catalog.get(dataset)
        if ds:
            ds.storage_tier = target_tier
            logger.info("Dataset %s moved to tier: %s", dataset, target_tier.value)
