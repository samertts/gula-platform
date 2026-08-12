from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app._compat import UTC
from app.health_data.enums import DataClassification, DataQuality, StorageTier

logger = logging.getLogger("gula.health_data.data_lake.catalog")


@dataclass
class PartitionMetadata:
    key: str
    path: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    row_count: int = 0
    size_bytes: int = 0
    format: str = "parquet"


@dataclass
class DatasetMetadata:
    name: str
    description: str = ""
    schema: dict[str, str] = field(default_factory=dict)
    partitions: list[PartitionMetadata] = field(default_factory=list)
    classification: DataClassification = DataClassification.INTERNAL
    quality: DataQuality = DataQuality.RAW
    storage_tier: StorageTier = StorageTier.HOT
    source_system: str = ""
    owner: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    record_count: int = 0
    size_bytes: int = 0
    retention_days: int = 365
    tags: list[str] = field(default_factory=list)
    extension: dict[str, Any] = field(default_factory=dict)


class DataLakeCatalog:
    _datasets: dict[str, DatasetMetadata] = {}

    def register(self, dataset: DatasetMetadata) -> None:
        self._datasets[dataset.name] = dataset
        logger.info("Dataset registered: %s", dataset.name)

    def get(self, name: str) -> DatasetMetadata | None:
        return self._datasets.get(name)

    def list(self, pattern: str | None = None) -> list[DatasetMetadata]:
        if not pattern:
            return list(self._datasets.values())
        return [ds for ds in self._datasets.values() if pattern.lower() in ds.name.lower()]

    def remove(self, name: str) -> bool:
        if name in self._datasets:
            del self._datasets[name]
            logger.info("Dataset removed: %s", name)
            return True
        return False

    def add_partition(self, dataset_name: str, partition: PartitionMetadata) -> None:
        ds = self.get(dataset_name)
        if not ds:
            raise ValueError(f"Dataset not found: {dataset_name}")
        ds.partitions.append(partition)
        ds.updated_at = datetime.now(UTC)

    def get_schema(self, dataset_name: str) -> dict[str, str] | None:
        ds = self.get(dataset_name)
        return ds.schema if ds else None

    def update_stats(self, dataset_name: str, record_count: int | None = None, size_bytes: int | None = None) -> None:
        ds = self.get(dataset_name)
        if not ds:
            raise ValueError(f"Dataset not found: {dataset_name}")
        if record_count is not None:
            ds.record_count = record_count
        if size_bytes is not None:
            ds.size_bytes = size_bytes
        ds.updated_at = datetime.now(UTC)
