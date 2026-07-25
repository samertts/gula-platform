from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app._compat import UTC
from app.health_data.warehouse.service import WarehouseQuery, WarehouseService

logger = logging.getLogger("gula.research_platform.open_apis")


@dataclass
class BulkExportResult:
    export_id: str
    resource_type: str
    format: str = "ndjson"
    record_count: int = 0
    file_urls: list[str] = field(default_factory=list)
    generated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    expires_at: datetime | None = None


class FHIRBulkExport:
    def __init__(self, warehouse: WarehouseService | None = None):
        self._warehouse = warehouse or WarehouseService()
        self._exports: dict[str, BulkExportResult] = {}

    def start_export(
        self,
        resource_type: str = "Patient",
        since: str = "",
        types: list[str] | None = None,
    ) -> BulkExportResult:
        import uuid

        export = BulkExportResult(
            export_id=str(uuid.uuid4()).replace("-", "").upper()[:26],
            resource_type=resource_type,
            format="ndjson",
        )
        self._exports[export.export_id] = export
        logger.info(
            "FHIR bulk export started: %s (type=%s)",
            export.export_id,
            resource_type,
        )
        return export

    def get_export_status(self, export_id: str) -> dict[str, Any]:
        export = self._exports.get(export_id)
        if not export:
            return {"error": "export not found"}
        return {
            "export_id": export.export_id,
            "resource_type": export.resource_type,
            "status": "completed" if export.file_urls else "running",
            "output": [
                {"type": export.resource_type, "url": url, "count": export.record_count}
                for url in export.file_urls
            ],
            "generated_at": export.generated_at.isoformat(),
        }

    def cancel_export(self, export_id: str) -> bool:
        if export_id in self._exports:
            del self._exports[export_id]
            return True
        return False


@dataclass
class ResearchAPIQuery:
    dataset: str
    filters: dict[str, Any] = field(default_factory=dict)
    columns: list[str] | None = None
    limit: int = 100
    offset: int = 0
    order_by: str = ""
    aggregation: str = ""


class ResearchAPI:
    def __init__(self, warehouse: WarehouseService | None = None):
        self._warehouse = warehouse or WarehouseService()
        self._queries: list[dict] = []

    def query_data(self, query: ResearchAPIQuery) -> dict[str, Any]:
        import time

        start = time.monotonic()
        wq = WarehouseQuery(
            filters=query.filters,
            limit=query.limit,
            offset=query.offset,
            order_by=query.order_by,
        )
        result = self._warehouse.query(wq)
        duration = round((time.monotonic() - start) * 1000, 1)

        record = {
            "dataset": query.dataset,
            "filters": query.filters,
            "result_size": result.get("returned_rows", 0),
            "duration_ms": duration,
            "timestamp": datetime.now(UTC).isoformat(),
        }
        self._queries.append(record)

        return {
            "data": result.get("rows", []),
            "metadata": {
                "dataset": query.dataset,
                "total_rows": result.get("total_rows", 0),
                "returned_rows": result.get("returned_rows", 0),
                "duration_ms": duration,
                "columns": query.columns or [],
            },
        }

    def get_dataset_info(self, dataset_name: str) -> dict[str, Any]:
        fact_data = self._warehouse.get_fact(dataset_name)
        dim_data = self._warehouse.get_dimension(dataset_name)
        total = len(fact_data) if fact_data else len(dim_data) if dim_data else 0
        return {
            "name": dataset_name,
            "record_count": total,
            "columns": list(fact_data[0].keys()) if fact_data else [],
            "available": bool(fact_data or dim_data),
        }

    def list_datasets(self) -> list[str]:
        return ["hd_wh_fact_encounter", "hd_wh_fact_lab_result", "hd_wh_fact_order"]

    def get_query_history(self, limit: int = 10) -> list[dict]:
        return self._queries[-limit:]


