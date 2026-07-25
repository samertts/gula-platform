from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from app.health_data.data_lake.catalog import DataLakeCatalog
from app.health_data.data_lake.storage import StorageBackend

logger = logging.getLogger("gula.health_data.data_lake.query")


@dataclass
class QueryResult:
    columns: list[str]
    rows: list[list[Any]]
    total_rows: int
    returned_rows: int
    duration_ms: float
    scan_bytes: int = 0


@dataclass
class DataLakeQuery:
    catalog: DataLakeCatalog
    storage: StorageBackend

    async def query(
        self,
        dataset: str,
        columns: list[str] | None = None,
        filters: dict[str, Any] | None = None,
        partition_filter: dict[str, str] | None = None,
        limit: int = 1000,
        offset: int = 0,
    ) -> QueryResult:
        import json
        import time

        start = time.monotonic()

        ds = self.catalog.get(dataset)
        if not ds:
            raise ValueError(f"Dataset not found: {dataset}")

        partitions = ds.partitions
        if partition_filter:
            partitions = [
                p
                for p in partitions
                if all(p.key.startswith(f"{k}={v}") for k, v in partition_filter.items())
            ]

        all_records: list[dict] = []
        scan_bytes = 0

        for part in partitions:
            try:
                data = await self.storage.read(part.path)
                scan_bytes += len(data)
                payload = json.loads(data.decode("utf-8"))
                records = payload.get("records", [])
                all_records.extend(records)
            except Exception as exc:
                logger.warning("Skipping partition %s: %s", part.key, exc)

        if filters:
            filtered = []
            for rec in all_records:
                match = True
                for key, value in filters.items():
                    if key not in rec or rec[key] != value:
                        match = False
                        break
                if match:
                    filtered.append(rec)
            all_records = filtered

        if columns:
            projected = []
            for rec in all_records:
                projected.append({k: rec.get(k) for k in columns if k in rec})
            all_records = projected

        total = len(all_records)
        page = all_records[offset : offset + limit]

        rows = []
        col_names = columns or (list(all_records[0].keys()) if all_records else [])
        for rec in page:
            rows.append([rec.get(c) for c in col_names])

        duration = (time.monotonic() - start) * 1000

        return QueryResult(
            columns=col_names,
            rows=rows,
            total_rows=total,
            returned_rows=len(rows),
            duration_ms=round(duration, 1),
            scan_bytes=scan_bytes,
        )
