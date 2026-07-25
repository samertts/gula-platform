from __future__ import annotations

import hashlib
import json
import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from app._compat import UTC
from app.health_data.data_lake.catalog import DataLakeCatalog, DatasetMetadata, PartitionMetadata
from app.health_data.data_lake.storage import StorageBackend
from app.health_data.enums import DataClassification, DataQuality, StorageTier

logger = logging.getLogger("gula.health_data.data_lake.ingestion")


@dataclass
class IngestionResult:
    dataset: str
    partition_key: str
    records_written: int
    bytes_written: int
    checksum: str
    duration_ms: float
    error: str | None = None


class IngestionPipeline:
    def __init__(self, catalog: DataLakeCatalog, storage: StorageBackend):
        self.catalog = catalog
        self.storage = storage
        self._validators: list[Callable[[list[dict]], list[str]]] = []

    def register_validator(self, validator: Callable[[list[dict]], list[str]]) -> None:
        self._validators.append(validator)

    async def ingest(
        self,
        dataset_name: str,
        records: list[dict],
        source_system: str = "",
        classification: DataClassification = DataClassification.INTERNAL,
        quality: DataQuality = DataQuality.RAW,
        storage_tier: StorageTier = StorageTier.HOT,
        partition_by: str | None = None,
        schema: dict[str, str] | None = None,
    ) -> IngestionResult:
        import time

        start = time.monotonic()

        for validator in self._validators:
            errors = validator(records)
            if errors:
                raise ValueError(f"Validation failed: {'; '.join(errors)}")

        ds = self.catalog.get(dataset_name)
        if not ds:
            ds = DatasetMetadata(
                name=dataset_name,
                source_system=source_system,
                classification=classification,
                quality=quality,
                storage_tier=storage_tier,
                schema=schema or {},
            )
            self.catalog.register(ds)

        partition_key = _build_partition_key(partition_by)

        payload = json.dumps(
            {"records": records, "ingested_at": datetime.now(UTC).isoformat()}, default=str
        )
        payload_bytes = payload.encode("utf-8")
        checksum = hashlib.sha256(payload_bytes).hexdigest()

        file_path = (
            f"{dataset_name}/{partition_key}/data_{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}.json"
        )
        await self.storage.write(file_path, payload_bytes)

        partition = PartitionMetadata(
            key=partition_key,
            path=file_path,
            row_count=len(records),
            size_bytes=len(payload_bytes),
        )
        self.catalog.add_partition(dataset_name, partition)
        self.catalog.update_stats(dataset_name, record_count=ds.record_count + len(records))

        duration = (time.monotonic() - start) * 1000

        logger.info(
            "Ingested %d records into %s/%s (%d bytes) in %.1fms",
            len(records),
            dataset_name,
            partition_key,
            len(payload_bytes),
            duration,
        )

        return IngestionResult(
            dataset=dataset_name,
            partition_key=partition_key,
            records_written=len(records),
            bytes_written=len(payload_bytes),
            checksum=checksum,
            duration_ms=round(duration, 1),
        )


def _build_partition_key(partition_by: str | None = None) -> str:
    now = datetime.now(UTC)
    if partition_by == "year":
        return f"year={now.year}"
    if partition_by == "month":
        return f"year={now.year}/month={now.month:02d}"
    if partition_by == "day":
        return f"year={now.year}/month={now.month:02d}/day={now.day:02d}"
    if partition_by == "hour":
        return f"year={now.year}/month={now.month:02d}/day={now.day:02d}/hour={now.hour:02d}"
    return f"ingested={now.strftime('%Y%m%d')}"