class StatisticsAPI:
    def __init__(self, warehouse: WarehouseService | None = None):
        self._warehouse = warehouse or WarehouseService()

    def descriptive(
        self,
        dataset: str,
        column: str,
        filters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        data = self._warehouse.get_fact(dataset)
        if filters:
            data = [r for r in data if all(r.get(k) == v for k, v in (filters or {}).items())]
        values = [r.get(column) for r in data if r.get(column) is not None]
        if not values:
            return {"error": "no data"}
        numeric = [v for v in values if isinstance(v, (int, float))]
        if not numeric:
            return {
                "count": len(values),
                "unique_values": len(set(values)),
            }
        import statistics

        n = len(numeric)
        return {
            "count": n,
            "mean": round(statistics.mean(numeric), 2),
            "median": round(statistics.median(numeric), 2),
            "stdev": round(statistics.stdev(numeric), 2) if n > 1 else 0,
            "min": round(min(numeric), 2),
            "max": round(max(numeric), 2),
            "q1": round(numeric[n // 4], 2) if n > 3 else numeric[0],
            "q3": round(numeric[3 * n // 4], 2) if n > 3 else numeric[-1],
        }

    def aggregation(
        self,
        dataset: str,
        measure: str,
        group_by: str | None = None,
        agg_func: str = "sum",
    ) -> dict[str, Any]:
        data = self._warehouse.get_fact(dataset)
        if group_by:
            groups: dict[str, float] = {}
            for r in data:
                key = str(r.get(group_by, "unknown"))
                val = r.get(measure, 0) or 0
                if agg_func == "sum":
                    groups[key] = groups.get(key, 0) + val
                elif agg_func == "count":
                    groups[key] = groups.get(key, 0) + 1
                elif agg_func == "avg":
                    groups.setdefault(key, 0)
                    groups[key] = (groups.get(key, 0) + val) / 2
            return {
                "aggregation": agg_func,
                "measure": measure,
                "group_by": group_by,
                "values": groups,
            }
        total = sum(r.get(measure, 0) or 0 for r in data)
        return {"aggregation": agg_func, "measure": measure, "value": total}

    def correlation(
        self,
        dataset: str,
        column_x: str,
        column_y: str,
    ) -> dict[str, Any]:
        data = self._warehouse.get_fact(dataset)
        pairs = [
            (r.get(column_x), r.get(column_y))
            for r in data
            if r.get(column_x) is not None and r.get(column_y) is not None
        ]
        if len(pairs) < 3:
            return {"error": "insufficient data for correlation"}
        import statistics

        xs = [p[0] for p in pairs]
        ys = [p[1] for p in pairs]
        try:
            r = statistics.correlation(xs, ys)
            return {
                "column_x": column_x,
                "column_y": column_y,
                "pearson_r": round(r, 4),
                "n": len(pairs),
                "interpretation": "strong"
                if abs(r) > 0.7
                else "moderate"
                if abs(r) > 0.4
                else "weak",
            }
        except Exception as exc:
            return {"error": str(exc)}


class OpenDataAPI:
    def __init__(self, warehouse: WarehouseService | None = None):
        self._warehouse = warehouse or WarehouseService()
        self._catalog: dict[str, dict] = {}

    def publish_dataset(
        self,
        name: str,
        description: str,
        category: str = "public_health",
        license: str = "CC-BY-4.0",
    ) -> dict[str, Any]:
        self._catalog[name] = {
            "name": name,
            "description": description,
            "category": category,
            "license": license,
            "published_at": datetime.now(UTC).isoformat(),
            "downloads": 0,
        }
        logger.info("Open data published: %s (license: %s)", name, license)
        return self._catalog[name]

    def list_datasets(self, category: str | None = None) -> list[dict]:
        if category:
            return [ds for ds in self._catalog.values() if ds.get("category") == category]
        return list(self._catalog.values())

    def get_dataset(self, name: str) -> dict | None:
        return self._catalog.get(name)

    def download(self, name: str, format: str = "json") -> dict[str, Any]:
        ds = self._catalog.get(name)
        if not ds:
            return {"error": "dataset not found"}
        ds["downloads"] = ds.get("downloads", 0) + 1
        data = self._warehouse.get_fact(name) or self._warehouse.get_dimension(name)
        return {
            "dataset": name,
            "format": format,
            "record_count": len(data),
            "data": data,
            "license": ds.get("license"),
        }

    def search_datasets(self, query: str) -> list[dict]:
        q = query.lower()
        return [
            ds
            for ds in self._catalog.values()
            if q in ds["name"].lower() or q in ds.get("description", "").lower()
        ]
